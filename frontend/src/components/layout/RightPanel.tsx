import { useState } from 'react';
import { useProjectStore } from '../../stores/projectStore';
import { useChapterStore } from '../../stores/chapterStore';
import { useUIStore } from '../../stores/uiStore';
import { useStreamStore } from '../../stores/streamStore';
import { chaptersApi } from '../../api/chapters';
import { api } from '../../api/client';
import { stateApi } from '../../api/state';
import { ExportModal } from '../chapter/ExportModal';

const statusLabel: Record<string, string> = {
  planned: '\u89C4\u5212',
  drafted: '\u8349\u7A3F',
  reviewed: '\u5DF2\u5BA1\u67E5',
  approved: '\u5DF2\u786E\u8BA4',
  locked: '\u5DF2\u9501\u5B9A',
};

interface ActionButton {
  label: string;
  action: string;
  apiCall: () => Promise<unknown>;
  requireStatus?: string[];
}

export function RightPanel() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const currentChapter = useChapterStore((s) => s.currentChapter);
  const notify = useUIStore((s) => s.notify);
  const selectAsset = useUIStore((s) => s.selectAsset);
  const loadChapters = useChapterStore((s) => s.loadChapters);
  const [loading, setLoading] = useState<string | null>(null);
  const [showExport, setShowExport] = useState(false);

  const pid = currentProject?.project_id;
  const ch = currentChapter?.chapter_number;
  const isStreaming = useStreamStore((s) => s.isStreaming);
  const streamDraft = useStreamStore((s) => s.streamDraft);
  const cancelStream = useStreamStore((s) => s.cancelStream);

  const runAction = async (key: string, fn: () => Promise<unknown>) => {
    if (!pid) { notify('\u8BF7\u5148\u9009\u62E9\u9879\u76EE', 'error'); return; }
    setLoading(key);
    try {
      const result = await fn();
      notify(`${key} \u5B8C\u6210`, 'success');
      if (pid) await loadChapters(pid);
      return result;
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(null);
    }
  };

  const chapterActions: ActionButton[] = ch ? [
    {
      label: '\u7F16\u8BD1\u4E0A\u4E0B\u6587',
      action: 'compile_context',
      apiCall: () => api.post(`/projects/${pid}/context/compile?chapter_number=${ch}`, {}),
    },
    {
      label: '\u751F\u6210\u89C4\u5212',
      action: 'plan',
      apiCall: () => chaptersApi.plan(pid!, ch!),
      requireStatus: ['planned'],
    },
    {
      label: '\u751F\u6210\u8349\u7A3F',
      action: 'draft',
      apiCall: () => chaptersApi.draft(pid!, ch!),
      requireStatus: ['planned'],
    },
    {
      label: '\u6587\u98CE\u6DA6\u8272',
      action: 'polish',
      apiCall: () => chaptersApi.polish(pid!, ch!),
      requireStatus: ['drafted'],
    },
    {
      label: '\u5BA1\u67E5 (4\u7EF4)',
      action: 'review',
      apiCall: () => chaptersApi.review(pid!, ch!, ['continuity', 'quality', 'cross_chapter', 'reader_sim']),
      requireStatus: ['drafted', 'reviewed'],
    },
    {
      label: '\u786E\u8BA4\u7AE0\u8282',
      action: 'approve',
      apiCall: () => chaptersApi.approve(pid!, ch!, ''),
      requireStatus: ['reviewed'],
    },
  ] : [];

  const isActionEnabled = (btn: ActionButton) => {
    if (!btn.requireStatus) return true;
    if (!currentChapter) return false;
    return btn.requireStatus.includes(currentChapter.status);
  };

  return (
    <div className="h-full overflow-y-auto p-3 space-y-4">
      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDCC1"} \u9879\u76EE\u7BA1\u7406</h3>
        <button
          onClick={() => runAction('health', () => api.get(`/health`))}
          disabled={!pid || !!loading}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          \u5065\u5EB7\u68C0\u67E5
        </button>
        <button
          onClick={() => setShowExport(true)}
          disabled={!pid}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          {"\u2B07"} \u5BFC\u51FA\u9879\u76EE
        </button>
      </div>

      {showExport && pid && <ExportModal projectId={pid} onClose={() => setShowExport(false)} />}

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83C\uDFA8"} \u6587\u98CE</h3>
        <button
          onClick={() => selectAsset({ type: 'style' })}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0"
        >
          \u67E5\u770B\u6587\u98CE\u8D44\u4EA7
        </button>
      </div>

      {currentChapter && (
        <div>
          <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">
            {"\uD83D\uDCDD"} \u7B2C {ch} \u7AE0
            <span className="ml-1 text-xs font-normal text-gray-400">
              ({statusLabel[currentChapter.status] || currentChapter.status})
            </span>
          </h3>
          {chapterActions.map((btn) => (
            <button
              key={btn.action}
              onClick={() => runAction(btn.label, btn.apiCall)}
              disabled={!isActionEnabled(btn) || !!loading}
              className={`w-full text-left px-3 py-2 text-sm rounded border-b last:border-b-0 ${
                isActionEnabled(btn) ? 'hover:bg-blue-50' : 'text-gray-400 cursor-not-allowed'
              } ${loading === btn.label ? 'animate-pulse' : ''}`}
            >
              {loading === btn.label ? '\u5904\u7406\u4E2D...' : btn.label}
            </button>
          ))}
          {currentChapter.status === 'planned' && (
            <button
              onClick={() => {
                if (isStreaming) {
                  if (window.confirm('确定要停止流式生成吗？已生成的内容不会丢失。')) {
                    cancelStream();
                  }
                } else {
                  streamDraft(pid!, ch!);
                }
              }}
              disabled={!!loading}
              className={`w-full text-left px-3 py-2 text-sm rounded border-b last:border-b-0 ${
                isStreaming ? 'text-red-600 hover:bg-red-50 font-medium' : 'hover:bg-blue-50'
              }`}
            >
              {isStreaming ? '\u2715 \u505C\u6B62\u6D41\u5F0F' : '\u25B6 \u6D41\u5F0F\u751F\u6210\u8349\u7A3F'}
            </button>
          )}
        </div>
      )}

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDCCA"} \u72B6\u6001</h3>
        <button
          onClick={() => runAction('\u66F4\u65B0\u72B6\u6001', () => stateApi.update(pid!, ch!))}
          disabled={!pid || !ch || !!loading}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          \u66F4\u65B0\u72B6\u6001
        </button>
        <button
          onClick={() => selectAsset({ type: 'state' })}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0"
        >
          \u67E5\u770B\u5FEB\u7167
        </button>
      </div>

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDD0D"} \u5BA1\u67E5</h3>
        <button
          onClick={() => selectAsset({ type: 'review' })}
          disabled={!currentChapter}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          \u67E5\u770B\u5BA1\u67E5\u62A5\u544A
        </button>
        <button
          onClick={() => selectAsset({ type: 'multi_reader' })}
          disabled={!currentChapter}
          className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 rounded border-b last:border-b-0 disabled:opacity-50 text-purple-700"
        >
          {"\uD83D\uDCCA"} \u591A\u8BFB\u8005\u753B\u50CF
        </button>
      </div>
    </div>
  );
}
