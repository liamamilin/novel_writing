import { create } from 'zustand';
import type { Chapter } from '../types';
import { chaptersApi } from '../api/chapters';

interface ChapterStore {
  chapters: Chapter[];
  currentChapter: Chapter | null;
  loading: boolean;
  error: string | null;
  setCurrentChapter: (ch: Chapter | null) => void;
  loadChapters: (projectId: string) => Promise<void>;
}

export const useChapterStore = create<ChapterStore>((set) => ({
  chapters: [],
  currentChapter: null,
  loading: false,
  error: null,
  setCurrentChapter: (ch) => set({ currentChapter: ch }),
  loadChapters: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const chapters = await chaptersApi.list(projectId);
      set({ chapters, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));