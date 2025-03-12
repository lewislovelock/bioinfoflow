"""
Command-line interface for BioinfoFlow.

This module provides the CLI commands for the BioinfoFlow workflow system.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any

import click
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

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


# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """BioinfoFlow: A workflow engine for bioinformatics."""
    if debug:
        # Set log level to DEBUG if debug flag is provided
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )
        logger.debug("Debug logging enabled")


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
            console = Console()
            
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
            click.echo(f"Running workflow with parallel execution (max {parallel} steps)")
        
        # Time limit settings
        enable_time_limits = not disable_time_limits
        if disable_time_limits:
            click.echo("Time limits are disabled for all steps")
        else:
            click.echo(f"Using default time limit of {default_time_limit} for steps without a specified limit")
        
        success = executor.execute(
            max_parallel=parallel,
            enable_time_limits=enable_time_limits,
            default_time_limit=default_time_limit
        )
        
        # Get run info
        run_info = executor.get_run_info()
        
        # Print summary
        click.echo("")
        if success:
            click.echo("Workflow run completed successfully")
        else:
            click.echo("Workflow run completed with errors")
        
        click.echo(f"Run ID: {run_info['run_id']}")
        click.echo(f"Run directory: {run_info['run_dir']}")
        
        # Print detailed step information
        if 'steps' in run_info and run_info['steps']:
            click.echo("\nStep details:")
            for step_name, step_info in run_info['steps'].items():
                status = step_info.get('status', 'unknown')
                duration = step_info.get('duration', 'unknown')
                exit_code = step_info.get('exit_code', 'unknown')
                
                if status == StepStatus.COMPLETED.value:
                    click.echo(f"  ✅ {step_name}: Completed in {duration}")
                elif status == StepStatus.TERMINATED_TIME_LIMIT.value:
                    time_limit = step_info.get('time_limit', 'unknown')
                    click.echo(f"  ⏱️  {step_name}: Terminated due to time limit ({time_limit}) after {duration}")
                elif status == StepStatus.FAILED.value:
                    click.echo(f"  ❌ {step_name}: Failed with exit code {exit_code} after {duration}")
                elif status == StepStatus.ERROR.value:
                    error = step_info.get('error', 'unknown error')
                    click.echo(f"  ❌ {step_name}: Error - {error}")
                elif status == StepStatus.RUNNING.value:
                    click.echo(f"  🔄 {step_name}: Running...")
                elif status == StepStatus.PENDING.value:
                    click.echo(f"  ⏳ {step_name}: Pending")
                elif status == StepStatus.SKIPPED.value:
                    click.echo(f"  ⏭️  {step_name}: Skipped")
                else:
                    click.echo(f"  ❓ {step_name}: {status}")
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--base-dir', '-d', type=click.Path(exists=True), help='Base directory for runs')
def list(base_dir: Optional[str]):
    """List workflow runs."""
    config = Config(base_dir)
    runs_dir = Path(config.runs_dir)
    
    if not runs_dir.exists():
        click.echo(f"No runs directory found at {runs_dir}")
        return
    
    click.echo(f"Workflow runs in {runs_dir}:")
    
    # Find all workflow directories
    workflow_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    
    if not workflow_dirs:
        click.echo("No workflow runs found")
        return
    
    # Print workflow runs
    for workflow_dir in sorted(workflow_dirs):
        click.echo(f"\n{workflow_dir.name}:")
        
        # Find all version directories
        version_dirs = [d for d in workflow_dir.iterdir() if d.is_dir()]
        
        for version_dir in sorted(version_dirs):
            click.echo(f"  Version {version_dir.name}:")
            
            # Find all run directories
            run_dirs = [d for d in version_dir.iterdir() if d.is_dir()]
            
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
                
                # Check if workflow completed successfully, not functional yet
                status_file = run_dir / "status.txt"
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        status = f.read().strip()
                else:
                    status = "Unknown"
                
                click.echo(f"    {run_id} ({formatted_time}) - {status} - Path: {run_dir}")


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
        click.echo(f"Run ID {run_id} not found")
        return
    
    click.echo(f"Run ID: {run_dir.name}")
    click.echo(f"Run directory: {run_dir}")
    
    # Check workflow file
    workflow_file = run_dir / "workflow.yaml"
    if workflow_file.exists():
        click.echo(f"Workflow file: {workflow_file}")
        
        # Load workflow metadata
        try:
            workflow = Workflow(workflow_file)
            click.echo(f"Workflow: {workflow.name} v{workflow.version}")
            click.echo(f"Description: {workflow.description}")
        except Exception as e:
            click.echo(f"Failed to load workflow metadata: {e}")
    else:
        click.echo("Workflow file not found")
    
    # Check status file
    status_file = run_dir / "status.txt"
    workflow_status = "Unknown"
    if status_file.exists():
        with open(status_file, 'r') as f:
            workflow_status = f.read().strip()
        click.echo(f"Status: {workflow_status}")
    else:
        click.echo("Status: Unknown")
    
    # Check step status
    steps_info = {}
    step_status_file = run_dir / "step_status.json"
    if step_status_file.exists():
        import json
        try:
            with open(step_status_file, 'r') as f:
                steps_info = json.load(f)
            
            if steps_info:
                click.echo("\nStep details:")
                for step_name, step_info in steps_info.items():
                    status = step_info.get('status', 'unknown')
                    duration = step_info.get('duration', 'unknown')
                    exit_code = step_info.get('exit_code', 'unknown')
                    
                    if status == StepStatus.COMPLETED.value:
                        click.echo(f"  ✅ {step_name}: Completed in {duration}")
                    elif status == StepStatus.TERMINATED_TIME_LIMIT.value:
                        time_limit = step_info.get('time_limit', 'unknown')
                        click.echo(f"  ⏱️  {step_name}: Terminated due to time limit ({time_limit}) after {duration}")
                    elif status == StepStatus.FAILED.value:
                        click.echo(f"  ❌ {step_name}: Failed with exit code {exit_code} after {duration}")
                    elif status == StepStatus.ERROR.value:
                        error = step_info.get('error', 'unknown error')
                        click.echo(f"  ❌ {step_name}: Error - {error}")
                    elif status == StepStatus.RUNNING.value:
                        click.echo(f"  🔄 {step_name}: Running...")
                    elif status == StepStatus.PENDING.value:
                        click.echo(f"  ⏳ {step_name}: Pending")
                    elif status == StepStatus.SKIPPED.value:
                        click.echo(f"  ⏭️  {step_name}: Skipped")
                    else:
                        click.echo(f"  ❓ {step_name}: {status}")
        except Exception as e:
            click.echo(f"Failed to load step status: {e}")
    
    # Check logs
    logs_dir = run_dir / "logs"
    if logs_dir.exists():
        click.echo("\nLogs:")
        for log_file in sorted(logs_dir.glob("*.log")):
            click.echo(f"  Path: {log_file}")
    else:
        click.echo("No logs found")
    
    # Check outputs
    outputs_dir = run_dir / "outputs"
    if outputs_dir.exists():
        click.echo("\nOutputs:")
        for output_file in sorted(outputs_dir.glob("*")):
            if output_file.is_file():
                size = output_file.stat().st_size
                click.echo(f"  Path: {output_file} ({size} bytes)")
    else:
        click.echo("No outputs found")


@cli.group()
def db():
    """Database management commands."""
    if not has_database:
        click.echo("Database functionality is not available.")
        sys.exit(1)


@db.command()
def init():
    """Initialize database schema."""
    try:
        # Create database tables
        db_config.create_tables()
        click.echo("Database initialized successfully.")
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)
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
                click.echo("No workflows found in the database.")
                return
            
            click.echo("\nWorkflows in database:")
            for workflow in workflows:
                click.echo(f"  ID: {workflow.id}, Name: {workflow.name}, Version: {workflow.version}")
                if workflow.description:
                    click.echo(f"    Description: {workflow.description}")
                click.echo(f"    Created: {workflow.created_at}")
                
                # Get run count
                run_repo = RunRepository(session)
                runs = run_repo.get_by_workflow_id(workflow.id)
                click.echo(f"    Runs: {len(runs)}")
                
                click.echo("")
                
        finally:
            session.close()
            
    except Exception as e:
        click.echo(f"Error listing workflows: {e}", err=True)
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
                click.echo(f"Workflow with ID {workflow_id} not found.")
                return
            
            click.echo(f"\nRuns for workflow '{workflow.name}' v{workflow.version}:")
            
            # Get runs
            run_repo = RunRepository(session)
            runs = run_repo.get_by_workflow_id(workflow_id)
            
            if not runs:
                click.echo("  No runs found.")
                return
            
            for run in runs:
                click.echo(f"  Run ID: {run.run_id}")
                click.echo(f"    Status: {run.status}")
                click.echo(f"    Started: {run.start_time}")
                if run.end_time:
                    click.echo(f"    Ended: {run.end_time}")
                    duration = run.end_time - run.start_time
                    click.echo(f"    Duration: {duration}")
                click.echo(f"    Run directory: {run.run_dir}")
                
                # Get step count
                from bioinfoflow.db.repositories.step_repository import StepRepository
                step_repo = StepRepository(session)
                steps = step_repo.get_by_run_id(run.id)
                click.echo(f"    Steps: {len(steps)}")
                
                click.echo("")
                
        finally:
            session.close()
            
    except Exception as e:
        click.echo(f"Error listing runs: {e}", err=True)
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
                click.echo(f"Run with ID {run_id} not found.")
                return
            
            # Get workflow
            workflow_repo = WorkflowRepository(session)
            workflow = workflow_repo.get_by_id(run.workflow_id)
            
            click.echo(f"\nSteps for run '{run_id}' of workflow '{workflow.name}' v{workflow.version}:")
            
            # Get steps
            from bioinfoflow.db.repositories.step_repository import StepRepository
            step_repo = StepRepository(session)
            steps = step_repo.get_by_run_id(run.id)
            
            if not steps:
                click.echo("  No steps found.")
                return
            
            for step in steps:
                if step.status == "COMPLETED":
                    status_icon = "✅"
                elif step.status == "RUNNING":
                    status_icon = "🔄"
                elif step.status == "FAILED":
                    status_icon = "❌"
                elif step.status == "TERMINATED_TIME_LIMIT":
                    status_icon = "⏱️"
                elif step.status == "PENDING":
                    status_icon = "⏳"
                elif step.status == "SKIPPED":
                    status_icon = "⏭️"
                else:
                    status_icon = "❓"
                    
                click.echo(f"  {status_icon} {step.step_name}: {step.status}")
                
                if step.start_time:
                    click.echo(f"    Started: {step.start_time}")
                if step.end_time:
                    click.echo(f"    Ended: {step.end_time}")
                    duration = step.end_time - step.start_time
                    click.echo(f"    Duration: {duration}")
                if step.log_file:
                    click.echo(f"    Log file: {step.log_file}")
                if step.outputs:
                    click.echo(f"    Outputs: {len(step.outputs.get('files', []))} files")
                
                click.echo("")
                
        finally:
            session.close()
            
    except Exception as e:
        click.echo(f"Error listing steps: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli() 