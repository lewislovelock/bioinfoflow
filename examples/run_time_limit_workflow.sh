#!/bin/bash
# Example script to run the time_limit_workflow.yaml example
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "${SCRIPT_DIR}/.."

# Install the package in development mode if not already installed
pip install -e .

# Run the time limit workflow with default settings
echo "Running the time limit workflow example with default settings..."
bioinfoflow run "${SCRIPT_DIR}/time_limit_workflow.yaml" --parallel 2

# Run with a custom default time limit
echo -e "\n\nRunning with a custom default time limit..."
bioinfoflow run "${SCRIPT_DIR}/time_limit_workflow.yaml" --parallel 2 --default-time-limit 2m

# Run with time limits disabled
echo -e "\n\nRunning with time limits disabled..."
bioinfoflow run "${SCRIPT_DIR}/time_limit_workflow.yaml" --parallel 2 --disable-time-limits

echo "Done!" 