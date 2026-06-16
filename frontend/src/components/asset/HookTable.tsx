import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { hooksApi } from '../../api/hooks';
import type { Hook } from '../../types';
import { useState, useEffect } from 'react';

const urgencyColor: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
};

const statusLabel: Record<string, string> = {
  open: '\u5F00\u653E',
  triggered: '\u5DF2\u89E6\u53D1',
  resolved: '\u5DF2\u89E3\u51B3',
  abandoned: '\u5DF2\u653E\u5F03',
};

export function HookTable() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [hooks, setHooks] = useState<Hook[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      hooksApi.list(currentProject.project_id)
        .then(setHooks)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleCreate = async () => {
    if (!currentProject) return;
    try {
      const newHook = await hooksApi.create(currentProject.project_id, {
        content: '\u65B0\u4F0F\u7B14',
        status: 'open',
        priority: 'medium',
      });
      setHooks([...hooks, newHook]);
      notify('\u4F0F\u7B14\u5DF2\u521B\u5EFA', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) return <div className="text-gray-400 text-sm py-4">\u8BF7\u5148\u9009\u62E9\u9879\u76EE</div>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">\u4F0F\u7B14</h3>
        <button onClick={handleCreate} className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
          + \u65B0\u5EFA
        </button>
      </div>

      {loading && <div className="text-gray-400 text-sm">\u52A0\u8F7D\u4E2D...</div>}

      {hooks.length === 0 && !loading && (
        <div className="text-gray-400 text-sm">\u6682\u65E0\u4F0F\u7B14</div>
      )}

      <div className="space-y-2">
        {hooks.map((h) => (
          <div key={h.hook_id} className="border rounded p-3 flex items-start justify-between">
            <div>
              <p className="text-sm">{h.content}</p>
              {h.source_chapter && (
                <p className="text-xs text-gray-400 mt-1">\u6765\u6E90: \u7B2C {h.source_chapter} \u7AE0</p>
              )}
            </div>
            <div className="flex gap-2 shrink-0">
              <span className={`text-xs px-1.5 py-0.5 rounded ${urgencyColor[h.priority] || 'bg-gray-100'}`}>
                {h.priority}
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                {statusLabel[h.status] || h.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}