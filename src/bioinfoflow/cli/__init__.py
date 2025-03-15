"""
Command-line interface module for BioinfoFlow.

This module provides the command-line interface for running and managing
BioinfoFlow workflows.
"""
# Import the core CLI functionality
from bioinfoflow.cli.cli_core import cli

# Import all commands to register them with the CLI
from bioinfoflow.cli.commands import run
from bioinfoflow.cli.commands import list
from bioinfoflow.cli.commands import status
from bioinfoflow.cli.commands import db
from bioinfoflow.cli.commands import serve

# Import the main CLI entry point
from bioinfoflow.cli.main import cli_main


def main():
    """Main entry point for the CLI."""
    return cli_main() 