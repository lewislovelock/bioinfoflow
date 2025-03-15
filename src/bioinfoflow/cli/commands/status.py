"""
Status command for the BioinfoFlow CLI.

This module provides the command for checking the status of BioinfoFlow workflow runs.
"""

import sys
import json
from pathlib import Path
from typing import Optional

import click
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from bioinfoflow.core.config import Config
from bioinfoflow.core.workflow import Workflow
from bioinfoflow.core.models import StepStatus
from bioinfoflow.cli.cli_core import console, cli


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