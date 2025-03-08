#!/bin/bash
# Example script to run the parallel_workflow.yaml example
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "${SCRIPT_DIR}/.."

# Install the package in development mode if not already installed
pip install -e .

# Run the parallel workflow with 4 parallel steps
echo "Running the parallel workflow example with parallel execution..."
bioinfoflow run "${SCRIPT_DIR}/parallel_workflow.yaml" --parallel 4

echo "Done!" 