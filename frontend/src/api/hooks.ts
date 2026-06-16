import { api } from './client';
import type { Hook } from '../types';

export const hooksApi = {
  list: (pid: string) => api.get<Hook[]>(`/projects/${pid}/hooks`),
  create: (pid: string, data: Partial<Hook>) =>
    api.post<Hook>(`/projects/${pid}/hooks`, data),
};
