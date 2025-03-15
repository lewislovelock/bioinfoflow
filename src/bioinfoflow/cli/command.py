"""
This file has been refactored into multiple modules.

The CLI functionality has been divided into multiple modules:
- cli_core.py - Core CLI setup and utilities
- commands/run.py - Run workflow command
- commands/list.py - List workflow runs command 
- commands/status.py - Status command
- commands/db.py - Database commands
- commands/serve.py - API server command

This file remains only for backwards compatibility and will be removed in a future version.
"""

import warnings

warnings.warn(
    "The 'command.py' module has been refactored into separate modules. "
    "Please import from 'bioinfoflow.cli' instead.",
    DeprecationWarning, 
    stacklevel=2
)

# Import from the new location for backwards compatibility
from bioinfoflow.cli.cli_core import cli 