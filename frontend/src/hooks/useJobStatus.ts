import { useState, useEffect, useCallback } from 'react';
import type { Job } from '../types';
import { getJob } from '../api/client';

export function useJobStatus(jobId: string | null, pollInterval = 2000) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const jobData = await getJob(jobId);
      setJob(jobData);
      setError(null);

      if (jobData.status === 'completed' || jobData.status === 'failed') {
        setIsPolling(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job status');
    }
  }, [jobId]);

  useEffect(() => {
    if (jobId) {
      setIsPolling(true);
      fetchStatus();
    }
  }, [jobId, fetchStatus]);

  useEffect(() => {
    if (!isPolling || !jobId) return;

    const interval = setInterval(fetchStatus, pollInterval);
    return () => clearInterval(interval);
  }, [isPolling, jobId, pollInterval, fetchStatus]);

  return { job, error, isPolling, refetch: fetchStatus };
}
