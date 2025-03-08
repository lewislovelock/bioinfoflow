"""
Command-line interface for BioinfoFlow.

This module provides the CLI commands for the BioinfoFlow workflow system.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any

import click
from loguru import logger

from bioinfoflow.core.config import Config
from bioinfoflow.core.workflow import Workflow
from bioinfoflow.execution.executor import WorkflowExecutor


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
def run(workflow_file: str, input: tuple, dry_run: bool, parallel: int):
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
            click.echo("\nDry run - workflow validation:")
            click.echo(f"  Name: {workflow.name}")
            click.echo(f"  Version: {workflow.version}")
            click.echo(f"  Description: {workflow.description}")
            click.echo(f"  Steps: {len(workflow.steps)}")
            click.echo("\nStep execution order:")
            for i, step_name in enumerate(workflow.get_execution_order(), 1):
                step = workflow.steps[step_name]
                click.echo(f"  {i}. {step_name} (container: {step.container})")
                click.echo(f"     Command: {step.command}")
                click.echo(f"     Dependencies: {step.after or 'None'}")
            return
        
        # Create executor
        executor = WorkflowExecutor(workflow, input_overrides)
        
        # Execute workflow
        if parallel > 1:
            click.echo(f"Running workflow with parallel execution (max {parallel} steps)")
        success = executor.execute(max_parallel=parallel)
        
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
    else:
        click.echo("Workflow file not found")
    
    # Check status file
    status_file = run_dir / "status.txt"
    if status_file.exists():
        with open(status_file, 'r') as f:
            status = f.read().strip()
        click.echo(f"Status: {status}")
    else:
        click.echo("Status: Unknown")
    
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


if __name__ == "__main__":
    cli() 