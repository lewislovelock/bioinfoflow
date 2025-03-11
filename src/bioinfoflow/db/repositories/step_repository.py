"""
Step repository for BioinfoFlow.

This module provides database operations for workflow steps.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..models.step import Step


class StepRepository:
    """
    Step repository class.
    
    Provides database operations for workflow steps.
    """
    
    def __init__(self, session: Session):
        """
        Initialize step repository.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(
        self,
        run_id: int,
        step_name: str,
        status: str = "PENDING",
        log_file: Optional[str] = None,
        outputs: Optional[Dict[str, Any]] = None
    ) -> Step:
        """
        Create a new step.
        
        Args:
            run_id: ID of the run
            step_name: Name of the step
            status: Initial step status (default: "PENDING")
            log_file: Path to log file
            outputs: Step outputs as dictionary
            
        Returns:
            Created step
        """
        step = Step(
            run_id=run_id,
            step_name=step_name,
            status=status,
            log_file=log_file,
            outputs=outputs
        )
        
        try:
            self.session.add(step)
            self.session.commit()
            self.session.refresh(step)
            logger.info(f"Created step '{step_name}' with ID {step.id}")
            return step
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create step: {e}")
            raise
    
    def get_by_id(self, step_id: int) -> Optional[Step]:
        """
        Get step by ID.
        
        Args:
            step_id: Step ID
            
        Returns:
            Step or None if not found
        """
        return self.session.query(Step).filter(Step.id == step_id).first()
    
    def get_by_run_and_name(self, run_id: int, step_name: str) -> Optional[Step]:
        """
        Get step by run ID and step name.
        
        Args:
            run_id: Run ID
            step_name: Step name
            
        Returns:
            Step or None if not found
        """
        return self.session.query(Step).filter(
            Step.run_id == run_id,
            Step.step_name == step_name
        ).first()
    
    def get_by_run_id(self, run_id: int) -> List[Step]:
        """
        Get all steps for a run.
        
        Args:
            run_id: Run ID
            
        Returns:
            List of steps
        """
        return self.session.query(Step).filter(Step.run_id == run_id).all()
    
    def update_status(
        self,
        step_id: int,
        status: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[Step]:
        """
        Update step status.
        
        Args:
            step_id: Step ID
            status: New status
            start_time: Start time (for "RUNNING" status)
            end_time: End time (for terminal status)
            
        Returns:
            Updated step or None if not found
        """
        step = self.get_by_id(step_id)
        if not step:
            logger.warning(f"Step with ID {step_id} not found for status update")
            return None
        
        step.status = status
        
        # Set start time for "RUNNING" status
        if status == "RUNNING" and not step.start_time:
            step.start_time = start_time or datetime.utcnow()
        
        # Set end time for terminal states
        if status in ["COMPLETED", "FAILED", "TERMINATED_TIME_LIMIT"] and not step.end_time:
            step.end_time = end_time or datetime.utcnow()
        
        try:
            self.session.commit()
            self.session.refresh(step)
            logger.info(f"Updated step {step_id} status to {status}")
            return step
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update step status: {e}")
            raise
    
    def update(self, step_id: int, **kwargs) -> Optional[Step]:
        """
        Update step.
        
        Args:
            step_id: Step ID
            **kwargs: Fields to update
            
        Returns:
            Updated step or None if not found
        """
        step = self.get_by_id(step_id)
        if not step:
            logger.warning(f"Step with ID {step_id} not found for update")
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(step, key):
                setattr(step, key, value)
        
        try:
            self.session.commit()
            self.session.refresh(step)
            logger.info(f"Updated step with ID {step_id}")
            return step
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update step: {e}")
            raise
    
    def delete(self, step_id: int) -> bool:
        """
        Delete step.
        
        Args:
            step_id: Step ID
            
        Returns:
            True if deleted, False if not found
        """
        step = self.get_by_id(step_id)
        if not step:
            logger.warning(f"Step with ID {step_id} not found for deletion")
            return False
        
        try:
            self.session.delete(step)
            self.session.commit()
            logger.info(f"Deleted step with ID {step_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete step: {e}")
            raise 