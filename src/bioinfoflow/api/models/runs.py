"""
Run API models for BioinfoFlow.

This module defines the Pydantic models for run API operations,
representing workflow execution status and results.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from bioinfoflow.core.models import StepStatus


class RunSummary(BaseModel):
    """Summary information about a workflow run."""
    id: int
    run_id: str
    workflow_id: int
    workflow_name: str
    workflow_version: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[str] = None


class StepDetail(BaseModel):
    """Detailed information about a workflow step."""
    id: int
    step_name: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None
    log_file: Optional[str] = None
    outputs: Optional[Dict[str, Any]] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if the step is in a terminal state."""
        return self.status in [
            StepStatus.COMPLETED.value,
            StepStatus.FAILED.value,
            StepStatus.ERROR.value,
            StepStatus.TERMINATED_TIME_LIMIT.value,
            StepStatus.SKIPPED.value
        ]


class RunDetail(RunSummary):
    """Detailed information about a workflow run."""
    steps: Dict[str, StepDetail] = Field(default_factory=dict)
    inputs: Optional[Dict[str, Any]] = None
    run_dir: str


class RunResumeRequest(BaseModel):
    """Request model for resuming a run."""
    parallel: int = Field(1, description="Maximum number of steps to execute in parallel")
    enable_time_limits: bool = True
    default_time_limit: str = "1h"
    step_overrides: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Override settings for specific steps when resuming"
    ) 