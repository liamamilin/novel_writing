import { api } from './client';

export const exportApi = {
  export: (pid: string, format: string, options?: { chapter_range?: string; include_title?: boolean }) =>
    api.post<{ task_id: string; format: string; path: string }>(`/projects/${pid}/export`, {
      format,
      ...options,
    }),
};

export function getDownloadUrl(pid: string, taskId: string): string {
  return `/api/projects/${pid}/exports/${taskId}/download`;
}
