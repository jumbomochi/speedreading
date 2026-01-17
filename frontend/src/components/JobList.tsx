import { useState, useEffect } from 'react';
import type { Job } from '../types';
import { listJobs, deleteJob } from '../api/client';

interface Props {
  onJobSelect: (job: Job) => void;
}

export function JobList({ onJobSelect }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const { jobs } = await listJobs();
      setJobs(jobs);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    if (confirm('Delete this job?')) {
      await deleteJob(jobId);
      fetchJobs();
    }
  };

  if (loading) {
    return <div className="job-list-loading">Loading jobs...</div>;
  }

  if (jobs.length === 0) {
    return <div className="job-list-empty">No jobs yet. Upload a file to get started.</div>;
  }

  return (
    <div className="job-list">
      {jobs.map((job) => (
        <div
          key={job.id}
          className={`job-item status-${job.status}`}
          onClick={() => onJobSelect(job)}
        >
          <div className="job-item-header">
            <span className="job-filename">{job.filename}</span>
            <span className={`job-status ${job.status}`}>{job.status}</span>
          </div>
          <div className="job-item-details">
            <span className="job-step">{job.current_step}</span>
            {job.status === 'processing' && (
              <span className="job-progress">{job.progress_percent}%</span>
            )}
          </div>
          <button
            className="job-delete"
            onClick={(e) => handleDelete(e, job.id)}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}
