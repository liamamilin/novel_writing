import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { bibleApi } from '../../api/bible';
import { useState, useEffect } from 'react';

interface BibleChangelog {
  version: number;
  changes: string[];
  updated_at?: string;
}

interface BibleUpdateItem {
  file: string;
  section: string;
  change: string;
  reason: string;
}

interface BibleProposal {
  proposal_id: string;
  trigger_chapter: string;
  items: BibleUpdateItem[];
}

export function BibleVersion() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [changelog, setChangelog] = useState<BibleChangelog[]>([]);
  const [loading, setLoading] = useState(false);
  const [proposal, setProposal] = useState<BibleProposal | null>(null);

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
      setProposal(result?.proposal as BibleProposal | null);
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleApplyUpdate = async () => {
    if (!currentProject || !proposal) return;
    try {
      await bibleApi.applyUpdate(currentProject.project_id, proposal.items, proposal.trigger_chapter);
      notify('Bible 已更新', 'success');
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
        <div className="border rounded p-3 space-y-2">
          <div className="text-xs text-gray-500">提案: {proposal.proposal_id?.slice(0, 8)}…</div>
          <div className="space-y-1">
            {proposal.items.map((item, i) => (
              <div key={i} className="bg-gray-50 rounded p-2 text-xs">
                <span className="font-medium">{item.file}</span> — {item.change}
                <div className="text-gray-400">{item.reason}</div>
              </div>
            ))}
          </div>
          <button
            onClick={handleApplyUpdate}
            className="text-sm bg-green-500 text-white px-3 py-1.5 rounded hover:bg-green-600"
          >
            应用更新
          </button>
        </div>
      )}
    </div>
  );
}