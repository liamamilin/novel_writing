import { useState } from 'react';
import { exportApi, getDownloadUrl } from '../../api/export';

interface ExportModalProps {
  projectId: string;
  onClose: () => void;
}

const FORMATS = [
  { value: 'txt', label: '纯文本 (.txt)' },
  { value: 'md', label: 'Markdown (.md)' },
  { value: 'epub', label: '电子书 (.epub)' },
  { value: 'docx', label: 'Word (.docx)' },
];

export function ExportModal({ projectId, onClose }: ExportModalProps) {
  const [format, setFormat] = useState('txt');
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await exportApi.export(projectId, format);
      setTaskId(res.task_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (taskId) {
      window.open(getDownloadUrl(projectId, taskId), '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold mb-4">导出项目</h3>

        <label className="block text-sm text-gray-600 mb-2">选择格式</label>
        <div className="space-y-2 mb-4">
          {FORMATS.map((f) => (
            <label key={f.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="format"
                value={f.value}
                checked={format === f.value}
                onChange={() => setFormat(f.value)}
                className="accent-blue-500"
              />
              <span className="text-sm">{f.label}</span>
            </label>
          ))}
        </div>

        {error && (
          <div className="text-red-600 text-sm mb-3 bg-red-50 px-3 py-2 rounded">{error}</div>
        )}

        {taskId ? (
          <div className="space-y-2">
            <div className="text-green-600 text-sm mb-2">导出完成</div>
            <button
              onClick={handleDownload}
              className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 text-sm"
            >
              下载文件
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-600 py-2 rounded hover:bg-gray-50 text-sm"
            >
              取消
            </button>
            <button
              onClick={handleExport}
              disabled={loading}
              className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
            >
              {loading ? '导出中...' : '开始导出'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
