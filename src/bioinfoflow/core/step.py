"""
Step module for BioinfoFlow.

This module defines the Step class, representing a single execution unit within a workflow.
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

from bioinfoflow.core.path_resolver import PathResolver


class Step:
    """
    Step class representing a single execution unit in a workflow.
    
    Each step has a container image, command to execute, resource requirements,
    and optional dependencies on other steps.
    """
    
    def __init__(
        self, 
        name: str,
        container: str,
        command: str,
        resources: Dict[str, Any] = None,
        after: List[str] = None
    ):
        """
        Initialize a workflow step.
        
        Args:
            name: Step name
            container: Container image
            command: Command to execute
            resources: Resource requirements (cpu, memory)
            after: List of step names this step depends on
        """
        self.name = name
        self.container = container
        self.command = command
        self.resources = resources or {"cpu": 1, "memory": "1G"}
        self.after = after or []
        
        # Validate required fields
        if not self.container:
            raise ValueError(f"Step '{name}' must specify a container image")
        if not self.command:
            raise ValueError(f"Step '{name}' must specify a command")
        
        logger.debug(f"Initialized step '{name}' with container '{container}'")
    
    def get_cpu_request(self) -> int:
        """
        Get the CPU request for this step.
        
        Returns:
            Number of CPU cores
        """
        return self.resources.get("cpu", 1)
    
    def get_memory_request(self) -> str:
        """
        Get the memory request for this step.
        
        Returns:
            Memory requirement string (e.g., "1G")
        """
        return self.resources.get("memory", "1G")
    
    def resolve_command(self, resolver: PathResolver) -> str:
        """
        Resolve variables in the command.
        
        Args:
            resolver: PathResolver instance for variable substitution
            
        Returns:
            Resolved command string
        """
        try:
            # Update context with step-specific information
            step_context = {
                "step": {
                    "name": self.name,
                    "resources": self.resources
                }
            }
            resolver.update_context(step_context)
            
            # Resolve variables in command
            resolved_command = resolver.resolve_variables(self.command)
            logger.debug(f"Resolved command for step '{self.name}': {resolved_command}")
            
            return resolved_command
        except Exception as e:
            logger.error(f"Error resolving command for step '{self.name}': {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert step to dictionary.
        
        Returns:
            Dictionary representation of the step
        """
        return {
            "name": self.name,
            "container": self.container,
            "command": self.command,
            "resources": self.resources,
            "after": self.after
        }
    
    @staticmethod
    def from_dict(name: str, step_dict: Dict[str, Any]) -> 'Step':
        """
        Create a Step instance from a dictionary.
        
        Args:
            name: Step name
            step_dict: Dictionary containing step definition
            
        Returns:
            New Step instance
        """
        return Step(
            name=name,
            container=step_dict.get("container"),
            command=step_dict.get("command"),
            resources=step_dict.get("resources", {"cpu": 1, "memory": "1G"}),
            after=step_dict.get("after", [])
        ) 