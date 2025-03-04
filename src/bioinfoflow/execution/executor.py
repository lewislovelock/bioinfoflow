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
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from loguru import logger

from bioinfoflow.core.workflow import Workflow
from bioinfoflow.core.path_resolver import PathResolver
from bioinfoflow.io.input_manager import InputManager
from bioinfoflow.io.output_manager import OutputManager
from bioinfoflow.execution.container import ContainerRunner


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
        
        logger.info(f"Initialized executor for workflow '{workflow.name}' with run_id: {self.run_id}")
    
    def execute(self) -> bool:
        """
        Execute the workflow.
        
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
            
            # Get execution order
            execution_order = self.workflow.get_execution_order()
            logger.info(f"Execution order: {', '.join(execution_order)}")
            
            # Execute each step
            for step_name in execution_order:
                success = self.execute_step(step_name)
                if not success:
                    logger.error(f"Step '{step_name}' failed, aborting workflow")
                    return False
                
                # Update context with step outputs
                step_outputs = self.output_manager.get_step_outputs(step_name)
                self.context["steps"][step_name] = {
                    "outputs": {
                        "files": [str(p) for p in step_outputs]
                    }
                }
                
                # Update path resolver context
                self.path_resolver.update_context({"steps": self.context["steps"]})
            
            # Clean up temporary files
            self.output_manager.cleanup_temp_files()
            
            logger.info(f"Workflow execution completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return False
    
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