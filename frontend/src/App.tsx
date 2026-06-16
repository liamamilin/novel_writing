import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThreeColumnLayout } from './components/layout/ThreeColumnLayout';
import { LeftPanel } from './components/layout/LeftPanel';
import { CenterPanel } from './components/layout/CenterPanel';
import { RightPanel } from './components/layout/RightPanel';
import { ActivityDrawer } from './components/layout/ActivityDrawer';
import { HealthBadge } from './components/layout/HealthBadge';
import { ProjectList } from './pages/ProjectList';
import { ProjectCreate } from './pages/ProjectCreate';
import { useUIStore } from './stores/uiStore';
import { useProjectStore } from './stores/projectStore';
import { useState } from 'react';

const queryClient = new QueryClient();

function MainLayout() {
  const { notification, clearNotification } = useUIStore();
  const currentProject = useProjectStore((s) => s.currentProject);
  const [activityOpen, setActivityOpen] = useState(false);

  return (
    <div>
      {notification && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-2 rounded shadow-lg text-white cursor-pointer ${
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
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}