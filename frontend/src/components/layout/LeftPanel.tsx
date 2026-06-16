import { useProjectStore } from '../../stores/projectStore';
import { AssetTree } from '../asset/AssetTree';
import { ChapterList } from '../chapter/ChapterList';

export function LeftPanel() {
  const projects = useProjectStore((s) => s.projects);
  const currentProject = useProjectStore((s) => s.currentProject);
  const selectProject = useProjectStore((s) => s.selectProject);

  return (
    <div className="h-full overflow-y-auto p-3 space-y-4">
      <div>
        <h2 className="font-bold text-lg mb-2">\u9879\u76EE</h2>
        <select
          className="w-full border rounded p-1.5 text-sm"
          value={currentProject?.project_id || ''}
          onChange={(e) => selectProject(e.target.value)}
        >
          <option value="">\u9009\u62E9\u9879\u76EE...</option>
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
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