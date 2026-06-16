import { api } from './client';
import type { Hook } from '../types';

export const hooksApi = {
  list: (pid: string) => api.get<Hook[]>(`/projects/${pid}/hooks`),
  create: (pid: string, data: Partial<Hook>) =>
    api.post<Hook>(`/projects/${pid}/hooks`, data),
  update: (pid: string, hookId: string, updates: Record<string, unknown>) =>
    api.put<Hook>(`/projects/${pid}/hooks/${hookId}`, updates),
  trigger: (pid: string, hookId: string) =>
    api.post<Hook>(`/projects/${pid}/hooks/${hookId}/trigger`),
  resolve: (pid: string, hookId: string) =>
    api.post<Hook>(`/projects/${pid}/hooks/${hookId}/resolve`),
};
