"""
Input management module for BioinfoFlow.

This module handles workflow input file management, including:
- Resolving input paths (absolute or relative to current directory)
- Processing glob patterns
- Creating symbolic links or copying files to run directory
"""
import os
import glob
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from loguru import logger


class InputManager:
    """
    Input file management class.
    
    Handles the processing of workflow input files, including path resolution,
    glob pattern expansion, and file copying/linking.
    """
    
    def __init__(self, inputs_config: Dict[str, Any], inputs_dir: Path):
        """
        Initialize input manager.
        
        Args:
            inputs_config: Input configuration from workflow definition
            inputs_dir: Directory for input files in run directory
        """
        self.inputs_config = inputs_config
        self.inputs_dir = Path(inputs_dir)
        self.resolved_inputs: Dict[str, Union[str, List[str]]] = {}
        
        # Ensure inputs directory exists
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized InputManager with inputs directory: {inputs_dir}")
    
    def process_inputs(self, cli_inputs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process all input files.
        
        Args:
            cli_inputs: Optional command-line input overrides
            
        Returns:
            Dictionary mapping input names to resolved paths
        """
        # Merge CLI input overrides with workflow inputs
        effective_inputs = self.inputs_config.copy()
        if cli_inputs:
            effective_inputs.update(cli_inputs)
            logger.debug(f"Updated inputs with CLI overrides: {cli_inputs}")
        
        # Process each input
        for input_name, input_path in effective_inputs.items():
            try:
                self._process_single_input(input_name, input_path)
            except Exception as e:
                logger.error(f"Failed to process input '{input_name}': {e}")
                raise
        
        logger.info(f"Processed {len(self.resolved_inputs)} input(s)")
        return self.resolved_inputs
    
    def _process_single_input(self, input_name: str, input_path: str) -> None:
        """
        Process a single input path.
        
        Args:
            input_name: Name of the input
            input_path: Path pattern for the input
        """
        # Convert to absolute path if relative
        if not os.path.isabs(input_path):
            input_path = os.path.join(os.getcwd(), input_path)
        
        # Expand glob pattern
        source_paths = glob.glob(input_path, recursive=True)
        
        if not source_paths:
            logger.warning(f"No files found matching input path: {input_path}")
            self.resolved_inputs[input_name] = []
            return
        
        resolved_paths = []
        
        for source_path in source_paths:
            source_path = Path(source_path).absolute()
            
            if not source_path.exists():
                logger.warning(f"Input file does not exist: {source_path}")
                continue
            
            # Create target path in inputs directory
            target_path = self.inputs_dir / source_path.name
            
            try:
                self._link_or_copy_file(source_path, target_path)
                resolved_paths.append(str(target_path))
                logger.debug(f"Processed input file: {source_path} -> {target_path}")
            except Exception as e:
                logger.error(f"Failed to process file {source_path}: {e}")
                raise
        
        # Store resolved paths
        if len(resolved_paths) == 1:
            self.resolved_inputs[input_name] = resolved_paths[0]
        else:
            self.resolved_inputs[input_name] = resolved_paths
    
    def _link_or_copy_file(self, source: Path, target: Path) -> None:
        """
        Create a symbolic link or copy a file.
        
        Attempts to create a symbolic link first, falls back to copying if linking fails.
        
        Args:
            source: Source file path
            target: Target file path
        """
        if target.exists():
            if target.is_symlink() and target.resolve() == source.resolve():
                logger.debug(f"Link already exists: {target} -> {source}")
                return
            logger.warning(f"Target already exists, removing: {target}")
            target.unlink()
        
        try:
            # Try to create a symbolic link first
            os.symlink(source, target)
            logger.debug(f"Created symlink: {target} -> {source}")
        except OSError as e:
            # Fall back to copying if symlink fails
            logger.warning(f"Failed to create symlink, falling back to copy: {e}")
            shutil.copy2(source, target)
            logger.debug(f"Copied file: {source} -> {target}")
    
    def get_input_path(self, input_name: str) -> Optional[Union[str, List[str]]]:
        """
        Get the resolved path(s) for an input.
        
        Args:
            input_name: Name of the input
            
        Returns:
            Resolved path(s) or None if not found
        """
        return self.resolved_inputs.get(input_name)
    
    def validate_inputs(self) -> bool:
        """
        Validate that all required inputs are present and accessible.
        
        Returns:
            True if all inputs are valid, False otherwise
        """
        for input_name, paths in self.resolved_inputs.items():
            if not paths:
                logger.error(f"No files found for input '{input_name}'")
                return False
            
            if isinstance(paths, str):
                paths = [paths]
            
            for path in paths:
                if not os.path.exists(path):
                    logger.error(f"Input file not found: {path}")
                    return False
        
        return True 