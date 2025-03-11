"""
Workflow execution module for BioinfoFlow.

This module handles the execution of workflows, including:
- Setting up run directories
- Processing inputs
- Executing steps in dependency order
- Managing outputs
"""
import os
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from loguru import logger

from bioinfoflow.core.workflow import Workflow
from bioinfoflow.core.path_resolver import PathResolver
from bioinfoflow.core.models import StepStatus
from bioinfoflow.io.input_manager import InputManager
from bioinfoflow.io.output_manager import OutputManager
from bioinfoflow.execution.container import ContainerRunner
from bioinfoflow.execution.scheduler import Scheduler


class WorkflowExecutor:
    """
    Workflow executor class.
    
    Handles the execution of a complete workflow, coordinating between
    the core, IO, and execution components.
    """
    
    def __init__(self, workflow: Workflow, cli_inputs: Optional[Dict[str, str]] = None):
        """
        Initialize workflow executor.
        
        Args:
            workflow: Workflow to execute
            cli_inputs: Command-line input overrides
        """
        self.workflow = workflow
        self.cli_inputs = cli_inputs or {}
        self.run_id = workflow.generate_run_id()
        self.config = workflow.config
        
        # Create run directory structure
        self.dirs = self.config.create_run_structure(
            workflow.name, 
            workflow.version, 
            self.run_id
        )
        
        # Save workflow copy
        workflow.save_workflow_copy(self.dirs["run_dir"])
        
        # Initialize managers
        self.input_manager = InputManager(workflow.inputs, self.dirs["inputs_dir"])
        self.output_manager = OutputManager(self.dirs["outputs_dir"], self.dirs["tmp_dir"])
        self.container_runner = ContainerRunner(self.dirs["run_dir"])
        
        # Initialize context for variable resolution
        self.context = {
            "run_dir": str(self.dirs["run_dir"]),
            "config": {
                "base_dir": str(self.config.base_dir),
                "refs": str(self.config.refs_dir)
            },
            "resources": {},
            "steps": {}
        }
        
        # Initialize path resolver
        self.path_resolver = PathResolver(self.context)
        
        # Initialize scheduler
        self.scheduler = Scheduler(self.workflow.steps)
        
        # Time limit configuration
        self.enable_time_limits = True  # Global switch for time limits
        self.default_time_limit = "1h"  # Default time limit if not specified
        
        # Initialize step status tracking
        self._init_step_status()
        
        # Load existing step status information if available
        self._load_step_status()
        
        logger.info(f"Initialized executor for workflow '{workflow.name}' with run_id: {self.run_id}")
    
    def _init_step_status(self):
        """Initialize step status for all steps."""
        self.context["steps"] = {}
        for step_name in self.workflow.steps:
            self.context["steps"][step_name] = {
                "status": StepStatus.PENDING.value,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "exit_code": None
            }
    
    def update_step_status(self, step_name: str, status: StepStatus, **kwargs):
        """
        Update the status of a step.
        
        Args:
            step_name: Name of the step
            status: New status
            **kwargs: Additional status information
        """
        if step_name not in self.context["steps"]:
            self.context["steps"][step_name] = {}
        
        self.context["steps"][step_name]["status"] = status.value
        
        # Update additional information
        for key, value in kwargs.items():
            self.context["steps"][step_name][key] = value
            
        logger.debug(f"Updated step '{step_name}' status to {status.value}")
    
    def execute(self, max_parallel: int = 1, enable_time_limits: bool = True, default_time_limit: str = "1h") -> bool:
        """
        Execute the workflow.
        
        Args:
            max_parallel: Maximum number of steps to execute in parallel (default: 1 for sequential execution)
            enable_time_limits: Whether to enforce time limits (default: True)
            default_time_limit: Default time limit for steps that don't specify one (default: 1h)
            
        Returns:
            True if execution was successful, False otherwise
        """
        logger.info(f"Starting execution of workflow '{self.workflow.name}' v{self.workflow.version}")
        
        # Update time limit configuration
        self.enable_time_limits = enable_time_limits
        self.default_time_limit = default_time_limit
        
        try:
            # Process inputs
            resolved_inputs = self.input_manager.process_inputs(self.cli_inputs)
            self.context["inputs"] = resolved_inputs
            
            # Update path resolver context
            self.path_resolver.update_context({"inputs": resolved_inputs})
            
            # Validate inputs
            if not self.input_manager.validate_inputs():
                logger.error("Input validation failed")
                return False
            
            if max_parallel <= 1:
                # Sequential execution (original behavior)
                return self._execute_sequential()
            else:
                # Parallel execution
                return self._execute_parallel(max_parallel)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return False
    
    def _execute_sequential(self) -> bool:
        """
        Execute workflow steps sequentially.
        
        Returns:
            True if execution was successful, False otherwise
        """
        # Get execution order
        execution_order = self.workflow.get_execution_order()
        logger.info(f"Sequential execution order: {', '.join(execution_order)}")
        
        # Execute each step
        for step_name in execution_order:
            success = self.execute_step(step_name)
            if not success:
                logger.error(f"Step '{step_name}' failed, aborting workflow")
                # Save step status information
                self._save_step_status()
                return False
        
        # Clean up temporary files
        self.output_manager.cleanup_temp_files()
        
        # Save step status information
        self._save_step_status()
        
        logger.success(f"Workflow execution completed successfully")
        return True
    
    def _execute_parallel(self, max_parallel: int) -> bool:
        """
        Execute workflow steps in parallel where possible.
        
        Args:
            max_parallel: Maximum number of steps to execute in parallel
            
        Returns:
            True if execution was successful, False otherwise
        """
        logger.info(f"Starting parallel execution with max_parallel={max_parallel}")
        
        completed_steps: Set[str] = set()
        failed_steps: Set[str] = set()
        
        # Create thread pool executor
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Continue until all steps are completed or any step fails
            while not self.scheduler.is_complete(completed_steps) and not failed_steps:
                # Get steps that are ready to execute
                ready_steps = self.scheduler.get_ready_steps(completed_steps)
                
                if not ready_steps:
                    # No steps are ready, but workflow is not complete
                    # This could happen if there's a circular dependency
                    logger.error("No steps are ready to execute, but workflow is not complete")
                    # Save step status information
                    self._save_step_status()
                    return False
                
                logger.info(f"Ready steps for parallel execution: {', '.join(ready_steps)}")
                
                # Submit ready steps to executor
                future_to_step = {
                    executor.submit(self.execute_step, step_name): step_name
                    for step_name in ready_steps
                    if step_name not in completed_steps
                }
                
                # Wait for steps to complete
                for future in concurrent.futures.as_completed(future_to_step):
                    step_name = future_to_step[future]
                    try:
                        success = future.result()
                        if success:
                            logger.success(f"Step '{step_name}' completed successfully")
                            completed_steps.add(step_name)
                        else:
                            logger.error(f"Step '{step_name}' failed")
                            failed_steps.add(step_name)
                            # Save step status information
                            self._save_step_status()
                            return False
                    except Exception as e:
                        logger.error(f"Exception executing step '{step_name}': {e}")
                        failed_steps.add(step_name)
                        # Save step status information
                        self._save_step_status()
                        return False
        
        # Clean up temporary files
        self.output_manager.cleanup_temp_files()
        
        # Save step status information
        self._save_step_status()
        
        logger.success(f"Workflow execution completed successfully")
        return True
    
    def _update_step_context(self, step_name: str) -> None:
        """
        Update context with step outputs.
        
        Args:
            step_name: Name of the completed step
        """
        step_outputs = self.output_manager.get_step_outputs(step_name)
        
        # Don't overwrite status information - just add outputs
        if step_name not in self.context["steps"]:
            self.context["steps"][step_name] = {}
            
        self.context["steps"][step_name]["outputs"] = {
            "files": [str(p) for p in step_outputs]
        }
        
        # Update path resolver context
        self.path_resolver.update_context({"steps": self.context["steps"]})
    
    def execute_step(self, step_name: str) -> bool:
        """
        Execute a single workflow step.
        
        Args:
            step_name: Name of the step to execute
            
        Returns:
            True if step execution was successful, False otherwise
        """
        step = self.workflow.steps[step_name]
        
        logger.info(f"Executing step '{step_name}'")
        
        # Update step status to running
        start_time = time.time()
        self.update_step_status(
            step_name, 
            StepStatus.RUNNING, 
            start_time=start_time
        )
        
        try:
            # Prepare step-specific context
            step_context = {
                "resources": step.resources,
                "step": {
                    "name": step_name
                }
            }
            self.path_resolver.update_context(step_context)
            
            # Resolve command
            resolved_command = step.resolve_command(self.path_resolver)
            
            # Prepare log file
            log_file = self.dirs["logs_dir"] / f"{step_name}.log"
            
            # Ensure container image is available
            if not self.container_runner.ensure_image_available(step.container):
                logger.error(f"Failed to ensure container image: {step.container}")
                end_time = time.time()
                self.update_step_status(
                    step_name, 
                    StepStatus.ERROR, 
                    end_time=end_time,
                    duration=f"{end_time - start_time:.2f}s",
                    error="Failed to ensure container image"
                )
                return False
            
            # Apply time limit settings
            resources = step.resources.copy()
            
            if self.enable_time_limits:
                # If no time limit is specified, use the default
                if "time_limit" not in resources or not resources["time_limit"]:
                    resources["time_limit"] = self.default_time_limit
                    logger.info(f"Using default time limit for step '{step_name}': {self.default_time_limit}")
            else:
                # If time limits are disabled, remove any time limit
                if "time_limit" in resources:
                    logger.info(f"Time limits disabled, ignoring time limit for step '{step_name}'")
                    resources.pop("time_limit")
            
            # Execute container
            exit_code = self.container_runner.run_container(
                image=step.container,
                command=resolved_command,
                resources=resources,
                log_file=log_file
            )
            
            # Update step outputs in context
            self._update_step_context(step_name)
            
            # Calculate duration
            end_time = time.time()
            duration = end_time - start_time
            duration_str = f"{duration:.2f}s"
            
            if exit_code == 0:
                logger.success(f"Step '{step_name}' completed successfully in {duration:.2f} seconds")
                self.update_step_status(
                    step_name, 
                    StepStatus.COMPLETED, 
                    end_time=end_time,
                    duration=duration_str,
                    exit_code=exit_code
                )
                return True
            elif exit_code == 124:
                # Special handling for time limit termination
                logger.warning(f"Step '{step_name}' was terminated after {duration:.2f} seconds due to time limit")
                
                # Write to log file that the step was terminated due to time limit
                with open(log_file, 'a') as f:
                    f.write(f"\n\n### STEP TERMINATED DUE TO TIME LIMIT ###\n")
                    f.write(f"The step was running for {duration:.2f} seconds when it reached its time limit.\n")
                
                # Record time limit termination in context
                self.update_step_status(
                    step_name, 
                    StepStatus.TERMINATED_TIME_LIMIT, 
                    end_time=end_time,
                    duration=duration_str,
                    exit_code=exit_code,
                    time_limit=resources.get("time_limit", "unknown")
                )
                
                # For now, we still consider this a failure, but we could make this configurable
                return False
            else:
                logger.error(f"Step '{step_name}' failed with exit code {exit_code}")
                self.update_step_status(
                    step_name, 
                    StepStatus.FAILED, 
                    end_time=end_time,
                    duration=duration_str,
                    exit_code=exit_code
                )
                return False
                
        except Exception as e:
            logger.error(f"Error executing step '{step_name}': {e}")
            
            # Record error in context
            end_time = time.time()
            self.update_step_status(
                step_name, 
                StepStatus.ERROR, 
                end_time=end_time,
                duration=f"{end_time - start_time:.2f}s",
                error=str(e)
            )
            
            return False
    
    def get_run_info(self) -> Dict[str, Any]:
        """
        Get information about the workflow run.
        
        Returns:
            Dictionary with run information
        """
        # First save latest step status to ensure it's up to date
        self._save_step_status()
        
        # Calculate overall workflow status
        overall_status = "completed"
        for step_info in self.context["steps"].values():
            if step_info["status"] in [
                StepStatus.FAILED.value, 
                StepStatus.ERROR.value, 
                StepStatus.TERMINATED_TIME_LIMIT.value
            ]:
                overall_status = "failed"
                break
            elif step_info["status"] in [StepStatus.RUNNING.value, StepStatus.PENDING.value]:
                overall_status = "running"
                break
        
        return {
            "workflow": self.workflow.name,
            "version": self.workflow.version,
            "run_id": self.run_id,
            "start_time": self.context.get("start_time", ""),
            "end_time": self.context.get("end_time", ""),
            "status": overall_status,
            "steps": self.context.get("steps", {}),
            "run_dir": str(self.dirs["run_dir"])
        }
    
    def _save_step_status(self):
        """Save step status information to a JSON file."""
        import json
        
        run_dir = self.dirs["run_dir"]
        step_status_file = run_dir / "step_status.json"
        
        try:
            # Create a clean copy of the steps data
            steps_data = {}
            for step_name, step_info in self.context["steps"].items():
                steps_data[step_name] = {k: v for k, v in step_info.items()}
                
                # Remove large or complex objects that don't need to be saved
                if "outputs" in steps_data[step_name]:
                    # Keep only the file paths, not the full objects
                    file_paths = steps_data[step_name]["outputs"].get("files", [])
                    steps_data[step_name]["outputs"] = {"files": file_paths}
            
            # Write to file
            with open(step_status_file, 'w') as f:
                json.dump(steps_data, f, indent=2)
                
            logger.debug(f"Saved step status information to {step_status_file}")
            
            # Also save overall workflow status
            status_file = run_dir / "status.txt"
            overall_status = "completed"
            
            # Check if any step failed
            for step_info in steps_data.values():
                if step_info["status"] in [
                    StepStatus.FAILED.value, 
                    StepStatus.ERROR.value, 
                    StepStatus.TERMINATED_TIME_LIMIT.value
                ]:
                    overall_status = "failed"
                    break
            
            with open(status_file, 'w') as f:
                f.write(overall_status)
                
            logger.debug(f"Saved workflow status ({overall_status}) to {status_file}")
            
        except Exception as e:
            logger.error(f"Failed to save step status information: {e}")
    
    def _load_step_status(self):
        """Load step status information from a JSON file."""
        import json
        
        run_dir = self.dirs["run_dir"]
        step_status_file = run_dir / "step_status.json"
        
        if not step_status_file.exists():
            return
        
        try:
            with open(step_status_file, 'r') as f:
                steps_data = json.load(f)
            
            # Update context with loaded data
            for step_name, step_info in steps_data.items():
                if step_name not in self.context["steps"]:
                    self.context["steps"][step_name] = {}
                
                for k, v in step_info.items():
                    self.context["steps"][step_name][k] = v
            
            logger.debug(f"Loaded step status information from {step_status_file}")
            
        except Exception as e:
            logger.error(f"Failed to load step status information: {e}") 