"""
Command-line interface for BioinfoFlow.

This module provides the CLI commands for the BioinfoFlow workflow system.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from threading import Thread, Event

import click
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live

from bioinfoflow.core.config import Config
from bioinfoflow.core.workflow import Workflow
from bioinfoflow.core.models import StepStatus
from bioinfoflow.execution.executor import WorkflowExecutor

# Import database modules if available
try:
    from bioinfoflow.db.config import db_config
    from bioinfoflow.db.service import DatabaseService
    from bioinfoflow.db.repositories.workflow_repository import WorkflowRepository
    from bioinfoflow.db.repositories.run_repository import RunRepository
    has_database = True
except ImportError:
    has_database = False
    logger.warning("Database module not available, database functionality disabled")


# Configure loguru logger - remove default handler
logger.remove()

# Create a global console instance for rich output
console = Console()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """BioinfoFlow: A workflow engine for bioinformatics."""
    # Configure logging based on debug flag
    if debug:
        # Set log level to DEBUG if debug flag is provided
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )
        logger.debug("Debug logging enabled")
    else:
        # In normal mode, only log warnings and errors to stderr
        logger.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <level>{message}</level>",
            level="WARNING",
            colorize=True,
        )
        
        # Also log to file for all levels
        log_dir = Path.home() / ".bioinfoflow" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "bioinfoflow.log"
        logger.add(
            str(log_file),
            rotation="10 MB",
            retention="1 week",
            level="INFO",
        )


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
                                    progress.update(step_tasks[step_name], completed=100)
                                    
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
                    time.sleep(0.5)
            
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


@cli.command()
@click.option('--base-dir', '-d', type=click.Path(exists=True), help='Base directory for runs')
def list(base_dir: Optional[str]):
    """List workflow runs."""
    config = Config(base_dir)
    runs_dir = Path(config.runs_dir)
    
    if not runs_dir.exists():
        console.print(f"[yellow]No runs directory found at[/] {runs_dir}")
        return
    
    console.print(f"[bold]Workflow runs in[/] {runs_dir}:")
    
    # Find all workflow directories
    workflow_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    
    if not workflow_dirs:
        console.print("[yellow]No workflow runs found[/]")
        return
    
    # Print workflow runs
    for workflow_dir in sorted(workflow_dirs):
        console.print(f"\n[bold cyan]{workflow_dir.name}:[/]")
        
        # Find all version directories
        version_dirs = [d for d in workflow_dir.iterdir() if d.is_dir()]
        
        for version_dir in sorted(version_dirs):
            console.print(f"  [bold]Version {version_dir.name}:[/]")
            
            # Find all run directories
            run_dirs = [d for d in version_dir.iterdir() if d.is_dir()]
            
            # Create a table for runs
            if run_dirs:
                run_table = Table(show_header=True, box=None, pad_edge=False)
                run_table.add_column("Run ID", style="cyan")
                run_table.add_column("Timestamp", style="green")
                run_table.add_column("Status", style="bold")
                run_table.add_column("Path", style="dim")
                
                for run_dir in sorted(run_dirs, key=lambda d: d.stat().st_mtime, reverse=True):
                    # Get run timestamp from directory name
                    run_id = run_dir.name
                    ymd = run_id.split('_')[0]
                    hms = run_id.split('_')[1]
                    
                    # Format timestamp
                    try:
                        year = ymd[0:4]
                        month = ymd[4:6]
                        day = ymd[6:8]
                        hour = hms[0:2]
                        minute = hms[2:4]
                        second = hms[4:6]
                        formatted_time = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                    except:
                        formatted_time = "Unknown"
                    
                    # Check if workflow completed successfully
                    status_file = run_dir / "status.txt"
                    if status_file.exists():
                        with open(status_file, 'r') as f:
                            status = f.read().strip()
                            status_style = "green" if status == "completed" else "red"
                            status_text = Text(status, style=status_style)
                    else:
                        status_text = Text("Unknown", style="yellow")
                    
                    run_table.add_row(run_id, formatted_time, status_text, str(run_dir))
                
                console.print(run_table)
            else:
                console.print("    [dim]No runs found[/]")


@cli.command()
@click.argument('run_id')
@click.option('--base-dir', '-d', type=click.Path(exists=True), help='Base directory for runs')
def status(run_id: str, base_dir: Optional[str]):
    """Check the status of a workflow run."""
    config = Config(base_dir)
    runs_dir = Path(config.runs_dir)
    
    # Find the run directory
    run_dir = None
    for workflow_dir in runs_dir.iterdir():
        if not workflow_dir.is_dir():
            continue
        
        for version_dir in workflow_dir.iterdir():
            if not version_dir.is_dir():
                continue
            
            for rd in version_dir.iterdir():
                if rd.name.endswith(run_id):
                    run_dir = rd
                    break
            
            if run_dir:
                break
        
        if run_dir:
            break
    
    if not run_dir:
        console.print(f"[bold red]Run ID {run_id} not found[/]")
        return
    
    # Create a panel for run information
    run_info = [
        f"[bold cyan]Run ID:[/] {run_dir.name}",
        f"[bold cyan]Run directory:[/] {run_dir}"
    ]
    
    # Check workflow file
    workflow_file = run_dir / "workflow.yaml"
    if workflow_file.exists():
        run_info.append(f"[bold cyan]Workflow file:[/] {workflow_file}")
        
        # Load workflow metadata
        try:
            workflow = Workflow(workflow_file)
            run_info.append(f"[bold cyan]Workflow:[/] {workflow.name} v{workflow.version}")
            run_info.append(f"[bold cyan]Description:[/] {workflow.description}")
        except Exception as e:
            run_info.append(f"[bold red]Failed to load workflow metadata:[/] {e}")
    else:
        run_info.append("[yellow]Workflow file not found[/]")
    
    # Check status file
    status_file = run_dir / "status.txt"
    workflow_status = "Unknown"
    if status_file.exists():
        with open(status_file, 'r') as f:
            workflow_status = f.read().strip()
        status_style = "green" if workflow_status == "completed" else "red"
        run_info.append(f"[bold cyan]Status:[/] [{status_style}]{workflow_status}[/]")
    else:
        run_info.append("[bold cyan]Status:[/] [yellow]Unknown[/]")
    
    # Display run information panel
    console.print(Panel("\n".join(run_info), title=f"[bold]Run Status: {run_id}[/]", border_style="blue"))
    
    # Check step status
    steps_info = {}
    step_status_file = run_dir / "step_status.json"
    if step_status_file.exists():
        import json
        try:
            with open(step_status_file, 'r') as f:
                steps_info = json.load(f)
            
            if steps_info:
                # Create a table for step details
                step_table = Table(title="Step Details", show_header=True)
                step_table.add_column("Status", width=3)
                step_table.add_column("Step", style="cyan")
                step_table.add_column("Status", style="bold")
                step_table.add_column("Duration", style="green")
                step_table.add_column("Details", style="dim")
                
                for step_name, step_info in steps_info.items():
                    status = step_info.get('status', 'unknown')
                    duration = step_info.get('duration', 'unknown')
                    exit_code = step_info.get('exit_code', 'unknown')
                    
                    if status == StepStatus.COMPLETED.value:
                        status_icon = "✅"
                        status_text = Text("Completed", style="green")
                        details = ""
                    elif status == StepStatus.TERMINATED_TIME_LIMIT.value:
                        status_icon = "⏱️"
                        status_text = Text("Terminated", style="yellow")
                        time_limit = step_info.get('time_limit', 'unknown')
                        details = f"Time limit: {time_limit}"
                    elif status == StepStatus.FAILED.value:
                        status_icon = "❌"
                        status_text = Text("Failed", style="red")
                        details = f"Exit code: {exit_code}"
                    elif status == StepStatus.ERROR.value:
                        status_icon = "❌"
                        status_text = Text("Error", style="red")
                        error = step_info.get('error', 'unknown error')
                        details = error
                    elif status == StepStatus.RUNNING.value:
                        status_icon = "🔄"
                        status_text = Text("Running", style="yellow")
                        details = ""
                    elif status == StepStatus.PENDING.value:
                        status_icon = "⏳"
                        status_text = Text("Pending", style="dim")
                        details = ""
                    elif status == StepStatus.SKIPPED.value:
                        status_icon = "⏭️"
                        status_text = Text("Skipped", style="dim")
                        details = ""
                    else:
                        status_icon = "❓"
                        status_text = Text(status, style="yellow")
                        details = ""
                    
                    step_table.add_row(status_icon, step_name, status_text, duration, details)
                
                console.print(step_table)
        except Exception as e:
            console.print(f"[bold red]Failed to load step status:[/] {e}")
    
    # Check logs
    logs_dir = run_dir / "logs"
    if logs_dir.exists():
        log_files = list(sorted(logs_dir.glob("*.log")))
        if log_files:
            log_table = Table(title="Log Files", show_header=True)
            log_table.add_column("File", style="cyan")
            log_table.add_column("Size", style="green")
            
            for log_file in log_files:
                size = log_file.stat().st_size
                size_str = f"{size} bytes"
                if size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                
                log_table.add_row(str(log_file), size_str)
            
            console.print(log_table)
        else:
            console.print("[yellow]No log files found[/]")
    else:
        console.print("[yellow]No logs directory found[/]")
    
    # Check outputs
    outputs_dir = run_dir / "outputs"
    if outputs_dir.exists():
        output_files = list(sorted(outputs_dir.glob("*")))
        if output_files:
            output_table = Table(title="Output Files", show_header=True)
            output_table.add_column("File", style="cyan")
            output_table.add_column("Size", style="green")
            
            for output_file in output_files:
                if output_file.is_file():
                    size = output_file.stat().st_size
                    size_str = f"{size} bytes"
                    if size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    
                    output_table.add_row(str(output_file), size_str)
            
            console.print(output_table)
        else:
            console.print("[yellow]No output files found[/]")
    else:
        console.print("[yellow]No outputs directory found[/]")


@cli.group()
def db():
    """Database management commands."""
    if not has_database:
        console.print("[bold red]Database functionality is not available.[/]")
        sys.exit(1)


@db.command()
def init():
    """Initialize database schema."""
    try:
        # Create database tables
        db_config.create_tables()
        console.print("[bold green]Database initialized successfully.[/]")
    except Exception as e:
        console.print(f"[bold red]Error initializing database:[/] {e}", err=True)
        sys.exit(1)


@db.command()
def list_workflows():
    """List workflows stored in the database."""
    try:
        session = db_config.get_session()
        
        try:
            workflow_repo = WorkflowRepository(session)
            workflows = workflow_repo.get_all()
            
            if not workflows:
                console.print("[yellow]No workflows found in the database.[/]")
                return
            
            # Create a table for workflows
            workflow_table = Table(title="Workflows in Database", show_header=True)
            workflow_table.add_column("ID", style="dim")
            workflow_table.add_column("Name", style="cyan")
            workflow_table.add_column("Version", style="green")
            workflow_table.add_column("Description", style="yellow")
            workflow_table.add_column("Created", style="dim")
            workflow_table.add_column("Runs", style="magenta")
            
            for workflow in workflows:
                # Get run count
                run_repo = RunRepository(session)
                runs = run_repo.get_by_workflow_id(workflow.id)
                
                workflow_table.add_row(
                    str(workflow.id),
                    workflow.name,
                    workflow.version,
                    workflow.description or "",
                    str(workflow.created_at),
                    str(len(runs))
                )
            
            console.print(workflow_table)
                
        finally:
            session.close()
            
    except Exception as e:
        console.print(f"[bold red]Error listing workflows:[/] {e}", err=True)
        sys.exit(1)


@db.command()
@click.argument('workflow_id', type=int)
def list_runs(workflow_id: int):
    """List runs for a workflow."""
    try:
        session = db_config.get_session()
        
        try:
            # Get workflow
            workflow_repo = WorkflowRepository(session)
            workflow = workflow_repo.get_by_id(workflow_id)
            
            if not workflow:
                console.print(f"[bold red]Workflow with ID {workflow_id} not found.[/]")
                return
            
            console.print(f"\n[bold]Runs for workflow[/] [cyan]'{workflow.name}'[/] [green]v{workflow.version}[/]:")
            
            # Get runs
            run_repo = RunRepository(session)
            runs = run_repo.get_by_workflow_id(workflow_id)
            
            if not runs:
                console.print("  [yellow]No runs found.[/]")
                return
            
            # Create a table for runs
            run_table = Table(show_header=True)
            run_table.add_column("Run ID", style="cyan")
            run_table.add_column("Status", style="bold")
            run_table.add_column("Started", style="green")
            run_table.add_column("Ended", style="green")
            run_table.add_column("Duration", style="yellow")
            run_table.add_column("Steps", style="magenta")
            
            for run in runs:
                # Get step count
                from bioinfoflow.db.repositories.step_repository import StepRepository
                step_repo = StepRepository(session)
                steps = step_repo.get_by_run_id(run.id)
                
                # Format status with color
                status_style = "green" if run.status == "COMPLETED" else "red" if run.status == "FAILED" else "yellow"
                status_text = Text(run.status, style=status_style)
                
                # Calculate duration if run has ended
                duration = ""
                if run.end_time:
                    duration = str(run.end_time - run.start_time)
                
                run_table.add_row(
                    run.run_id,
                    status_text,
                    str(run.start_time),
                    str(run.end_time) if run.end_time else "",
                    duration,
                    str(len(steps))
                )
            
            console.print(run_table)
                
        finally:
            session.close()
            
    except Exception as e:
        console.print(f"[bold red]Error listing runs:[/] {e}", err=True)
        sys.exit(1)


@db.command()
@click.argument('run_id')
def list_steps(run_id: str):
    """List steps for a run."""
    try:
        session = db_config.get_session()
        
        try:
            # Get run
            run_repo = RunRepository(session)
            run = run_repo.get_by_run_id(run_id)
            
            if not run:
                console.print(f"[bold red]Run with ID {run_id} not found.[/]")
                return
            
            # Get workflow
            workflow_repo = WorkflowRepository(session)
            workflow = workflow_repo.get_by_id(run.workflow_id)
            
            console.print(f"\n[bold]Steps for run[/] [cyan]'{run_id}'[/] of workflow [green]'{workflow.name}'[/] v{workflow.version}:")
            
            # Get steps
            from bioinfoflow.db.repositories.step_repository import StepRepository
            step_repo = StepRepository(session)
            steps = step_repo.get_by_run_id(run.id)
            
            if not steps:
                console.print("  [yellow]No steps found.[/]")
                return
            
            # Create a table for steps
            step_table = Table(show_header=True)
            step_table.add_column("Status", width=3)
            step_table.add_column("Step Name", style="cyan")
            step_table.add_column("Status", style="bold")
            step_table.add_column("Started", style="green")
            step_table.add_column("Ended", style="green")
            step_table.add_column("Duration", style="yellow")
            
            for step in steps:
                # Determine status icon and style
                if step.status == "COMPLETED":
                    status_icon = "✅"
                    status_text = Text(step.status, style="green")
                elif step.status == "RUNNING":
                    status_icon = "🔄"
                    status_text = Text(step.status, style="yellow")
                elif step.status == "FAILED":
                    status_icon = "❌"
                    status_text = Text(step.status, style="red")
                elif step.status == "TERMINATED_TIME_LIMIT":
                    status_icon = "⏱️"
                    status_text = Text(step.status, style="yellow")
                elif step.status == "PENDING":
                    status_icon = "⏳"
                    status_text = Text(step.status, style="dim")
                elif step.status == "SKIPPED":
                    status_icon = "⏭️"
                    status_text = Text(step.status, style="dim")
                else:
                    status_icon = "❓"
                    status_text = Text(step.status, style="yellow")
                
                # Calculate duration if step has ended
                duration = ""
                if step.start_time and step.end_time:
                    duration = str(step.end_time - step.start_time)
                
                step_table.add_row(
                    status_icon,
                    step.step_name,
                    status_text,
                    str(step.start_time) if step.start_time else "",
                    str(step.end_time) if step.end_time else "",
                    duration
                )
            
            console.print(step_table)
            
            # Show additional details for steps with outputs
            for step in steps:
                if step.outputs and 'files' in step.outputs:
                    console.print(f"\n[bold]Outputs for step[/] [cyan]{step.step_name}[/]:")
                    for file_path in step.outputs['files']:
                        console.print(f"  {file_path}")
                
                if step.log_file:
                    console.print(f"[bold]Log file for step[/] [cyan]{step.step_name}[/]: {step.log_file}")
                
        finally:
            session.close()
            
    except Exception as e:
        console.print(f"[bold red]Error listing steps:[/] {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli() 