"""
Runs router for BioinfoFlow API.

This module provides API endpoints for run management.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from bioinfoflow.core.models import StepStatus
from bioinfoflow.api.models.runs import RunSummary, RunDetail, StepDetail, RunResumeRequest
from bioinfoflow.api.dependencies import (
    get_db,
    get_workflow_repository,
    get_run_repository,
    get_step_repository,
    has_database
)

# Check if database is available
if not has_database:
    raise ImportError("Database module not available, API cannot function without it")

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    responses={404: {"description": "Run not found"}},
)


@router.get("/", response_model=List[RunSummary])
async def list_runs(
    workflow_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    List all runs, optionally filtered by workflow.
    
    Args:
        workflow_id: Optional workflow ID to filter by
        
    Returns:
        List of run summaries
    """
    run_repo = get_run_repository(db)
    workflow_repo = get_workflow_repository(db)
    
    if workflow_id:
        # Check if workflow exists
        workflow = workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        runs = run_repo.get_by_workflow_id(workflow_id)
    else:
        runs = run_repo.get_all()
    
    result = []
    for run in runs:
        # Get workflow
        workflow = workflow_repo.get_by_id(run.workflow_id)
        
        # Calculate duration if run has ended
        duration = None
        if run.end_time:
            duration = str(run.end_time - run.start_time)
        
        result.append(RunSummary(
            id=run.id,
            run_id=run.run_id,
            workflow_id=run.workflow_id,
            workflow_name=workflow.name,
            workflow_version=workflow.version,
            status=run.status,
            start_time=run.start_time,
            end_time=run.end_time,
            duration=duration
        ))
    
    return result


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a run.
    
    Args:
        run_id: ID of the run
        
    Returns:
        Detailed run information
    """
    run_repo = get_run_repository(db)
    workflow_repo = get_workflow_repository(db)
    step_repo = get_step_repository(db)
    
    # Get run
    run = run_repo.get_by_run_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get workflow
    workflow = workflow_repo.get_by_id(run.workflow_id)
    
    # Get steps
    steps = step_repo.get_by_run_id(run.id)
    
    # Calculate duration if run has ended
    duration = None
    if run.end_time:
        duration = str(run.end_time - run.start_time)
    
    # Prepare steps detail
    steps_detail = {}
    for step in steps:
        # Calculate duration if step has ended
        step_duration = None
        if step.start_time and step.end_time:
            step_duration = str(step.end_time - step.start_time)
        
        # Create step detail
        steps_detail[step.step_name] = StepDetail(
            id=step.id,
            step_name=step.step_name,
            status=step.status,
            start_time=step.start_time,
            end_time=step.end_time,
            duration=step_duration,
            log_file=step.log_file,
            outputs=step.outputs
        )
    
    return RunDetail(
        id=run.id,
        run_id=run.run_id,
        workflow_id=run.workflow_id,
        workflow_name=workflow.name,
        workflow_version=workflow.version,
        status=run.status,
        start_time=run.start_time,
        end_time=run.end_time,
        duration=duration,
        steps=steps_detail,
        inputs=run.inputs,
        run_dir=run.run_dir
    )


@router.get("/{run_id}/steps", response_model=Dict[str, StepDetail])
async def get_run_steps(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get steps for a run.
    
    Args:
        run_id: ID of the run
        
    Returns:
        Dictionary mapping step names to step details
    """
    run_repo = get_run_repository(db)
    step_repo = get_step_repository(db)
    
    # Get run
    run = run_repo.get_by_run_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get steps
    steps = step_repo.get_by_run_id(run.id)
    
    # Prepare response
    result = {}
    for step in steps:
        # Calculate duration if step has ended
        step_duration = None
        if step.start_time and step.end_time:
            step_duration = str(step.end_time - step.start_time)
        
        # Create step detail
        result[step.step_name] = StepDetail(
            id=step.id,
            step_name=step.step_name,
            status=step.status,
            start_time=step.start_time,
            end_time=step.end_time,
            duration=step_duration,
            log_file=step.log_file,
            outputs=step.outputs
        )
    
    return result


@router.delete("/{run_id}", status_code=204)
async def delete_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a run.
    
    Args:
        run_id: ID of the run to delete
    """
    run_repo = get_run_repository(db)
    
    # Get run
    run = run_repo.get_by_run_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Can only delete completed or failed runs
    if run.status not in ["COMPLETED", "FAILED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete run with status {run.status}. "
                   f"Only completed or failed runs can be deleted."
        )
    
    # Delete run
    success = run_repo.delete(run_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete run"
        )


@router.post("/{run_id}/resume", response_model=RunSummary)
async def resume_run(
    run_id: str,
    resume_req: RunResumeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resume a failed run.
    
    Args:
        run_id: ID of the run to resume
        resume_req: Resume request parameters
        
    Returns:
        Summary of the resumed run
    """
    # PLACEHOLDER FOR MVP - Resume functionality will be implemented in future versions
    raise HTTPException(
        status_code=501,
        detail="Resume functionality not implemented yet"
    ) 