"""
Scheduler module for BioinfoFlow.

This module handles step scheduling based on dependencies.
Supports both sequential and parallel execution strategies.
"""
from typing import Dict, List, Set, Any, Optional
from loguru import logger


class Scheduler:
    """
    Step scheduler class.
    
    Determines the execution order of steps based on dependencies.
    Supports identifying steps that can be executed in parallel.
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
                for dep in self.steps[step_name].after:
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
        
        A step is ready to execute if all its dependencies have been completed
        and it hasn't been completed yet.
        
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
            dependencies = set(step.after)
            if dependencies.issubset(completed_steps):
                ready_steps.append(step_name)
        
        logger.debug(f"Ready steps: {', '.join(ready_steps) if ready_steps else 'None'}")
        return ready_steps
    
    def get_dependency_levels(self) -> List[List[str]]:
        """
        Group steps by dependency level for optimal parallel execution.
        
        Returns:
            List of lists, where each inner list contains steps that can be executed in parallel
        """
        # Get execution order first to validate no cycles
        execution_order = self.get_execution_order()
        
        # Create a dependency graph
        graph = {step_name: set(self.steps[step_name].after) for step_name in self.steps}
        
        # Group steps by level
        levels = []
        remaining_steps = set(self.steps.keys())
        
        while remaining_steps:
            # Find steps with no remaining dependencies
            current_level = []
            for step_name in list(remaining_steps):
                if not graph[step_name].intersection(remaining_steps):
                    current_level.append(step_name)
            
            if not current_level:
                # This shouldn't happen if the graph is valid
                logger.error("Dependency resolution error: circular dependency detected")
                break
            
            # Add current level to levels
            levels.append(current_level)
            
            # Remove steps in current level from remaining steps
            remaining_steps -= set(current_level)
        
        logger.debug(f"Dependency levels: {levels}")
        return levels
    
    def is_complete(self, completed_steps: Set[str]) -> bool:
        """
        Check if all steps are complete.
        
        Args:
            completed_steps: Set of completed step names
            
        Returns:
            True if all steps are complete, False otherwise
        """
        return len(completed_steps) == len(self.steps) 