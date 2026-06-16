import { useUIStore, type AssetType } from '../../stores/uiStore';

const assets: { type: AssetType; icon: string; label: string }[] = [
  { type: 'bible', icon: '\uD83D\uDCD6', label: 'Bible' },
  { type: 'style', icon: '\uD83C\uDFA8', label: '\u6587\u98CE\u8D44\u4EA7' },
  { type: 'chapter', icon: '\uD83D\uDCDD', label: '\u7AE0\u8282' },
  { type: 'state', icon: '\uD83D\uDCCA', label: '\u72B6\u6001' },
  { type: 'hooks', icon: '\uD83D\uDD17', label: '\u4F0F\u7B14' },
  { type: 'subplots', icon: '\uD83D\uDCC8', label: '\u5B50\u7EBF' },
  { type: 'strategy', icon: '\u2699\uFE0F', label: '\u7B56\u7565' },
];

export function AssetTree() {
  const selectedAsset = useUIStore((s) => s.selectedAsset);
  const selectAsset = useUIStore((s) => s.selectAsset);

  return (
    <div className="space-y-1">
      <h3 className="font-semibold text-sm text-gray-500 uppercase mb-1 px-2">\u8D44\u4EA7</h3>
      {assets.map((a) => (
        <button
          key={a.type}
          onClick={() => selectAsset({ type: a.type })}
          className={`w-full text-left px-3 py-1.5 text-sm rounded hover:bg-gray-100 transition-colors ${
            selectedAsset?.type === a.type ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
          }`}
        >
          <span className="mr-2">{a.icon}</span>
          {a.label}
        </button>
      ))}
    </div>
  );
}