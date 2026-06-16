import { api } from './client';
import type { StyleAsset } from '../types';

export const stylesApi = {
  uploadSample: (pid: string, text: string) =>
    api.post<{ sample_id: string }>(`/projects/${pid}/styles/style-samples`, {
      sample_name: 'upload', text,
    }),
  analyze: (pid: string, sampleIds: string[], styleName: string) =>
    api.post<{ task_id: string; status: string } | StyleAsset>(
      `/projects/${pid}/styles/analyze`, { sample_ids: sampleIds, style_name: styleName },
    ),
  get: (pid: string, sid: string) =>
    api.get<StyleAsset>(`/projects/${pid}/styles/${sid}`),
  list: (pid: string) =>
    api.get<StyleAsset[]>(`/projects/${pid}/styles`),
};
