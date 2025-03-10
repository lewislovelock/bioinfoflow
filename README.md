# BioinfoFlow MVP Specification 🧬

## Overview 📋

BioinfoFlow is a bioinformatics workflow engine designed for reproducible, container-native data analysis pipelines. This MVP version emphasizes simplicity following Occam's razor, focusing on the essential functionality:

- Workflow definition
- Step execution
- Input management
- Directory resolution
- Resource allocation

Experimental features are retained as hooks for future expansion but not required for core functionality.

## Core Concepts 💡

### Workflow

A named, versioned pipeline that includes:
- Description (optional)
- Global configuration
- Input definitions
- Execution steps

### Steps

Basic execution units within a workflow. Each step defines:
- Container image
- Command to execute
- Resource requirements (CPU, memory)
- Dependencies on other steps

### Directory Configuration & Path Resolution

A global `base_dir` is used to generate directories for:
- References
- Workflow definitions
- Run logs and outputs

Users can customize these directories or use the defaults.

### Variable Substitution

Use the `${...}` syntax to reference:
- Configuration values: `${config.parameter}`
- Input paths: `${inputs.path}`
- Outputs from previous steps: `${steps.step_name.outputs.output_name}`

This enables dynamic command construction based on workflow context.

## Directory Structure 📁

### Base Configuration

The default directory structure is organized around `base_dir` (defaults to current working directory):

```
${base_dir}/
├── refs/          # Reference data
├── workflows/     # Workflow definitions
└── runs/          # Workflow run logs and outputs
```

### Path Resolution Rules

- **Absolute paths** (starting with `/`): Used as-is
- **Relative paths**: Resolved based on context:
  - Input paths: Resolved relative to the current working directory when the workflow is launched
  - Output paths: Relative to `${base_dir}/runs/<workflow_name>/<version>/<run_id>/outputs/`
  - Reference paths: Relative to `${base_dir}/refs/`

When a workflow is executed, input files are automatically copied or symbolically linked to the `${run_dir}/inputs/` directory, making them accessible within the workflow regardless of their original location.

### Run Directory Structure

Each workflow execution creates a structured directory:

```
${base_dir}/runs/
└── <workflow_name>/
    └── <version>/
        └── <run_id>/           # Timestamp + random string
            ├── workflow.yaml   # Copy of workflow definition
            ├── inputs/         # Input files/links
            ├── outputs/        # Generated output files
            ├── logs/           # Execution logs
            └── tmp/            # Temporary files (deleted after analysis)
```

## YAML Definition Structure ⚙️

Below is a simplified YAML example demonstrating the core fields:

```yaml
# Workflow basic information
name: my_workflow          # Required: Workflow name
version: "1.0.0"           # Required: Workflow version
description: "Example workflow demonstrating the MVP design"  # Optional description

# Global configuration
config:
  base_dir: "/your/path"    # Optional: Custom base directory (default: current directory)
  refs: "refs"              # Reference data directory (relative to base_dir)
  workflows: "workflows"    # Workflow definitions directory
  runs: "runs"              # Workflow run logs directory

# Input configuration
inputs:
  path: "path/to/input/*.fastq.gz"  # Input path supporting glob patterns (relative to current directory or absolute)

# Workflow steps definition
steps:
  fastqc:                                     # Step name
    container: "biocontainers/fastqc:v0.11.9" # Container image
    command: "fastqc ${inputs.path} -o ${run_dir}/outputs"  # Command to execute
    resources:                                # Resource requirements
      cpu: 2
      memory: "4G"
      time_limit: "1h"                        # Optional time limit (e.g., 1h, 30m, 2h30m, 45s)
    after: []                                 # Dependencies (none for this step)

  bwa_mem:
    container: "biocontainers/bwa:v0.7.17"
    # The "command:" below uses YAML's multi-line syntax (>) for readability
    # It joins lines with spaces, making long commands more readable
    command: >
      bwa mem -t ${resources.cpu} ${config.refs}/genome.fa ${inputs.path} |
      samtools sort -o ${run_dir}/outputs/aligned.bam
    resources:
      cpu: 8
      memory: "16G"
      time_limit: "2h30m"                     # 2 hours and 30 minutes time limit
    after: [fastqc]                           # Depends on the fastqc step
```

## Quick Start Guide 🚀

### 1. Installation

Clone the repository and install the package in development mode:

```bash
git clone https://github.com/lewislovelock/bioinfoflow.git
cd bioinfoflow
pip install -e .
```

Alternatively, you can install directly from GitHub:

```bash
pip install git+https://github.com/lewislovelock/bioinfoflow.git
```

### 2. Create a Workflow Definition

You can create a new workflow definition using the init command:

```bash
bioinfoflow init my_workflow --output my_workflow.yaml
```

This will create a template workflow file that you can customize. Alternatively, you can use one of the example workflows:

```bash
cp examples/simple_workflow.yaml my_workflow.yaml
```

### 3. Run the Workflow

To run a workflow, use the run command:

```bash
bioinfoflow run my_workflow.yaml
```

This will:
1. Create the necessary directory structure
2. Copy or symbolically link input files to the run directory
3. Execute each step in the correct order
4. Save the workflow status and logs

You can also specify input paths directly via command line:

```bash
bioinfoflow run my_workflow.yaml --input path=/path/to/your/input/*.fastq.gz
```

#### Parallel Execution

BioinfoFlow supports parallel execution of workflow steps. Steps that don't depend on each other can be executed simultaneously:

```bash
bioinfoflow run my_workflow.yaml --parallel 4
```

This will execute up to 4 steps in parallel when possible, while still respecting dependencies between steps. For complex workflows with independent branches, this can significantly improve execution time.

#### Time Limits

You can set time limits for each step in your workflow to prevent long-running steps from consuming resources indefinitely:

```yaml
steps:
  my_step:
    container: "ubuntu:latest"
    command: "my_command"
    resources:
      cpu: 1
      memory: "1G"
      time_limit: "30m"  # 30 minutes time limit
```

Time limits can be specified in hours (`h`), minutes (`m`), and seconds (`s`), and can be combined (e.g., `1h30m`, `2h45m30s`). If a step exceeds its time limit, it will be terminated automatically.

You can control time limits via command-line options:

```bash
# Disable time limits for all steps
bioinfoflow run my_workflow.yaml --disable-time-limits

# Set a custom default time limit for steps that don't specify one
bioinfoflow run my_workflow.yaml --default-time-limit 2h30m

# Combine with parallel execution
bioinfoflow run my_workflow.yaml --parallel 4 --default-time-limit 1h
```

By default, steps without a specified time limit will use a default limit of 1 hour.

### 4. Check Workflow Status

To list all workflow runs:

```bash
bioinfoflow list
```

To check the status of a specific run:

```bash
bioinfoflow status <run_id>
```

### 5. Example Workflow

Here's a simple example workflow that demonstrates the core functionality:

```yaml
name: simple_workflow
version: "1.0.0"
description: "A simple workflow example"

inputs:
  path: "input/*.txt"

steps:
  hello_world:
    container: "ubuntu:20.04"
    command: "echo 'Hello, BioinfoFlow!' > ${run_dir}/outputs/hello.txt"
    resources:
      cpu: 1
      memory: "1G"
    after: []

  count_words:
    container: "ubuntu:20.04"
    command: "wc -w ${run_dir}/outputs/hello.txt > ${run_dir}/outputs/word_count.txt"
    resources:
      cpu: 1
      memory: "1G"
    after: [hello_world]
```

This workflow has two steps:
1. `hello_world`: Creates a text file with a greeting
2. `count_words`: Counts the words in the greeting file, depending on the completion of the first step

## Experimental Features 🧪

These are included as placeholders for future expansion but not required for the MVP:

```yaml
# Optional metadata
metadata:
  author: "Your Name"
  tags: [example, mvp]
  license: MIT

# Condition-based execution
conditions:
  - name: check_input
    when: "exists:${inputs.path}"
    skip: false

# Pre/post execution hooks
hooks:
  before_step:
    - name: "setup"
      script: "setup.sh"
  after_step:
    - name: "cleanup"
      script: "cleanup.sh"

# Completion notifications
notifications:
  email:
    recipients: ["user@example.com"]
    subject: "Workflow Completed"
    body: "The workflow has completed successfully."
  slack:
    channel: "#workflow-notifications"
    message: "Workflow completed successfully"
    webhook_url: "https://hooks.slack.com/services/..."
```

## Best Practices 🎯

- Use container versioning (e.g., `image:v1.2.3` instead of `image:latest`)
- Document expected inputs and outputs
- Provide reasonable resource defaults
- Use relative paths when possible for portability
- For inputs, use paths relative to your current directory or absolute paths
- Clean up temporary files in your workflows

## Version Information 📌

This document describes BioinfoFlow MVP v0.1.0.

Future versions will expand functionality based on user feedback while maintaining the core principles of simplicity and reproducibility.