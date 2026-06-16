import { useState, useEffect } from 'react';
import { api } from '../../api/client';

export function HealthBadge() {
  const [status, setStatus] = useState<'loading' | 'ok' | 'degraded' | 'error'>('loading');

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.get<{ status: string }>('/health');
        setStatus(res.status as 'ok' | 'degraded');
      } catch {
        setStatus('error');
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

  return (
    <span className="fixed top-3 left-4 z-30 flex items-center gap-1.5 text-xs">
      <span className={'inline-block w-2 h-2 rounded-full ' + colorMap[status]} />
      <span className="text-gray-500">{status}</span>
    </span>
  );
}
