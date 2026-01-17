import sys
from pathlib import Path
from datetime import datetime

# Add parent directory for speedreading import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from speedreading import (
    extract_text_from_file,
    generate_speed_reading_video,
    generate_chunked_videos,
    tokenize_text,
    clean_text,
)
from ..config import settings
from ..models import JobStatus


def process_video_job(job_id: str, job_manager):
    """
    Background task to process video generation.

    This runs in a thread pool and updates job status throughout.
    """
    try:
        # Get job details
        job = job_manager.get_job(job_id)
        if not job:
            return

        # Mark as processing
        job_manager.update_job(
            job_id,
            status=JobStatus.PROCESSING.value,
            started_at=datetime.utcnow().isoformat(),
            current_step="Extracting text from document"
        )

        # Get stored job data for upload path
        job_data = job_manager.get_job_data(job_id)
        if not job_data:
            return

        upload_path = job_data["upload_path"]
        params = job.params

        # Extract text
        text = extract_text_from_file(upload_path, preprocess=params.preprocess)
        words = tokenize_text(clean_text(text))
        total_words = len(words)

        job_manager.update_job(
            job_id,
            total_words=total_words,
            current_step=f"Found {total_words} words, starting video generation",
            progress_percent=10
        )

        # Create output directory
        output_dir = settings.OUTPUTS_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build output filename
        original_name = Path(job.filename).stem
        output_path = output_dir / f"{original_name}.mp4"

        # Common parameters
        video_opts = dict(
            start_wpm=params.start_wpm,
            peak_wpm=params.peak_wpm,
            ramp_words=params.ramp_words,
            ramp_style=params.ramp_style.value,
            width=params.width,
            height=params.height,
            font_size=params.font_size,
            bg_color=params.bg_color,
            text_color=params.text_color,
            orp_color=params.orp_color,
            fps=params.fps,
            show_wpm=params.show_wpm,
        )

        # Generate video(s)
        job_manager.update_job(
            job_id,
            current_step="Generating video frames",
            progress_percent=20
        )

        if params.chunk_duration:
            # Generate multiple chunked videos
            output_files = generate_chunked_videos(
                text=text,
                output_path=str(output_path),
                chunk_duration=params.chunk_duration,
                **video_opts
            )
            output_filenames = [Path(f).name for f in output_files]
        else:
            # Generate single video
            generate_speed_reading_video(
                text=text,
                output_path=str(output_path),
                **video_opts
            )
            output_filenames = [output_path.name]

        # Calculate total duration
        total_duration = 0
        try:
            from moviepy import VideoFileClip
            for fname in output_filenames:
                video_path = output_dir / fname
                clip = VideoFileClip(str(video_path))
                total_duration += clip.duration
                clip.close()
        except Exception:
            pass  # Duration calculation is optional

        # Mark as completed
        job_manager.update_job(
            job_id,
            status=JobStatus.COMPLETED.value,
            completed_at=datetime.utcnow().isoformat(),
            progress_percent=100,
            current_step="Complete",
            output_files=output_filenames,
            video_duration_seconds=total_duration if total_duration > 0 else None
        )

    except Exception as e:
        # Mark as failed
        job_manager.update_job(
            job_id,
            status=JobStatus.FAILED.value,
            completed_at=datetime.utcnow().isoformat(),
            error_message=str(e),
            current_step="Failed"
        )
