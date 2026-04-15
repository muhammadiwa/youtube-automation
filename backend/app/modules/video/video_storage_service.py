"""Video storage service for handling video file operations.

Wraps the universal StorageService to provide video-specific storage operations.
Supports local, S3, and MinIO backends via existing storage infrastructure.
Requirements: 1.1
"""

from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import UploadFile

from app.core.storage import storage_service, StorageResult


class VideoStorageService:
    """Handle video file storage using universal storage backend.
    
    Provides video-specific methods for:
    - Uploading video files
    - Deleting video files
    - Generating video URLs
    - Managing thumbnails
    
    Storage keys format:
    - Videos: videos/{user_id}/{video_id}.{ext}
    - Thumbnails: thumbnails/{video_id}.jpg
    - Custom thumbnails: thumbnails/{video_id}_custom.jpg
    """

    def __init__(self):
        """Initialize video storage service."""
        self.storage = storage_service

    async def save_video(
        self,
        user_id: UUID,
        video_id: UUID,
        file: UploadFile,
    ) -> tuple[str, int]:
        """Save video file to storage.
        
        Args:
            user_id: Owner of the video
            video_id: Unique video identifier
            file: Uploaded file object
            
        Returns:
            tuple[str, int]: (storage_key, file_size)
            
        Raises:
            Exception: If upload fails
        """
        # Generate storage key
        ext = Path(file.filename).suffix if file.filename else ".mp4"
        key = f"videos/{user_id}/{video_id}{ext}"
        
        # Read file content
        content = await file.read()
        
        # Upload to storage (works for local, S3, MinIO)
        result = await self.storage.upload_file(
            key=key,
            content=content,
            content_type=file.content_type or "video/mp4"
        )
        
        if not result.success:
            raise Exception(f"Failed to upload video: {result.error_message}")
        
        return key, result.file_size

    async def delete_video(self, key: str) -> bool:
        """Delete video file from storage.
        
        Args:
            key: Storage key of the video
            
        Returns:
            bool: True if deleted successfully
        """
        return await self.storage.delete_file(key)

    async def get_video_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Get video URL (presigned for S3, direct for local).
        
        Args:
            key: Storage key of the video
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Video URL
        """
        return await self.storage.get_url(key, expires_in)

    async def video_exists(self, key: str) -> bool:
        """Check if video exists in storage.
        
        Args:
            key: Storage key of the video
            
        Returns:
            bool: True if video exists
        """
        return await self.storage.exists(key)

    async def save_thumbnail(
        self,
        video_id: UUID,
        content: bytes,
        custom: bool = False
    ) -> str:
        """Save thumbnail to storage.
        
        Args:
            video_id: Video identifier
            content: Thumbnail image content (JPEG)
            custom: Whether this is a custom uploaded thumbnail
            
        Returns:
            str: Storage key of the thumbnail
            
        Raises:
            Exception: If upload fails
        """
        suffix = "_custom" if custom else ""
        key = f"thumbnails/{video_id}{suffix}.jpg"
        
        result = await self.storage.upload_file(
            key=key,
            content=content,
            content_type="image/jpeg"
        )
        
        if not result.success:
            raise Exception(f"Failed to upload thumbnail: {result.error_message}")
        
        return key

    async def delete_thumbnail(self, key: str) -> bool:
        """Delete thumbnail from storage.
        
        Args:
            key: Storage key of the thumbnail
            
        Returns:
            bool: True if deleted successfully
        """
        return await self.storage.delete_file(key)

    async def get_thumbnail_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Get thumbnail URL.
        
        Args:
            key: Storage key of the thumbnail
            expires_in: URL expiration time in seconds
            
        Returns:
            str: Thumbnail URL
        """
        return await self.storage.get_url(key, expires_in)


# Global video storage service instance
video_storage_service = VideoStorageService()
