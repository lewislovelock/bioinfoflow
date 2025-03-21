// API response types for BioinfoFlow API

// Common status enum for steps and runs
export enum Status {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  ERROR = "ERROR",
  TERMINATED_TIME_LIMIT = "TERMINATED_TIME_LIMIT",
  SKIPPED = "SKIPPED"
}

// Workflow types
export interface WorkflowSummary {
  id: number;
  name: string;
  version: string;
  description?: string;
  created_at: string;
  run_count: number;
}

export interface WorkflowStep {
  name: string;
  container: string;
  command: string;
  resources: {
    cpu?: number;
    memory?: string;
    time_limit?: string;
  };
  after: string[];
}

export interface WorkflowDetail extends WorkflowSummary {
  steps: Record<string, WorkflowStep>;
}

export interface WorkflowRunRequest {
  inputs?: Record<string, string>;
  parallel?: number;
  enable_time_limits?: boolean;
  default_time_limit?: string;
}

export interface WorkflowCreate {
  name: string;
  version: string;
  description?: string;
  yaml_content: string;
}

// Run types
export interface RunSummary {
  id: number;
  run_id: string;
  workflow_id: number;
  workflow_name: string;
  workflow_version: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration?: string;
}

export interface StepDetail {
  id: number;
  step_name: string;
  status: string;
  start_time?: string;
  end_time?: string;
  duration?: string;
  exit_code?: number;
  error?: string;
  log_file?: string;
  outputs?: {
    files?: string[];
    [key: string]: any;
  };
}

export interface RunDetail extends RunSummary {
  steps: Record<string, StepDetail>;
  inputs?: Record<string, any>;
  run_dir: string;
}

export interface RunResumeRequest {
  parallel?: number;
  enable_time_limits?: boolean;
  default_time_limit?: string;
  step_overrides?: Record<string, Record<string, any>>;
}

// Health check
export interface HealthResponse {
  status: string;
  version: string;
  database_available: boolean;
}

// Error response
export interface ErrorResponse {
  detail: string;
} 