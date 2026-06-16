import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';
import { AssetTree } from '../asset/AssetTree';
import { ChapterList } from '../chapter/ChapterList';

export function LeftPanel() {
  const navigate = useNavigate();
  const projects = useProjectStore((s) => s.projects);
  const currentProject = useProjectStore((s) => s.currentProject);
  const selectProject = useProjectStore((s) => s.selectProject);

  return (
    <div className="h-full overflow-y-auto p-3 space-y-4">
      <div>
        <h2 className="font-bold text-lg mb-2">项目</h2>
        <select
          className="w-full border rounded p-1.5 text-sm"
          value={currentProject?.project_id || ''}
          onChange={(e) => {
            selectProject(e.target.value);
            navigate('/project/' + e.target.value);
          }}
        >
          <option value="">选择项目...</option>
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>{p.project_name} · {p.genre || ''}</option>
          ))}
        </select>
      </div>

      {currentProject && (
        <>
          <AssetTree />
          <div className="border-t pt-3">
            <ChapterList />
          </div>
        </>
      )}
    </div>
  );
}