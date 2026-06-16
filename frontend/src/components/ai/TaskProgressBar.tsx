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
        <span>\u63D0\u4EA4\u4E2D...</span>
      </div>
    );
  }

  if (!task) return null;

  if (task.status === 'success') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700">
        <span className="text-lg">\u2713</span>
        <span>\u5B8C\u6210</span>
      </div>
    );
  }

  if (task.status === 'failed') {
    return (
      <div className="flex items-center gap-2 text-sm text-red-700">
        <span className="text-lg">\u2717</span>
        <span>\u5931\u8D25</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-blue-600">
      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <span>\u5904\u7406\u4E2D...</span>
      <span className="text-xs text-gray-400">({task.task_type})</span>
    </div>
  );
}