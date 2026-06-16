import { api } from './client';

export const bibleApi = {
  direction: (pid: string, idea: string, genre?: string) =>
    api.post<{ variants: Record<string, unknown>[] }>(
      `/projects/${pid}/bible/direction`, { idea, genre },
    ),
  generateDirections: (pid: string, idea: string, genre?: string) =>
    api.post<{ variants: Record<string, unknown>[] }>(
      `/projects/${pid}/bible/direction`, { idea, genre },
    ),
  generateCharacters: (pid: string, directionId: string) =>
    api.post<{ characters: Record<string, unknown>[] }>(
      `/projects/${pid}/bible/characters`, { direction_id: directionId },
    ),
  generate: (pid: string, directionId: string, characters?: Record<string, unknown>[]) =>
    api.post<{ bible_files: Record<string, string>; bible_version: number }>(
      `/projects/${pid}/bible/generate`, { direction_id: directionId, characters },
    ),
  get: (pid: string) =>
    api.get<Record<string, string>>(`/projects/${pid}/bible`),
  getVersion: (pid: string) =>
    api.get<{ version: number; changelog: Record<string, unknown>[] }>(`/projects/${pid}/bible/version`),
  getUpdateProposal: (pid: string) =>
    api.get<{ proposal: Record<string, unknown> | null }>(`/projects/${pid}/bible/update-proposal`),
  applyUpdate: (pid: string, updates?: { file: string; section: string; change: string; reason: string }[], triggerChapter?: string) =>
    api.post<{ bible_version: number }>(`/projects/${pid}/bible/update`, { updates, trigger_chapter: triggerChapter }),
};