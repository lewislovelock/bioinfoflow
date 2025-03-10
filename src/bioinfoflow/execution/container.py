"""
Container management module for BioinfoFlow.

This module handles Docker container operations, including:
- Building Docker commands
- Running containers with appropriate resource limits
- Handling container output
"""
import os
import subprocess
import threading
import time
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from loguru import logger


class ContainerRunner:
    """
    Container execution management class.
    
    Handles Docker container operations for workflow steps.
    """
    
    def __init__(self, run_dir: Path):
        """
        Initialize container runner.
        
        Args:
            run_dir: Workflow run directory
        """
        self.run_dir = Path(run_dir)
        logger.debug(f"Initialized ContainerRunner with run_dir: {run_dir}")
        
        # Ensure outputs directory exists
        outputs_dir = self.run_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def run_container(
        self,
        image: str,
        command: str,
        resources: Dict[str, Any],
        volumes: Optional[Dict[str, str]] = None,
        working_dir: str = "/data",
        log_file: Optional[Path] = None
    ) -> int:
        """
        Run a container with the specified parameters.
        
        Args:
            image: Container image
            command: Command to execute
            resources: Resource requirements (cpu, memory, time_limit)
            volumes: Additional volume mappings
            working_dir: Working directory inside container
            log_file: File to write container output
            
        Returns:
            Container exit code
        """
        # Build Docker command
        docker_cmd = self.build_docker_command(
            image=image,
            command=command,
            resources=resources,
            volumes=volumes,
            working_dir=working_dir
        )
        
        logger.info(f"Running container: {image}")
        logger.debug(f"Docker command: {' '.join(docker_cmd)}")
        
        # Get time limit in seconds if specified
        time_limit_seconds = None
        if "time_limit" in resources and resources["time_limit"]:
            # Parse time limit
            time_limit = resources["time_limit"]
            time_limit_seconds = self._parse_time_limit(time_limit)
            logger.info(f"Container will be terminated after {time_limit} ({time_limit_seconds} seconds)")
        
        try:
            # Run the container
            if log_file:
                with open(log_file, 'w') as log:
                    process = subprocess.Popen(
                        docker_cmd,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
            else:
                process = subprocess.Popen(
                    docker_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Stream output to logger in a separate thread
                if process.stdout:
                    threading.Thread(
                        target=self._stream_output,
                        args=(process.stdout,),
                        daemon=True
                    ).start()
            
            # Wait for process with timeout if specified
            if time_limit_seconds:
                return self._wait_with_timeout(process, time_limit_seconds, image)
            else:
                # Wait for process to complete without timeout
                exit_code = process.wait()
                
                if exit_code == 0:
                    logger.info(f"Container completed successfully")
                elif exit_code == 2:
                    # Exit code 2 often indicates a shell syntax error in the command
                    logger.error(f"Container command failed with syntax error (exit code {exit_code}). Check your command syntax.")
                else:
                    logger.error(f"Container failed with exit code {exit_code}")
                
                return exit_code
            
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return 1
    
    def _stream_output(self, stdout):
        """Stream process output to logger."""
        for line in stdout:
            logger.info(line.strip())
    
    def _wait_with_timeout(self, process, timeout_seconds: int, image: str) -> int:
        """
        Wait for process to complete with timeout.
        
        Args:
            process: Subprocess process
            timeout_seconds: Timeout in seconds
            image: Container image name for logging
            
        Returns:
            Exit code (124 for timeout, process exit code otherwise)
        """
        start_time = time.time()
        
        try:
            exit_code = process.wait(timeout=timeout_seconds)
            
            if exit_code == 0:
                logger.info(f"Container completed successfully")
            elif exit_code == 2:
                # Exit code 2 often indicates a shell syntax error in the command
                logger.error(f"Container command failed with syntax error (exit code {exit_code}). Check your command syntax.")
            else:
                logger.error(f"Container failed with exit code {exit_code}")
            
            return exit_code
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            logger.warning(f"Container {image} timed out after {elapsed:.2f} seconds")
            
            # Get container ID and kill it
            try:
                # Find and kill the container
                container_id = self._get_container_id(process.pid)
                if container_id:
                    logger.info(f"Killing container {container_id} due to time limit")
                    subprocess.run(["docker", "kill", container_id], check=False)
            except Exception as e:
                logger.error(f"Error killing container: {e}")
            
            # Kill the process
            process.kill()
            
            try:
                # Wait for the process to terminate
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.error("Failed to terminate process after killing container")
            
            # Log that this was a timeout termination, not a failure
            logger.warning(f"Step terminated due to time limit (not an error)")
            
            return 124  # Standard timeout exit code
    
    def _get_container_id(self, pid: int) -> Optional[str]:
        """
        Get Docker container ID from process PID.
        
        Args:
            pid: Process ID
            
        Returns:
            Container ID or None if not found
        """
        try:
            # Get running containers
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}"],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            
            container_ids = result.stdout.strip().split('\n')
            
            # If there's only one container running, it's likely the one we want
            if len(container_ids) == 1 and container_ids[0]:
                return container_ids[0]
                
            # If there are multiple containers, we need to find the right one
            # This is a simplification for the MVP - ideally we would track container IDs
            # when we start them, but that would require larger changes
            if container_ids:
                # Return the most recently started container
                # This is a reasonable assumption for the MVP since workflows typically
                # start containers in sequence or with a small number in parallel
                return container_ids[0]
                
        except Exception as e:
            logger.error(f"Error getting container ID: {e}")
        
        return None
    
    def _parse_time_limit(self, time_limit: str) -> int:
        """
        Parse time limit string to seconds.
        
        Args:
            time_limit: Time limit string (e.g., 1h, 30m, 2h30m)
            
        Returns:
            Time limit in seconds
        """
        total_seconds = 0
        
        # Handle complex time formats like 1h30m15s
        parts = []
        current_number = ""
        
        for char in time_limit:
            if char.isdigit():
                current_number += char
            elif char in "hms" and current_number:
                parts.append((int(current_number), char))
                current_number = ""
        
        # Process the parts
        for value, unit in parts:
            if unit == 'h':
                total_seconds += value * 3600
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
        
        return total_seconds
    
    def build_docker_command(
        self,
        image: str,
        command: str,
        resources: Dict[str, Any],
        volumes: Optional[Dict[str, str]] = None,
        working_dir: str = "/data"
    ) -> List[str]:
        """
        Build the Docker command to run.
        
        Args:
            image: Container image
            command: Command to execute
            resources: Resource requirements
            volumes: Additional volumes to mount
            working_dir: Working directory in container
            
        Returns:
            List of command parts
        """
        docker_cmd = ["docker", "run", "--rm"]
        
        # Add resource constraints
        if "cpu" in resources:
            docker_cmd.extend(["--cpus", str(resources["cpu"])])
        
        if "memory" in resources:
            docker_cmd.extend(["--memory", resources["memory"]])
        
        # Add volume mounts
        docker_cmd.extend(["-v", f"{self.run_dir}:/data"])
        
        if volumes:
            for host_path, container_path in volumes.items():
                docker_cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Set working directory
        docker_cmd.extend(["-w", working_dir])
        
        # Add container image
        docker_cmd.append(image)
        
        # Modify command to use container paths instead of host paths
        # Replace host run directory with container mount point
        modified_command = command.replace(str(self.run_dir), "/data")
        
        # Add command
        docker_cmd.extend(["sh", "-c", modified_command])
        
        return docker_cmd
    
    def check_image_exists(self, image: str) -> bool:
        """
        Check if a Docker image exists locally.
        
        Args:
            image: Image name
            
        Returns:
            True if image exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking image existence: {e}")
            return False
    
    def pull_image(self, image: str) -> bool:
        """
        Pull a Docker image.
        
        Args:
            image: Image name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling image: {image}")
            result = subprocess.run(
                ["docker", "pull", image],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            logger.debug(f"Pull completed: {image}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull image {image}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error pulling image: {e}")
            return False
    
    def ensure_image_available(self, image: str) -> bool:
        """
        Ensure a Docker image is available, pulling if necessary.
        
        Args:
            image: Image name
            
        Returns:
            True if image is available, False otherwise
        """
        if self.check_image_exists(image):
            return True
        
        return self.pull_image(image) 