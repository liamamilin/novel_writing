import { useState, useEffect } from 'react';
import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { subplotsApi } from '../../api/subplots';
import type { Subplot } from '../../types';

const STATUS_OPTIONS = ['setup', 'escalating', 'climax', 'resolving', 'resolved', 'idle', 'abandoned'];
const TYPE_OPTIONS = ['main_plot', 'secondary', 'romance', 'mystery', 'world_building'];
const statusColor: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  idle: 'bg-yellow-100 text-yellow-700',
  resolved: 'bg-gray-200 text-gray-600',
};

export function SubplotTable() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [subplots, setSubplots] = useState<Subplot[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editType, setEditType] = useState('secondary');
  const [editStatus, setEditStatus] = useState('setup');
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      subplotsApi.list(currentProject.project_id)
        .then(setSubplots)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleCreate = async () => {
    if (!currentProject || !newName.trim()) return;
    try {
      await subplotsApi.create(currentProject.project_id, {
        name: newName,
        type: 'secondary',
        status: 'setup',
      });
      const updated = await subplotsApi.list(currentProject.project_id);
      setSubplots(updated);
      setShowCreate(false);
      setNewName('');
      notify('子线已创建', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleUpdate = async (subplotId: string, updates: Record<string, unknown>) => {
    if (!currentProject) return;
    try {
      await subplotsApi.update(currentProject.project_id, subplotId, updates);
      setSubplots(subplots.map(s => s.subplot_id === subplotId ? { ...s, ...updates } : s));
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleDelete = async (subplotId: string) => {
    if (!currentProject) return;
    if (!window.confirm('确定删除此子线？')) return;
    try {
      await subplotsApi.delete(currentProject.project_id, subplotId);
      setSubplots(subplots.filter(s => s.subplot_id !== subplotId));
      notify('子线已删除', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) return <div className="text-sm text-gray-400 py-4">请先选择项目</div>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">子线</h3>
        <button onClick={() => setShowCreate(true)} className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
          + 新建
        </button>
      </div>

      {loading && <div className="text-gray-400 text-sm">加载中...</div>}

      {showCreate && (
        <div className="border rounded p-3 space-y-2 bg-gray-50">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full border rounded px-2 py-1 text-sm"
            placeholder="子线名称"
            autoFocus
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">创建</button>
            <button onClick={() => setShowCreate(false)} className="text-xs text-gray-500 px-2 py-1">取消</button>
          </div>
        </div>
      )}

      {subplots.length === 0 && !loading && (
        <div className="text-gray-400 text-sm">暂无子线</div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 pr-4">名称</th>
              <th className="text-left py-2 pr-4">类型</th>
              <th className="text-left py-2 pr-4">状态</th>
              <th className="text-left py-2">操作</th>
            </tr>
          </thead>
          <tbody>
            {subplots.map((s) => (
              <tr key={s.subplot_id} className="border-b hover:bg-gray-50">
                <td className="py-2 pr-4">
                  {editingId === s.subplot_id ? (
                    <input value={editName} onChange={(e) => setEditName(e.target.value)}
                      className="border rounded px-1 py-0.5 text-xs w-24" />
                  ) : (
                    <span className="font-medium">{s.name}</span>
                  )}
                </td>
                <td className="py-2 pr-4">
                  {editingId === s.subplot_id ? (
                    <select value={editType} onChange={(e) => setEditType(e.target.value)}
                      className="border rounded px-1 py-0.5 text-xs">
                      {TYPE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  ) : (
                    <span>{s.type}</span>
                  )}
                </td>
                <td className="py-2 pr-4">
                  {editingId === s.subplot_id ? (
                    <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}
                      className="border rounded px-1 py-0.5 text-xs">
                      {STATUS_OPTIONS.map(st => <option key={st} value={st}>{st}</option>)}
                    </select>
                  ) : (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${statusColor[s.status] || 'bg-gray-100'}`}>
                      {s.status}
                    </span>
                  )}
                </td>
                <td className="py-2">
                  {editingId === s.subplot_id ? (
                    <div className="flex gap-1">
                      <button onClick={() => { handleUpdate(s.subplot_id, { name: editName, type: editType, status: editStatus }); setEditingId(null); }}
                        className="text-xs text-blue-600 hover:text-blue-800">保存</button>
                      <button onClick={() => setEditingId(null)} className="text-xs text-gray-400">取消</button>
                    </div>
                  ) : (
                    <div className="flex gap-1">
                      <button onClick={() => { setEditingId(s.subplot_id); setEditName(s.name); setEditType(s.type); setEditStatus(s.status || 'setup'); }}
                        className="text-xs text-blue-600 hover:text-blue-800">编辑</button>
                      <button onClick={() => handleDelete(s.subplot_id)}
                        className="text-xs text-red-500 hover:text-red-700">删除</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
