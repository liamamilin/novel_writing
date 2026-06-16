import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { sharedApi } from '../api/shared';

export function SharedReader() {
  const { token } = useParams<{ token: string }>();
  const [project, setProject] = useState<{ project_name: string; genre?: string } | null>(null);
  const [chapters, setChapters] = useState<{ chapter_number: number; title: string; status: string }[]>([]);
  const [currentCh, setCurrentCh] = useState<number | null>(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([
      sharedApi.getProject(token),
      sharedApi.getChapters(token),
    ])
      .then(([proj, chs]) => {
        setProject(proj);
        setChapters(chs.chapters);
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token || currentCh === null) return;
    sharedApi.getChapter(token, currentCh)
      .then((res) => setContent(res.content))
      .catch((e) => setContent('（加载失败：' + (e as Error).message + '）'));
  }, [token, currentCh]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-gray-400 text-sm">
        加载共享项目...
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-red-600 text-sm">
        无法访问：{error}
      </div>
    );
  }

  if (!project) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-gray-400 text-sm">
        分享链接无效或已过期
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-1">{project.project_name}</h1>
      {project.genre && <p className="text-sm text-gray-500 mb-4">{project.genre}</p>}

      <div className="flex gap-4 mb-6">
        <div className="w-48 shrink-0">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">章节</h3>
          <div className="space-y-1">
            {chapters.map((ch) => (
              <button
                key={ch.chapter_number}
                onClick={() => setCurrentCh(ch.chapter_number)}
                className={`block w-full text-left text-sm px-2 py-1 rounded ${
                  currentCh === ch.chapter_number
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                第 {ch.chapter_number} 章 — {ch.title || '(无标题)'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          {currentCh === null ? (
            <p className="text-gray-400 text-sm py-8 text-center">选择一个章节开始阅读</p>
          ) : (
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">
              {content || '(暂无内容)'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
