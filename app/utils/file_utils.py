"""
File upload utilities: validation, saving, URL generation.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileTooLargeException, InvalidFileTypeException
from app.core.logging import get_logger

log = get_logger(__name__)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
ALLOWED_TYPES = set(settings.allowed_image_types_list)
MAX_SIZE = settings.max_file_size_bytes


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _build_unique_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower() or ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


async def validate_and_save_image(file: UploadFile, sub_dir: str = "predictions") -> tuple[str, str]:
    """
    Validate file type and size, then persist to disk.

    Returns:
        (relative_path, full_path)  e.g.  ("predictions/abc.jpg", "/abs/path/predictions/abc.jpg")
    """
    ensure_upload_dir()

    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise InvalidFileTypeException(
            detail=f"Received: {content_type}. Allowed: {ALLOWED_TYPES}"
        )

    # Read content (needed for size check and saving)
    content = await file.read()

    if len(content) > MAX_SIZE:
        raise FileTooLargeException(
            detail=f"File size {len(content) / 1024 / 1024:.1f} MB exceeds limit {settings.MAX_FILE_SIZE_MB} MB."
        )

    dest_dir = UPLOAD_DIR / sub_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = _build_unique_filename(file.filename or "upload.jpg")
    full_path = dest_dir / filename
    relative_path = f"{sub_dir}/{filename}"

    async with aiofiles.open(full_path, "wb") as f:
        await f.write(content)

    log.info(f"Saved upload: {relative_path} ({len(content)} bytes)")
    return relative_path, str(full_path)


def get_image_url(relative_path: str, base_url: str = "") -> str:
    """Convert a relative file path to a public URL."""
    return f"{base_url}/static/{relative_path}"


def delete_file(relative_path: str) -> None:
    full_path = UPLOAD_DIR / relative_path
    if full_path.exists():
        full_path.unlink()
        log.info(f"Deleted file: {relative_path}")