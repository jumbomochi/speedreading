from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
import json

from ..models import JobResponse, JobListResponse, VideoParams
from ..services.file_handler import save_upload, validate_file
from ..workers.background import process_video_job

router = APIRouter()


@router.post("/", response_model=JobResponse)
async def create_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    params: str = Form(default="{}")
):
    """
    Create a new video generation job.

    - Accepts PDF, EPUB, or TXT file
    - Validates file type and size
    - Stores file and creates job record
    - Queues background processing
    """
    job_manager = request.app.state.job_manager

    # Validate file
    validate_file(file)

    # Parse parameters
    try:
        params_dict = json.loads(params)
        video_params = VideoParams(**params_dict)
    except Exception as e:
        raise HTTPException(400, f"Invalid parameters: {e}")

    # Save upload and create job
    job_id = job_manager.create_job()
    upload_path = await save_upload(file, job_id)

    # Initialize job record
    job = job_manager.initialize_job(
        job_id=job_id,
        filename=file.filename or "upload",
        upload_path=str(upload_path),
        params=video_params
    )

    # Queue background processing
    background_tasks.add_task(
        process_video_job,
        job_id=job_id,
        job_manager=job_manager
    )

    return job


@router.get("/", response_model=JobListResponse)
async def list_jobs(request: Request, limit: int = 20, offset: int = 0):
    """List all jobs with pagination."""
    job_manager = request.app.state.job_manager
    jobs, total = job_manager.list_jobs(limit=limit, offset=offset)
    return JobListResponse(jobs=jobs, total=total)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(request: Request, job_id: str):
    """Get status of a specific job."""
    job_manager = request.app.state.job_manager
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/{job_id}")
async def delete_job(request: Request, job_id: str):
    """Cancel and delete a job."""
    job_manager = request.app.state.job_manager
    success = job_manager.delete_job(job_id)
    if not success:
        raise HTTPException(404, "Job not found")
    return {"status": "deleted"}
