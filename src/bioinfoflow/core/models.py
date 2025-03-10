"""
Core data models for BioinfoFlow.

This module defines the Pydantic models used throughout the application.
"""

import re
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, field_validator, model_validator

class Resources(BaseModel):
    """Model for step resource requirements"""
    
    cpu: int = Field(1, description="Number of CPU cores", ge=1)
    memory: str = Field("1G", description="Memory requirement")
    time_limit: Optional[str] = Field(None, description="Time limit for step execution (e.g., 1h, 30m)")
    
    @field_validator('memory')
    @classmethod
    def validate_memory_format(cls, v):
        """Validate memory format (e.g., 1G, 500M)"""
        pattern = r'^(\d+)([MGT])$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid memory format: {v}. Expected format: <number><unit> (e.g., 1G, 500M)")
        return v
    
    @field_validator('time_limit')
    @classmethod
    def validate_time_limit_format(cls, v):
        """Validate time limit format (e.g., 1h, 30m, 2h30m)"""
        if v is None:
            return v
            
        pattern = r'^(\d+)([hms])(?:(\d+)([ms]))?(?:(\d+)([s]))?$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid time limit format: {v}. Expected format: <number><unit> (e.g., 1h, 30m, 2h30m)")
        return v
    
    def get_time_limit_seconds(self) -> Optional[int]:
        """
        Convert time limit to seconds.
        
        Returns:
            Time limit in seconds or None if not set
        """
        if not self.time_limit:
            return None
            
        total_seconds = 0
        
        # Handle complex time formats like 1h30m15s
        parts = re.findall(r'(\d+)([hms])', self.time_limit)
        
        for value, unit in parts:
            value = int(value)
            if unit == 'h':
                total_seconds += value * 3600
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
        
        return total_seconds


class Step(BaseModel):
    """Model for workflow step definition"""
    
    container: str = Field(..., description="Container image")
    command: str = Field(..., description="Execution command")
    resources: Resources = Field(default_factory=Resources, description="Resource requirements")
    after: List[str] = Field(default_factory=list, description="Dependencies")
    
    @field_validator('container')
    @classmethod
    def validate_container(cls, v):
        """Validate container image format"""
        if not v:
            raise ValueError("Container image cannot be empty")
        return v
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        """Validate command is not empty"""
        if not v:
            raise ValueError("Command cannot be empty")
        return v


class Config(BaseModel):
    """Model for global configuration"""
    
    base_dir: Optional[str] = Field(None, description="Base directory")
    refs: str = Field("refs", description="Reference data directory")
    workflows: str = Field("workflows", description="Workflow definitions directory")
    runs: str = Field("runs", description="Workflow run logs directory")
    
    @field_validator('base_dir')
    @classmethod
    def validate_base_dir(cls, v):
        """Validate base directory if provided"""
        if v is not None and not v:
            raise ValueError("Base directory cannot be empty if provided")
        return v


class Metadata(BaseModel):
    """Model for optional workflow metadata"""
    
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = None


class Workflow(BaseModel):
    """
    Model for complete workflow definition
    
    This is the main model that represents a workflow definition as specified in a YAML file.
    """
    
    name: str = Field(..., description="Workflow name")
    version: str = Field(..., description="Workflow version")
    description: Optional[str] = Field(None, description="Workflow description")
    config: Config = Field(default_factory=Config, description="Global configuration")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input definitions")
    steps: Dict[str, Step] = Field(..., description="Workflow steps")
    metadata: Optional[Metadata] = Field(None, description="Optional metadata")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate workflow name format"""
        if not v:
            raise ValueError("Workflow name cannot be empty")
        
        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid workflow name: {v}. Only alphanumeric characters, underscores, and hyphens are allowed.")
        
        return v
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        """Validate workflow version format (semver)"""
        if not v:
            raise ValueError("Workflow version cannot be empty")
        
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        simple_pattern = r'^\d+\.\d+\.\d+$'
        
        if not (re.match(pattern, v) or re.match(simple_pattern, v)):
            raise ValueError(f"Invalid version format: {v}. Expected semver format (e.g., 1.0.0)")
        
        return v
    
    @model_validator(mode='after')
    def validate_steps_dependencies(self):
        """Validate that all step dependencies exist and there are no circular dependencies"""
        steps = self.steps
        
        # Check that all dependencies exist
        for step_name, step in steps.items():
            for dep in step.after:
                if dep not in steps:
                    raise ValueError(f"Step '{step_name}' depends on non-existent step '{dep}'")
        
        # Check for circular dependencies using DFS
        visited = set()
        temp_mark = set()
        
        def visit(step_name):
            if step_name in temp_mark:
                raise ValueError(f"Circular dependency detected involving step '{step_name}'")
            
            if step_name not in visited:
                temp_mark.add(step_name)
                
                # Visit all dependencies
                for dep in steps[step_name].after:
                    visit(dep)
                
                temp_mark.remove(step_name)
                visited.add(step_name)
        
        # Visit each step
        for step_name in steps:
            if step_name not in visited:
                visit(step_name)
        
        return self
    
    def get_execution_order(self) -> List[str]:
        """
        Determine the execution order of steps based on dependencies.
        
        Returns:
            List of step names in execution order.
        """
        steps = self.steps
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(step_name):
            if step_name in temp_mark:
                raise ValueError(f"Circular dependency detected involving step '{step_name}'")
            
            if step_name not in visited:
                temp_mark.add(step_name)
                
                # Visit all dependencies
                for dep in self.steps[step_name].after:
                    visit(dep)
                
                temp_mark.remove(step_name)
                visited.add(step_name)
                order.append(step_name)
        
        # Visit each step
        for step_name in self.steps:
            if step_name not in visited:
                visit(step_name)
        
        # The order is already correct for execution sequence
        # In a topological sort, nodes are added to the result after all their
        # dependencies have been processed, so no need to reverse
        return order