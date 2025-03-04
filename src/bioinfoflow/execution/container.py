"""
Container management module for BioinfoFlow.

This module handles Docker container operations, including:
- Building Docker commands
- Running containers with appropriate resource limits
- Handling container output
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
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
            resources: Resource requirements (cpu, memory)
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
                
                # Stream output to logger
                for line in process.stdout:
                    logger.info(line.strip())
            
            # Wait for process to complete
            exit_code = process.wait()
            
            if exit_code == 0:
                logger.info(f"Container completed successfully")
            else:
                logger.error(f"Container failed with exit code {exit_code}")
            
            return exit_code
            
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return 1
    
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