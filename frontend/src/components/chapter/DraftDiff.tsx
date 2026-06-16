import { useState } from 'react';
import ReactDiffViewer from 'react-diff-viewer-continued';

interface DraftDiffProps {
  leftContent: string;
  rightContent: string;
  leftTitle?: string;
  rightTitle?: string;
}

export function DraftDiff({ leftContent, rightContent, leftTitle, rightTitle }: DraftDiffProps) {
  const [splitView, setSplitView] = useState(true);

  if (!leftContent && !rightContent) {
    return <div className="text-sm text-gray-400">选择两个版本以查看差异</div>;
  }

  return (
    <div className="border border-gray-200 rounded overflow-hidden">
      <div className="flex items-center justify-between bg-gray-50 px-3 py-1.5 border-b border-gray-200">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>{leftTitle || '旧版'}</span>
          <span className="text-gray-300">vs</span>
          <span>{rightTitle || '新版'}</span>
        </div>
        <button
          onClick={() => setSplitView(!splitView)}
          className="text-xs text-blue-600 hover:text-blue-800"
        >
          {splitView ? '统一视图' : '分栏视图'}
        </button>
      </div>
      <div className="overflow-auto max-h-[400px] text-sm">
        <ReactDiffViewer
          oldValue={leftContent}
          newValue={rightContent}
          splitView={splitView}
          showDiffOnly={false}
          hideLineNumbers={false}
        />
      </div>
    </div>
  );
}
