import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { subplotsApi } from '../../api/subplots';
import type { Subplot } from '../../types';
import { useState, useEffect } from 'react';

export function SubplotTable() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [subplots, setSubplots] = useState<Subplot[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      subplotsApi.list(currentProject.project_id)
        .then(setSubplots)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleCreate = async () => {
    if (!currentProject) return;
    try {
const newSub = await subplotsApi.create(currentProject.project_id, {
        name: '新子线',
        type: 'secondary',
        status: 'active',
      });
      setSubplots([...subplots, newSub]);
      notify('\u5B50\u7EBF\u5DF2\u521B\u5EFA', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) return <div className="text-gray-400 text-sm py-4">\u8BF7\u5148\u9009\u62E9\u9879\u76EE</div>;

  const statusColor: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    idle: 'bg-yellow-100 text-yellow-700',
    resolved: 'bg-gray-200 text-gray-600',
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">\u5B50\u7EBF</h3>
        <button onClick={handleCreate} className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
          + \u65B0\u5EFA
        </button>
      </div>

      {loading && <div className="text-gray-400 text-sm">\u52A0\u8F7D\u4E2D...</div>}

      {subplots.length === 0 && !loading && (
        <div className="text-gray-400 text-sm">\u6682\u65E0\u5B50\u7EBF</div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 pr-4">ID</th>
              <th className="text-left py-2 pr-4">\u540D\u79F0</th>
              <th className="text-left py-2 pr-4">\u7C7B\u578B</th>
              <th className="text-left py-2">\u72B6\u6001</th>
            </tr>
          </thead>
          <tbody>
            {subplots.map((s) => (
              <tr key={s.subplot_id} className="border-b hover:bg-gray-50">
                <td className="py-2 pr-4 font-mono text-xs">{s.subplot_id.slice(0, 8)}</td>
                <td className="py-2 pr-4">{s.name}</td>
                <td className="py-2 pr-4">{s.type}</td>
                <td className="py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${statusColor[s.status] || 'bg-gray-100'}`}>
                    {s.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}