"""Unit tests for VideoStorageService.

Tests video storage operations with mocked storage backend.
"""

import pytest
from io import BytesIO
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile

from app.modules.video.video_storage_service import VideoStorageService
from app.core.storage import StorageResult


@pytest.fixture
def video_storage_service():
    """Create VideoStorageService instance."""
    return VideoStorageService()


@pytest.fixture
def mock_upload_file():
    """Create mock UploadFile."""
    content = b"fake video content"
    # Create UploadFile with headers to set content_type
    file = UploadFile(
        filename="test_video.mp4",
        file=BytesIO(content),
        headers={"content-type": "video/mp4"}
    )
    return file


@pytest.mark.asyncio
class TestVideoStorageService:
    """Test VideoStorageService methods."""

    async def test_save_video_success(
        self,
        video_storage_service,
        mock_upload_file
    ):
        """Test successful video upload."""
        user_id = uuid4()
        video_id = uuid4()
        
        # Mock storage service
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=True,
                key=f"videos/{user_id}/{video_id}.mp4",
                url="https://example.com/video.mp4",
                file_size=1024
            )
            
            # Call save_video
            key, file_size = await video_storage_service.save_video(
                user_id=user_id,
                video_id=video_id,
                file=mock_upload_file
            )
            
            # Assertions
            assert key == f"videos/{user_id}/{video_id}.mp4"
            assert file_size == 1024
            mock_upload.assert_called_once()

    async def test_save_video_failure(
        self,
        video_storage_service,
        mock_upload_file
    ):
        """Test video upload failure."""
        user_id = uuid4()
        video_id = uuid4()
        
        # Mock storage service to return failure
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=False,
                key="",
                url="",
                error_message="Storage error"
            )
            
            # Call save_video and expect exception
            with pytest.raises(Exception) as exc_info:
                await video_storage_service.save_video(
                    user_id=user_id,
                    video_id=video_id,
                    file=mock_upload_file
                )
            
            assert "Failed to upload video" in str(exc_info.value)

    async def test_save_video_without_extension(
        self,
        video_storage_service
    ):
        """Test video upload without file extension."""
        user_id = uuid4()
        video_id = uuid4()
        
        # Create file without extension
        file = UploadFile(
            filename=None,
            file=BytesIO(b"content")
        )
        
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=True,
                key=f"videos/{user_id}/{video_id}.mp4",
                url="https://example.com/video.mp4",
                file_size=7
            )
            
            key, _ = await video_storage_service.save_video(
                user_id=user_id,
                video_id=video_id,
                file=file
            )
            
            # Should default to .mp4
            assert key.endswith(".mp4")

    async def test_delete_video(self, video_storage_service):
        """Test video deletion."""
        key = "videos/user123/video456.mp4"
        
        with patch.object(
            video_storage_service.storage,
            'delete_file',
            new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True
            
            result = await video_storage_service.delete_video(key)
            
            assert result is True
            mock_delete.assert_called_once_with(key)

    async def test_get_video_url(self, video_storage_service):
        """Test getting video URL."""
        key = "videos/user123/video456.mp4"
        expected_url = "https://example.com/video.mp4"
        
        with patch.object(
            video_storage_service.storage,
            'get_url',
            new_callable=AsyncMock
        ) as mock_get_url:
            mock_get_url.return_value = expected_url
            
            url = await video_storage_service.get_video_url(key)
            
            assert url == expected_url
            mock_get_url.assert_called_once_with(key, 3600)

    async def test_get_video_url_custom_expiry(self, video_storage_service):
        """Test getting video URL with custom expiry."""
        key = "videos/user123/video456.mp4"
        expires_in = 7200
        
        with patch.object(
            video_storage_service.storage,
            'get_url',
            new_callable=AsyncMock
        ) as mock_get_url:
            mock_get_url.return_value = "https://example.com/video.mp4"
            
            await video_storage_service.get_video_url(key, expires_in)
            
            mock_get_url.assert_called_once_with(key, expires_in)

    async def test_video_exists(self, video_storage_service):
        """Test checking if video exists."""
        key = "videos/user123/video456.mp4"
        
        with patch.object(
            video_storage_service.storage,
            'exists',
            new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.return_value = True
            
            exists = await video_storage_service.video_exists(key)
            
            assert exists is True
            mock_exists.assert_called_once_with(key)

    async def test_save_thumbnail_success(self, video_storage_service):
        """Test successful thumbnail upload."""
        video_id = uuid4()
        content = b"fake thumbnail content"
        
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=True,
                key=f"thumbnails/{video_id}.jpg",
                url="https://example.com/thumb.jpg",
                file_size=512
            )
            
            key = await video_storage_service.save_thumbnail(
                video_id=video_id,
                content=content,
                custom=False
            )
            
            assert key == f"thumbnails/{video_id}.jpg"
            mock_upload.assert_called_once()

    async def test_save_custom_thumbnail(self, video_storage_service):
        """Test saving custom thumbnail."""
        video_id = uuid4()
        content = b"custom thumbnail"
        
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=True,
                key=f"thumbnails/{video_id}_custom.jpg",
                url="https://example.com/thumb.jpg",
                file_size=512
            )
            
            key = await video_storage_service.save_thumbnail(
                video_id=video_id,
                content=content,
                custom=True
            )
            
            assert key == f"thumbnails/{video_id}_custom.jpg"
            assert "_custom" in key

    async def test_save_thumbnail_failure(self, video_storage_service):
        """Test thumbnail upload failure."""
        video_id = uuid4()
        content = b"thumbnail"
        
        with patch.object(
            video_storage_service.storage,
            'upload_file',
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = StorageResult(
                success=False,
                key="",
                url="",
                error_message="Upload failed"
            )
            
            with pytest.raises(Exception) as exc_info:
                await video_storage_service.save_thumbnail(
                    video_id=video_id,
                    content=content
                )
            
            assert "Failed to upload thumbnail" in str(exc_info.value)

    async def test_delete_thumbnail(self, video_storage_service):
        """Test thumbnail deletion."""
        key = "thumbnails/video123.jpg"
        
        with patch.object(
            video_storage_service.storage,
            'delete_file',
            new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True
            
            result = await video_storage_service.delete_thumbnail(key)
            
            assert result is True
            mock_delete.assert_called_once_with(key)

    async def test_get_thumbnail_url(self, video_storage_service):
        """Test getting thumbnail URL."""
        key = "thumbnails/video123.jpg"
        expected_url = "https://example.com/thumb.jpg"
        
        with patch.object(
            video_storage_service.storage,
            'get_url',
            new_callable=AsyncMock
        ) as mock_get_url:
            mock_get_url.return_value = expected_url
            
            url = await video_storage_service.get_thumbnail_url(key)
            
            assert url == expected_url
            mock_get_url.assert_called_once_with(key, 3600)
