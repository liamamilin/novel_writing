import type { TaskInfo } from '../../hooks/useTaskPolling';

interface TaskProgressBarProps {
  task: TaskInfo | null | undefined;
  isLoading: boolean;
}

export function TaskProgressBar({ task, isLoading }: TaskProgressBarProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span>提交中...</span>
      </div>
    );
  }

  if (!task) return null;

  if (task.status === 'success') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700">
        <span className="text-lg">✓</span>
        <span>完成</span>
      </div>
    );
  }

  if (task.status === 'failed') {
    return (
      <div className="flex items-center gap-2 text-sm text-red-700">
        <span className="text-lg">✗</span>
        <span>失败</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-blue-600">
      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <span>处理中...</span>
      <span className="text-xs text-gray-400">({task.task_type})</span>
    </div>
  );
}