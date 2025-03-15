"""
Run command for the BioinfoFlow CLI.

This module provides the command for running BioinfoFlow workflows.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from threading import Thread, Event

import click
from loguru import logger
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from bioinfoflow.core.workflow import Workflow
from bioinfoflow.core.models import StepStatus
from bioinfoflow.execution.executor import WorkflowExecutor
from bioinfoflow.cli.cli_core import console, cli


@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--input', '-i', multiple=True, help='Input override in the format key=value')
@click.option('--dry-run', is_flag=True, help='Validate workflow without executing')
@click.option('--parallel', '-p', type=int, default=1, help='Maximum number of steps to execute in parallel (default: 1)')
@click.option('--disable-time-limits', is_flag=True, help='Disable time limits for all steps')
@click.option('--default-time-limit', type=str, default="1h", help='Default time limit for steps that don\'t specify one (default: 1h)')
def run(workflow_file: str, input: tuple, dry_run: bool, parallel: int, disable_time_limits: bool, default_time_limit: str):
    """Run a workflow from a YAML file."""
    workflow_file = Path(workflow_file)
    
    # Parse input overrides
    input_overrides = {}
    for item in input:
        if '=' in item:
            key, value = item.split('=', 1)
            input_overrides[key] = value
        
    try:
        # Load workflow
        workflow = Workflow(workflow_file)
        
        if dry_run:
            # Create workflow info panel
            workflow_info = Panel(
                f"[bold cyan]Name:[/] {workflow.name}\n"
                f"[bold cyan]Version:[/] {workflow.version}\n"
                f"[bold cyan]Description:[/] {workflow.description}\n"
                f"[bold cyan]Steps:[/] {len(workflow.steps)}",
                title="[bold]Workflow Information[/]",
                border_style="blue"
            )
            console.print("\n[bold]Dry run - workflow validation:[/]")
            console.print(workflow_info)
            
            # Create step execution table
            table = Table(title="Step Execution Order", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=4)
            table.add_column("Step Name", style="cyan")
            table.add_column("Container", style="green")
            table.add_column("Dependencies", style="yellow")
            table.add_column("Time Limit", style="red")
            
            for i, step_name in enumerate(workflow.get_execution_order(), 1):
                step = workflow.steps[step_name]
                time_limit = step.resources.get("time_limit", "Not set")
                dependencies = ", ".join(step.after) if step.after else "None"
                
                table.add_row(
                    str(i),
                    step_name,
                    step.container,
                    dependencies,
                    time_limit
                )
            
            console.print(table)
            
            # Create command details tree
            console.print("\n[bold]Command Details:[/]")
            tree = Tree("[bold]Steps[/]")
            
            for step_name in workflow.get_execution_order():
                step = workflow.steps[step_name]
                step_node = tree.add(f"[cyan]{step_name}[/]")
                step_node.add(f"[yellow]Command:[/] {step.command}")
            
            console.print(tree)
            return
        
        # Create executor
        executor = WorkflowExecutor(workflow, input_overrides)
        
        # Execute workflow
        if parallel > 1:
            console.print(f"Running workflow with [bold cyan]parallel execution[/] (max {parallel} steps)")
        
        # Time limit settings
        enable_time_limits = not disable_time_limits
        if disable_time_limits:
            console.print("[yellow]Time limits are disabled[/] for all steps")
        else:
            console.print(f"Using default time limit of [bold]{default_time_limit}[/] for steps without a specified limit")
        
        # Get execution order to track progress
        execution_order = workflow.get_execution_order()
        total_steps = len(execution_order)
        
        # Create a progress display
        console.print(f"\n[bold]Executing workflow[/] [cyan]{workflow.name}[/] [green]v{workflow.version}[/] with [bold]{total_steps}[/] steps")
        
        # Create a progress context with multiple progress bars
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=console,
            expand=True
        ) as progress:
            # Create overall progress bar
            overall_task = progress.add_task(f"[cyan]Overall progress[/]", total=total_steps)
            
            # Dictionary to store task IDs for each step
            step_tasks = {}
            
            # Create a task for each step (initially hidden)
            for step_name in execution_order:
                step_task = progress.add_task(f"[yellow]{step_name}[/]", total=100, visible=False)
                step_tasks[step_name] = step_task
            
            # Create a stop event for the progress monitoring thread
            stop_event = Event()
            
            # Function to monitor step status and update progress
            def monitor_progress():
                completed_steps = 0
                step_statuses = {}
                
                while not stop_event.is_set():
                    # Get current run info
                    run_info = executor.get_run_info()
                    
                    if 'steps' in run_info and run_info['steps']:
                        # Update step progress
                        for step_name, step_info in run_info['steps'].items():
                            if step_name not in step_tasks:
                                continue
                                
                            status = step_info.get('status', 'unknown')
                            
                            # Only update if status has changed
                            if step_name not in step_statuses or step_statuses[step_name] != status:
                                step_statuses[step_name] = status
                                
                                if status == StepStatus.PENDING.value:
                                    # Make the step visible when it becomes pending
                                    progress.update(step_tasks[step_name], visible=True, completed=0)
                                elif status == StepStatus.RUNNING.value:
                                    # Just ensure it's visible and not complete
                                    progress.update(step_tasks[step_name], visible=True, completed=50)
                                elif status in [StepStatus.COMPLETED.value, StepStatus.FAILED.value, 
                                              StepStatus.ERROR.value, StepStatus.TERMINATED_TIME_LIMIT.value,
                                              StepStatus.SKIPPED.value]:
                                    # Step is done (success or failure), mark as complete
                                    progress.update(step_tasks[step_name], visible=True, completed=100)
                                    
                        # Update the overall progress
                        new_completed_steps = sum(1 for s, info in run_info['steps'].items() 
                                               if info.get('status') in [StepStatus.COMPLETED.value, 
                                                                        StepStatus.FAILED.value,
                                                                        StepStatus.ERROR.value, 
                                                                        StepStatus.TERMINATED_TIME_LIMIT.value,
                                                                        StepStatus.SKIPPED.value])
                        
                        if new_completed_steps != completed_steps:
                            completed_steps = new_completed_steps
                            progress.update(overall_task, completed=completed_steps)
                    
                    # Sleep briefly to avoid excessive CPU usage
                    time.sleep(0.1)
            
            # Start the progress monitoring thread
            monitor_thread = Thread(target=monitor_progress)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                # Execute the workflow
                success = executor.execute(
                    max_parallel=parallel,
                    enable_time_limits=enable_time_limits,
                    default_time_limit=default_time_limit
                )
                
                # Ensure all progress bars are updated to 100% when workflow is complete
                if success:
                    # Update all step tasks to 100%
                    for step_name in execution_order:
                        progress.update(step_tasks[step_name], visible=True, completed=100)
                    # Update overall progress to 100%
                    progress.update(overall_task, completed=total_steps)
                    
                # Give the progress bars a moment to render
                time.sleep(0.5)
                
            finally:
                # Stop the progress monitoring thread
                stop_event.set()
                monitor_thread.join(timeout=1.0)
        
        # Get run info
        run_info = executor.get_run_info()
        
        # Print summary
        console.print("")
        if success:
            console.print("[bold green]Workflow run completed successfully[/]")
        else:
            console.print("[bold red]Workflow run completed with errors[/]")
        
        console.print(f"[bold]Run ID:[/] {run_info['run_id']}")
        console.print(f"[bold]Run directory:[/] {run_info['run_dir']}")
        
        # Print detailed step information
        if 'steps' in run_info and run_info['steps']:
            console.print("\n[bold]Step details:[/]")
            
            # Create a table for step details
            step_table = Table(show_header=False, box=None)
            step_table.add_column("Status", style="bold")
            step_table.add_column("Details")
            
            for step_name, step_info in run_info['steps'].items():
                status = step_info.get('status', 'unknown')
                duration = step_info.get('duration', 'unknown')
                exit_code = step_info.get('exit_code', 'unknown')
                
                if status == StepStatus.COMPLETED.value:
                    status_text = "✅"
                    details = f"[cyan]{step_name}:[/] Completed in [green]{duration}[/]"
                elif status == StepStatus.TERMINATED_TIME_LIMIT.value:
                    status_text = "⏱️"
                    time_limit = step_info.get('time_limit', 'unknown')
                    details = f"[cyan]{step_name}:[/] Terminated due to time limit ([yellow]{time_limit}[/]) after {duration}"
                elif status == StepStatus.FAILED.value:
                    status_text = "❌"
                    details = f"[cyan]{step_name}:[/] Failed with exit code [red]{exit_code}[/] after {duration}"
                elif status == StepStatus.ERROR.value:
                    status_text = "❌"
                    error = step_info.get('error', 'unknown error')
                    details = f"[cyan]{step_name}:[/] Error - [red]{error}[/]"
                elif status == StepStatus.RUNNING.value:
                    status_text = "🔄"
                    details = f"[cyan]{step_name}:[/] [yellow]Running...[/]"
                elif status == StepStatus.PENDING.value:
                    status_text = "⏳"
                    details = f"[cyan]{step_name}:[/] [dim]Pending[/]"
                elif status == StepStatus.SKIPPED.value:
                    status_text = "⏭️"
                    details = f"[cyan]{step_name}:[/] [dim]Skipped[/]"
                else:
                    status_text = "❓"
                    details = f"[cyan]{step_name}:[/] {status}"
                
                step_table.add_row(status_text, details)
            
            console.print(step_table)
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1) 