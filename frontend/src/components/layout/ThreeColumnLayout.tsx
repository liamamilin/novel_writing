import { useUIStore } from '../../stores/uiStore';

interface Props {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
}

export function ThreeColumnLayout({ left, center, right }: Props) {
  const { leftPanelOpen, rightPanelOpen, toggleLeft, toggleRight } = useUIStore();

  return (
    <div className="flex h-screen bg-gray-50">
      {leftPanelOpen && (
        <aside className="w-72 border-r bg-white overflow-y-auto flex-shrink-0">
          <div className="p-2">{left}</div>
        </aside>
      )}
      <button onClick={toggleLeft} className="absolute left-0 top-1/2 z-10 bg-white border p-1 text-xs">
        {leftPanelOpen ? '◀' : '▶'}
      </button>

      <main className="flex-1 overflow-y-auto p-4">{center}</main>

      {rightPanelOpen && (
        <aside className="w-80 border-l bg-white overflow-y-auto flex-shrink-0">
          <div className="p-2">{right}</div>
        </aside>
      )}
      <button onClick={toggleRight} className="absolute right-0 top-1/2 z-10 bg-white border p-1 text-xs">
        {rightPanelOpen ? '▶' : '◀'}
      </button>
    </div>
  );
}
