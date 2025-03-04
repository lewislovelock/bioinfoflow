"""
Workflow module for BioinfoFlow.

This module handles parsing and validation of workflow YAML files,
providing a structured representation of a workflow.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import shutil
from loguru import logger

from ..core.config import Config
from ..core.models import Workflow as WorkflowModel, Step as StepModel
from ..core.step import Step


class Workflow:
    """
    Workflow class representing a complete BioinfoFlow workflow.
    
    Parses and validates workflow YAML files and provides methods
    for working with workflow definitions.
    """
    
    def __init__(self, yaml_path: Union[str, Path]):
        """
        Initialize workflow from a YAML file.
        
        Args:
            yaml_path: Path to the workflow YAML file
        """
        self.yaml_path = Path(yaml_path).absolute()
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.yaml_path}")
        
        # Initialize properties
        self.name = ""
        self.version = ""
        self.description = ""
        self.config = Config()
        self.inputs = {}
        self.steps = {}
        self.metadata = {}
        
        # Parsed model
        self.model = None
        
        # Parse the YAML file
        self._parse_yaml()
        logger.info(f"Loaded workflow '{self.name}' v{self.version}")
    
    def _parse_yaml(self) -> None:
        """
        Parse YAML file and initialize workflow properties.
        
        Validates the workflow using Pydantic models and sets up class properties.
        
        Raises:
            ValueError: If the YAML is invalid or missing required fields
        """
        try:
            # Read YAML file
            with open(self.yaml_path, 'r') as f:
                workflow_dict = yaml.safe_load(f)
            
            # Validate using Pydantic model
            self.model = WorkflowModel(**workflow_dict)
            
            # Set properties from validated model
            self.name = self.model.name
            self.version = self.model.version
            self.description = self.model.description or ""
            
            # Update configuration
            if self.model.config:
                self.config.update_from_dict(self.model.config.dict())
            
            # Set inputs
            self.inputs = self.model.inputs
            
            # Set metadata
            if self.model.metadata:
                self.metadata = self.model.metadata.dict()
            
            # Process steps - convert StepModel to Step class
            for step_name, step_model in self.model.steps.items():
                # Convert StepModel to Step class
                step = Step(
                    name=step_name,
                    container=step_model.container,
                    command=step_model.command,
                    resources=step_model.resources.dict() if step_model.resources else None,
                    after=step_model.after
                )
                self.steps[step_name] = step
            
        except Exception as e:
            logger.error(f"Failed to parse workflow YAML: {e}")
            raise ValueError(f"Invalid workflow definition: {e}")
    
    def generate_run_id(self) -> str:
        """
        Generate a unique run ID.
        
        Returns:
            Run ID string in format "YYYYMMDD_HHMMSS_<random>"
        """
        return self.config.generate_run_id()
    
    def save_workflow_copy(self, run_dir: Path) -> None:
        """
        Save a copy of the workflow definition to the run directory.
        
        Args:
            run_dir: Run directory path
        """
        target_path = run_dir / "workflow.yaml"
        try:
            shutil.copy2(self.yaml_path, target_path)
            logger.debug(f"Saved workflow copy to {target_path}")
        except Exception as e:
            logger.error(f"Failed to save workflow copy: {e}")
            raise
    
    def get_execution_order(self) -> List[str]:
        """
        Determine the execution order of steps based on dependencies.
        
        Returns:
            List of step names in execution order
        """
        if self.model:
            return self.model.get_execution_order()
        
        # Fallback implementation if model is not available
        # (though this shouldn't happen in normal operation)
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(step_name):
            """Helper function for topological sort"""
            if step_name in temp_mark:
                raise ValueError(f"Circular dependency detected in step '{step_name}'")
            
            if step_name not in visited:
                temp_mark.add(step_name)
                
                step = self.steps[step_name]
                for dep in step.after:
                    visit(dep)
                
                temp_mark.remove(step_name)
                visited.add(step_name)
                order.append(step_name)
        
        # Visit each step
        for step_name in self.steps:
            if step_name not in visited:
                visit(step_name)
        
        # Reverse to get correct execution order
        # return list(reversed(order))
        return order
    
    def validate(self) -> bool:
        """
        Validate workflow definition.
        
        Returns:
            True if the workflow is valid, False otherwise
        """
        try:
            # The workflow was already validated during initialization
            # But we can add additional validation steps here if needed
            
            # Check if all steps have valid containers
            for step_name, step in self.steps.items():
                if not step.container:
                    logger.error(f"Step '{step_name}' has no container specified")
                    return False
                
                if not step.command:
                    logger.error(f"Step '{step_name}' has no command specified")
                    return False
            
            # Verify there are no circular dependencies
            try:
                self.get_execution_order()
            except ValueError as e:
                logger.error(f"Dependency error: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert workflow to dictionary.
        
        Returns:
            Dictionary representation of the workflow
        """
        if self.model:
            return self.model.dict()
        
        # Fallback implementation
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "config": {
                "base_dir": str(self.config.base_dir),
                "refs": str(self.config.refs_dir.relative_to(self.config.base_dir)),
                "workflows": str(self.config.workflows_dir.relative_to(self.config.base_dir)),
                "runs": str(self.config.runs_dir.relative_to(self.config.base_dir)),
            },
            "inputs": self.inputs,
            "steps": {name: step.dict() for name, step in self.steps.items()},
            "metadata": self.metadata
        } 