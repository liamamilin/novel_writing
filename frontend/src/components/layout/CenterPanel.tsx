import { useUIStore } from '../../stores/uiStore';
import { useChapterStore } from '../../stores/chapterStore';
import { useProjectStore } from '../../stores/projectStore';
import { lazy, Suspense, useState, useEffect } from 'react';
import { chaptersApi } from '../../api/chapters';
import type { ReviewData } from '../review/ReviewTabs';
import { api } from '../../api/client';
import { ErrorBoundary } from '../ErrorBoundary';

const ChapterEditor = lazy(() => import('../chapter/ChapterEditor').then(m => ({ default: m.ChapterEditor })));
const ReviewTabs = lazy(() => import('../review/ReviewTabs').then(m => ({ default: m.ReviewTabs })));
const BibleViewer = lazy(() => import('../asset/BibleViewer').then(m => ({ default: m.BibleViewer })));
const SubplotTable = lazy(() => import('../asset/SubplotTable').then(m => ({ default: m.SubplotTable })));
const HookTable = lazy(() => import('../asset/HookTable').then(m => ({ default: m.HookTable })));
const StrategyForm = lazy(() => import('../asset/StrategyForm').then(m => ({ default: m.StrategyForm })));
const SnapshotList = lazy(() => import('../asset/SnapshotList').then(m => ({ default: m.SnapshotList })));
const MultiReaderChart = lazy(() => import('../chapter/MultiReaderChart').then(m => ({ default: m.MultiReaderChart })));

const assetComponents: Record<string, React.ComponentType> = {
  bible: BibleViewer,
  state: SnapshotList,
  hooks: HookTable,
  subplots: SubplotTable,
  strategy: StrategyForm,
};

function Loading() {
  return <div className="flex items-center justify-center h-full text-gray-400 text-sm">加载中...</div>;
}

export function CenterPanel() {
  const selectedAsset = useUIStore((s) => s.selectedAsset);
  const currentChapter = useChapterStore((s) => s.currentChapter);
  const currentProject = useProjectStore((s) => s.currentProject);

  const renderContent = () => {
    if (selectedAsset) {
      if (selectedAsset.type === 'chapter' && currentChapter) {
        return (
          <div className="h-full p-4 overflow-y-auto overflow-x-hidden">
            <Suspense fallback={<Loading />}>
              <ChapterEditor />
            </Suspense>
          </div>
        );
      }

      if (selectedAsset.type === 'review' && currentProject && currentChapter) {
        return <ReviewPanel projectId={currentProject.project_id} chapterNumber={currentChapter.chapter_number} />;
      }

      if (selectedAsset.type === 'style') {
        return (
          <div className="h-full p-4 overflow-y-auto overflow-x-hidden">
            <Suspense fallback={<Loading />}>
              <StyleViewer />
            </Suspense>
          </div>
        );
      }

      if (selectedAsset.type === 'multi_reader' && currentProject && currentChapter) {
        return (
          <div className="h-full p-4 overflow-y-auto overflow-x-hidden">
            <Suspense fallback={<Loading />}>
              <MultiReaderChart projectId={currentProject.project_id} chapterNumber={currentChapter.chapter_number} />
            </Suspense>
          </div>
        );
      }

      const Component = assetComponents[selectedAsset.type];
      if (Component) {
        return (
          <div className="h-full p-4 overflow-y-auto overflow-x-hidden">
            <Suspense fallback={<Loading />}>
              <Component />
            </Suspense>
          </div>
        );
      }
    }

    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>选择左侧资产或章节开始编辑</p>
      </div>
    );
  };

  return <ErrorBoundary>{renderContent()}</ErrorBoundary>;
}

function ReviewPanel({ projectId, chapterNumber }: { projectId: string; chapterNumber: number }) {
  const notify = useUIStore((s) => s.notify);
  const [reviews, setReviews] = useState<Record<string, ReviewData> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    chaptersApi.getReviews(projectId, chapterNumber)
      .then((res) => {
        const parsed: Record<string, ReviewData> = {};
        for (const [key, raw] of Object.entries(res.reviews)) {
          const body = (raw as string) || '';
          const summary = body ? (body.split('## ').find(s => s.startsWith('Summary'))?.split('\n').slice(1).join('\n').trim() || '') : '';
          const issues = body ? body.split('### Issue').slice(1).map(i => i.trim()).filter(Boolean) : [];
          parsed[key] = { summary, issues, fix_instructions: [] };
        }
        setReviews(Object.keys(parsed).length > 0 ? parsed : null);
      })
      .catch(() => notify('加载审查报告失败', 'error'))
      .finally(() => setLoading(false));
  }, [projectId, chapterNumber]);

  if (loading) return <div className="flex items-center justify-center h-full text-gray-400 text-sm py-8">加载审查中...</div>;
  if (!reviews) return <div className="flex items-center justify-center h-full text-gray-400 text-sm py-8">暂无审查数据</div>;

  return (
    <div className="h-full p-4 overflow-y-auto">
      <Suspense fallback={<div className="text-sm text-gray-400 py-8">加载中...</div>}>
        <ReviewTabs reviews={reviews} onApplyFix={(fix) => {
          notify('修复指令已记录：' + fix.description, 'info');
        }} />
      </Suspense>
    </div>
  );
}

function StyleViewer() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [text, setText] = useState('');
  const [result, setResult] = useState<string | null>(null);

  const handleTest = async () => {
    if (!currentProject || !text.trim()) return;
    try {
      const res = await api.post(`/projects/${currentProject.project_id}/styles/default-style/test-paragraph`, { topic: text });
      setResult(JSON.stringify(res, null, 2));
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-lg">文风特征</h3>
      <div className="bg-gray-50 rounded p-3 text-sm">
        <p className="text-gray-500 mb-2">文风分析完成后在这里展示风格特征（句长、节奏、主题词、修辞等）。</p>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">测试段落</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm h-24"
          placeholder="输入一段文字测试文风匹配..."
        />
        <button onClick={handleTest} className="mt-2 text-sm bg-blue-500 text-white px-3 py-1.5 rounded hover:bg-blue-600">
          测试文风匹配
        </button>
      </div>
      {result && (
        <pre className="text-xs bg-gray-50 rounded p-3 whitespace-pre-wrap">{result}</pre>
      )}
    </div>
  );
}