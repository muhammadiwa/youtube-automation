"""CDN storage utilities for transcoded outputs.

Requirements: 10.5 - Store transcoded output in CDN-backed storage.
Uses the universal storage module for backend flexibility.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from app.core.storage import Storage, StorageResult, get_storage
from app.modules.transcoding.schemas import CDNUploadResult


def convert_to_cdn_result(result: StorageResult, bucket: str = "") -> CDNUploadResult:
    """Convert StorageResult to CDNUploadResult for backward compatibility.
    
    Args:
        result: Storage result
        bucket: Bucket name (for compatibility)
        
    Returns:
        CDNUploadResult
    """
    return CDNUploadResult(
        success=result.success,
        bucket=bucket,
        key=result.key,
        cdn_url=result.url,
        file_size=result.file_size,
        etag=result.etag,
        error_message=result.error_message,
    )


class CDNStorage:
    """CDN-backed storage for transcoded videos.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    
    This is a wrapper around the universal Storage class for backward compatibility.
    """

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize CDN storage.
        
        Args:
            storage: Storage instance (uses default if not provided)
        """
        self._storage = storage or get_storage()

    def generate_key(
        self,
        job_id: uuid.UUID,
        resolution: str,
        extension: str = "mp4",
    ) -> str:
        """Generate storage key for transcoded output.
        
        Args:
            job_id: Transcode job ID
            resolution: Output resolution
            extension: File extension
            
        Returns:
            Storage key
        """
        return self._storage.generate_key(
            prefix="transcoded",
            filename=f"{job_id}/{resolution}.{extension}",
            include_date=True,
        )

    def get_cdn_url(self, key: str, expires_in: int = 3600) -> str:
        """Get CDN URL for an object.
        
        Args:
            key: Storage key
            expires_in: URL expiration in seconds
            
        Returns:
            CDN/Storage URL
        """
        return self._storage.get_url(key, expires_in)

    def upload_file(
        self,
        file_path: str,
        key: str,
        content_type: str = "video/mp4",
    ) -> CDNUploadResult:
        """Upload file to CDN storage.
        
        Requirements: 10.5 - Store transcoded output in CDN-backed storage.
        
        Args:
            file_path: Local file path
            key: Storage key
            content_type: MIME type
            
        Returns:
            Upload result
        """
        result = self._storage.upload(file_path, key, content_type)
        return convert_to_cdn_result(result)

    def delete_file(self, key: str) -> bool:
        """Delete file from CDN storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted successfully
        """
        return self._storage.delete(key)

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Generate presigned URL for temporary access.
        
        Args:
            key: Storage key
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        try:
            return self._storage.get_url(key, expires_in)
        except Exception:
            return None

    def file_exists(self, key: str) -> bool:
        """Check if file exists in storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if file exists
        """
        return self._storage.exists(key)


def get_default_storage() -> CDNStorage:
    """Get default CDN storage instance.
    
    Returns:
        CDNStorage instance
    """
    return CDNStorage()


async def upload_transcoded_output(
    job_id: uuid.UUID,
    file_path: str,
    resolution: str,
    storage: Optional[CDNStorage] = None,
) -> CDNUploadResult:
    """Upload transcoded output to CDN storage.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    
    Args:
        job_id: Transcode job ID
        file_path: Local file path
        resolution: Output resolution
        storage: CDN storage instance (uses default if not provided)
        
    Returns:
        Upload result
    """
    if storage is None:
        storage = get_default_storage()
    
    key = storage.generate_key(job_id, resolution)
    return storage.upload_file(file_path, key)


def cleanup_local_file(file_path: str) -> bool:
    """Clean up local file after CDN upload.
    
    Args:
        file_path: Local file path to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


# Thumbnail storage utilities
class ThumbnailStorage:
    """Storage for AI-generated thumbnails."""

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize thumbnail storage.
        
        Args:
            storage: Storage instance (uses default if not provided)
        """
        self._storage = storage or get_storage()

    def generate_key(
        self,
        video_id: uuid.UUID,
        thumbnail_id: str,
        extension: str = "jpg",
    ) -> str:
        """Generate storage key for thumbnail.
        
        Args:
            video_id: Video ID
            thumbnail_id: Thumbnail identifier
            extension: File extension
            
        Returns:
            Storage key
        """
        return self._storage.generate_key(
            prefix="thumbnails",
            filename=f"{video_id}/{thumbnail_id}.{extension}",
            include_date=True,
        )

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "image/jpeg",
    ) -> StorageResult:
        """Upload thumbnail to storage.
        
        Args:
            file_path: Local file path
            key: Storage key
            content_type: MIME type
            
        Returns:
            Upload result
        """
        return self._storage.upload(file_path, key, content_type)

    def get_url(self, key: str, expires_in: int = 86400) -> str:
        """Get URL for thumbnail.
        
        Args:
            key: Storage key
            expires_in: URL expiration in seconds (default 24 hours)
            
        Returns:
            Thumbnail URL
        """
        return self._storage.get_url(key, expires_in)

    def delete(self, key: str) -> bool:
        """Delete thumbnail from storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted successfully
        """
        return self._storage.delete(key)


# Video upload storage utilities
class VideoStorage:
    """Storage for uploaded videos."""

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize video storage.
        
        Args:
            storage: Storage instance (uses default if not provided)
        """
        self._storage = storage or get_storage()

    def generate_key(
        self,
        account_id: uuid.UUID,
        video_id: uuid.UUID,
        filename: str,
    ) -> str:
        """Generate storage key for video.
        
        Args:
            account_id: YouTube account ID
            video_id: Video ID
            filename: Original filename
            
        Returns:
            Storage key
        """
        extension = filename.split(".")[-1] if "." in filename else "mp4"
        return self._storage.generate_key(
            prefix=f"videos/{account_id}",
            filename=f"{video_id}.{extension}",
            include_date=True,
        )

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "video/mp4",
    ) -> StorageResult:
        """Upload video to storage.
        
        Args:
            file_path: Local file path
            key: Storage key
            content_type: MIME type
            
        Returns:
            Upload result
        """
        return self._storage.upload(file_path, key, content_type)

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for video.
        
        Args:
            key: Storage key
            expires_in: URL expiration in seconds
            
        Returns:
            Video URL
        """
        return self._storage.get_url(key, expires_in)

    def delete(self, key: str) -> bool:
        """Delete video from storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted successfully
        """
        return self._storage.delete(key)

    def exists(self, key: str) -> bool:
        """Check if video exists in storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if video exists
        """
        return self._storage.exists(key)
