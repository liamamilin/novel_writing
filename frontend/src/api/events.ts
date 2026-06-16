import { api } from './client';

export interface ProjectEvent {
  event_id: string;
  project_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export const eventsApi = {
  list: (pid: string, limit = 50, offset = 0) =>
    api.get<{ events: ProjectEvent[]; limit: number; offset: number }>(
      `/projects/${pid}/events?limit=${limit}&offset=${offset}`,
    ),
  share: (pid: string, actor = 'user') =>
    api.post<{ share_token: string; url: string }>(`/projects/${pid}/share`, { actor }),
};
