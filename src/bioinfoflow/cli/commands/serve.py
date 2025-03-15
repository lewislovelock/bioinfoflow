"""
Serve command for the BioinfoFlow CLI.

This module provides the command for starting the BioinfoFlow API server.
"""

import sys

import click
from loguru import logger

from bioinfoflow.cli.cli_core import console, cli, has_database


@cli.command()
@click.option('--host', default="127.0.0.1", help='Host to bind the API server to')
@click.option('--port', default=8000, type=int, help='Port to bind the API server to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def serve(host: str, port: int, reload: bool):
    """Start the BioinfoFlow API server."""
    try:
        # Import uvicorn
        import uvicorn
    except ImportError:
        console.print("[bold red]Error:[/] uvicorn is required to run the API server")
        console.print("Install it with: [bold]pip install uvicorn[standard][/]")
        sys.exit(1)
    
    # Import FastAPI app
    try:
        from bioinfoflow.api import app
    except ImportError:
        console.print("[bold red]Error:[/] FastAPI is required to run the API server")
        console.print("Install it with: [bold]pip install fastapi[/]")
        sys.exit(1)
    
    # Check if database is available - but don't reinitialize it
    # as it's already done in main.py
    if not has_database:
        console.print("[bold yellow]Warning:[/] Database module not available")
        console.print("Some API features may not work correctly")
    
    # Print information
    console.print(f"\n[bold]Starting BioinfoFlow API server[/]")
    console.print(f"API documentation will be available at: [bold cyan]http://{host}:{port}/api/docs[/]")
    
    # Start uvicorn server
    console.print(f"\n[bold green]Server starting...[/]")
    
    try:
        uvicorn.run(
            "bioinfoflow.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        console.print(f"[bold red]Error starting server:[/] {e}")
        sys.exit(1) 