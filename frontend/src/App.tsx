import { BrowserRouter, Routes, Route, useParams, useSearchParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThreeColumnLayout } from './components/layout/ThreeColumnLayout';
import { LeftPanel } from './components/layout/LeftPanel';
import { CenterPanel } from './components/layout/CenterPanel';
import { RightPanel } from './components/layout/RightPanel';
import { ActivityDrawer } from './components/layout/ActivityDrawer';
import { HealthBadge } from './components/layout/HealthBadge';
import { ProjectList } from './pages/ProjectList';
import { ProjectCreate } from './pages/ProjectCreate';
import { SharedReader } from './pages/SharedReader';
import { useUIStore } from './stores/uiStore';
import { useProjectStore } from './stores/projectStore';
import { useChapterStore } from './stores/chapterStore';
import { useState, useEffect } from 'react';
import { TokenModal } from './components/auth/TokenModal';

const queryClient = new QueryClient();

function MainLayout() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const { notification, clearNotification } = useUIStore();
  const currentProject = useProjectStore((s) => s.currentProject);
  const selectProject = useProjectStore((s) => s.selectProject);
  const selectAsset = useUIStore((s) => s.selectAsset);
  const [activityOpen, setActivityOpen] = useState(false);

  const [showTokenModal, setShowTokenModal] = useState(false);
  const clearChapters = useChapterStore((s) => s.clearChapters);
  const chapters = useChapterStore((s) => s.chapters);
  const setCurrentChapter = useChapterStore((s) => s.setCurrentChapter);
  const loadProjects = useProjectStore((s) => s.loadProjects);

  useEffect(() => {
    const handler = () => setShowTokenModal(true);
    window.addEventListener('auth:required', handler);
    return () => window.removeEventListener('auth:required', handler);
  }, []);

  // B1 + N4 + N14: sync route param + load projects + clear stale selection
  useEffect(() => {
    loadProjects();
    if (id && (!currentProject || currentProject.project_id !== id)) {
      clearChapters();
      selectAsset(null);
      selectProject(id);
    }
  }, [id, currentProject, selectProject, clearChapters, loadProjects, selectAsset]);

  // N1: restore chapter/asset from URL query after chapters load.
  // Auto-select first chapter if none specified.
  useEffect(() => {
    if (!currentProject || chapters.length === 0) return;
    const chParam = searchParams.get('ch');
    if (chParam) {
      const ch = chapters.find((c) => c.chapter_number === Number(chParam));
      if (ch && (!useChapterStore.getState().currentChapter || useChapterStore.getState().currentChapter?.chapter_id !== ch.chapter_id)) {
        setCurrentChapter(ch);
        selectAsset({ type: 'chapter', id: ch.chapter_id });
      }
    } else if (!useChapterStore.getState().currentChapter) {
      const first = chapters[0];
      setCurrentChapter(first);
      selectAsset({ type: 'chapter', id: first.chapter_id });
    }
  }, [currentProject?.project_id, chapters.length]);

  return (
    <div>
      {notification && (
        <div
          className={`fixed top-20 right-4 z-50 px-4 py-2 rounded shadow-lg text-white cursor-pointer max-w-sm text-sm ${
            notification.type === 'error' ? 'bg-red-500' :
            notification.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
          }`}
          onClick={clearNotification}
        >
          {notification.message}
        </div>
      )}

      <HealthBadge />
      {currentProject && (
        <>
          <button
            onClick={() => setActivityOpen(true)}
            className="fixed top-3 right-4 z-30 text-xs bg-white border border-gray-300 rounded px-2 py-1 text-gray-600 hover:bg-gray-50 shadow-sm"
            title="活动"
          >
            {'\uD83D\uDD14'} 活动
          </button>
          <ActivityDrawer
            projectId={currentProject.project_id}
            open={activityOpen}
            onClose={() => setActivityOpen(false)}
          />
        </>
      )}

      <ThreeColumnLayout
        left={<LeftPanel />}
        center={<CenterPanel />}
        right={<RightPanel />}
      />

      {showTokenModal && <TokenModal onClose={() => setShowTokenModal(false)} />}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/project/new" element={<ProjectCreate />} />
          <Route path="/project/:id" element={<MainLayout />} />
          <Route path="/shared/:token" element={<SharedReader />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}