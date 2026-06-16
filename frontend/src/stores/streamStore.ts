import { create } from 'zustand';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getToken } from '../api/client';
import { useUIStore } from './uiStore';
import { useChapterStore } from './chapterStore';

interface StreamStore {
  isStreaming: boolean;
  streamedContent: string;
  streamDraft: (projectId: string, chapterNumber: number) => Promise<string>;
  cancelStream: () => void;
  clearStreamedContent: () => void;
}

export const useStreamStore = create<StreamStore>((set) => {
  let abortController: AbortController | null = null;

  return {
    isStreaming: false,
    streamedContent: '',

    streamDraft: async (projectId, chapterNumber) => {
      set({ isStreaming: true, streamedContent: '' });
      const ctrl = new AbortController();
      abortController = ctrl;

      let full = '';
      try {
        await fetchEventSource(`/api/projects/${projectId}/chapters/${chapterNumber}/draft/stream`, {
          method: 'POST',
          body: JSON.stringify({}),
          headers: {
            'Content-Type': 'application/json',
            ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
          },
          signal: ctrl.signal,
          onmessage(ev) {
            try {
              const data = JSON.parse(ev.data);
              if (data.error) {
                try { useUIStore.getState().notify(data.error, 'error'); } catch {}
                set({ isStreaming: false });
                return;
              }
              if (data.token) {
                full += data.token;
                set({ streamedContent: full });
              }
              if (data.done) {
                set({ isStreaming: false, streamedContent: data.full || full });
                // B3: auto-refresh chapter status after stream completes
                useChapterStore.getState().loadChapters(projectId);
              }
            } catch { /* skip */ }
          },
          onclose() {
            set({ isStreaming: false });
          },
          onerror(err) {
            try { useUIStore.getState().notify(String(err), 'error'); } catch {}
            set({ isStreaming: false });
            throw err;
          },
        });
      } catch {
        set({ isStreaming: false });
      }
      return full;
    },

    cancelStream: () => {
      if (!abortController) return;
      abortController.abort();
      const partial = useStreamStore.getState().streamedContent;
      set({ isStreaming: false });
      if (partial.length > 0) {
        try { useUIStore.getState().notify(`已停止，生成了约 ${partial.length} 字，未保存`, 'info'); } catch {}
      }
    },

    clearStreamedContent: () => {
      set({ streamedContent: '' });
    },
  };
});
