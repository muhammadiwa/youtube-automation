"""Streaming upload handler for efficient video file uploads.

Implements chunked file streaming to avoid memory issues with large files.
The file is streamed directly to disk without loading entirely into memory.
"""

import os
import uuid
import aiofiles
import logging
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass

from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)

# Chunk size for streaming (1MB)
CHUNK_SIZE = 1024 * 1024

# Max file size (10GB)
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024

# Allowed video extensions
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}


@dataclass
class UploadResult:
    """Result of a file upload operation."""
    file_path: str
    file_size: int
    original_filename: str
    content_type: Optional[str]


class UploadError(Exception):
    """Base exception for upload errors."""
    pass


class FileTooLargeError(UploadError):
    """File exceeds maximum allowed size."""
    pass


class InvalidFileTypeError(UploadError):
    """File type is not allowed."""
    pass


async def stream_upload_to_disk(
    file: UploadFile,
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> UploadResult:
    """Stream upload file directly to disk without loading into memory.
    
    Args:
        file: FastAPI UploadFile object
        progress_callback: Optional async callback(bytes_written, total_bytes)
        
    Returns:
        UploadResult with file path and metadata
        
    Raises:
        FileTooLargeError: If file exceeds MAX_FILE_SIZE
        InvalidFileTypeError: If file extension is not allowed
    """
    # Validate file extension
    original_filename = file.filename or "video.mp4"
    file_ext = os.path.splitext(original_filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"File type '{file_ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Create upload directory
    upload_dir = getattr(settings, 'LOCAL_STORAGE_PATH', './storage') + "/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Stream file to disk
    total_bytes = 0
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                    
                total_bytes += len(chunk)
                
                # Check file size limit
                if total_bytes > MAX_FILE_SIZE:
                    # Clean up partial file
                    await out_file.close()
                    os.remove(file_path)
                    raise FileTooLargeError(
                        f"File exceeds maximum size of {MAX_FILE_SIZE / (1024*1024*1024):.1f}GB"
                    )
                
                await out_file.write(chunk)
                
                # Report progress
                if progress_callback:
                    try:
                        await progress_callback(total_bytes, 0)  # Total unknown during stream
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
        
        logger.info(f"File uploaded: {file_path} ({total_bytes} bytes)")
        
        return UploadResult(
            file_path=file_path,
            file_size=total_bytes,
            original_filename=original_filename,
            content_type=file.content_type,
        )
        
    except (FileTooLargeError, InvalidFileTypeError):
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Upload failed: {e}")
        raise UploadError(f"Upload failed: {str(e)}")


async def cleanup_upload(file_path: str) -> bool:
    """Clean up an uploaded file.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if file was deleted, False if it didn't exist
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up upload: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup {file_path}: {e}")
        return False


def get_upload_dir() -> str:
    """Get the upload directory path, creating it if needed."""
    upload_dir = getattr(settings, 'LOCAL_STORAGE_PATH', './storage') + "/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir
