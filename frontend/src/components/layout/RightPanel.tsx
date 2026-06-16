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
  planned: '规划',
  drafted: '草稿',
  reviewed: '已审查',
  approved: '已确认',
  locked: '已锁定',
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
    if (!pid) { notify('请先选择项目', 'error'); return; }
    setLoading(key);
    try {
      const result = await fn();
      if (key !== 'check') notify(`${key} 完成`, 'success');
      if (pid) await loadChapters(pid);
      return result;
    } catch (e) {
      const msg = (e as Error).message;
      if (msg !== 'cancelled') notify(msg, 'error');
    } finally {
      setLoading(null);
    }
  };

  const chapterActions: ActionButton[] = ch ? [
    {
      label: '编译上下文',
      action: 'compile_context',
      apiCall: () => api.post(`/projects/${pid}/context/compile?chapter_number=${ch}`, {}),
    },
    {
      label: '生成规划',
      action: 'plan',
      apiCall: () => chaptersApi.plan(pid!, ch!),
      requireStatus: ['planned'],
    },
    {
      label: '生成草稿',
      action: 'draft',
      apiCall: () => chaptersApi.draft(pid!, ch!),
      requireStatus: ['planned'],
    },
    {
      label: '文风润色',
      action: 'polish',
      apiCall: () => chaptersApi.polish(pid!, ch!),
      requireStatus: ['drafted'],
    },
    {
      label: '审查 (4维)',
      action: 'review',
      apiCall: () => chaptersApi.review(pid!, ch!, ['continuity', 'quality', 'cross_chapter', 'reader_sim']),
      requireStatus: ['drafted', 'reviewed'],
    },
    {
      label: '确认章节',
      action: 'approve',
      apiCall: async () => {
        const ok = window.confirm('确认将本章标记为"已确认"？之后将不可编辑。');
        if (!ok) throw new Error('cancelled');
        return chaptersApi.approve(pid!, ch!, '');
      },
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
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDCC1"} 项目管理</h3>
        <button
          onClick={async () => {
            if (!pid) { notify('请先选择项目', 'error'); return; }
            setLoading('check');
            try {
              const res = await api.rawGet<any>('/health');
              const llm = res.checks?.llm;
              const parts = [
                `数据库: ${res.checks?.database?.status || '?'}`,
                `存储: ${res.checks?.storage?.status || '?'}`,
                `LLM: ${llm?.status || '?'} (${llm?.detail?.model || '?'})`,
              ];
              if (llm?.detail?.latency_ms) parts.push(`延迟: ${llm.detail.latency_ms}ms`);
              notify('系统状态: ' + parts.join(' | '), res.status === 'ok' ? 'success' : 'error');
            } catch (e) {
              notify('健康检查失败: ' + (e as Error).message, 'error');
            } finally {
              setLoading(null);
            }
          }}
          disabled={!!loading}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          {loading === 'check' ? '检查中...' : `\u{1F3A5} 系统状态检查`}
        </button>
        <button
          onClick={() => setShowExport(true)}
          disabled={!pid}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          {"⬇"} 导出项目
        </button>
      </div>

      {showExport && pid && <ExportModal projectId={pid} onClose={() => setShowExport(false)} />}

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83C\uDFA8"} 文风</h3>
        <button
          onClick={() => selectAsset({ type: 'style' })}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0"
        >
          查看文风资产
        </button>
      </div>

      {currentChapter && (
        <div>
          <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">
            {"\uD83D\uDCDD"} 第 {ch} 章
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
              {loading === btn.label ? '处理中...' : btn.label}
            </button>
          ))}
          {currentChapter.status === 'planned' && (
            <button
              onClick={() => {
                if (isStreaming) {
                  if (window.confirm('确定要停止流式生成吗？未完成部分不会被保存。')) {
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
              {isStreaming ? '✕ 停止流式' : '▶ 流式生成草稿'}
            </button>
          )}
        </div>
      )}

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDCCA"} 状态</h3>
        <button
          onClick={() => runAction('更新状态', () => stateApi.update(pid!, ch!))}
          disabled={!pid || !ch || !!loading}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          更新状态
        </button>
        <button
          onClick={() => selectAsset({ type: 'state' })}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0"
        >
          查看快照
        </button>
      </div>

      <div>
        <h3 className="font-bold text-sm text-gray-500 uppercase mb-1">{"\uD83D\uDD0D"} 审查</h3>
        <button
          onClick={() => selectAsset({ type: 'review' })}
          disabled={!currentChapter}
          className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded border-b last:border-b-0 disabled:opacity-50"
        >
          查看审查报告
        </button>
        <button
          onClick={() => selectAsset({ type: 'multi_reader' })}
          disabled={!currentChapter}
          className="w-full text-left px-3 py-2 text-sm hover:bg-purple-50 rounded border-b last:border-b-0 disabled:opacity-50 text-purple-700"
        >
          {"\uD83D\uDCCA"} 多读者画像
        </button>
      </div>
    </div>
  );
}
