"""
Run repository for BioinfoFlow.

This module provides database operations for workflow runs.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..models.run import Run


class RunRepository:
    """
    Run repository class.
    
    Provides database operations for workflow runs.
    """
    
    def __init__(self, session: Session):
        """
        Initialize run repository.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(
        self,
        workflow_id: int,
        run_id: str,
        run_dir: str,
        status: str = "RUNNING",
        inputs: Optional[Dict[str, Any]] = None
    ) -> Run:
        """
        Create a new run.
        
        Args:
            workflow_id: ID of the workflow
            run_id: Unique identifier for the run
            run_dir: Directory path for run outputs
            status: Initial run status (default: "RUNNING")
            inputs: Input parameters as a dictionary
            
        Returns:
            Created run
        """
        run = Run(
            workflow_id=workflow_id,
            run_id=run_id,
            status=status,
            run_dir=run_dir,
            inputs=inputs,
            start_time=datetime.now(datetime.timezone.utc)
        )
        
        try:
            self.session.add(run)
            self.session.commit()
            self.session.refresh(run)
            logger.info(f"Created run with ID {run.id} and run_id {run_id}")
            return run
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create run: {e}")
            raise
    
    def get_by_id(self, run_id: int) -> Optional[Run]:
        """
        Get run by ID.
        
        Args:
            run_id: Run ID
            
        Returns:
            Run or None if not found
        """
        return self.session.query(Run).filter(Run.id == run_id).first()
    
    def get_by_run_id(self, run_id: str) -> Optional[Run]:
        """
        Get run by run_id (string identifier).
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run or None if not found
        """
        return self.session.query(Run).filter(Run.run_id == run_id).first()
    
    def get_by_workflow_id(self, workflow_id: int) -> List[Run]:
        """
        Get all runs for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of runs
        """
        return self.session.query(Run).filter(Run.workflow_id == workflow_id).all()
    
    def get_all(self) -> List[Run]:
        """
        Get all runs.
        
        Returns:
            List of all runs
        """
        return self.session.query(Run).all()
    
    def update_status(self, run_id: str, status: str, end_time: Optional[datetime] = None) -> Optional[Run]:
        """
        Update run status.
        
        Args:
            run_id: Run identifier
            status: New status
            end_time: End time (set automatically for completed/failed status)
            
        Returns:
            Updated run or None if not found
        """
        run = self.get_by_run_id(run_id)
        if not run:
            logger.warning(f"Run with run_id {run_id} not found for status update")
            return None
        
        run.status = status
        
        # Set end time automatically for terminal states
        if status in ["COMPLETED", "FAILED"] and not run.end_time:
            run.end_time = end_time or datetime.now(datetime.timezone.utc)
        
        try:
            self.session.commit()
            self.session.refresh(run)
            logger.info(f"Updated run {run_id} status to {status}")
            return run
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update run status: {e}")
            raise
    
    def update(self, run_id: str, **kwargs) -> Optional[Run]:
        """
        Update run.
        
        Args:
            run_id: Run identifier
            **kwargs: Fields to update
            
        Returns:
            Updated run or None if not found
        """
        run = self.get_by_run_id(run_id)
        if not run:
            logger.warning(f"Run with run_id {run_id} not found for update")
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        
        try:
            self.session.commit()
            self.session.refresh(run)
            logger.info(f"Updated run with run_id {run_id}")
            return run
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update run: {e}")
            raise
    
    def delete(self, run_id: str) -> bool:
        """
        Delete run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            True if deleted, False if not found
        """
        run = self.get_by_run_id(run_id)
        if not run:
            logger.warning(f"Run with run_id {run_id} not found for deletion")
            return False
        
        try:
            self.session.delete(run)
            self.session.commit()
            logger.info(f"Deleted run with run_id {run_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete run: {e}")
            raise 