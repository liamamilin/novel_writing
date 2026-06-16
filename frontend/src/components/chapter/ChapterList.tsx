import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';
import { useChapterStore } from '../../stores/chapterStore';
import { useUIStore } from '../../stores/uiStore';
import { useStreamStore } from '../../stores/streamStore';
import { chaptersApi } from '../../api/chapters';
import { bibleApi } from '../../api/bible';

const statusConfig: Record<string, { bg: string; text: string; label: string; icon: string }> = {
  planned: { bg: 'bg-gray-200', text: 'text-gray-600', label: '\u89C4\u5212', icon: '\uD83D\uDCDD' },
  drafted: { bg: 'bg-yellow-200', text: 'text-yellow-700', label: '\u8349\u7A3F', icon: '\u270F\uFE0F' },
  reviewed: { bg: 'bg-blue-200', text: 'text-blue-700', label: '\u5DF2\u5BA1\u67E5', icon: '\uD83D\uDD0D' },
  approved: { bg: 'bg-green-200', text: 'text-green-700', label: '\u5DF2\u786E\u8BA4', icon: '\u2705' },
  locked: { bg: 'bg-gray-400', text: 'text-gray-800', label: '\u5DF2\u9501\u5B9A', icon: '\uD83D\uDD12' },
};

export function ChapterList() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const chapters = useChapterStore((s) => s.chapters);
  const currentChapter = useChapterStore((s) => s.currentChapter);
  const loadChapters = useChapterStore((s) => s.loadChapters);
  const setCurrentChapter = useChapterStore((s) => s.setCurrentChapter);
  const selectAsset = useUIStore((s) => s.selectAsset);
  const notify = useUIStore((s) => s.notify);
  const [creating, setCreating] = useState(false);
  const [, setSearchParams] = useSearchParams();
  const isStreaming = useStreamStore((s) => s.isStreaming);
  const clearStreamedContent = useStreamStore((s) => s.clearStreamedContent);

  useEffect(() => {
    if (currentProject) {
      loadChapters(currentProject.project_id);
    }
  }, [currentProject, loadChapters]);

  if (!currentProject) {
    return (
      <div className="text-sm text-gray-400 px-2 py-4">
        \u8BF7\u5148\u9009\u62E9\u9879\u76EE
      </div>
    );
  }

  if (chapters.length === 0) {
    const handleCreateFirst = async () => {
      if (!currentProject) return;
      setCreating(true);
      try {
        // verify Bible exists before planning
        try {
          await bibleApi.get(currentProject.project_id);
        } catch {
          notify('请先生成 Bible（右侧面板 → Bible 生成），再创建章节', 'error');
          setCreating(false);
          return;
        }
        await chaptersApi.plan(currentProject.project_id, 1, '开场章节');
        await loadChapters(currentProject.project_id);
        notify('第 1 章已创建', 'success');
      } catch (e) {
        notify((e as Error).message, 'error');
      } finally {
        setCreating(false);
      }
    };
    return (
      <div className="text-sm text-gray-400 px-2 py-4 space-y-2">
        <p>\u6682\u65E0\u7AE0\u8282</p>
        <button
          onClick={handleCreateFirst}
          disabled={creating}
          className="bg-blue-500 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-600 disabled:opacity-50"
        >
          {creating ? '\u521B\u5EFA\u4E2D...' : '+ \u521B\u5EFA\u7B2C 1 \u7AE0'}
        </button>
      </div>
    );
  }

  const handleCreateNext = async () => {
    if (!currentProject) return;
    const nextNum = Math.max(...chapters.map(c => c.chapter_number), 0) + 1;
    setCreating(true);
    try {
      await chaptersApi.plan(currentProject.project_id, nextNum, '');
      await loadChapters(currentProject.project_id);
      notify(`第 ${nextNum} 章已创建`, 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-1">
      <h3 className="font-semibold text-sm text-gray-500 uppercase mb-1 px-2">章节</h3>
      {chapters.map((ch) => {
        const cfg = statusConfig[ch.status] || statusConfig.planned;
        return (
          <button
            key={ch.chapter_id}
            onClick={() => {
              if (isStreaming) {
                notify('正在流式生成中，请等待完成后再切换', 'error');
                return;
              }
              clearStreamedContent();
              setCurrentChapter(ch);
              selectAsset({ type: 'chapter', id: ch.chapter_id });
              setSearchParams({ ch: String(ch.chapter_number), asset: 'chapter' });
            }}
            className={`w-full text-left px-3 py-1.5 text-sm rounded hover:bg-gray-100 transition-colors flex items-center justify-between ${
              currentChapter?.chapter_id === ch.chapter_id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
            }`}
          >
            <span>
              第 {ch.chapter_number} 章
              {ch.title ? ` — ${ch.title}` : ''}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${cfg.bg} ${cfg.text}`}>
              {cfg.icon} {cfg.label}
            </span>
          </button>
        );
      })}
      <button
        onClick={handleCreateNext}
        disabled={creating}
        className="w-full text-left px-3 py-1.5 text-sm mt-1 border border-dashed border-gray-300 rounded text-gray-500 hover:bg-gray-50 hover:text-blue-600 disabled:opacity-50"
      >
        {creating ? '创建中...' : `+ 创建第 ${Math.max(...chapters.map(c => c.chapter_number), 0) + 1} 章`}
      </button>
    </div>
  );
}