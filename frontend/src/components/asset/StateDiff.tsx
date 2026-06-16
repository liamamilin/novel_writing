import ReactDiffViewer from 'react-diff-viewer-continued';

interface StateDiffProps {
  oldText: string;
  newText: string;
  oldTitle?: string;
  newTitle?: string;
}

export function StateDiff({ oldText, newText, oldTitle = '更新前', newTitle = '更新后' }: StateDiffProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded">{oldTitle}</span>
        <span>→</span>
        <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded">{newTitle}</span>
      </div>
      <div className="border rounded overflow-hidden">
        <ReactDiffViewer
          oldValue={oldText}
          newValue={newText}
          splitView={true}
          hideLineNumbers={false}
          styles={{
            contentText: { fontSize: '13px' },
          }}
        />
      </div>
    </div>
  );
}