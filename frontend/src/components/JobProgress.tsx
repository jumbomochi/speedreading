import { useJobStatus } from '../hooks/useJobStatus';
import { getVideoDownloadUrl } from '../api/client';

interface Props {
  jobId: string;
}

export function JobProgress({ jobId }: Props) {
  const { job, error, isPolling } = useJobStatus(jobId);

  if (error) {
    return <div className="job-error">Error: {error}</div>;
  }

  if (!job) {
    return <div className="job-loading">Loading...</div>;
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`job-progress status-${job.status}`}>
      <div className="job-header">
        <h3>{job.filename}</h3>
        <span className={`job-status ${job.status}`}>{job.status}</span>
      </div>

      {(job.status === 'pending' || job.status === 'processing') && (
        <div className="progress-container">
          <div
            className="progress-bar"
            style={{ width: `${job.progress_percent}%` }}
          />
          <span className="progress-text">{job.progress_percent}%</span>
        </div>
      )}

      <p className="current-step">{job.current_step}</p>

      {job.total_words && (
        <p className="word-count">
          {job.total_words.toLocaleString()} words
        </p>
      )}

      {job.status === 'failed' && job.error_message && (
        <div className="error-details">
          <strong>Error:</strong> {job.error_message}
        </div>
      )}

      {job.status === 'completed' && (
        <div className="download-section">
          <h4>Download Videos</h4>
          {job.video_duration_seconds && (
            <p>Total duration: {formatDuration(job.video_duration_seconds)}</p>
          )}
          <ul className="download-list">
            {job.output_files.map((filename) => (
              <li key={filename}>
                <a
                  href={getVideoDownloadUrl(job.id, filename)}
                  download={filename}
                  className="download-link"
                >
                  {filename}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {isPolling && <span className="polling-indicator">Updating...</span>}
    </div>
  );
}
