"""Streaming upload handler for efficient video file uploads.

Implements chunked file streaming to avoid memory issues with large files.
The file is streamed directly to disk without loading entirely into memory.

Hybrid Storage Approach:
- Files are first streamed to local temp storage (for FFmpeg processing)
- After processing, files are uploaded to cloud storage (R2/S3) if configured
- Local temp files are cleaned up after successful cloud upload
"""

import asyncio
import json
import os
import subprocess
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

# Allowed image extensions for thumbnails
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def get_temp_dir() -> str:
    """Get the temp directory path for local processing, creating it if needed.
    
    This is always local filesystem, used for:
    - Video uploads before processing
    - FFmpeg temp files
    - Files that need local access before cloud upload
    """
    temp_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def get_upload_dir() -> str:
    """Get the upload directory path, creating it if needed.
    
    DEPRECATED: Use get_temp_dir() for temp files, then upload to cloud storage.
    Kept for backward compatibility.
    """
    upload_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@dataclass
class UploadResult:
    """Result of a file upload operation."""
    file_path: str  # Local temp path (for processing)
    file_size: int
    original_filename: str
    content_type: Optional[str]
    storage_key: Optional[str] = None  # Cloud storage key (after upload to R2/S3)
    storage_url: Optional[str] = None  # Cloud storage URL


class UploadError(Exception):
    """Base exception for upload errors."""
    pass


class FileTooLargeError(UploadError):
    """File exceeds maximum allowed size."""
    pass


class InvalidFileTypeError(UploadError):
    """File type is not allowed."""
    pass


async def stream_upload_to_temp(
    file: UploadFile,
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> UploadResult:
    """Stream upload file to local temp storage for processing.
    
    This saves the file locally first so FFmpeg can process it.
    After processing, use upload_to_cloud_storage() to move to R2/S3.
    
    Args:
        file: FastAPI UploadFile object
        progress_callback: Optional async callback(bytes_written, total_bytes)
        
    Returns:
        UploadResult with local temp file path and metadata
        
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
    
    # Use temp directory for local processing
    temp_dir = get_temp_dir()
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(temp_dir, unique_filename)
    
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
                        await progress_callback(total_bytes, 0)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
        
        logger.info(f"File uploaded to temp: {file_path} ({total_bytes} bytes)")
        
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


# Alias for backward compatibility
async def stream_upload_to_disk(
    file: UploadFile,
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> UploadResult:
    """Alias for stream_upload_to_temp() for backward compatibility."""
    return await stream_upload_to_temp(file, progress_callback)


async def upload_to_cloud_storage(
    local_path: str,
    storage_key: str,
    content_type: str = "video/mp4",
    cleanup_local: bool = True,
) -> tuple[str, str]:
    """Upload a local file to cloud storage (R2/S3/MinIO).
    
    Args:
        local_path: Path to local file
        storage_key: Key/path in cloud storage (e.g., "videos/user_id/video_id.mp4")
        content_type: MIME type of the file
        cleanup_local: Whether to delete local file after successful upload
        
    Returns:
        Tuple of (storage_key, storage_url)
        
    Raises:
        UploadError: If upload fails
    """
    from app.core.storage import get_storage
    
    storage = get_storage()
    
    # Check if using cloud storage
    if settings.STORAGE_BACKEND == "local":
        # For local backend, just move file to final location
        final_path = os.path.join(settings.LOCAL_STORAGE_PATH, storage_key)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        
        if cleanup_local and local_path != final_path:
            import shutil
            shutil.move(local_path, final_path)
        elif local_path != final_path:
            import shutil
            shutil.copy2(local_path, final_path)
        
        url = storage.get_url(storage_key)
        logger.info(f"File stored locally: {storage_key}")
        return storage_key, url
    
    # Upload to cloud storage (R2/S3/MinIO)
    try:
        result = storage.upload(local_path, storage_key, content_type)
        
        if not result.success:
            raise UploadError(f"Cloud upload failed: {result.error_message}")
        
        # Cleanup local temp file
        if cleanup_local and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Cleaned up temp file: {local_path}")
        
        logger.info(f"File uploaded to cloud: {storage_key}")
        return result.key, result.url
        
    except Exception as e:
        logger.error(f"Cloud upload failed: {e}")
        raise UploadError(f"Cloud upload failed: {str(e)}")


async def upload_thumbnail_to_storage(
    content: bytes,
    video_id: str,
    file_ext: str = ".jpg",
    content_type: str = "image/jpeg",
) -> tuple[str, str]:
    """Upload thumbnail directly to storage (cloud or local).
    
    Args:
        content: Thumbnail image bytes
        video_id: Video ID for generating storage key
        file_ext: File extension (default: .jpg)
        content_type: MIME type (default: image/jpeg)
        
    Returns:
        Tuple of (storage_key, storage_url)
    """
    from app.core.storage import storage_service
    
    storage_key = f"thumbnails/{video_id}{file_ext}"
    
    result = await storage_service.upload_file(
        key=storage_key,
        content=content,
        content_type=content_type,
    )
    
    if not result.success:
        raise UploadError(f"Thumbnail upload failed: {result.error_message}")
    
    url = await storage_service.get_url(storage_key)
    logger.info(f"Thumbnail uploaded: {storage_key}")
    
    return storage_key, url


async def cleanup_upload(file_path: str) -> bool:
    """Clean up an uploaded file (local temp or storage).
    
    Args:
        file_path: Path to the file to delete (local path or storage key)
        
    Returns:
        True if file was deleted, False if it didn't exist
    """
    try:
        # Check if it's a local file path
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up local file: {file_path}")
            return True
        
        # Try to delete from cloud storage if it looks like a storage key
        if not file_path.startswith("/") and not file_path.startswith("."):
            try:
                from app.core.storage import storage_service
                result = await storage_service.delete_file(file_path)
                if result:
                    logger.info(f"Cleaned up storage file: {file_path}")
                return result
            except Exception as e:
                logger.warning(f"Failed to cleanup from storage {file_path}: {e}")
        
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup {file_path}: {e}")
        return False


def cleanup_temp_file(file_path: str) -> bool:
    """Synchronously clean up a local temp file.
    
    Args:
        file_path: Path to the local file to delete
        
    Returns:
        True if file was deleted, False if it didn't exist
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup temp file {file_path}: {e}")
        return False


async def get_video_duration(file_path: str) -> Optional[int]:
    """Extract video duration using ffprobe.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Optional[int]: Duration in seconds, or None if extraction fails
    """
    try:
        # Use ffprobe to get video duration
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        # Run ffprobe asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.warning(f"ffprobe failed for {file_path}: {stderr.decode()}")
            return None
        
        # Parse JSON output
        data = json.loads(stdout.decode())
        
        # Try to get duration from format first
        if "format" in data and "duration" in data["format"]:
            duration = float(data["format"]["duration"])
            return int(duration)
        
        # Fallback: get duration from video stream
        if "streams" in data:
            for stream in data["streams"]:
                if stream.get("codec_type") == "video" and "duration" in stream:
                    duration = float(stream["duration"])
                    return int(duration)
        
        logger.warning(f"Could not find duration in ffprobe output for {file_path}")
        return None
        
    except FileNotFoundError:
        logger.error("ffprobe not found. Please install FFmpeg.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe output: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return None


def get_video_duration_sync(file_path: str) -> Optional[int]:
    """Extract video duration using ffprobe (synchronous version).
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Optional[int]: Duration in seconds, or None if extraction fails
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        
        # Try to get duration from format first
        if "format" in data and "duration" in data["format"]:
            duration = float(data["format"]["duration"])
            return int(duration)
        
        # Fallback: get duration from video stream
        if "streams" in data:
            for stream in data["streams"]:
                if stream.get("codec_type") == "video" and "duration" in stream:
                    duration = float(stream["duration"])
                    return int(duration)
        
        return None
        
    except FileNotFoundError:
        logger.error("ffprobe not found. Please install FFmpeg.")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"ffprobe timed out for {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return None
