import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import { 
  WorkflowCreate, 
  WorkflowRunRequest, 
  RunResumeRequest,
  WorkflowDetail,
  RunDetail
} from '@/types/api';

// Query keys for caching
export const queryKeys = {
  health: ['health'],
  workflows: {
    all: ['workflows'],
    detail: (id: number) => ['workflows', id],
  },
  runs: {
    all: ['runs'],
    detail: (id: number) => ['runs', id],
    logs: (id: number, stepName: string) => ['runs', id, 'logs', stepName],
  },
};

// Health check hook
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealth(),
  });
}

// Workflow hooks
export function useWorkflows() {
  return useQuery({
    queryKey: queryKeys.workflows.all,
    queryFn: () => apiClient.workflows.getAll(),
  });
}

export function useWorkflow(id: number) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => apiClient.workflows.getById(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (workflow: WorkflowCreate) => apiClient.workflows.create(workflow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => apiClient.workflows.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
    },
  });
}

export function useRunWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      workflowId, 
      params 
    }: { 
      workflowId: number; 
      params: WorkflowRunRequest 
    }) => apiClient.workflows.run(workflowId, params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
    },
  });
}

// Run hooks
export function useRuns() {
  return useQuery({
    queryKey: queryKeys.runs.all,
    queryFn: () => apiClient.runs.getAll(),
  });
}

export function useRun(id: number) {
  return useQuery({
    queryKey: queryKeys.runs.detail(id),
    queryFn: () => apiClient.runs.getById(id),
    enabled: !!id,
  });
}

export function useRunLogs(id: number, stepName: string) {
  return useQuery({
    queryKey: queryKeys.runs.logs(id, stepName),
    queryFn: () => apiClient.runs.getLogs(id, stepName),
    enabled: !!id && !!stepName,
  });
}

export function useResumeRun() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      runId, 
      params 
    }: { 
      runId: number; 
      params: RunResumeRequest 
    }) => apiClient.runs.resume(runId, params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.detail(data.id) });
    },
  });
}

export function useCancelRun() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (runId: number) => apiClient.runs.cancel(runId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.detail(data.id) });
    },
  });
} 