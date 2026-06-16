import { useState, useEffect, useCallback } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { useChapterStore } from '../../stores/chapterStore';
import { useProjectStore } from '../../stores/projectStore';
import { useStreamStore } from '../../stores/streamStore';
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
  const [activeTab, setActiveTab] = useState<'plan' | 'draft' | 'final'>('draft');
  const [content, setContent] = useState('');
  const isStreaming = useStreamStore((s) => s.isStreaming);
  const streamedContent = useStreamStore((s) => s.streamedContent);
  const [showDiff, setShowDiff] = useState(false);
  const [diffOld, setDiffOld] = useState('');
  const [diffNew, setDiffNew] = useState('');
  const [diffOldTitle, setDiffOldTitle] = useState('');
  const [diffNewTitle, setDiffNewTitle] = useState('');

  useEffect(() => {
    if (currentChapter) {
      if (currentChapter.status === 'planned') setActiveTab('plan');
      else if (currentChapter.status === 'locked' || currentChapter.status === 'approved') setActiveTab('final');
      else setActiveTab('draft');
    }
  }, [currentChapter]);

  const handleDraftSelect = useCallback((_draftId: number, _content: string) => {
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
  }, [currentProject, loadChapters]);

  if (!currentProject || !currentChapter) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>选择一个章节开始编辑</p>
      </div>
    );
  }

  const isReadOnly = currentChapter.status === 'approved' || currentChapter.status === 'locked';
  const currentStatusIdx = STATUS_FLOW.indexOf(currentChapter.status as typeof STATUS_FLOW[number]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-bold">
          第 {currentChapter.chapter_number} 章
          {currentChapter.title ? ` — ${currentChapter.title}` : ''}
          <span className="ml-2 text-sm font-normal text-gray-500">
            ({statusLabel[currentChapter.status] || currentChapter.status})
          </span>
        </h2>
      </div>

      <div className="flex items-center gap-1 mb-3">
        {STATUS_FLOW.map((s, i) => {
          const active = i <= currentStatusIdx;
          const isCurrent = s === currentChapter.status;
          return (
            <div key={s} className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full ${
                  isCurrent ? 'bg-blue-500 ring-2 ring-blue-200' :
                  active ? 'bg-blue-400' :
                  'bg-gray-300'
                }`}
                title={statusLabel[s]}
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
        <div className="flex gap-2">
          {(['plan', 'draft', 'final'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              disabled={isStreaming}
              className={`px-3 py-1 text-sm rounded border ${
                activeTab === tab ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
              } ${isStreaming ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {tab === 'plan' ? '规划' : tab === 'draft' ? '草稿' : '终稿'}
            </button>
          ))}
        </div>
        <DraftSelector
          projectId={currentProject.project_id}
          chapterNumber={currentChapter.chapter_number}
          onSelect={handleDraftSelect}
          onPromote={handlePromote}
        />
      </div>

      {isStreaming && (
        <div className="flex items-center gap-2 mb-3 bg-blue-50 border border-blue-200 text-blue-700 text-sm px-3 py-2 rounded">
          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          正在流式生成草稿...
          <span className="ml-auto text-xs text-blue-400">{streamedContent.length} chars</span>
        </div>
      )}

      {showDiff ? (
        <div className="flex-1 overflow-auto">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-600">版本对比</h4>
            <button
              onClick={() => setShowDiff(false)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              返回编辑
            </button>
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
          <MDEditor
            value={isStreaming ? streamedContent : content}
            onChange={(v) => !isReadOnly && !isStreaming && setContent(v || '')}
            preview={isStreaming || isReadOnly ? 'preview' : 'edit'}
            hideToolbar={isStreaming || isReadOnly}
            height="100%"
          />
        </div>
      )}
    </div>
  );
}
