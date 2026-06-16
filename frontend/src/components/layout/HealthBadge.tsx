import { useState, useEffect } from 'react';
import { api } from '../../api/client';

interface HealthDetail {
  database?: { status: string };
  storage?: { status: string };
  llm?: { status: string; detail?: { model?: string; latency_ms?: number; key_configured?: boolean; base_url?: string; status_code?: number } };
}

export function HealthBadge() {
  const [status, setStatus] = useState<'loading' | 'ok' | 'degraded' | 'error'>('loading');
  const [detail, setDetail] = useState<HealthDetail | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.rawGet<{ status: string; checks: HealthDetail }>('/health');
        setStatus(res.status as 'ok' | 'degraded');
        setDetail(res.checks);
      } catch {
        setStatus('error');
        setDetail(null);
      }
    };
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  const colorMap: Record<string, string> = {
    ok: 'bg-green-500',
    degraded: 'bg-yellow-500',
    error: 'bg-red-500',
    loading: 'bg-gray-400',
  };

  if (status === 'loading') return null;

  const labelMap: Record<string, string> = {
    ok: '正常',
    degraded: '异常',
    error: '不可达',
  };

  return (
    <span
      className="fixed top-3 left-4 z-30 flex items-center gap-1.5 text-xs cursor-pointer"
      onClick={() => setShowTooltip(v => !v)}
    >
      <span className={'inline-block w-2 h-2 rounded-full ' + colorMap[status]} />
      <span className="text-gray-500">{labelMap[status] || status}</span>
      {showTooltip && detail && (
        <span className="absolute top-5 left-0 bg-gray-800 text-white text-xs rounded px-3 py-2 whitespace-nowrap z-40 shadow space-y-1 min-w-[200px]">
          <div className="flex justify-between"><span>数据库:</span><span>{detail.database?.status || '?'}</span></div>
          <div className="flex justify-between"><span>存储:</span><span>{detail.storage?.status || '?'}</span></div>
          <div className="flex justify-between"><span>LLM:</span><span>{detail.llm?.status || '?'}</span></div>
          {detail.llm?.detail?.latency_ms != null && <div className="flex justify-between"><span>延迟:</span><span>{detail.llm.detail.latency_ms}ms</span></div>}
          {detail.llm?.detail?.model && <div className="flex justify-between text-gray-400"><span>模型:</span><span>{detail.llm.detail.model}</span></div>}
          <div className="text-gray-500 text-[10px] pt-1 border-t border-gray-700 mt-1">点击切换</div>
        </span>
      )}
    </span>
  );
}
