import { useState, useEffect, useCallback } from 'react';
import { eventsApi } from '../../api/events';
import type { ProjectEvent } from '../../api/events';

interface ActivityDrawerProps {
  projectId: string;
  open: boolean;
  onClose: () => void;
}

const actionLabels: Record<string, string> = {
  create_project: '创建项目',
  create_chapter: '创建章节',
  share_link_created: '生成分享链接',
  draft_generated: '生成草稿',
  chapter_approved: '确认章节',
  state_updated: '更新状态',
};

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return ts;
  }
}

export function ActivityDrawer({ projectId, open, onClose }: ActivityDrawerProps) {
  const [events, setEvents] = useState<ProjectEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [shareLoading, setShareLoading] = useState(false);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await eventsApi.list(projectId);
      setEvents(res.events);
    } catch { /* ignore */ }
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    if (open) {
      loadEvents();
    }
  }, [open, loadEvents]);

  const handleShare = async () => {
    setShareLoading(true);
    try {
      const res = await eventsApi.share(projectId);
      setShareUrl(`${window.location.origin}${res.url}`);
      await loadEvents();
    } catch { /* ignore */ }
    setShareLoading(false);
  };

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
    }
  };

  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      )}
      <div
        className={`fixed top-0 right-0 h-full w-80 bg-white shadow-xl z-50 transform transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h3 className="font-bold text-sm">活动时间线</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
          </div>

          <div className="flex gap-2 px-4 py-2 border-b border-gray-100">
            <button
              onClick={handleShare}
              disabled={shareLoading}
              className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {shareLoading ? '生成中...' : '生成分享链接'}
            </button>
          </div>

          {shareUrl && (
            <div className="px-4 py-2 bg-blue-50 border-b border-blue-100 flex items-center gap-2">
              <span className="text-xs text-blue-700 truncate flex-1">{shareUrl}</span>
              <button
                onClick={handleCopy}
                className="text-xs text-blue-600 hover:text-blue-800 whitespace-nowrap"
              >
                复制
              </button>
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="text-sm text-gray-400 text-center py-8">加载中...</div>
            ) : events.length === 0 ? (
              <div className="text-sm text-gray-400 text-center py-8">暂无活动</div>
            ) : (
              <div className="relative">
                <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-200" />
                {events.map((ev) => (
                  <div key={ev.event_id} className="flex items-start gap-3 px-4 py-3">
                    <div className="w-3 h-3 rounded-full bg-blue-400 mt-1 shrink-0 relative z-10" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-700">
                        {actionLabels[ev.action] || ev.action}
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {ev.actor} &middot; {formatTime(ev.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
