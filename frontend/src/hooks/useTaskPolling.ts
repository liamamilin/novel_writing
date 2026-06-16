import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export interface TaskInfo {
  task_id: string;
  project_id: string;
  task_type: string;
  status: string;
}

export function useTaskPolling(projectId: string | null, taskId: string | null) {
  return useQuery({
    queryKey: ['task', projectId, taskId],
    queryFn: () => api.get<TaskInfo>(`/projects/${projectId}/tasks/${taskId}`),
    enabled: !!projectId && !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'success' || status === 'failed' ? false : 2000;
    },
  });
}