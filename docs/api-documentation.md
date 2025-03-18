# BioinfoFlow API Documentation

This document provides details on the available API endpoints for the BioinfoFlow frontend development.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not implement authentication.

## Health Check

### Check API Health

```
GET /api/health
```

Returns the status of the API and its dependencies.

**Response**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database_available": true
}
```

## Workflows

### List All Workflows

```
GET /api/v1/workflows
```

Returns a list of all workflows in the system.

**Response**

```json
[
  {
    "id": 1,
    "name": "simple_workflow",
    "version": "1.0.0",
    "description": "A simple workflow demonstration",
    "created_at": "2023-04-01T12:00:00.000Z",
    "run_count": 5
  },
  {
    "id": 2,
    "name": "rna_seq_analysis",
    "version": "2.1.0",
    "description": "RNA-Seq analysis pipeline",
    "created_at": "2023-04-02T10:30:00.000Z",
    "run_count": 3
  }
]
```

### Get Workflow Details

```
GET /api/v1/workflows/{workflow_id}
```

Returns detailed information about a specific workflow, including steps.

**Parameters**

- `workflow_id` (path): ID of the workflow to retrieve

**Response**

```json
{
  "id": 1,
  "name": "simple_workflow",
  "version": "1.0.0",
  "description": "A simple workflow demonstration",
  "created_at": "2023-04-01T12:00:00.000Z",
  "steps": {
    "hello_world": {
      "name": "hello_world",
      "container": "ubuntu:latest",
      "command": "echo 'Hello, BioinfoFlow!' > #{outputs}/hello.txt",
      "resources": {
        "cpu": 1,
        "memory": "1G"
      },
      "after": []
    },
    "count_words": {
      "name": "count_words",
      "container": "ubuntu:latest",
      "command": "wc -w #{outputs}/hello.txt > #{outputs}/word_count.txt",
      "resources": {
        "cpu": 1,
        "memory": "1G"
      },
      "after": ["hello_world"]
    }
  }
}
```

### Create Workflow

```
POST /api/v1/workflows
```

Creates a new workflow.

**Request Body**

```json
{
  "name": "new_workflow",
  "version": "1.0.0",
  "description": "A new workflow",
  "yaml_content": "name: new_workflow\nversion: 1.0.0\ndescription: A new workflow\nsteps:\n  step1:\n    container: ubuntu:latest\n    command: echo 'Hello' > #{outputs}/output.txt\n    resources:\n      cpu: 1\n      memory: 1G"
}
```

**Response**

Returns the created workflow with details, similar to the GET workflow response.

### Run Workflow

```
POST /api/v1/workflows/{workflow_id}/run
```

Starts a workflow execution.

**Parameters**

- `workflow_id` (path): ID of the workflow to run

**Request Body**

```json
{
  "inputs": {
    "input_file": "/path/to/input.txt"
  },
  "parallel": 2,
  "enable_time_limits": true,
  "default_time_limit": "1h"
}
```

**Response**

```json
{
  "id": 12,
  "run_id": "20250315_222427_e95ac3fc",
  "workflow_id": 1,
  "workflow_name": "simple_workflow",
  "workflow_version": "1.0.0",
  "status": "RUNNING",
  "start_time": "2025-03-15T22:24:27.000Z",
  "end_time": null,
  "duration": null
}
```

## Runs

### List All Runs

```
GET /api/v1/runs
```

Returns a list of all workflow runs.

**Query Parameters**

- `workflow_id` (optional): Filter runs by workflow ID

**Response**

```json
[
  {
    "id": 12,
    "run_id": "20250315_222427_e95ac3fc",
    "workflow_id": 1,
    "workflow_name": "simple_workflow",
    "workflow_version": "1.0.0",
    "status": "COMPLETED",
    "start_time": "2025-03-15T22:24:27.000Z",
    "end_time": "2025-03-15T22:24:28.000Z",
    "duration": "0:00:01"
  },
  {
    "id": 11,
    "run_id": "20250315_220015_a7b3c9d2",
    "workflow_id": 2,
    "workflow_name": "rna_seq_analysis",
    "workflow_version": "2.1.0",
    "status": "RUNNING",
    "start_time": "2025-03-15T22:00:15.000Z",
    "end_time": null,
    "duration": null
  }
]
```

### Get Run Details

```
GET /api/v1/runs/{run_id}
```

Returns detailed information about a specific run, including all steps.

**Parameters**

- `run_id` (path): ID of the run to retrieve

**Response**

```json
{
  "id": 12,
  "run_id": "20250315_222427_e95ac3fc",
  "workflow_id": 1,
  "workflow_name": "simple_workflow",
  "workflow_version": "1.0.0",
  "status": "COMPLETED",
  "start_time": "2025-03-15T22:24:27.000Z",
  "end_time": "2025-03-15T22:24:28.000Z",
  "duration": "0:00:01",
  "steps": {
    "hello_world": {
      "id": 49,
      "step_name": "hello_world",
      "status": "COMPLETED",
      "start_time": "2025-03-15T22:24:27.738Z",
      "end_time": "2025-03-15T22:24:27.994Z",
      "duration": "0:00:00.256",
      "exit_code": 0,
      "log_file": "/runs/simple_workflow/1.0.0/20250315_222427_e95ac3fc/logs/hello_world.log",
      "outputs": {
        "files": [
          "/runs/simple_workflow/1.0.0/20250315_222427_e95ac3fc/outputs/hello.txt"
        ]
      }
    },
    "count_words": {
      "id": 50,
      "step_name": "count_words",
      "status": "COMPLETED",
      "start_time": "2025-03-15T22:24:27.998Z",
      "end_time": "2025-03-15T22:24:28.255Z",
      "duration": "0:00:00.257",
      "exit_code": 0,
      "log_file": "/runs/simple_workflow/1.0.0/20250315_222427_e95ac3fc/logs/count_words.log",
      "outputs": {
        "files": [
          "/runs/simple_workflow/1.0.0/20250315_222427_e95ac3fc/outputs/word_count.txt"
        ]
      }
    }
  },
  "inputs": {
    "input_file": "/path/to/input.txt"
  },
  "run_dir": "/runs/simple_workflow/1.0.0/20250315_222427_e95ac3fc"
}
```

### Get Run Steps

```
GET /api/v1/runs/{run_id}/steps
```

Returns information about all steps in a run.

**Parameters**

- `run_id` (path): ID of the run to retrieve steps for

**Response**

Returns a dictionary of step details, similar to the steps field in the run details response.

### Delete Run

```
DELETE /api/v1/runs/{run_id}
```

Deletes a run (only completed or failed runs can be deleted).

**Parameters**

- `run_id` (path): ID of the run to delete

**Response**

Returns status code 204 (No Content) on success.

### Resume Run

```
POST /api/v1/runs/{run_id}/resume
```

Resumes a failed run.

**Parameters**

- `run_id` (path): ID of the run to resume

**Request Body**

```json
{
  "parallel": 2,
  "enable_time_limits": true,
  "default_time_limit": "1h",
  "step_overrides": {
    "failed_step": {
      "command": "modified command"
    }
  }
}
```

**Response**

Returns information about the resumed run, similar to the run workflow response.

## Error Responses

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Request was successful
- `204 No Content`: Request was successful (for DELETE operations)
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists (for workflow creation with the same name/version)
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error description"
}
```

## Data Models

### Workflow

- **WorkflowSummary** - Used in list views
  - `id` (integer): Workflow ID
  - `name` (string): Workflow name
  - `version` (string): Workflow version
  - `description` (string, optional): Workflow description
  - `created_at` (datetime): Creation timestamp
  - `run_count` (integer): Number of runs

- **WorkflowDetail** - Used for detailed views
  - All fields from WorkflowSummary
  - `steps` (object): Dictionary of step information
    - Key: Step name
    - Value: Step details (`name`, `container`, `command`, `resources`, `after`)

### Run

- **RunSummary** - Used in list views
  - `id` (integer): Run ID in database
  - `run_id` (string): Unique run identifier
  - `workflow_id` (integer): ID of the workflow
  - `workflow_name` (string): Name of the workflow
  - `workflow_version` (string): Version of the workflow
  - `status` (string): Current run status (PENDING, RUNNING, COMPLETED, FAILED, etc.)
  - `start_time` (datetime): When the run started
  - `end_time` (datetime, optional): When the run ended
  - `duration` (string, optional): Run duration formatted as string

- **RunDetail** - Used for detailed views
  - All fields from RunSummary
  - `steps` (object): Dictionary of step details
  - `inputs` (object): Input parameters used
  - `run_dir` (string): Directory path containing run outputs

### Step

- **StepDetail** - Used for step information
  - `id` (integer): Step ID in database
  - `step_name` (string): Name of the step
  - `status` (string): Current step status
  - `start_time` (datetime, optional): When the step started
  - `end_time` (datetime, optional): When the step ended
  - `duration` (string, optional): Step duration formatted as string
  - `exit_code` (integer, optional): Exit code if completed
  - `error` (string, optional): Error message if failed
  - `log_file` (string, optional): Path to log file
  - `outputs` (object, optional): Step outputs

## Step Status Values

The following status values are used for both runs and steps:

- `PENDING`: Not started yet
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully completed
- `FAILED`: Failed with non-zero exit code
- `ERROR`: Failed due to an error (before execution)
- `TERMINATED_TIME_LIMIT`: Terminated due to time limit
- `SKIPPED`: Skipped (due to dependencies failing)

## Additional Information

- The API uses FastAPI with automatic OpenAPI documentation.
- Full API documentation is available at `/api/docs`.
- Alternative documentation in ReDoc format is available at `/api/redoc`. 