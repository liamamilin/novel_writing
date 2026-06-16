import { useUIStore } from '../../stores/uiStore';
import { useChapterStore } from '../../stores/chapterStore';
import { useProjectStore } from '../../stores/projectStore';
import { lazy, Suspense } from 'react';

const ChapterEditor = lazy(() => import('../chapter/ChapterEditor').then(m => ({ default: m.ChapterEditor })));
const ReviewTabs = lazy(() => import('../review/ReviewTabs').then(m => ({ default: m.ReviewTabs })));
const BibleVersion = lazy(() => import('../asset/BibleVersion').then(m => ({ default: m.BibleVersion })));
const SubplotTable = lazy(() => import('../asset/SubplotTable').then(m => ({ default: m.SubplotTable })));
const HookTable = lazy(() => import('../asset/HookTable').then(m => ({ default: m.HookTable })));
const StrategyForm = lazy(() => import('../asset/StrategyForm').then(m => ({ default: m.StrategyForm })));
const SnapshotList = lazy(() => import('../asset/SnapshotList').then(m => ({ default: m.SnapshotList })));
const MultiReaderChart = lazy(() => import('../chapter/MultiReaderChart').then(m => ({ default: m.MultiReaderChart })));

const assetComponents: Record<string, React.ComponentType> = {
  bible: BibleVersion,
  style: BibleVersion,
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

  if (selectedAsset) {
    if (selectedAsset.type === 'chapter' && currentChapter) {
      return (
        <div className="h-full p-4 overflow-y-auto">
          <Suspense fallback={<Loading />}>
            <ChapterEditor />
          </Suspense>
        </div>
      );
    }

    if (selectedAsset.type === 'review') {
      return (
        <div className="h-full p-4 overflow-y-auto">
          <Suspense fallback={<Loading />}>
            <ReviewTabs reviews={{}} onApplyFix={() => {}} />
          </Suspense>
        </div>
      );
    }

    if (selectedAsset.type === 'multi_reader' && currentProject && currentChapter) {
      return (
        <div className="h-full p-4 overflow-y-auto">
          <Suspense fallback={<Loading />}>
            <MultiReaderChart projectId={currentProject.project_id} chapterNumber={currentChapter.chapter_number} />
          </Suspense>
        </div>
      );
    }

    const Component = assetComponents[selectedAsset.type];
    if (Component) {
      return (
        <div className="h-full p-4 overflow-y-auto">
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
}