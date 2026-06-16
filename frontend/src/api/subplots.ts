import { api } from './client';
import type { Subplot } from '../types';

export const subplotsApi = {
  list: (pid: string) => api.get<Subplot[]>(`/projects/${pid}/subplots`),
  create: (pid: string, data: { name: string; type: string; status?: string }) =>
    api.post<Subplot>(`/projects/${pid}/subplots`, data),
  update: (pid: string, subplotId: string, updates: Record<string, unknown>) =>
    api.put<Subplot>(`/projects/${pid}/subplots/${subplotId}`, updates),
  delete: (pid: string, subplotId: string) =>
    api.delete<{ deleted: boolean }>(`/projects/${pid}/subplots/${subplotId}`),
};
