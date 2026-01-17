import type { Job, VideoParams } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function createJob(
  file: File,
  params: VideoParams
): Promise<Job> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('params', JSON.stringify(params));

  const response = await fetch(`${API_BASE}/jobs/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create job');
  }

  return response.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error('Job not found');
  }
  return response.json();
}

export async function listJobs(limit = 20, offset = 0): Promise<{ jobs: Job[]; total: number }> {
  const response = await fetch(`${API_BASE}/jobs/?limit=${limit}&offset=${offset}`);
  return response.json();
}

export async function deleteJob(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
}

export function getVideoDownloadUrl(jobId: string, filename: string): string {
  return `${API_BASE}/videos/${jobId}/${filename}`;
}
