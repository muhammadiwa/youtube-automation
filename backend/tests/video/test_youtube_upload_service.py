"""Unit tests for YouTubeUploadService.

Tests YouTube upload operations with mocked dependencies.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.youtube_upload_service import YouTubeUploadService
from app.modules.video.models import Video, VideoStatus
from app.modules.video.video_usage_tracker import VideoUsageStats


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def upload_service(mock_db):
    """Create YouTubeUploadService instance."""
    return YouTubeUploadService(mock_db)


@pytest.fixture
def mock_video():
    """Create mock Video object in library."""
    video = Video(
        id=uuid4(),
        user_id=uuid4(),
        title="Test Video",
        description="Test description",
        status=VideoStatus.IN_LIBRARY.value,
        file_path="/path/to/video.mp4",
        file_size=1024000,
        duration=120,
        upload_attempts=0,
        upload_progress=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return video


@pytest.mark.asyncio
class TestYouTubeUploadService:
    """Test YouTubeUploadService methods."""

    async def test_upload_to_youtube_success(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test successful upload queue."""
        user_id = mock_video.user_id
        account_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Mock Celery task
        with patch('app.modules.video.tasks.upload_video_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-123")
            
            result = await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=account_id,
                title="YouTube Title",
                description="YouTube description"
            )
        
        # Verify video was updated
        assert mock_video.status == VideoStatus.DRAFT.value
        assert mock_video.account_id == account_id
        assert mock_video.title == "YouTube Title"
        assert mock_video.description == "YouTube description"
        assert mock_video.upload_progress == 0
        assert mock_video.last_upload_error is None
        
        # Verify task was queued
        assert result["video_id"] == str(mock_video.id)
        assert result["task_id"] == "task-123"
        assert result["status"] == VideoStatus.DRAFT.value
        
        mock_db.commit.assert_called_once()

    async def test_upload_to_youtube_video_not_found(
        self,
        upload_service,
        mock_db
    ):
        """Test upload with non-existent video."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_to_youtube(
                video_id=uuid4(),
                user_id=uuid4(),
                account_id=uuid4()
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_upload_to_youtube_wrong_user(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload with wrong user ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=uuid4(),  # Different user
                account_id=uuid4()
            )
        
        assert exc_info.value.status_code == 404

    async def test_upload_to_youtube_invalid_status(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload with video in invalid status."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.UPLOADING.value
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=uuid4()
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot be uploaded" in exc_info.value.detail.lower()

    async def test_upload_to_youtube_no_file_path(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload with missing file path."""
        user_id = mock_video.user_id
        mock_video.file_path = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=uuid4()
            )
        
        assert exc_info.value.status_code == 400
        assert "file path" in exc_info.value.detail.lower()

    async def test_upload_to_youtube_with_optional_params(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload with all optional parameters."""
        user_id = mock_video.user_id
        account_id = uuid4()
        scheduled_time = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with patch('app.modules.video.tasks.upload_video_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-456")
            
            await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=account_id,
                title="New Title",
                description="New description",
                tags=["tag1", "tag2"],
                category_id="10",
                visibility="public",
                scheduled_publish_at=scheduled_time
            )
        
        assert mock_video.title == "New Title"
        assert mock_video.description == "New description"
        assert mock_video.tags == ["tag1", "tag2"]
        assert mock_video.category_id == "10"
        assert mock_video.visibility == "public"
        assert mock_video.scheduled_publish_at == scheduled_time

    async def test_upload_to_youtube_uses_library_title(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload uses library title when not provided."""
        user_id = mock_video.user_id
        original_title = mock_video.title
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with patch('app.modules.video.tasks.upload_video_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-789")
            
            await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=uuid4()
            )
        
        assert mock_video.title == original_title

    async def test_get_upload_progress_success(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test getting upload progress."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.UPLOADING.value
        mock_video.upload_progress = 45
        mock_video.upload_attempts = 1
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        progress = await upload_service.get_upload_progress(
            video_id=mock_video.id,
            user_id=user_id
        )
        
        assert progress["video_id"] == str(mock_video.id)
        assert progress["status"] == VideoStatus.UPLOADING.value
        assert progress["progress"] == 45
        assert progress["upload_attempts"] == 1

    async def test_get_upload_progress_not_found(
        self,
        upload_service,
        mock_db
    ):
        """Test getting progress for non-existent video."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.get_upload_progress(
                video_id=uuid4(),
                user_id=uuid4()
            )
        
        assert exc_info.value.status_code == 404

    async def test_get_upload_progress_with_youtube_id(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test progress includes YouTube ID when uploaded."""
        user_id = mock_video.user_id
        mock_video.youtube_id = "abc123"
        mock_video.status = VideoStatus.PROCESSING.value
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        progress = await upload_service.get_upload_progress(
            video_id=mock_video.id,
            user_id=user_id
        )
        
        assert progress["youtube_id"] == "abc123"

    async def test_retry_upload_success(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test retrying failed upload."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.FAILED.value
        mock_video.upload_attempts = 1
        mock_video.last_upload_error = "Previous error"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with patch('app.modules.video.tasks.upload_video_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="retry-task-123")
            
            result = await upload_service.retry_upload(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert mock_video.status == VideoStatus.DRAFT.value
        assert mock_video.upload_progress == 0
        assert mock_video.last_upload_error is None
        
        assert result["video_id"] == str(mock_video.id)
        assert result["task_id"] == "retry-task-123"
        assert result["attempt"] == 2

    async def test_retry_upload_max_attempts_exceeded(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test retry fails when max attempts exceeded."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.FAILED.value
        mock_video.upload_attempts = 3  # Max attempts
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.retry_upload(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "maximum" in exc_info.value.detail.lower()

    async def test_retry_upload_invalid_status(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test retry fails for video in invalid status."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.UPLOADING.value
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.retry_upload(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot be retried" in exc_info.value.detail.lower()

    async def test_cancel_upload_success(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test cancelling upload."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.DRAFT.value
        mock_video.upload_progress = 0
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        result = await upload_service.cancel_upload(
            video_id=mock_video.id,
            user_id=user_id
        )
        
        assert mock_video.status == VideoStatus.IN_LIBRARY.value
        assert mock_video.upload_progress == 0
        
        assert result["video_id"] == str(mock_video.id)
        assert result["status"] == VideoStatus.IN_LIBRARY.value
        
        mock_db.commit.assert_called_once()

    async def test_cancel_upload_invalid_status(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test cancel fails for video in invalid status."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.PUBLISHED.value
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.cancel_upload(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot be cancelled" in exc_info.value.detail.lower()

    async def test_get_youtube_video_info_success(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test getting YouTube video info."""
        user_id = mock_video.user_id
        mock_video.youtube_id = "xyz789"
        mock_video.youtube_url = "https://youtube.com/watch?v=xyz789"
        mock_video.youtube_status = "published"
        mock_video.youtube_uploaded_at = datetime.utcnow()
        mock_video.view_count = 1000
        mock_video.like_count = 50
        mock_video.comment_count = 10
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Mock usage tracker
        mock_stats = VideoUsageStats(youtube_uploads=2)
        with patch.object(
            upload_service.usage_tracker,
            'get_usage_stats',
            new_callable=AsyncMock,
            return_value=mock_stats
        ):
            info = await upload_service.get_youtube_video_info(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert info["video_id"] == str(mock_video.id)
        assert info["youtube_id"] == "xyz789"
        assert info["youtube_url"] == "https://youtube.com/watch?v=xyz789"
        assert info["youtube_status"] == "published"
        assert info["view_count"] == 1000
        assert info["like_count"] == 50
        assert info["comment_count"] == 10
        assert info["upload_count"] == 2

    async def test_get_youtube_video_info_not_uploaded(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test getting info for video not uploaded to YouTube."""
        user_id = mock_video.user_id
        mock_video.youtube_id = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.get_youtube_video_info(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "not uploaded" in exc_info.value.detail.lower()

    async def test_upload_to_youtube_from_failed_status(
        self,
        upload_service,
        mock_db,
        mock_video
    ):
        """Test upload can be queued from failed status."""
        user_id = mock_video.user_id
        mock_video.status = VideoStatus.FAILED.value
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with patch('app.modules.video.tasks.upload_video_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-retry")
            
            result = await upload_service.upload_to_youtube(
                video_id=mock_video.id,
                user_id=user_id,
                account_id=uuid4()
            )
        
        assert result["status"] == VideoStatus.DRAFT.value
