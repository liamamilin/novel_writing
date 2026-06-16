import { useState } from 'react';
import { chaptersApi } from '../../api/chapters';

interface ReviewResult {
  persona_id: string;
  persona_name: string;
  error?: string;
  feedback?: string;
  [key: string]: unknown;
}

const personaColors: Record<string, string> = {
  action_addicted: '#ef4444',
  romance_fan: '#ec4899',
  literary_critic: '#8b5cf6',
  newcomer: '#22c55e',
  critic: '#f59e0b',
};

interface MultiReaderChartProps {
  projectId: string;
  chapterNumber: number;
}

function scoreBars(result: ReviewResult) {
  const entries = Object.entries(result).filter(
    ([k, v]) => k.endsWith('_score') && typeof v === 'number'
  );
  return entries.map(([key, val]) => {
    const label = key
      .replace(/_score$/, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
    return { label, value: val as number };
  });
}

export function MultiReaderChart({ projectId, chapterNumber }: MultiReaderChartProps) {
  const [results, setResults] = useState<ReviewResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runReview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await chaptersApi.multiReaderReview(projectId, chapterNumber);
      setResults(res.results as ReviewResult[]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-sm text-gray-700">多读者画像评分</h4>
        <button
          onClick={runReview}
          disabled={loading}
          className="text-xs bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600 disabled:opacity-50"
        >
          {loading ? '评估中...' : results ? '重新评估' : '开始评估'}
        </button>
      </div>

      {error && (
        <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded">{error}</div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span className="inline-block w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
          正在评估各读者画像...
        </div>
      )}

      {results && !loading && (
        <div className="grid grid-cols-1 gap-3">
          {results.map((r) => {
            if (r.error) {
              return (
                <div key={r.persona_id} className="border border-gray-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-500">{r.persona_name}</div>
                  <div className="text-xs text-red-500 mt-1">评分失败: {r.error}</div>
                </div>
              );
            }

            const color = personaColors[r.persona_id] || '#3b82f6';
            const bars = scoreBars(r);

            return (
              <div key={r.persona_id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-sm font-medium">{r.persona_name}</span>
                </div>
                <div className="space-y-1.5">
                  {bars.map((b) => (
                    <div key={b.label}>
                      <div className="flex justify-between text-xs text-gray-500 mb-0.5">
                        <span>{b.label}</span>
                        <span className="font-medium">{b.value}/10</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{ width: `${(b.value / 10) * 100}%`, backgroundColor: color }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                {r.feedback && (
                  <div className="mt-2 text-xs text-gray-500 italic line-clamp-2">
                    &ldquo;{String(r.feedback)}&rdquo;
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!results && !loading && !error && (
        <div className="text-sm text-gray-400">点击"开始评估"查看 5 种读者画像对本章的评分</div>
      )}
    </div>
  );
}
