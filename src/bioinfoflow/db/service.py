"""
Database service module for BioinfoFlow.

This module provides a unified interface for database operations,
integrating with the workflow execution system.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from loguru import logger

from bioinfoflow.core.models import StepStatus
from .config import get_db_session
from .repositories.workflow_repository import WorkflowRepository
from .repositories.run_repository import RunRepository
from .repositories.step_repository import StepRepository


class DatabaseService:
    """
    Database service class.
    
    Provides a unified interface for database operations.
    """
    
    @staticmethod
    def store_workflow(yaml_path: Path, session: Optional[Session] = None) -> int:
        """
        Store workflow definition in database.
        
        Args:
            yaml_path: Path to workflow YAML file
            session: Optional database session
            
        Returns:
            Workflow ID in the database
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            # Read workflow YAML file
            with open(yaml_path, 'r') as f:
                yaml_content = f.read()
            
            # Extract workflow metadata from file content
            import yaml
            workflow_dict = yaml.safe_load(yaml_content)
            name = workflow_dict.get('name', '')
            version = workflow_dict.get('version', '')
            description = workflow_dict.get('description', '')
            
            # Check if workflow already exists
            workflow_repo = WorkflowRepository(session)
            existing_workflow = workflow_repo.get_by_name_version(name, version)
            
            if existing_workflow:
                logger.info(f"Workflow '{name}' v{version} already exists with ID {existing_workflow.id}")
                return existing_workflow.id
            
            # Create new workflow
            workflow = workflow_repo.create(
                name=name,
                version=version,
                yaml_content=yaml_content,
                description=description
            )
            
            return workflow.id
            
        except Exception as e:
            logger.error(f"Failed to store workflow: {e}")
            raise
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def create_run(
        workflow_id: int,
        run_id: str,
        run_dir: str,
        inputs: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> int:
        """
        Create run record in database.
        
        Args:
            workflow_id: Workflow ID
            run_id: Run identifier
            run_dir: Run directory
            inputs: Input parameters
            session: Optional database session
            
        Returns:
            Run ID in the database
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            run_repo = RunRepository(session)
            run = run_repo.create(
                workflow_id=workflow_id,
                run_id=run_id,
                run_dir=run_dir,
                status="RUNNING",
                inputs=inputs
            )
            
            return run.id
            
        except Exception as e:
            logger.error(f"Failed to create run record: {e}")
            raise
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def update_run_status(
        run_id: str,
        status: str,
        session: Optional[Session] = None
    ) -> bool:
        """
        Update run status in database.
        
        Args:
            run_id: Run identifier
            status: New status
            session: Optional database session
            
        Returns:
            True if successful, False otherwise
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            run_repo = RunRepository(session)
            run = run_repo.update_status(run_id, status)
            return run is not None
            
        except Exception as e:
            logger.error(f"Failed to update run status: {e}")
            return False
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def create_step(
        db_run_id: int,
        step_name: str,
        session: Optional[Session] = None
    ) -> int:
        """
        Create step record in database.
        
        Args:
            db_run_id: Run ID in the database
            step_name: Step name
            session: Optional database session
            
        Returns:
            Step ID in the database
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            step_repo = StepRepository(session)
            step = step_repo.create(
                run_id=db_run_id,
                step_name=step_name,
                status="PENDING"
            )
            
            return step.id
            
        except Exception as e:
            logger.error(f"Failed to create step record: {e}")
            raise
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def update_step_status(
        step_id: int,
        status: str,
        log_file: Optional[str] = None,
        outputs: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session: Optional[Session] = None
    ) -> bool:
        """
        Update step status in database.
        
        Args:
            step_id: Step ID
            status: New status
            log_file: Log file path
            outputs: Step outputs
            start_time: Start time
            end_time: End time
            session: Optional database session
            
        Returns:
            True if successful, False otherwise
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            step_repo = StepRepository(session)
            
            # Update status
            step = step_repo.update_status(
                step_id=step_id,
                status=status,
                start_time=start_time,
                end_time=end_time
            )
            
            if not step:
                return False
            
            # Update other fields if provided
            updates = {}
            if log_file is not None:
                updates['log_file'] = log_file
            if outputs is not None:
                updates['outputs'] = outputs
            
            if updates:
                step = step_repo.update(step_id, **updates)
            
            return step is not None
            
        except Exception as e:
            logger.error(f"Failed to update step status: {e}")
            return False
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def get_run_steps(run_id: str, session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Get steps for a run.
        
        Args:
            run_id: Run identifier
            session: Optional database session
            
        Returns:
            List of step dictionaries
        """
        close_session = False
        if session is None:
            session = next(get_db_session())
            close_session = True
        
        try:
            # Get database run ID
            run_repo = RunRepository(session)
            run = run_repo.get_by_run_id(run_id)
            
            if not run:
                return []
            
            # Get steps
            step_repo = StepRepository(session)
            steps = step_repo.get_by_run_id(run.id)
            
            # Convert to dictionaries
            step_dicts = []
            for step in steps:
                step_dict = {
                    'id': step.id,
                    'step_name': step.step_name,
                    'status': step.status,
                    'start_time': step.start_time,
                    'end_time': step.end_time,
                    'log_file': step.log_file,
                    'outputs': step.outputs
                }
                step_dicts.append(step_dict)
            
            return step_dicts
            
        except Exception as e:
            logger.error(f"Failed to get run steps: {e}")
            return []
        finally:
            if close_session:
                session.close()
    
    @staticmethod
    def map_step_status(step_status: StepStatus) -> str:
        """
        Map internal step status to database status.
        
        Args:
            step_status: Internal step status
            
        Returns:
            Database status string
        """
        # Simple mapping for now
        mapping = {
            StepStatus.PENDING: "PENDING",
            StepStatus.RUNNING: "RUNNING",
            StepStatus.COMPLETED: "COMPLETED",
            StepStatus.FAILED: "FAILED",
            StepStatus.TERMINATED_TIME_LIMIT: "TERMINATED_TIME_LIMIT",
            StepStatus.SKIPPED: "SKIPPED",
            StepStatus.ERROR: "ERROR"
        }
        
        return mapping.get(step_status, "UNKNOWN") 