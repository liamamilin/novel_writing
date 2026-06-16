import { useState, useEffect } from 'react';
import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { bibleApi } from '../../api/bible';

const BIBLE_TABS = [
  { key: 'character_profiles.md', label: '角色档案' },
  { key: 'world_setting.md', label: '世界观' },
  { key: 'novel_bible.md', label: '全书大纲' },
  { key: 'volume_plan.md', label: '卷规划' },
  { key: 'chapter_plan.md', label: '章节规划' },
  { key: 'version', label: '版本变更' },
];

export function BibleViewer() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [activeTab, setActiveTab] = useState('character_profiles.md');
  const [content, setContent] = useState('');
  const [changelog, setChangelog] = useState<{ version: number; changes: string[] }[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    bibleApi.get(currentProject.project_id).then((data) => {
      if (activeTab === 'version') return;
      setContent((data as Record<string, string>)[activeTab] || '');
    }).catch(() => {}).finally(() => setLoading(false));
  }, [currentProject, activeTab]);

  const handleTabChange = (key: string) => {
    setActiveTab(key);
    if (key === 'version') {
      setLoading(true);
      bibleApi.getVersion(currentProject!.project_id).then((data: any) => {
        setChangelog(data.changelog || []);
        setContent('');
      }).catch(() => {}).finally(() => setLoading(false));
    } else if (currentProject) {
      setLoading(true);
      bibleApi.get(currentProject.project_id).then((data) => {
        setContent((data as Record<string, string>)[key] || '');
      }).catch(() => {}).finally(() => setLoading(false));
    }
  };

  if (!currentProject) {
    return <div className="text-sm text-gray-400 py-4">请先选择项目</div>;
  }

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-lg">Bible 内容</h3>

      <div className="flex gap-1 border-b overflow-x-auto">
        {BIBLE_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            className={`px-3 py-1.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === tab.key
                ? 'border-blue-500 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <div className="text-gray-400 text-sm">加载中...</div>}

      {!loading && activeTab === 'version' && (
        <div className="space-y-2">
          {changelog.length === 0 && <div className="text-gray-400 text-sm">暂无版本记录</div>}
          {changelog.map((cl, i) => (
            <div key={i} className="border rounded p-3">
              <div className="text-sm font-medium">Version {cl.version}</div>
              <ul className="text-xs text-gray-500 mt-1 list-disc pl-4">
                {cl.changes.map((c, j) => <li key={j}>{c}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}

      {!loading && activeTab !== 'version' && (
        <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
          {content || '(暂无内容)'}
        </div>
      )}

      {activeTab === 'version' && (
        <button
          onClick={async () => {
            try {
              const res = await bibleApi.getUpdateProposal(currentProject.project_id);
              if (res?.proposal) {
                const prop = res.proposal as { items?: { file: string; change: string; reason: string }[] };
                const ok = window.confirm('确定应用 Bible 更新提议？');
                if (ok && prop.items) {
                  const items = (prop.items as any[]).map((item: any) => ({ file: item.file, section: item.section || '', change: item.change, reason: item.reason }));
                  await bibleApi.applyUpdate(currentProject.project_id, items);
                  notify('Bible 已更新', 'success');
                }
              } else {
                notify('暂无更新提议', 'info');
              }
            } catch (e) {
              notify((e as Error).message, 'error');
            }
          }}
          className="text-sm bg-blue-500 text-white px-3 py-1.5 rounded hover:bg-blue-600"
        >
          检查并应用更新
        </button>
      )}
    </div>
  );
}
