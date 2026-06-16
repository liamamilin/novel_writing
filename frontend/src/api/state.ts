import { api } from './client';

export interface SnapshotInfo {
  snapshot_id: string;
  chapter_number: number;
}

export const stateApi = {
  snapshots: (pid: string) =>
    api.get<SnapshotInfo[]>(`/projects/${pid}/state/snapshots`),
  update: (pid: string, ch: number) =>
    api.post<{ snapshot_path: string; updated_files: string[]; health_issues: number }>(
      `/projects/${pid}/chapters/${ch}/state/update`,
    ),
  rollback: (pid: string, target: number) =>
    api.post<{ restored_to_chapter: number }>(
      `/projects/${pid}/state/rollback`, { target_chapter: target },
    ),
};
