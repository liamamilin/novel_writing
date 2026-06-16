import { api } from './client';
import type { Project } from '../types';

export const projectsApi = {
  list: () => api.get<Project[]>('/projects'),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: { project_name: string; genre: string; idea?: string }) =>
    api.post<{ project_id: string; status: string }>('/projects', data),
  update: (id: string, data: Partial<Project>) =>
    api.put<Project>(`/projects/${id}`, data),
};
