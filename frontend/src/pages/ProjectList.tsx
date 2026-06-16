import { useEffect, useState } from 'react';
import { useProjectStore } from '../stores/projectStore';

export function ProjectList() {
  const { projects, loadProjects, createProject } = useProjectStore();
  const [name, setName] = useState('');
  const [genre, setGenre] = useState('');

  useEffect(() => { loadProjects(); }, []);

  const handleCreate = async () => {
    if (!name || !genre) return;
    await createProject({ project_name: name, genre });
    setName('');
    setGenre('');
    await loadProjects();
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Novel Writing Runtime</h1>
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="font-semibold mb-3">创建项目</h2>
        <input
          className="w-full border rounded p-2 mb-2"
          placeholder="项目名称"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="w-full border rounded p-2 mb-2"
          placeholder="小说类型（如: 都市修仙）"
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
        />
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          创建项目
        </button>
      </div>
      <div className="space-y-2">
        {projects.map((p) => (
          <div key={p.project_id} className="bg-white rounded shadow p-3 flex justify-between">
            <div>
              <span className="font-medium">{p.project_name}</span>
              <span className="ml-2 text-sm text-gray-500">{p.genre}</span>
            </div>
            <span className="text-sm text-gray-400">{p.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
