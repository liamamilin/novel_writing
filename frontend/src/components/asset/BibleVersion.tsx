import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { bibleApi } from '../../api/bible';
import { useState, useEffect } from 'react';

interface BibleChangelog {
  version: number;
  changes: string[];
  updated_at?: string;
}

export function BibleVersion() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [changelog, setChangelog] = useState<BibleChangelog[]>([]);
  const [loading, setLoading] = useState(false);
  const [proposal, setProposal] = useState<string | null>(null);

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      bibleApi.getVersion(currentProject.project_id)
        .then((data: any) => {
          setChangelog(data.changelog || []);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleCheckProposal = async () => {
    if (!currentProject) return;
    try {
      const result = await bibleApi.getUpdateProposal(currentProject.project_id);
      setProposal(JSON.stringify(result, null, 2));
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleApplyUpdate = async () => {
    if (!currentProject) return;
    try {
      await bibleApi.applyUpdate(currentProject.project_id);
      notify('Bible \u5DF2\u66F4\u65B0', 'success');
      setProposal(null);
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) {
    return <div className="text-gray-400 text-sm py-4">\u8BF7\u5148\u9009\u62E9\u9879\u76EE</div>;
  }

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-lg">Bible \u7248\u672C</h3>

      {loading && <div className="text-gray-400 text-sm">\u52A0\u8F7D\u4E2D...</div>}

      {changelog.length > 0 && (
        <div className="space-y-2">
          {changelog.map((cl, i) => (
            <div key={i} className="border rounded p-3">
              <div className="text-sm font-medium">Version {cl.version}</div>
              <ul className="text-xs text-gray-500 mt-1 list-disc pl-4">
                {cl.changes.map((c, j) => (
                  <li key={j}>{c}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleCheckProposal}
          className="text-sm bg-blue-500 text-white px-3 py-1.5 rounded hover:bg-blue-600"
        >
          \u67E5\u770B\u66F4\u65B0\u63D0\u8BAE
        </button>
      </div>

      {proposal && (
        <div className="border rounded p-3">
          <pre className="text-xs whitespace-pre-wrap">{proposal}</pre>
          <button
            onClick={handleApplyUpdate}
            className="mt-2 text-sm bg-green-500 text-white px-3 py-1.5 rounded hover:bg-green-600"
          >
            \u5E94\u7528\u66F4\u65B0
          </button>
        </div>
      )}
    </div>
  );
}