"""
Core functionality for the BioinfoFlow CLI.

This module provides the core command-line interface setup for BioinfoFlow,
including the main CLI group and shared utilities.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger
from rich.console import Console

# Remove default logger handler to avoid duplicate logs
logger.remove()

# Create a global console instance for rich output
console = Console()

# Check if database modules are available
try:
    from bioinfoflow.db.config import db_config
    from bioinfoflow.db.service import DatabaseService
    from bioinfoflow.db.repositories.workflow_repository import WorkflowRepository
    from bioinfoflow.db.repositories.run_repository import RunRepository
    has_database = True
except ImportError:
    has_database = False
    logger.warning("Database module not available, database functionality disabled")


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