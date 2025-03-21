import axios, { AxiosError, AxiosInstance } from 'axios';
import { 
  HealthResponse, 
  WorkflowSummary, 
  WorkflowDetail, 
  WorkflowCreate,
  WorkflowRunRequest,
  RunSummary,
  RunDetail,
  RunResumeRequest,
  ErrorResponse
} from '@/types/api';

// API base URL - can be configured via environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API prefix - adjust based on the actual API documentation
const API_PREFIX = '/api/v1'; // This might need to be updated based on docs

// Create a configured axios instance
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handling helper
const handleApiError = (error: unknown): never => {
  if (error instanceof AxiosError) {
    const errorResponse = error.response?.data as ErrorResponse;
    throw new Error(errorResponse?.detail || error.message);
  }
  throw error;
};

// API client functions
export const apiClient = {
  // Health check
  getHealth: async (): Promise<HealthResponse> => {
    try {
      const response = await axiosInstance.get<HealthResponse>(`${API_PREFIX}/health`);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Workflow endpoints
  workflows: {
    // Get all workflows
    getAll: async (): Promise<WorkflowSummary[]> => {
      try {
        const response = await axiosInstance.get<WorkflowSummary[]>(`${API_PREFIX}/workflows`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get a specific workflow by ID
    getById: async (id: number): Promise<WorkflowDetail> => {
      try {
        const response = await axiosInstance.get<WorkflowDetail>(`${API_PREFIX}/workflows/${id}`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Create a new workflow
    create: async (workflow: WorkflowCreate): Promise<WorkflowDetail> => {
      try {
        const response = await axiosInstance.post<WorkflowDetail>(`${API_PREFIX}/workflows`, workflow);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Run a workflow
    run: async (id: number, params: WorkflowRunRequest): Promise<RunDetail> => {
      try {
        const response = await axiosInstance.post<RunDetail>(`${API_PREFIX}/workflows/${id}/run`, params);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Delete a workflow
    delete: async (id: number): Promise<void> => {
      try {
        await axiosInstance.delete(`${API_PREFIX}/workflows/${id}`);
      } catch (error) {
        return handleApiError(error);
      }
    }
  },

  // Run endpoints
  runs: {
    // Get all runs
    getAll: async (): Promise<RunSummary[]> => {
      try {
        const response = await axiosInstance.get<RunSummary[]>(`${API_PREFIX}/runs`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get a specific run by ID
    getById: async (id: number): Promise<RunDetail> => {
      try {
        const response = await axiosInstance.get<RunDetail>(`${API_PREFIX}/runs/${id}`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Resume a run
    resume: async (id: number, params: RunResumeRequest): Promise<RunDetail> => {
      try {
        const response = await axiosInstance.post<RunDetail>(`${API_PREFIX}/runs/${id}/resume`, params);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Cancel a run
    cancel: async (id: number): Promise<RunDetail> => {
      try {
        const response = await axiosInstance.post<RunDetail>(`${API_PREFIX}/runs/${id}/cancel`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    },

    // Get run logs
    getLogs: async (id: number, stepName: string): Promise<string> => {
      try {
        const response = await axiosInstance.get<string>(`${API_PREFIX}/runs/${id}/logs/${stepName}`);
        return response.data;
      } catch (error) {
        return handleApiError(error);
      }
    }
  }
};

export default apiClient; 