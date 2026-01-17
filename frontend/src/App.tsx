import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ParameterControls } from './components/ParameterControls';
import { JobProgress } from './components/JobProgress';
import { JobList } from './components/JobList';
import type { VideoParams, Job } from './types';
import { DEFAULT_PARAMS } from './types';
import { createJob } from './api/client';
import './App.css';

function App() {
  const [params, setParams] = useState<VideoParams>(DEFAULT_PARAMS);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const job = await createJob(file, params);
      setCurrentJob(job);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJobSelect = (job: Job) => {
    setCurrentJob(job);
  };

  return (
    <div className="app-container">
      <header>
        <h1>Speed Reading Video Generator</h1>
        <p>Upload a document and generate an RSVP speed reading video</p>
      </header>

      <main>
        <div className="main-content">
          <section className="upload-section">
            <h2>Upload Document</h2>
            <FileUpload
              onFileSelect={handleFileUpload}
              isUploading={isSubmitting}
              acceptedTypes=".pdf,.epub,.txt"
            />
            {error && <div className="error-message">{error}</div>}
          </section>

          <section className="controls-section">
            <ParameterControls params={params} onChange={setParams} />
          </section>
        </div>

        {currentJob && (
          <section className="progress-section">
            <h2>Current Job</h2>
            <JobProgress jobId={currentJob.id} />
          </section>
        )}

        <section className="history-section">
          <h2>Recent Jobs</h2>
          <JobList onJobSelect={handleJobSelect} />
        </section>
      </main>
    </div>
  );
}

export default App;
