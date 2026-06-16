import { useCallback, useRef, useState } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { getToken } from '../api/client';

export function useStreamDraft() {
  const [streaming, setStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  const streamDraft = useCallback(async (projectId: string, chapterNumber: number) => {
    setStreaming(true);
    setStreamedText('');
    const ctrl = new AbortController();
    abortRef.current = ctrl;

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
              setStreamedText(full);
            }
            if (data.done) {
              setStreaming(false);
              setStreamedText(data.full || full);
            }
          } catch { /* skip */ }
        },
        onclose() {
          setStreaming(false);
        },
        onerror(err) {
          setStreaming(false);
          throw err;
        },
      });
    } catch {
      setStreaming(false);
    }
    return full;
  }, []);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, []);

  return { streamDraft, streaming, streamedText, cancelStream };
}
