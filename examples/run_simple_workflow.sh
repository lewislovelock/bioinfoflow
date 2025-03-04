#!/bin/bash
# Example script to run the simple_workflow.yaml example
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "${SCRIPT_DIR}/.."

# Install the package in development mode if not already installed
pip install -e .

# Run the simple workflow
echo "Running the simple workflow example..."
bioinfoflow run "${SCRIPT_DIR}/simple_workflow.yaml"

echo "Done!" 