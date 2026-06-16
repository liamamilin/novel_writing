export interface Project {
  project_id: string;
  project_name: string;
  genre: string;
  status: string;
  default_style_id?: string;
  current_chapter_id?: string;
  bible_version?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StyleAsset {
  style_id: string;
  style_name: string;
  narration?: string;
  sentence_rhythm?: string;
  dialogue_style?: string;
  avoid?: string[];
}

export interface Chapter {
  chapter_id: string;
  chapter_number: number;
  title?: string;
  status: 'planned' | 'drafted' | 'reviewed' | 'approved' | 'locked';
  rhythm_type?: string;
  summary?: string;
}

export interface Hook {
  hook_id: string;
  content: string;
  source_chapter?: string;
  status: string;
  priority: string;
  type?: string;
}

export interface Subplot {
  subplot_id: string;
  name: string;
  type: string;
  status: string;
  last_advanced?: string;
}

export interface Task {
  task_id: string;
  project_id: string;
  task_type: string;
  status: string;
}
