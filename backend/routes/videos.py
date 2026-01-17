from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from ..config import settings

router = APIRouter()


@router.get("/{job_id}/{filename}")
async def download_video(request: Request, job_id: str, filename: str):
    """Download a generated video file."""
    job_manager = request.app.state.job_manager
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(404, "Job not found")

    if filename not in job.output_files:
        raise HTTPException(404, "Video file not found")

    video_path = settings.OUTPUTS_DIR / job_id / filename

    if not video_path.exists():
        raise HTTPException(404, "Video file missing from storage")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=filename
    )


@router.get("/{job_id}")
async def get_all_videos(request: Request, job_id: str):
    """Get list of all video files for a job."""
    job_manager = request.app.state.job_manager
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": job_id,
        "files": job.output_files,
        "download_urls": [
            f"/api/videos/{job_id}/{f}" for f in job.output_files
        ]
    }
