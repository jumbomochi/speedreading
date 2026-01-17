from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RampStyle(str, Enum):
    SMOOTH = "smooth"
    LINEAR = "linear"
    STEPPED = "stepped"


class VideoParams(BaseModel):
    """Parameters matching CLI options from speedreading.py"""
    start_wpm: int = Field(default=200, ge=50, le=1000)
    peak_wpm: int = Field(default=600, ge=100, le=2000)
    ramp_words: Optional[int] = Field(default=None, ge=10, le=500)
    ramp_style: RampStyle = RampStyle.SMOOTH
    chunk_duration: Optional[float] = Field(default=None, ge=5, le=300)

    # Video dimensions
    width: int = Field(default=1920, ge=640, le=3840)
    height: int = Field(default=1080, ge=480, le=2160)
    font_size: int = Field(default=120, ge=24, le=300)
    fps: int = Field(default=30, ge=15, le=60)

    # Colors (hex format)
    bg_color: str = Field(default="#1a1a2e", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    orp_color: str = Field(default="#ff0000", pattern=r"^#[0-9a-fA-F]{6}$")

    show_wpm: bool = True
    preprocess: bool = True


class JobResponse(BaseModel):
    """Job status response"""
    id: str
    status: JobStatus
    filename: str
    params: VideoParams
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    progress_percent: int = 0
    current_step: str = ""
    total_words: Optional[int] = None
    processed_words: Optional[int] = None

    # Results
    output_files: list[str] = []
    error_message: Optional[str] = None
    video_duration_seconds: Optional[float] = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
