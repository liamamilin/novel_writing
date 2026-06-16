import { useUIStore, type AssetType } from '../../stores/uiStore';

const assets: { type: AssetType; icon: string; label: string }[] = [
  { type: 'bible', icon: '\uD83D\uDCD6', label: 'Bible' },
  { type: 'style', icon: '\uD83C\uDFA8', label: '文风资产' },
  { type: 'chapter', icon: '\uD83D\uDCDD', label: '章节' },
  { type: 'state', icon: '\uD83D\uDCCA', label: '状态' },
  { type: 'hooks', icon: '\uD83D\uDD17', label: '伏笔' },
  { type: 'subplots', icon: '\uD83D\uDCC8', label: '子线' },
  { type: 'strategy', icon: '⚙️', label: '策略' },
];

export function AssetTree() {
  const selectedAsset = useUIStore((s) => s.selectedAsset);
  const selectAsset = useUIStore((s) => s.selectAsset);

  return (
    <div className="space-y-1">
      <h3 className="font-semibold text-sm text-gray-500 uppercase mb-1 px-2">资产</h3>
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