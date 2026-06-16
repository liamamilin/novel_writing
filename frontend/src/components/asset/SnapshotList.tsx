import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { stateApi, type SnapshotInfo } from '../../api/state';
import { useState, useEffect } from 'react';

export function SnapshotList() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [snapshots, setSnapshots] = useState<SnapshotInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmChapter, setConfirmChapter] = useState<number | null>(null);

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      stateApi.snapshots(currentProject.project_id)
        .then(setSnapshots)
        .catch((e) => notify(e.message, 'error'))
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleRollback = async (chapterNumber: number) => {
    if (!currentProject) return;
    try {
      await stateApi.rollback(currentProject.project_id, chapterNumber);
      notify(`已回滚到第 ${chapterNumber} 章状态`, 'success');
      setConfirmChapter(null);
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) {
    return <div className="text-gray-400 text-sm py-4">请先选择项目</div>;
  }

  if (loading) {
    return <div className="text-gray-400 text-sm py-4">加载中...</div>;
  }

  if (snapshots.length === 0) {
    return <div className="text-gray-400 text-sm py-4">暂无快照</div>;
  }

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm text-gray-500 uppercase">状态快照</h3>
      {snapshots.map((snap) => (
        <div
          key={snap.snapshot_id}
          className="flex items-center justify-between border rounded p-3"
        >
          <div>
            <div className="text-sm font-medium">第 {snap.chapter_number} 章后快照</div>
            <div className="text-xs text-gray-400">{snap.snapshot_id}</div>
          </div>
          {confirmChapter === snap.chapter_number ? (
            <div className="flex gap-2">
              <button
                onClick={() => handleRollback(snap.chapter_number)}
                className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
              >
                确认回滚
              </button>
              <button
                onClick={() => setConfirmChapter(null)}
                className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-300"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmChapter(snap.chapter_number)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              回滚到此版本
            </button>
          )}
        </div>
      ))}
    </div>
  );
}