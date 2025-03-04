"""
Scheduler module for BioinfoFlow.

This module handles step scheduling based on dependencies.
For the MVP, this is a simple sequential scheduler, but could be
extended to support parallel execution in the future.
"""
from typing import Dict, List, Set, Any, Optional
from loguru import logger


class Scheduler:
    """
    Step scheduler class.
    
    Determines the execution order of steps based on dependencies.
    """
    
    def __init__(self, steps: Dict[str, Any]):
        """
        Initialize scheduler.
        
        Args:
            steps: Dictionary of workflow steps
        """
        self.steps = steps
        logger.debug(f"Initialized Scheduler with {len(steps)} steps")
    
    def get_execution_order(self) -> List[str]:
        """
        Determine the execution order of steps.
        
        Returns:
            List of step names in execution order
        """
        # Implementation of topological sort
        visited: Set[str] = set()
        temp_mark: Set[str] = set()
        order: List[str] = []
        
        def visit(step_name: str) -> None:
            """Helper function for topological sort"""
            if step_name in temp_mark:
                raise ValueError(f"Circular dependency detected involving step '{step_name}'")
            
            if step_name not in visited:
                temp_mark.add(step_name)
                
                # Visit all dependencies
                for dep in self.steps[step_name].get("after", []):
                    visit(dep)
                
                temp_mark.remove(step_name)
                visited.add(step_name)
                order.append(step_name)
        
        # Visit each step
        for step_name in self.steps:
            if step_name not in visited:
                visit(step_name)
        
        # Reverse order to get correct execution sequence
        execution_order = list(reversed(order))
        logger.debug(f"Determined execution order: {', '.join(execution_order)}")
        
        return execution_order
    
    def get_ready_steps(self, completed_steps: Set[str]) -> List[str]:
        """
        Get steps that are ready to execute.
        
        Args:
            completed_steps: Set of completed step names
            
        Returns:
            List of step names that are ready to execute
        """
        ready_steps = []
        
        for step_name, step in self.steps.items():
            # Skip completed steps
            if step_name in completed_steps:
                continue
            
            # Check if all dependencies are completed
            dependencies = set(step.get("after", []))
            if dependencies.issubset(completed_steps):
                ready_steps.append(step_name)
        
        return ready_steps
    
    def is_complete(self, completed_steps: Set[str]) -> bool:
        """
        Check if all steps are complete.
        
        Args:
            completed_steps: Set of completed step names
            
        Returns:
            True if all steps are complete, False otherwise
        """
        return len(completed_steps) == len(self.steps) 