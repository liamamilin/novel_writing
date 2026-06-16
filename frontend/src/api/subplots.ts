import { api } from './client';
import type { Subplot } from '../types';

export const subplotsApi = {
  list: (pid: string) => api.get<Subplot[]>(`/projects/${pid}/subplots`),
  create: (pid: string, data: { name: string; type: string; status?: string }) =>
    api.post<Subplot>(`/projects/${pid}/subplots`, data),
};
