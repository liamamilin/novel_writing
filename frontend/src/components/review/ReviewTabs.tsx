import { useState } from 'react';

const TABS = [
  { key: 'continuity', label: '\u8FDE\u8D2F\u6027' },
  { key: 'quality', label: '\u8D28\u91CF' },
  { key: 'cross_chapter', label: '\u8DE8\u7AE0' },
  { key: 'reader_sim', label: '\u8BFB\u8005\u6A21\u62DF' },
] as const;

export interface FixInstruction {
  severity: string;
  description: string;
  location?: string;
}

export interface ReviewData {
  summary: string;
  issues: string[];
  fix_instructions: FixInstruction[];
}

interface ReviewTabsProps {
  reviews: Record<string, ReviewData>;
  onApplyFix?: (instruction: FixInstruction) => void;
}

const severityOrder: Record<string, number> = { critical: 0, major: 1, minor: 2 };
const severityColor: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  major: 'bg-orange-100 text-orange-700',
  minor: 'bg-yellow-100 text-yellow-700',
};

export function ReviewTabs({ reviews, onApplyFix }: ReviewTabsProps) {
  const [activeTab, setActiveTab] = useState<string>('continuity');
  const data = reviews[activeTab];

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-500 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {!data ? (
        <div className="text-gray-400 text-sm py-8 text-center">\u6682\u65E0\u5BA1\u67E5\u6570\u636E</div>
      ) : (
        <>
          {data.summary && (
            <div className="bg-gray-50 p-3 rounded text-sm">{data.summary}</div>
          )}

          {data.issues.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm mb-2">\u53D1\u73B0\u95EE\u9898</h4>
              <ul className="space-y-1">
                {data.issues.map((issue, i) => (
                  <li key={i} className="text-sm text-gray-700 pl-3 border-l-2 border-gray-300">
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.fix_instructions.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm mb-2">\u4FEE\u590D\u6307\u4EE4</h4>
              <div className="space-y-2">
                {[...data.fix_instructions]
                  .sort((a, b) => (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9))
                  .map((fix, i) => (
                    <div key={i} className="border rounded p-3 flex items-start justify-between">
                      <div>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${severityColor[fix.severity] || 'bg-gray-100 text-gray-600'}`}>
                          {fix.severity}
                        </span>
                        {fix.location && (
                          <span className="text-xs text-gray-400 ml-2">{fix.location}</span>
                        )}
                        <p className="text-sm mt-1">{fix.description}</p>
                      </div>
                      {onApplyFix && (
                        <button
                          onClick={() => onApplyFix(fix)}
                          className="text-xs text-blue-600 hover:text-blue-800 shrink-0 ml-2"
                        >
                          \u5E94\u7528\u4FEE\u590D
                        </button>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}