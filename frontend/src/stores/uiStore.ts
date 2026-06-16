import { create } from 'zustand';

export type AssetType = 'bible' | 'style' | 'chapter' | 'state' | 'hooks' | 'subplots' | 'strategy' | 'review' | 'multi_reader';

export interface SelectedAsset {
  type: AssetType;
  id?: string;
}

interface UIStore {
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  notification: { message: string; type: 'success' | 'error' | 'info'; detail?: string } | null;
  selectedAsset: SelectedAsset | null;
  toggleLeft: () => void;
  toggleRight: () => void;
  notify: (message: string, type: 'success' | 'error' | 'info', detail?: string) => void;
  clearNotification: () => void;
  selectAsset: (asset: SelectedAsset | null) => void;
}

export interface Notification {
  message: string;
  type: 'success' | 'error' | 'info';
  detail?: string;
}

export const useUIStore = create<UIStore>((set) => ({
  leftPanelOpen: true,
  rightPanelOpen: true,
  notification: null,
  selectedAsset: null,
  toggleLeft: () => set((s) => ({ leftPanelOpen: !s.leftPanelOpen })),
  toggleRight: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  notify: (message, type, detail?) => {
    set({ notification: { message, type, detail } });
    const timeout = type === 'error' ? 8000 : type === 'info' ? 4000 : 3000;
    clearTimeout((window as any).__nwr_notify_timer);
    (window as any).__nwr_notify_timer = setTimeout(() => set({ notification: null }), timeout);
  },
  clearNotification: () => {
    clearTimeout((window as any).__nwr_notify_timer);
    set({ notification: null });
  },
  selectAsset: (asset) => set({ selectedAsset: asset }),
}));