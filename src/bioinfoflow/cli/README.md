# BioinfoFlow CLI

The Command-Line Interface (CLI) for BioinfoFlow provides a simple way to run and manage workflows.

## Commands

### Run a Workflow

```bash
bioinfoflow run <workflow_file> [--input key=value] [--dry-run] [--output-dir <path>]
```

Options:
- `--input key=value`: Override input values in the workflow
- `--dry-run`: Validate the workflow without executing
- `--output-dir`: Custom output directory

### List Workflow Runs

```bash
bioinfoflow list [--workflow <name>] [--limit <num>]
```

Options:
- `--workflow`: Filter by workflow name
- `--limit`: Limit number of results (default: 10)

### Check Workflow Status

```bash
bioinfoflow status <run_id>
```

## Examples

### Running a Simple Workflow

```bash
bioinfoflow run examples/simple_workflow.yaml
```

### Running a Workflow with Custom Inputs

```bash
bioinfoflow run examples/simple_workflow.yaml --input path=/path/to/input/*.txt
```

### Dry-Run to Validate a Workflow

```bash
bioinfoflow run examples/simple_workflow.yaml --dry-run
```

### List Recent Workflow Runs

```bash
bioinfoflow list
```

### Check Status of a Specific Run

```bash
bioinfoflow status 20250304_160326_953b937b
``` 