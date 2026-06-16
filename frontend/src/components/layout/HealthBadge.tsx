import { useState, useEffect, useRef } from 'react';
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
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.get<{ status: string; checks: HealthDetail }>('/health');
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
      onClick={() => window.open('/health', '_blank')}
      onMouseEnter={() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        setShowTooltip(true);
      }}
      onMouseLeave={() => {
        timerRef.current = setTimeout(() => setShowTooltip(false), 300);
      }}
    >
      <span className={'inline-block w-2 h-2 rounded-full ' + colorMap[status]} />
      <span className="text-gray-500">{labelMap[status] || status}</span>
      {showTooltip && detail && (
        <span className="absolute top-5 left-0 bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-40 shadow">
          DB: {detail.database?.status || '?'} | 存储: {detail.storage?.status || '?'} | LLM: {detail.llm?.status || '?'}
          {detail.llm?.detail?.latency_ms != null ? ` (${detail.llm.detail.latency_ms}ms)` : ''}
          <span className="block text-gray-400">点击查看完整 /health</span>
        </span>
      )}
    </span>
  );
}
