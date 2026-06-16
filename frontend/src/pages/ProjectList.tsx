import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';

export function ProjectList() {
  const navigate = useNavigate();
  const { projects, loadProjects } = useProjectStore();

  useEffect(() => { loadProjects(); }, []);

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Novel Writing Runtime</h1>
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
