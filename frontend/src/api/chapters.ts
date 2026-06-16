import { api } from './client';
import type { Chapter } from '../types';

export interface DraftInfo {
  version_id: number;
  path: string;
  size: number;
}

export interface DraftsListResponse {
  drafts: DraftInfo[];
  active_draft_id: number;
  draft_count: number;
}

export const chaptersApi = {
  list: (pid: string) =>
    api.get<Chapter[]>(`/projects/${pid}/chapters`),
  plan: (pid: string, ch: number, goal?: string) =>
    api.post<{ plan_path?: string; rhythm_type?: string; errors?: string[] }>(
      `/projects/${pid}/chapters/${ch}/plan`, { chapter_goal: goal },
    ),
  draft: (pid: string, ch: number) =>
    api.post<{ draft_path?: string; state_annotations_path?: string }>(
      `/projects/${pid}/chapters/${ch}/draft`, {},
    ),
  polish: (pid: string, ch: number) =>
    api.post<{ styled_draft_path?: string }>(
      `/projects/${pid}/chapters/${ch}/polish`, {},
    ),
  review: (pid: string, ch: number, types?: string[]) =>
    api.post<{ review_paths: Record<string, string>; has_critical_issues: boolean }>(
      `/projects/${pid}/chapters/${ch}/review`, { review_types: types },
    ),
  approve: (pid: string, ch: number, finalText: string) =>
    api.post<{ chapter_id: string; status: string; frozen: boolean }>(
      `/projects/${pid}/chapters/${ch}/approve`, { final_text: finalText },
    ),
  listDrafts: (pid: string, ch: number) =>
    api.get<DraftsListResponse>(`/projects/${pid}/chapters/${ch}/drafts`),
  getDraftContent: (pid: string, ch: number, draftId: number) =>
    api.get<{ draft_id: number; content: string }>(`/projects/${pid}/chapters/${ch}/drafts/${draftId}`),
  promoteDraft: (pid: string, ch: number, draftId: number) =>
    api.post<{ active_draft_id: number }>(`/projects/${pid}/chapters/${ch}/drafts/${draftId}/promote`, {}),
  multiReaderReview: (pid: string, ch: number, personaIds?: string[]) =>
    api.post<{ results: Record<string, unknown>[] }>(`/projects/${pid}/chapters/${ch}/review/multi-reader`, {
      persona_ids: personaIds,
    }),
  getContent: (pid: string, ch: number) =>
    api.get<{ content: string; source: string; draft_id?: number }>(`/projects/${pid}/chapters/${ch}/content`),
  saveContent: (pid: string, ch: number, content: string) =>
    api.post<{ draft_id: number; draft_count: number; status: string }>(`/projects/${pid}/chapters/${ch}/content`, {
      content,
    }),
};
