"""
Main CLI entry point for BioinfoFlow.

This module provides the main command-line interface entry point for
BioinfoFlow, handling argument parsing and routing to specific commands.
"""
import sys
from typing import Optional

from bioinfoflow.cli.command import cli


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # We're using Click now, so we just need to call the cli function
        cli(args)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


# Create a callable entry point for the CLI
def cli_main():
    """Entry point for CLI when called through setuptools."""
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main()) 