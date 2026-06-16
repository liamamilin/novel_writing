import { api } from './client';

export const exportApi = {
  export: (pid: string, format: string, chapterRange?: string, includeTitle?: boolean) =>
    api.post<{ task_id: string; format: string; path: string }>(`/projects/${pid}/export`, {
      format,
      chapter_range: chapterRange,
      include_title: includeTitle,
    }),
};

export function getDownloadUrl(pid: string, taskId: string): string {
  return `/api/projects/${pid}/exports/${taskId}/download`;
}
