"""
Output management module for BioinfoFlow.

This module handles workflow output file management, including:
- Managing output directory structure
- Tracking output files
- Cleaning up temporary files
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union
from loguru import logger


class OutputManager:
    """
    Output management class.
    
    Handles tracking and management of workflow outputs.
    """
    
    def __init__(self, outputs_dir: Union[str, Path], tmp_dir: Path):
        """
        Initialize output manager.
        
        Args:
            outputs_dir: Path to outputs directory
            tmp_dir: Path to temporary directory
        """
        self.outputs_dir = Path(outputs_dir)
        self.tmp_dir = Path(tmp_dir)
        self.tracked_outputs: List[Path] = []
        self.temp_files: List[Path] = []
        
        # Ensure directories exist
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Initialized OutputManager with outputs directory: {outputs_dir}")
    
    def prepare_step_output(self, step_name: str) -> Path:
        """
        Prepare output directory for a step.
        
        Args:
            step_name: Name of the step
            
        Returns:
            Path to step output directory
        """
        step_dir = self.outputs_dir / step_name
        step_dir.mkdir(exist_ok=True)
        return step_dir
    
    def track_output(self, path: Union[str, Path]) -> None:
        """
        Add an output file to tracking.
        
        Args:
            path: Path to output file
        """
        path = Path(path)
        if path.exists():
            self.tracked_outputs.append(path.absolute())
            logger.debug(f"Tracking output file: {path}")
        else:
            logger.warning(f"Cannot track non-existent output file: {path}")
    
    def get_step_outputs(self, step_name: str) -> List[Path]:
        """
        Get all output files for a step.
        
        Args:
            step_name: Name of the step
            
        Returns:
            List of output file paths
        """
        step_dir = self.outputs_dir / step_name
        if not step_dir.exists():
            return []
        
        outputs = []
        for path in step_dir.rglob("*"):
            if path.is_file():
                outputs.append(path)
        return outputs
    
    def create_temp_file(self, prefix: str = "", suffix: str = "") -> Path:
        """
        Create a temporary file.
        
        Args:
            prefix: Prefix for temporary file name
            suffix: Suffix for temporary file name
            
        Returns:
            Path to temporary file
        """
        import tempfile
        
        # Create temp file in tmp directory
        fd, path = tempfile.mkstemp(dir=self.tmp_dir, prefix=prefix, suffix=suffix)
        os.close(fd)
        
        logger.debug(f"Created temporary file: {path}")
        return Path(path)
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files."""
        try:
            if self.tmp_dir.exists():
                shutil.rmtree(self.tmp_dir)
                self.tmp_dir.mkdir(parents=True)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary files: {e}")
    
    def validate_outputs(self, expected_outputs: Dict[str, Any]) -> bool:
        """
        Validate that all expected outputs are present.
        
        Args:
            expected_outputs: Dictionary of expected outputs
            
        Returns:
            True if all expected outputs are present, False otherwise
        """
        for output_name, output_pattern in expected_outputs.items():
            if isinstance(output_pattern, str):
                path = self.outputs_dir / output_pattern
                if not path.exists():
                    logger.error(f"Expected output not found: {path}")
                    return False
            elif isinstance(output_pattern, list):
                for pattern in output_pattern:
                    path = self.outputs_dir / pattern
                    if not path.exists():
                        logger.error(f"Expected output not found: {path}")
                        return False
        
        return True
    
    def get_output_size(self) -> int:
        """
        Get total size of output files in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        for path in self.outputs_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
    
    def archive_outputs(self, archive_path: Path) -> None:
        """
        Archive output files to a compressed file.
        
        Args:
            archive_path: Path to create archive at
        """
        import tarfile
        
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(self.outputs_dir, arcname=self.outputs_dir.name)
            logger.info(f"Archived outputs to: {archive_path}")
        except Exception as e:
            logger.error(f"Failed to archive outputs: {e}")
            raise 