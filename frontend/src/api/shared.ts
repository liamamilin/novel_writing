import { api } from './client';

export const sharedApi = {
  getProject: (token: string) =>
    api.get<{ project_id: string; project_name: string; genre?: string }>(`/api/shared/${token}`),
  getChapters: (token: string) =>
    api.get<{ chapters: { chapter_id: string; chapter_number: number; title: string; status: string }[] }>(`/api/shared/${token}/chapters`),
  getChapter: (token: string, ch: number) =>
    api.get<{ project_id: string; project_name: string; chapter_number: number; file_type: string; content: string }>(
      `/api/shared/${token}/chapters/${ch}?file_type=final`,
    ),
};
