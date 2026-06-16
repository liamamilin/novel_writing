import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useUIStore } from '../stores/uiStore';
import { projectsApi } from '../api/projects';

export function ProjectList() {
  const navigate = useNavigate();
  const { projects, loadProjects } = useProjectStore();
  const notify = useUIStore((s) => s.notify);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => { loadProjects(); }, []);

  const handleCreateDemo = async () => {
    setDemoLoading(true);
    try {
      const result = await projectsApi.create({
        project_name: '示例项目',
        genre: '都市修仙',
        idea: '一个被家族抛弃的年轻人意外获得古老传承，在现代都市中崛起。',
      });
      notify('示例项目已创建', 'success');
      await loadProjects();
      navigate('/project/' + result.project_id);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold flex-1">Novel Writing Runtime</h1>
        <button
          onClick={handleCreateDemo}
          disabled={demoLoading}
          className="text-sm text-gray-500 hover:text-blue-600 border border-gray-300 rounded px-3 py-1.5 disabled:opacity-50"
        >
          {demoLoading ? '创建中...' : '加载示例项目'}
        </button>
      </div>
      <Link
        to="/project/new"
        className="inline-block bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-700 mb-6"
      >
        + 新建项目
      </Link>
      <div className="space-y-2">
        {projects.length === 0 && (
          <p className="text-gray-400 text-sm">暂无项目，点击上方按钮创建</p>
        )}
        {projects.map((p) => (
          <button
            key={p.project_id}
            onClick={() => navigate(`/project/${p.project_id}`)}
            className="w-full bg-white rounded shadow p-3 flex justify-between hover:bg-gray-50 text-left"
          >
            <div>
              <span className="font-medium">{p.project_name}</span>
              <span className="ml-2 text-sm text-gray-500">{p.genre}</span>
            </div>
            <span className="text-sm text-gray-400">{p.status}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
