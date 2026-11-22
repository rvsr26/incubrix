export interface Word {
  word_id: string;
  text: string;
  start: number;
  end: number;
  speaker?: string;
  confidence?: number;
}

export interface VideoMetadata {
  video_id: string;
  filename: string;
  duration_s: number;
  fps_num: number;
  fps_den: number;
  fps: number;
  has_audio: boolean;
  width: number;
  height: number;
  source_sha256?: string;
}

export interface Segment {
  segment_id: string;
  source_start: number;
  source_end: number;
  speed: number;
}

export interface Caption {
  caption_id: string;
  text: string;
  start_word_id: string;
  end_word_id: string;
  word_ids: string[];
  style?: {
    font_size?: number;
    color?: string;
    position?: string;
  };
}

export interface HistoryItem {
  label: string;
  timeline: Record<string, any>;
}

export interface Timeline {
  schema_version: string;
  video_id: string;
  source_duration_s: number;
  fps: number;
  has_audio: boolean;
  time_policy: string;
  segments: Segment[];
  captions: Caption[];
  word_effects: Array<{ word_id: string; effect: string }>;
  music?: any;
  history?: HistoryItem[];
  redo?: HistoryItem[];
}

export interface InstructionResponse {
  status: 'applied' | 'needs_clarification' | 'rejected';
  operations: any[];
  summary: {
    message?: string;
    before_duration_s?: number;
    after_duration_s?: number;
    delta_s?: number;
    code?: string;
    details?: any;
  };
  question?: string | null;
  options?: Array<{ id: number | string; label: string }>;
  timeline_hash: string;
  duration_s: number;
  instruction_latency_ms?: number;
}

