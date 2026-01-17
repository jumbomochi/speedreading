export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type RampStyle = 'smooth' | 'linear' | 'stepped';

export interface VideoParams {
  start_wpm: number;
  peak_wpm: number;
  ramp_words: number | null;
  ramp_style: RampStyle;
  chunk_duration: number | null;
  width: number;
  height: number;
  font_size: number;
  fps: number;
  bg_color: string;
  text_color: string;
  orp_color: string;
  show_wpm: boolean;
  preprocess: boolean;
}

export interface Job {
  id: string;
  status: JobStatus;
  filename: string;
  params: VideoParams;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  progress_percent: number;
  current_step: string;
  total_words: number | null;
  processed_words: number | null;
  output_files: string[];
  error_message: string | null;
  video_duration_seconds: number | null;
}

export const DEFAULT_PARAMS: VideoParams = {
  start_wpm: 200,
  peak_wpm: 600,
  ramp_words: null,
  ramp_style: 'smooth',
  chunk_duration: null,
  width: 1920,
  height: 1080,
  font_size: 120,
  fps: 30,
  bg_color: '#1a1a2e',
  text_color: '#ffffff',
  orp_color: '#ff0000',
  show_wpm: true,
  preprocess: true,
};
