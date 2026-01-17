from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import settings
from .routes import jobs, videos
from .services.job_manager import JobManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    settings.JOBS_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize job manager
    app.state.job_manager = JobManager()

    yield

    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="Speed Reading Video Generator API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])


@app.get("/")
async def root():
    return {"message": "Speed Reading Video Generator API", "docs": "/docs"}
