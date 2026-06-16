import { create } from 'zustand';

export type AssetType = 'bible' | 'style' | 'chapter' | 'state' | 'hooks' | 'subplots' | 'strategy' | 'review' | 'multi_reader';

export interface SelectedAsset {
  type: AssetType;
  id?: string;
}

interface UIStore {
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  notification: { message: string; type: 'success' | 'error' | 'info' } | null;
  selectedAsset: SelectedAsset | null;
  toggleLeft: () => void;
  toggleRight: () => void;
  notify: (message: string, type: 'success' | 'error' | 'info') => void;
  clearNotification: () => void;
  selectAsset: (asset: SelectedAsset | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  leftPanelOpen: true,
  rightPanelOpen: true,
  notification: null,
  selectedAsset: null,
  toggleLeft: () => set((s) => ({ leftPanelOpen: !s.leftPanelOpen })),
  toggleRight: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  notify: (message, type) => set({ notification: { message, type } }),
  clearNotification: () => set({ notification: null }),
  selectAsset: (asset) => set({ selectedAsset: asset }),
}));