import { useState, useEffect } from 'react';
import { chaptersApi } from '../../api/chapters';
import type { DraftInfo } from '../../api/chapters';

interface DraftSelectorProps {
  projectId: string;
  chapterNumber: number;
  onSelect: (draftId: number, content: string) => void;
  onPromote: (draftId: number) => void;
}

export function DraftSelector({ projectId, chapterNumber, onSelect, onPromote }: DraftSelectorProps) {
  const [drafts, setDrafts] = useState<DraftInfo[]>([]);
  const [activeId, setActiveId] = useState<number>(0);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    chaptersApi.listDrafts(projectId, chapterNumber).then((res) => {
      setDrafts(res.drafts);
      setActiveId(res.active_draft_id);
      setSelectedId(res.active_draft_id);
    }).finally(() => setLoading(false));
  }, [projectId, chapterNumber]);

  const handleChange = async (vid: number) => {
    setSelectedId(vid);
    const res = await chaptersApi.getDraftContent(projectId, chapterNumber, vid);
    onSelect(vid, res.content);
  };

  const handlePromote = async () => {
    await chaptersApi.promoteDraft(projectId, chapterNumber, selectedId);
    setActiveId(selectedId);
    onPromote(selectedId);
  };

  if (loading) {
    return <div className="text-xs text-gray-400">加载版本列表...</div>;
  }

  if (drafts.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <label className="text-gray-500 text-xs">版本:</label>
      <select
        value={selectedId}
        onChange={(e) => handleChange(Number(e.target.value))}
        className="border border-gray-300 rounded px-2 py-1 text-xs"
      >
        {drafts.map((d) => (
          <option key={d.version_id} value={d.version_id}>
            v{d.version_id} ({d.size} B)
          </option>
        ))}
      </select>
      {selectedId !== activeId && activeId > 0 && (
        <button
          onClick={handlePromote}
          className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
        >
          设为主版本
        </button>
      )}
      {selectedId === activeId && activeId > 0 && (
        <span className="text-xs text-green-600 font-medium">当前</span>
      )}
    </div>
  );
}
