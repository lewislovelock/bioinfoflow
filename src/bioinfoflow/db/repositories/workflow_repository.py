"""
Workflow repository for BioinfoFlow.

This module provides database operations for workflow definitions.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from ..models.workflow import Workflow


class WorkflowRepository:
    """
    Workflow repository class.
    
    Provides database operations for workflow definitions.
    """
    
    def __init__(self, session: Session):
        """
        Initialize workflow repository.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(self, name: str, version: str, yaml_content: str, description: Optional[str] = None) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            version: Workflow version
            yaml_content: YAML definition of the workflow
            description: Optional description
            
        Returns:
            Created workflow
        """
        workflow = Workflow(
            name=name,
            version=version,
            yaml_content=yaml_content,
            description=description
        )
        
        try:
            self.session.add(workflow)
            self.session.commit()
            self.session.refresh(workflow)
            logger.info(f"Created workflow '{name}' v{version} with ID {workflow.id}")
            return workflow
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    def get_by_id(self, workflow_id: int) -> Optional[Workflow]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow or None if not found
        """
        return self.session.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    def get_by_name_version(self, name: str, version: str) -> Optional[Workflow]:
        """
        Get workflow by name and version.
        
        Args:
            name: Workflow name
            version: Workflow version
            
        Returns:
            Workflow or None if not found
        """
        return self.session.query(Workflow).filter(
            Workflow.name == name,
            Workflow.version == version
        ).first()
    
    def get_all(self) -> List[Workflow]:
        """
        Get all workflows.
        
        Returns:
            List of all workflows
        """
        return self.session.query(Workflow).all()
    
    def update(self, workflow_id: int, **kwargs) -> Optional[Workflow]:
        """
        Update workflow.
        
        Args:
            workflow_id: Workflow ID
            **kwargs: Fields to update
            
        Returns:
            Updated workflow or None if not found
        """
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            logger.warning(f"Workflow with ID {workflow_id} not found for update")
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        try:
            self.session.commit()
            self.session.refresh(workflow)
            logger.info(f"Updated workflow with ID {workflow_id}")
            return workflow
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update workflow: {e}")
            raise
    
    def delete(self, workflow_id: int) -> bool:
        """
        Delete workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted, False if not found
        """
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            logger.warning(f"Workflow with ID {workflow_id} not found for deletion")
            return False
        
        try:
            self.session.delete(workflow)
            self.session.commit()
            logger.info(f"Deleted workflow with ID {workflow_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete workflow: {e}")
            raise 