"""
Database commands for the BioinfoFlow CLI.

This module provides the commands for managing the BioinfoFlow database.
"""

import sys
from typing import Optional

import click
from rich.table import Table
from rich.text import Text

from bioinfoflow.cli.cli_core import console, cli, has_database

# Check if database modules are available
if has_database:
    from bioinfoflow.db.config import db_config
    from bioinfoflow.db.repositories.workflow_repository import WorkflowRepository
    from bioinfoflow.db.repositories.run_repository import RunRepository
    from bioinfoflow.db.repositories.step_repository import StepRepository


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
        # Create database tables - this is already done in main.py
        # but we'll do it again here for the explicit init command
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