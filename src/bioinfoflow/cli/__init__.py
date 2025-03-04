"""
Command-line interface module for BioinfoFlow.

This module provides the command-line interface for running and managing
BioinfoFlow workflows.
"""
# Import the main CLI entry points
from bioinfoflow.cli.command import cli
from bioinfoflow.cli.main import cli_main


def main():
    """Main entry point for the CLI."""
    return cli_main() 