from fastapi import UploadFile, HTTPException
from pathlib import Path
import aiofiles

from ..config import settings

ALLOWED_EXTENSIONS = {'.pdf', '.epub', '.txt'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/epub+zip',
    'text/plain',
}


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def save_upload(file: UploadFile, job_id: str) -> Path:
    """Save uploaded file to storage."""
    filename = file.filename or f"upload{Path(file.filename or '.txt').suffix}"
    safe_filename = f"{job_id}_{filename}"

    upload_path = settings.UPLOADS_DIR / safe_filename

    async with aiofiles.open(upload_path, 'wb') as out_file:
        chunk_size = 1024 * 1024  # 1MB chunks
        while chunk := await file.read(chunk_size):
            await out_file.write(chunk)

    return upload_path
