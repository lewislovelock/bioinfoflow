"""
Configuration management module for BioinfoFlow.

This module handles global configuration settings and directory structure,
providing utilities for path resolution and workspace management.
"""
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import datetime
from loguru import logger


class Config:
    """
    Global configuration management class.
    
    Manages base directories and provides utilities for path resolution and
    directory structure creation.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize configuration with base directory.
        
        Args:
            base_dir: Base directory path, defaults to current working directory
        """
        self.base_dir = Path(base_dir or os.getcwd()).absolute()
        self.refs_dir = self.base_dir / "refs"
        self.workflows_dir = self.base_dir / "workflows"
        self.runs_dir = self.base_dir / "runs"
        
        # Ensure necessary directories exist
        self._ensure_directories()
        
        logger.debug(f"Initialized config with base_dir: {self.base_dir}")
    
    def _ensure_directories(self) -> None:
        """Create necessary directory structure if it doesn't exist."""
        for dir_path in [self.refs_dir, self.workflows_dir, self.runs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
        """
        if not config_dict:
            return
            
        if "base_dir" in config_dict:
            # Resolve variables in base_dir
            base_dir_str = config_dict["base_dir"]
            if "${PWD}" in base_dir_str:
                base_dir_str = base_dir_str.replace("${PWD}", os.getcwd())
            self.base_dir = Path(base_dir_str).absolute()
            
        # Update subdirectories
        self.refs_dir = self.base_dir / config_dict.get("refs", "refs")
        self.workflows_dir = self.base_dir / config_dict.get("workflows", "workflows")
        self.runs_dir = self.base_dir / config_dict.get("runs", "runs")
        
        # Re-ensure directories exist
        self._ensure_directories()
        # logger.info(f"Updated configuration with custom settings")
    
    def get_run_dir(self, workflow_name: str, version: str, run_id: str) -> Path:
        """
        Get directory path for a specific run.
        
        Args:
            workflow_name: Name of the workflow
            version: Workflow version
            run_id: Run identifier
            
        Returns:
            Path object for the run directory
        """
        return self.runs_dir / workflow_name / version / run_id
    
    def create_run_structure(self, workflow_name: str, version: str, run_id: str) -> Dict[str, Path]:
        """
        Create directory structure for a workflow run.
        
        Creates the following structure:
        ${base_dir}/runs/<workflow_name>/<version>/<run_id>/
            ├── inputs/
            ├── outputs/
            ├── logs/
            └── tmp/
        
        Args:
            workflow_name: Name of the workflow
            version: Workflow version
            run_id: Run identifier
            
        Returns:
            Dictionary mapping directory names to Path objects
        """
        run_dir = self.get_run_dir(workflow_name, version, run_id)
        
        # Create subdirectories
        inputs_dir = run_dir / "inputs"
        outputs_dir = run_dir / "outputs"
        logs_dir = run_dir / "logs"
        tmp_dir = run_dir / "tmp"
        
        for dir_path in [run_dir, inputs_dir, outputs_dir, logs_dir, tmp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Created run directory structure at {run_dir}")
        
        return {
            "run_dir": run_dir,
            "inputs_dir": inputs_dir,
            "outputs_dir": outputs_dir,
            "logs_dir": logs_dir,
            "tmp_dir": tmp_dir
        }
    
    def generate_run_id(self) -> str:
        """
        Generate a unique run ID.
        
        Returns:
            String in format "YYYYMMDD_HHMMSS_<random>"
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = uuid.uuid4().hex[:8]
        return f"{timestamp}_{random_suffix}"
    
    def resolve_path(self, path: str, context: Dict[str, Any]) -> Path:
        """
        Resolve a path based on context.
        
        Args:
            path: Path to resolve
            context: Context dictionary containing run information
            
        Returns:
            Resolved Path object
        """
        # Handle absolute paths
        if os.path.isabs(path):
            return Path(path)
        
        # Handle relative paths based on context
        if "run_dir" in context:
            run_dir = context["run_dir"]
            
            # Determine path type
            if "input" in path.lower():
                return Path(run_dir) / "inputs" / path
            elif "output" in path.lower():
                return Path(run_dir) / "outputs" / path
            elif "ref" in path.lower():
                return self.refs_dir / path
            else:
                # Default to run directory
                return Path(run_dir) / path
        
        # Default to relative to base_dir
        return self.base_dir / path 