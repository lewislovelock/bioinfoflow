"""
List command for the BioinfoFlow CLI.

This module provides the command for listing BioinfoFlow workflow runs.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.table import Table
from rich.text import Text

from bioinfoflow.core.config import Config
from bioinfoflow.cli.cli_core import console, cli


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