import { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react';
import { useChapterStore } from '../../stores/chapterStore';

const MDEditor = lazy(() => import('@uiw/react-md-editor'));
import { useProjectStore } from '../../stores/projectStore';
import { useStreamStore } from '../../stores/streamStore';
import { useUIStore } from '../../stores/uiStore';
import { chaptersApi } from '../../api/chapters';
import { DraftSelector } from './DraftSelector';
import { DraftDiff } from './DraftDiff';

const STATUS_FLOW = ['planned', 'drafted', 'reviewed', 'approved', 'locked'] as const;

const statusLabel: Record<string, string> = {
  planned: '规划',
  drafted: '草稿',
  reviewed: '已审查',
  approved: '已确认',
  locked: '已锁定',
};

export function ChapterEditor() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const currentChapter = useChapterStore((s) => s.currentChapter);
  const loadChapters = useChapterStore((s) => s.loadChapters);
  const notify = useUIStore((s) => s.notify);
  const [content, setContent] = useState('');
  const [loadedContent, setLoadedContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const isStreaming = useStreamStore((s) => s.isStreaming);
  const streamedContent = useStreamStore((s) => s.streamedContent);
  const [showDiff, setShowDiff] = useState(false);
  const [diffOld, setDiffOld] = useState('');
  const [diffNew, setDiffNew] = useState('');
  const [diffOldTitle, setDiffOldTitle] = useState('');
  const [diffNewTitle, setDiffNewTitle] = useState('');

  // B4: auto-load content when chapter changes
  useEffect(() => {
    if (!currentProject || !currentChapter) return;
    setContent('');
    setShowDiff(false);
    setSaving(false);
    // if streaming is in progress, don't clobber streamedContent
    if (isStreaming) return;

    // if chapter is planned, nothing to load
    if (currentChapter.status === 'planned') return;

    setContentLoading(true);
    chaptersApi.getContent(currentProject.project_id, currentChapter.chapter_number)
      .then((res) => {
        if (res.content) {
          setContent(res.content);
          setLoadedContent(res.content);
        } else {
          setLoadedContent('');
        }
      })
      .catch(() => {})
      .finally(() => setContentLoading(false));
  }, [currentProject?.project_id, currentChapter?.chapter_id, currentChapter?.chapter_number, currentChapter?.status]);

  const isReadOnly = currentChapter
    ? (currentChapter.status === 'approved' || currentChapter.status === 'locked')
    : true;
  const currentStatusIdx = currentChapter
    ? STATUS_FLOW.indexOf(currentChapter.status as typeof STATUS_FLOW[number])
    : -1;

  // B2: save content
  const handleSave = useCallback(async () => {
    if (!currentProject || !currentChapter || isReadOnly || isStreaming) return;
    setSaving(true);
    try {
      const res = await chaptersApi.saveContent(currentProject.project_id, currentChapter.chapter_number, content);
      if (res.reviews_invalidated) {
        notify('已保存 — 审查报告已失效，请重新审查', 'info');
      } else {
        notify('已保存为草稿 v' + res.draft_id, 'success');
      }
      if (res.status !== currentChapter.status && currentProject) {
        await loadChapters(currentProject.project_id);
      }
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setSaving(false);
    }
  }, [currentProject, currentChapter, content, isReadOnly, isStreaming, notify, loadChapters]);

  // N9: dirty state — warn on page leave
  const isDirty = content !== loadedContent && !isReadOnly && !isStreaming;

  useEffect(() => {
    if (isDirty) {
      const handler = (e: BeforeUnloadEvent) => {
        e.preventDefault();
        e.returnValue = '';
      };
      window.addEventListener('beforeunload', handler);
      return () => window.removeEventListener('beforeunload', handler);
    }
  }, [isDirty]);

  // N10: Ctrl+S to save (only when editor div is focused)
  const editorContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        const target = e.target as HTMLElement;
        if (editorContainerRef.current && editorContainerRef.current.contains(target) && !isReadOnly && !isStreaming) {
          e.preventDefault();
          handleSave();
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSave, isReadOnly, isStreaming]);

  const [selectedDraftId, setSelectedDraftId] = useState<number>(0);
  const handleDraftSelect = useCallback((_draftId: number, _content: string) => {
    setSelectedDraftId(_draftId);
    if (!showDiff) {
      setShowDiff(true);
      setDiffOld(content);
      setDiffOldTitle(`当前`);
      setDiffNewTitle(`v${_draftId}`);
      setDiffNew(_content);
    } else {
      setDiffNew(_content);
      setDiffNewTitle(`v${_draftId}`);
    }
  }, [content, showDiff]);

  const handlePromote = useCallback((_draftId: number) => {
    setShowDiff(false);
    if (currentProject) {
      loadChapters(currentProject.project_id);
    }
    // reload content after promote
    if (currentProject && currentChapter) {
      chaptersApi.getContent(currentProject.project_id, currentChapter.chapter_number)
        .then((res) => {
          if (res.content) setContent(res.content);
        })
        .catch(() => {});
    }
  }, [currentProject, currentChapter, loadChapters]);

  if (!currentProject || !currentChapter) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>选择一个章节开始编辑</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col" ref={editorContainerRef}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-bold">
          第 {currentChapter.chapter_number} 章
          {currentChapter.title ? ` — ${currentChapter.title}` : ''}
          <span className="ml-2 text-sm font-normal text-gray-500">
            ({statusLabel[currentChapter.status] || currentChapter.status})
          </span>
          <span className="ml-2 text-xs text-gray-400 font-normal">
            提示: 按 Ctrl+S 保存草稿
          </span>
        </h2>
      </div>

      <div className="flex items-center gap-1 mb-3">
        {STATUS_FLOW.map((s, i) => {
          const active = i <= currentStatusIdx;
          const isCurrent = s === currentChapter.status;
          return (
            <div key={s} className="flex items-center" title={statusLabel[s] + (i > 0 ? ` → 下一步: ${statusLabel[STATUS_FLOW[i-1]]}` : '')}>
              <div
                className={`w-3 h-3 rounded-full ${
                  isCurrent ? 'bg-blue-500 ring-2 ring-blue-200' :
                  active ? 'bg-blue-400' :
                  'bg-gray-300'
                }`}
              />
              {i < STATUS_FLOW.length - 1 && (
                <div className={`w-6 h-0.5 ${i < currentStatusIdx ? 'bg-blue-400' : 'bg-gray-300'}`} />
              )}
            </div>
          );
        })}
        <span className="ml-2 text-xs text-gray-500">
          {statusLabel[currentChapter.status]}
        </span>
      </div>

      {isReadOnly && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm px-3 py-2 rounded mb-3">
          此章节已锁定，不可编辑
        </div>
      )}

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 bg-gray-100 rounded px-2 py-0.5">
            {currentChapter.status === 'approved' || currentChapter.status === 'locked' ? '终稿' : '草稿'}
          </span>
          {!isReadOnly && !isStreaming && (
            <button
              onClick={handleSave}
              disabled={saving || contentLoading}
              className="px-3 py-1 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? '保存中...' : '保存'}
            </button>
          )}
        </div>
        <DraftSelector
          projectId={currentProject.project_id}
          chapterNumber={currentChapter.chapter_number}
          onSelect={handleDraftSelect}
          onPromote={handlePromote}
        />
      </div>

      {isStreaming && <StreamingProgress chars={streamedContent.length} />}

      {contentLoading && !isStreaming && (
        <div className="flex items-center justify-center h-full text-gray-400 text-sm">
          加载内容中...
        </div>
      )}

      {showDiff ? (
        <div className="flex-1 overflow-auto">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-600">版本对比</h4>
            <div className="flex gap-2">
              <button
                onClick={() => { setContent(diffNew); setLoadedContent(diffNew); setShowDiff(false); }}
                className="text-xs text-green-600 hover:text-green-800"
              >
                加载到编辑器 (v{selectedDraftId})
              </button>
              <button
                onClick={() => setShowDiff(false)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                返回编辑
              </button>
            </div>
          </div>
          <DraftDiff
            leftContent={diffOld}
            rightContent={diffNew}
            leftTitle={diffOldTitle}
            rightTitle={diffNewTitle}
          />
        </div>
      ) : (
        <div className="flex-1" data-color-mode="light">
          <Suspense fallback={<div className="flex items-center justify-center h-full text-gray-400 text-sm">加载编辑器...</div>}>
            <MDEditor
              value={isStreaming ? streamedContent : content}
              onChange={(v) => !isReadOnly && !isStreaming && setContent(v || '')}
              preview={isStreaming || isReadOnly ? 'preview' : 'edit'}
              hideToolbar={isStreaming || isReadOnly}
              height="100%"
            />
          </Suspense>
        </div>
      )}
    </div>
  );
}

function StreamingProgress({ chars }: { chars: number }) {
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setElapsed(Date.now() - startTime), 1000);
    return () => clearInterval(id);
  }, [startTime]);
  const sec = Math.floor(elapsed / 1000);
  const mm = String(Math.floor(sec / 60)).padStart(2, '0');
  const ss = String(sec % 60).padStart(2, '0');
  const cps = sec > 0 ? (chars / sec).toFixed(0) : '...';
  return (
    <div className="flex items-center gap-2 mb-3 bg-blue-50 border border-blue-200 text-blue-700 text-sm px-3 py-2 rounded">
      <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
      正在流式生成草稿...
      <span className="ml-auto text-xs text-blue-400">
        {chars} chars | {cps} c/s | {mm}:{ss}
      </span>
    </div>
  );
}
