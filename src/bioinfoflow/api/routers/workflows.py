"""
Workflow router for BioinfoFlow API.

This module provides API endpoints for workflow management.
"""
import tempfile
import yaml
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from bioinfoflow.core.workflow import Workflow
from bioinfoflow.execution.executor import WorkflowExecutor
from bioinfoflow.api.models.workflows import (
    WorkflowSummary, 
    WorkflowDetail, 
    WorkflowCreate,
    WorkflowRunRequest
)
from bioinfoflow.api.models.runs import RunSummary
from bioinfoflow.api.dependencies import (
    get_db, 
    get_workflow_repository,
    get_run_repository,
    get_config,
    has_database
)

# Check if database is available
if not has_database:
    raise ImportError("Database module not available, API cannot function without it")

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={404: {"description": "Workflow not found"}},
)


@router.get("/", response_model=List[WorkflowSummary])
async def list_workflows(
    db: Session = Depends(get_db)
):
    """
    List all workflows.
    
    Returns:
        List of workflow summaries
    """
    workflow_repo = get_workflow_repository(db)
    workflows = workflow_repo.get_all()
    
    result = []
    for workflow in workflows:
        # Get run count
        run_repo = get_run_repository(db)
        runs = run_repo.get_by_workflow_id(workflow.id)
        
        result.append(WorkflowSummary(
            id=workflow.id,
            name=workflow.name,
            version=workflow.version,
            description=workflow.description,
            created_at=workflow.created_at,
            run_count=len(runs)
        ))
    
    return result


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Detailed workflow information
    """
    workflow_repo = get_workflow_repository(db)
    db_workflow = workflow_repo.get_by_id(workflow_id)
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Parse YAML content to get step information
    try:
        workflow_dict = yaml.safe_load(db_workflow.yaml_content)
        core_workflow = Workflow.from_dict(workflow_dict)
        
        # Create detail model
        return WorkflowDetail.from_core_workflow(
            core_workflow,
            db_workflow.id,
            db_workflow.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse workflow: {str(e)}"
        )


@router.post("/", response_model=WorkflowDetail)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new workflow.
    
    Args:
        workflow: Workflow creation data
        
    Returns:
        Created workflow details
    """
    workflow_repo = get_workflow_repository(db)
    
    # Check if workflow with same name and version already exists
    existing = workflow_repo.get_by_name_version(
        workflow.name, 
        workflow.version
    )
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Workflow '{workflow.name}' v{workflow.version} already exists"
        )
    
    # Validate YAML content
    try:
        workflow_dict = yaml.safe_load(workflow.yaml_content)
        core_workflow = Workflow.from_dict(workflow_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid workflow definition: {str(e)}"
        )
    
    # Create workflow in database
    db_workflow = workflow_repo.create(
        name=workflow.name,
        version=workflow.version,
        yaml_content=workflow.yaml_content,
        description=workflow.description
    )
    
    # Return created workflow
    return WorkflowDetail.from_core_workflow(
        core_workflow,
        db_workflow.id,
        db_workflow.created_at
    )


def _run_workflow_background(
    workflow_id: int,
    run_req: WorkflowRunRequest,
    config_base_dir: Optional[str] = None
):
    """
    Background task to run a workflow.
    
    Args:
        workflow_id: ID of the workflow to run
        run_req: Run request parameters
        config_base_dir: Optional base directory for configuration
    """
    try:
        # Get workflow from database
        db = next(get_db())
        workflow_repo = get_workflow_repository(db)
        db_workflow = workflow_repo.get_by_id(workflow_id)
        
        if not db_workflow:
            raise ValueError(f"Workflow with ID {workflow_id} not found")
        
        # Create a temporary YAML file for the workflow
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            tmp.write(db_workflow.yaml_content)
            tmp_path = tmp.name
        
        try:
            # Load workflow from temporary file
            workflow = Workflow(tmp_path)
            
            # Create executor
            executor = WorkflowExecutor(workflow, run_req.inputs)
            
            # Execute workflow
            executor.execute(
                max_parallel=run_req.parallel,
                enable_time_limits=run_req.enable_time_limits,
                default_time_limit=run_req.default_time_limit
            )
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
            
    except Exception as e:
        # Log error
        from loguru import logger
        logger.error(f"Background workflow execution failed: {e}")


@router.post("/{workflow_id}/run", response_model=RunSummary)
async def run_workflow(
    workflow_id: int,
    run_req: WorkflowRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    config = Depends(get_config)
):
    """
    Run a workflow.
    
    Args:
        workflow_id: ID of the workflow to run
        run_req: Run request parameters
        
    Returns:
        Summary of the created run
    """
    workflow_repo = get_workflow_repository(db)
    db_workflow = workflow_repo.get_by_id(workflow_id)
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create a temporary YAML file for the workflow
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp.write(db_workflow.yaml_content)
        tmp_path = tmp.name
    
    try:
        # Load workflow from temporary file to generate run_id
        workflow = Workflow(tmp_path)
        
        # Create executor (don't execute yet)
        executor = WorkflowExecutor(workflow, run_req.inputs)
        
        # Get run_id and run_dir
        run_id = executor.run_id
        run_dir = executor.dirs["run_dir"]
        
        # Create run record in database
        run_repo = get_run_repository(db)
        run = run_repo.create(
            workflow_id=workflow_id,
            run_id=run_id,
            run_dir=str(run_dir),
            status="PENDING",
            inputs=run_req.inputs
        )
        
        # Start background execution
        background_tasks.add_task(
            _run_workflow_background, 
            workflow_id, 
            run_req,
            str(config.base_dir)
        )
        
        # Return run summary
        return RunSummary(
            id=run.id,
            run_id=run.run_id,
            workflow_id=workflow_id,
            workflow_name=db_workflow.name,
            workflow_version=db_workflow.version,
            status=run.status,
            start_time=run.start_time
        )
    
    except Exception as e:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        ) 