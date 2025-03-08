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
        
        logger.info(f"Initialized executor for workflow '{workflow.name}' with run_id: {self.run_id}")
    
    def execute(self, max_parallel: int = 1) -> bool:
        """
        Execute the workflow.
        
        Args:
            max_parallel: Maximum number of steps to execute in parallel (default: 1 for sequential execution)
            
        Returns:
            True if execution was successful, False otherwise
        """
        logger.info(f"Starting execution of workflow '{self.workflow.name}' v{self.workflow.version}")
        
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
                return False
            
            # Update context with step outputs
            self._update_step_context(step_name)
        
        # Clean up temporary files
        self.output_manager.cleanup_temp_files()
        
        logger.info(f"Workflow execution completed successfully")
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
                            logger.info(f"Step '{step_name}' completed successfully")
                            completed_steps.add(step_name)
                            # Update context with step outputs
                            self._update_step_context(step_name)
                        else:
                            logger.error(f"Step '{step_name}' failed")
                            failed_steps.add(step_name)
                            return False
                    except Exception as e:
                        logger.error(f"Exception executing step '{step_name}': {e}")
                        failed_steps.add(step_name)
                        return False
        
        # Clean up temporary files
        self.output_manager.cleanup_temp_files()
        
        logger.info(f"Workflow execution completed successfully")
        return True
    
    def _update_step_context(self, step_name: str) -> None:
        """
        Update context with step outputs.
        
        Args:
            step_name: Name of the completed step
        """
        step_outputs = self.output_manager.get_step_outputs(step_name)
        self.context["steps"][step_name] = {
            "outputs": {
                "files": [str(p) for p in step_outputs]
            }
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
                return False
            
            # Execute container
            start_time = time.time()
            
            exit_code = self.container_runner.run_container(
                image=step.container,
                command=resolved_command,
                resources=step.resources,
                log_file=log_file
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if exit_code == 0:
                logger.info(f"Step '{step_name}' completed successfully in {duration:.2f} seconds")
                return True
            else:
                logger.error(f"Step '{step_name}' failed with exit code {exit_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing step '{step_name}': {e}")
            return False
    
    def get_run_info(self) -> Dict[str, Any]:
        """
        Get information about the workflow run.
        
        Returns:
            Dictionary with run information
        """
        return {
            "workflow": self.workflow.name,
            "version": self.workflow.version,
            "run_id": self.run_id,
            "start_time": self.context.get("start_time", ""),
            "end_time": self.context.get("end_time", ""),
            "status": self.context.get("status", "unknown"),
            "steps": self.context.get("steps", {}),
            "run_dir": str(self.dirs["run_dir"])
        } 