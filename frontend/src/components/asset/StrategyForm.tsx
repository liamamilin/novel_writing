import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { api } from '../../api/client';
import { useState, useEffect } from 'react';

interface WritingStrategy {
  strategy_id: string;
  chapter_length: { min: number; max: number };
  pacing_strategy: { type: string };
  subplot_policy: { max_simultaneous: number };
}

export function StrategyForm() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [strategy, setStrategy] = useState<WritingStrategy | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      api.get<WritingStrategy>(`/projects/${currentProject.project_id}/strategy`)
        .then(setStrategy)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleSave = async () => {
    if (!currentProject || !strategy) return;
    try {
      await api.put(`/projects/${currentProject.project_id}/strategy`, strategy);
      notify('\u7B56\u7565\u5DF2\u4FDD\u5B58', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) return <div className="text-gray-400 text-sm py-4">\u8BF7\u5148\u9009\u62E9\u9879\u76EE</div>;

  if (loading) return <div className="text-gray-400 text-sm">\u52A0\u8F7D\u4E2D...</div>;

  if (!strategy) return <div className="text-gray-400 text-sm">\u6682\u65E0\u7B56\u7565\u914D\u7F6E</div>;

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-lg">\u5199\u4F5C\u7B56\u7565</h3>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">\u7AE0\u8282\u5B57\u6570\u8303\u56F4</label>
          <div className="flex gap-2 items-center">
            <input
              type="number"
              value={strategy.chapter_length.min}
              onChange={(e) => setStrategy({ ...strategy, chapter_length: { ...strategy.chapter_length, min: Number(e.target.value) } })}
              className="w-24 border rounded px-2 py-1 text-sm"
            />
            <span className="text-sm text-gray-500">~</span>
            <input
              type="number"
              value={strategy.chapter_length.max}
              onChange={(e) => setStrategy({ ...strategy, chapter_length: { ...strategy.chapter_length, max: Number(e.target.value) } })}
              className="w-24 border rounded px-2 py-1 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">\u8282\u594F\u7C7B\u578B</label>
          <input
            type="text"
            value={strategy.pacing_strategy.type}
            onChange={(e) => setStrategy({ ...strategy, pacing_strategy: { type: e.target.value } })}
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">\u6700\u5927\u5E76\u884C\u5B50\u7EBF</label>
          <input
            type="number"
            value={strategy.subplot_policy.max_simultaneous}
            onChange={(e) => setStrategy({ ...strategy, subplot_policy: { ...strategy.subplot_policy, max_simultaneous: Number(e.target.value) } })}
            className="w-24 border rounded px-2 py-1 text-sm"
          />
        </div>
      </div>

      <button
        onClick={handleSave}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm"
      >
        \u4FDD\u5B58\u7B56\u7565
      </button>
    </div>
  );
}