import { useState, useEffect } from 'react';
import { useProjectStore } from '../../stores/projectStore';
import { useUIStore } from '../../stores/uiStore';
import { hooksApi } from '../../api/hooks';
import type { Hook } from '../../types';

const urgencyColor: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
};

const statusLabel: Record<string, string> = {
  open: '开放',
  triggered: '已触发',
  resolved: '已解决',
  abandoned: '已放弃',
};

export function HookTable() {
  const currentProject = useProjectStore((s) => s.currentProject);
  const notify = useUIStore((s) => s.notify);
  const [hooks, setHooks] = useState<Hook[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editPriority, setEditPriority] = useState('medium');
  const [showCreate, setShowCreate] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newPriority, setNewPriority] = useState('medium');

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      hooksApi.list(currentProject.project_id)
        .then(setHooks)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [currentProject]);

  const handleCreate = async () => {
    if (!currentProject || !newContent.trim()) return;
    try {
      const newHook = await hooksApi.create(currentProject.project_id, {
        content: newContent,
        status: 'open',
        priority: newPriority,
      });
      setHooks([...hooks, newHook]);
      setShowCreate(false);
      setNewContent('');
      notify('伏笔已创建', 'success');
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleUpdate = async (hookId: string, updates: Record<string, unknown>) => {
    if (!currentProject) return;
    try {
      await hooksApi.update(currentProject.project_id, hookId, updates);
      setHooks(hooks.map(h => h.hook_id === hookId ? { ...h, ...updates } : h));
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  const handleStatusAction = async (hookId: string, action: string) => {
    if (!currentProject) return;
    try {
      if (action === 'trigger') await hooksApi.trigger(currentProject.project_id, hookId);
      else if (action === 'resolve') await hooksApi.resolve(currentProject.project_id, hookId);
      const updated = await hooksApi.list(currentProject.project_id);
      setHooks(updated);
    } catch (e) {
      notify((e as Error).message, 'error');
    }
  };

  if (!currentProject) return <div className="text-sm text-gray-400 py-4">请先选择项目</div>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">伏笔</h3>
        <button onClick={() => setShowCreate(true)} className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
          + 新建
        </button>
      </div>

      {loading && <div className="text-gray-400 text-sm">加载中...</div>}

      {showCreate && (
        <div className="border rounded p-3 space-y-2 bg-gray-50">
          <input
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            className="w-full border rounded px-2 py-1 text-sm"
            placeholder="伏笔内容（如：主角身世之谜）"
            autoFocus
          />
          <div className="flex gap-2 items-center">
            <select value={newPriority} onChange={(e) => setNewPriority(e.target.value)} className="border rounded px-2 py-1 text-xs">
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">关键</option>
            </select>
            <button onClick={handleCreate} className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">创建</button>
            <button onClick={() => setShowCreate(false)} className="text-xs text-gray-500 px-2 py-1">取消</button>
          </div>
        </div>
      )}

      {hooks.length === 0 && !loading && (
        <div className="text-gray-400 text-sm">暂无伏笔</div>
      )}

      <div className="space-y-2">
        {hooks.map((h) => (
          <div key={h.hook_id} className="border rounded p-3 space-y-2">
            {editingId === h.hook_id ? (
              <div className="space-y-2">
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full border rounded px-2 py-1 text-sm"
                  rows={2}
                />
                <div className="flex gap-2 items-center">
                  <select value={editPriority} onChange={(e) => setEditPriority(e.target.value)} className="border rounded px-2 py-1 text-xs">
                    <option value="low">低</option>
                    <option value="medium">中</option>
                    <option value="high">高</option>
                    <option value="critical">关键</option>
                  </select>
                  <button onClick={() => { handleUpdate(h.hook_id, { content: editContent, priority: editPriority }); setEditingId(null); }} className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">保存</button>
                  <button onClick={() => setEditingId(null)} className="text-xs text-gray-500 px-2 py-1">取消</button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm">{h.content}</p>
                  {h.source_chapter && (
                    <p className="text-xs text-gray-400 mt-1">来源: 第 {h.source_chapter} 章</p>
                  )}
                </div>
                <div className="flex gap-2 shrink-0 items-center">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${urgencyColor[h.priority] || 'bg-gray-100'}`}>
                    {h.priority}
                  </span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                    {statusLabel[h.status] || h.status}
                  </span>
                </div>
              </div>
            )}

            <div className="flex gap-1">
              <button onClick={() => { setEditingId(h.hook_id); setEditContent(h.content); setEditPriority(h.priority); }} className="text-xs text-blue-600 hover:text-blue-800">编辑</button>
              {h.status === 'open' && <button onClick={() => handleStatusAction(h.hook_id, 'trigger')} className="text-xs text-orange-600 hover:text-orange-800">已触发</button>}
              {(h.status === 'open' || h.status === 'triggered') && <button onClick={() => handleStatusAction(h.hook_id, 'resolve')} className="text-xs text-green-600 hover:text-green-800">已解决</button>}
              {h.status !== 'abandoned' && <button onClick={() => handleUpdate(h.hook_id, { status: 'abandoned' })} className="text-xs text-gray-400 hover:text-gray-600">放弃</button>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
