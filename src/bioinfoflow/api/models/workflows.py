"""
Workflow API models for BioinfoFlow.

This module defines the Pydantic models for workflow API operations,
reusing and extending core models when appropriate.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from bioinfoflow.core.models import Step as CoreStep
from bioinfoflow.core.models import Workflow as CoreWorkflow


class WorkflowBase(BaseModel):
    """Base model for workflow operations."""
    name: str
    version: str
    description: Optional[str] = None


class WorkflowCreate(WorkflowBase):
    """Model for creating a workflow."""
    yaml_content: str


class WorkflowStep(BaseModel):
    """Model for workflow steps in API responses."""
    name: str
    container: str
    command: str
    resources: Dict[str, Any]
    after: List[str] = Field(default_factory=list)


class WorkflowDetail(WorkflowBase):
    """Detailed workflow information for API responses."""
    id: int
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict)
    created_at: datetime

    @classmethod
    def from_core_workflow(cls, workflow: CoreWorkflow, workflow_id: int, created_at: datetime):
        """Convert core workflow model to API model."""
        steps = {}
        for name, step in workflow.steps.items():
            steps[name] = WorkflowStep(
                name=name,
                container=step.container,
                command=step.command,
                resources=step.resources,
                after=step.after
            )
        
        return cls(
            id=workflow_id,
            name=workflow.name,
            version=workflow.version,
            description=workflow.description,
            steps=steps,
            created_at=created_at
        )


class WorkflowSummary(WorkflowBase):
    """Summary workflow information for API list responses."""
    id: int
    created_at: datetime
    run_count: int = 0


class WorkflowRunRequest(BaseModel):
    """Request model for running a workflow."""
    inputs: Dict[str, str] = Field(default_factory=dict)
    parallel: int = Field(1, description="Maximum number of steps to execute in parallel")
    enable_time_limits: bool = True
    default_time_limit: str = "1h" 