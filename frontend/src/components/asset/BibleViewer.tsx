import { useState, useEffect } from 'react';
import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { bibleApi } from '../../api/bible';
import { useNavigate } from 'react-router-dom';

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
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('character_profiles.md');
  const [content, setContent] = useState('');
  const [changelog, setChangelog] = useState<{ version: number; changes: string[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');

  useEffect(() => {
    if (!currentProject) return;
    setEditing(false);
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
        <>
          {editing ? (
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              rows={20}
            />
          ) : (
            <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm overflow-hidden">
              {content || '(暂无内容)'}
            </div>
          )}
          {!content && !editing && (
            <div className="bg-gray-50 rounded p-4 space-y-3 border">
              <p className="text-sm text-gray-500">
                当前项目还没有 Bible。推荐使用初始化向导生成完整的方向设定和角色概念，再生成 Bible。
              </p>
              <p className="text-sm text-gray-400">
                也可以基于当前项目信息一键补全（质量取决于项目类型的完善程度）。
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/project/new')}
                  className="bg-blue-500 text-white px-4 py-1.5 text-sm rounded hover:bg-blue-600"
                >
                  推荐：进入初始化向导
                </button>
                <button
                  onClick={async () => {
                    if (!currentProject) return;
                    const lowInfo = !currentProject.idea && !currentProject.target_reader && !currentProject.core_selling_point;
                    if (lowInfo && !window.confirm('项目简介等信息为空，生成质量可能较低，是否继续？')) return;
                    setGenerating(true);
                    try {
                      await bibleApi.generate(currentProject.project_id, '', []);
                      notify('Bible 已生成', 'success');
                      handleTabChange(activeTab);
                    } catch (e) {
                      notify((e as Error).message, 'error');
                    } finally {
                      setGenerating(false);
                    }
                  }}
                  disabled={generating}
                  className="px-4 py-1.5 text-sm rounded border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                >
                  {generating ? '生成中...' : '一键补全 Bible'}
                </button>
              </div>
              <button
                onClick={() => { setEditText(content); setEditing(true); }}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                手动编辑
              </button>
            </div>
          )}
          {editing && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={async () => {
                  if (!currentProject) return;
                  try {
                    await bibleApi.applyUpdate(currentProject.project_id, [{ file: activeTab, section: '', change: editText, reason: '手动编辑' }]);
                    setContent(editText);
                    setEditing(false);
                    notify('已保存', 'success');
                  } catch (e) {
                    notify((e as Error).message, 'error');
                  }
                }}
                className="bg-green-500 text-white px-4 py-1.5 text-sm rounded hover:bg-green-600"
              >
                保存
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-1.5 text-sm rounded border border-gray-300 text-gray-600 hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          )}
        </>
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
