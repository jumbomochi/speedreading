import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from filelock import FileLock

from ..config import settings
from ..models import JobResponse, JobStatus, VideoParams


class JobManager:
    """
    File-based job storage and management.

    Each job is stored as a JSON file in storage/jobs/{job_id}.json
    Uses file locking for concurrent access safety.
    """

    def create_job(self) -> str:
        """Generate a new unique job ID."""
        return str(uuid.uuid4())[:8]

    def _job_path(self, job_id: str) -> Path:
        return settings.JOBS_DIR / f"{job_id}.json"

    def _lock_path(self, job_id: str) -> Path:
        return settings.JOBS_DIR / f"{job_id}.lock"

    def initialize_job(
        self,
        job_id: str,
        filename: str,
        upload_path: str,
        params: VideoParams
    ) -> JobResponse:
        """Create initial job record."""
        job_data = {
            "id": job_id,
            "status": JobStatus.PENDING.value,
            "filename": filename,
            "upload_path": upload_path,
            "params": params.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress_percent": 0,
            "current_step": "Queued",
            "total_words": None,
            "processed_words": None,
            "output_files": [],
            "error_message": None,
            "video_duration_seconds": None,
        }

        with FileLock(self._lock_path(job_id)):
            with open(self._job_path(job_id), 'w') as f:
                json.dump(job_data, f, indent=2)

        return self._to_response(job_data)

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Retrieve job by ID."""
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return None

        with FileLock(self._lock_path(job_id)):
            with open(job_path, 'r') as f:
                job_data = json.load(f)

        return self._to_response(job_data)

    def get_job_data(self, job_id: str) -> Optional[dict]:
        """Retrieve raw job data by ID."""
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return None

        with FileLock(self._lock_path(job_id)):
            with open(job_path, 'r') as f:
                return json.load(f)

    def update_job(self, job_id: str, **updates) -> Optional[JobResponse]:
        """Update job fields."""
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return None

        with FileLock(self._lock_path(job_id)):
            with open(job_path, 'r') as f:
                job_data = json.load(f)

            job_data.update(updates)

            with open(job_path, 'w') as f:
                json.dump(job_data, f, indent=2)

        return self._to_response(job_data)

    def list_jobs(self, limit: int = 20, offset: int = 0) -> tuple[list[JobResponse], int]:
        """List all jobs, sorted by creation time (newest first)."""
        job_files = list(settings.JOBS_DIR.glob("*.json"))

        # Sort by modification time (newest first)
        job_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        total = len(job_files)
        jobs = []

        for job_file in job_files[offset:offset + limit]:
            job_id = job_file.stem
            job = self.get_job(job_id)
            if job:
                jobs.append(job)

        return jobs, total

    def delete_job(self, job_id: str) -> bool:
        """Delete job and associated files."""
        job_path = self._job_path(job_id)
        if not job_path.exists():
            return False

        job_data = self.get_job_data(job_id)
        if not job_data:
            return False

        # Delete upload file
        upload_path = Path(job_data.get("upload_path", ""))
        if upload_path.exists():
            upload_path.unlink()

        # Delete output directory
        output_dir = settings.OUTPUTS_DIR / job_id
        if output_dir.exists():
            shutil.rmtree(output_dir)

        # Delete job file and lock
        job_path.unlink()
        lock_path = self._lock_path(job_id)
        if lock_path.exists():
            lock_path.unlink()

        return True

    def _to_response(self, job_data: dict) -> JobResponse:
        """Convert stored dict to JobResponse."""
        params = VideoParams(**job_data.get("params", {}))

        return JobResponse(
            id=job_data["id"],
            status=JobStatus(job_data["status"]),
            filename=job_data["filename"],
            params=params,
            created_at=datetime.fromisoformat(job_data["created_at"]),
            started_at=datetime.fromisoformat(job_data["started_at"]) if job_data.get("started_at") else None,
            completed_at=datetime.fromisoformat(job_data["completed_at"]) if job_data.get("completed_at") else None,
            progress_percent=job_data.get("progress_percent", 0),
            current_step=job_data.get("current_step", ""),
            total_words=job_data.get("total_words"),
            processed_words=job_data.get("processed_words"),
            output_files=job_data.get("output_files", []),
            error_message=job_data.get("error_message"),
            video_duration_seconds=job_data.get("video_duration_seconds"),
        )
