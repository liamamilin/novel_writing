import { create } from 'zustand';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getToken } from '../api/client';

interface StreamStore {
  isStreaming: boolean;
  streamedContent: string;
  streamDraft: (projectId: string, chapterNumber: number) => Promise<string>;
  cancelStream: () => void;
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
              if (data.token) {
                full += data.token;
                set({ streamedContent: full });
              }
              if (data.done) {
                set({ isStreaming: false, streamedContent: data.full || full });
              }
            } catch { /* skip */ }
          },
          onclose() {
            set({ isStreaming: false });
          },
          onerror(err) {
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
      abortController?.abort();
      set({ isStreaming: false });
    },
  };
});
