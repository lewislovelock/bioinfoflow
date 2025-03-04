"""
Path resolver module for BioinfoFlow.

This module handles path resolution and variable substitution in commands
and paths, supporting the ${...} syntax.
"""
import re
import os
from pathlib import Path
from typing import Dict, Any, Union, Optional
from loguru import logger


class PathResolver:
    """
    Path resolver class for resolving paths and variables.
    
    Handles variable substitution in commands and paths using ${...} syntax.
    """
    
    def __init__(self, context: Dict[str, Any]):
        """
        Initialize path resolver with context.
        
        Args:
            context: Dictionary containing context variables for substitution
        """
        self.context = context
        logger.debug(f"Initialized PathResolver with context keys: {list(context.keys())}")
    
    def resolve_variables(self, string: str) -> str:
        """
        Resolve variables in a string using ${...} syntax.
        
        Args:
            string: String containing variables to resolve
            
        Returns:
            String with variables resolved
        """
        if not string:
            return string
            
        # Pattern to match ${...} expressions
        pattern = r'\${([^}]*)}'
        
        def replace_var(match):
            """Replace a single variable match"""
            var_path = match.group(1)
            
            # Split the path into components
            components = var_path.split('.')
            
            # Navigate through the context
            value = self.context
            for component in components:
                if isinstance(value, dict) and component in value:
                    value = value[component]
                elif hasattr(value, component):
                    # Support for object attributes
                    value = getattr(value, component)
                else:
                    logger.warning(f"Variable not found: ${{{var_path}}}")
                    return match.group(0)  # Return the original expression if not found
            
            # Convert to string
            return str(value)
        
        # Replace all variables
        result = re.sub(pattern, replace_var, string)
        
        # Log if any substitutions weren't performed (still contain ${...})
        if '${' in result:
            logger.warning(f"Some variables could not be resolved in: {result}")
        
        return result
    
    def resolve_path(self, path: str) -> Path:
        """
        Resolve a path with variable substitution.
        
        Args:
            path: Path string with variables
            
        Returns:
            Resolved Path object
        """
        # First resolve any variables
        resolved_path = self.resolve_variables(path)
        
        # Handle absolute paths
        if os.path.isabs(resolved_path):
            return Path(resolved_path)
        
        # Handle relative paths based on context
        run_dir = None
        if 'run_dir' in self.context:
            run_dir = self.context['run_dir']
        
        if run_dir:
            run_dir_path = Path(run_dir)
            
            # Handle special directories
            if resolved_path.startswith('inputs/'):
                return run_dir_path / resolved_path
            elif resolved_path.startswith('outputs/'):
                return run_dir_path / resolved_path
            elif resolved_path.startswith('tmp/'):
                return run_dir_path / resolved_path
            elif resolved_path.startswith('logs/'):
                return run_dir_path / resolved_path
                
            # Handle references to step outputs
            if resolved_path.startswith('steps/'):
                parts = resolved_path.split('/')
                if len(parts) >= 3:
                    step_name = parts[1]
                    output_path = '/'.join(parts[2:])
                    return run_dir_path / 'outputs' / step_name / output_path
            
            # Default to relative to run directory
            return run_dir_path / resolved_path
        
        # Default to relative to current directory
        return Path(os.getcwd()) / resolved_path
    
    def update_context(self, new_context: Dict[str, Any]) -> None:
        """
        Update the resolver context with new values.
        
        Args:
            new_context: New context values to add/update
        """
        # Deep update for nested dictionaries
        self._deep_update(self.context, new_context)
        logger.debug(f"Updated PathResolver context with keys: {list(new_context.keys())}")
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get_context_value(self, path: str) -> Any:
        """
        Get a value from the context by dot-notation path.
        
        Args:
            path: Dot-notation path to the value (e.g., "config.base_dir")
            
        Returns:
            Value from context or None if not found
        """
        # Split the path into components
        components = path.split('.')
        
        # Navigate through the context
        value = self.context
        for component in components:
            if isinstance(value, dict) and component in value:
                value = value[component]
            elif hasattr(value, component):
                # Support for object attributes
                value = getattr(value, component)
            else:
                logger.warning(f"Path not found in context: {path}")
                return None
        
        return value 