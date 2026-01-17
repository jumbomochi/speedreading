from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = STORAGE_DIR / "uploads"
    JOBS_DIR: Path = STORAGE_DIR / "jobs"
    OUTPUTS_DIR: Path = STORAGE_DIR / "outputs"

    # Limits
    MAX_UPLOAD_SIZE_MB: int = 100
    MAX_CONCURRENT_JOBS: int = 2
    JOB_RETENTION_HOURS: int = 24

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
