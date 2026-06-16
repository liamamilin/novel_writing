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
      notify(`\u5DF2\u56DE\u6EDA\u5230\u7B2C ${chapterNumber} \u7AE0\u72B6\u6001`, 'success');
      setConfirmChapter(null);
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) {
    return <div className="text-gray-400 text-sm py-4">\u8BF7\u5148\u9009\u62E9\u9879\u76EE</div>;
  }

  if (loading) {
    return <div className="text-gray-400 text-sm py-4">\u52A0\u8F7D\u4E2D...</div>;
  }

  if (snapshots.length === 0) {
    return <div className="text-gray-400 text-sm py-4">\u6682\u65E0\u5FEB\u7167</div>;
  }

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm text-gray-500 uppercase">\u72B6\u6001\u5FEB\u7167</h3>
      {snapshots.map((snap) => (
        <div
          key={snap.snapshot_id}
          className="flex items-center justify-between border rounded p-3"
        >
          <div>
            <div className="text-sm font-medium">\u7B2C {snap.chapter_number} \u7AE0\u540E\u5FEB\u7167</div>
            <div className="text-xs text-gray-400">{snap.snapshot_id}</div>
          </div>
          {confirmChapter === snap.chapter_number ? (
            <div className="flex gap-2">
              <button
                onClick={() => handleRollback(snap.chapter_number)}
                className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
              >
                \u786E\u8BA4\u56DE\u6EDA
              </button>
              <button
                onClick={() => setConfirmChapter(null)}
                className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-300"
              >
                \u53D6\u6D88
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmChapter(snap.chapter_number)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              \u56DE\u6EDA\u5230\u6B64\u7248\u672C
            </button>
          )}
        </div>
      ))}
    </div>
  );
}