"""Unit tests for VideoLibraryService.

Tests video library operations with mocked dependencies.
"""

import pytest
from io import BytesIO
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.video_library_service import (
    VideoLibraryService,
    VideoFilters,
    Pagination
)
from app.modules.video.models import Video, VideoStatus
from app.modules.video.video_metadata_extractor import VideoFileMetadata


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def library_service(mock_db):
    """Create VideoLibraryService instance."""
    return VideoLibraryService(mock_db)


@pytest.fixture
def mock_upload_file():
    """Create mock UploadFile."""
    content = b"fake video content"
    file = UploadFile(
        filename="test_video.mp4",
        file=BytesIO(content),
        headers={"content-type": "video/mp4"}
    )
    return file


@pytest.fixture
def mock_video():
    """Create mock Video object."""
    video = Video(
        id=uuid4(),
        user_id=uuid4(),
        title="Test Video",
        description="Test description",
        status=VideoStatus.IN_LIBRARY.value,
        file_path="videos/user123/video456.mp4",
        file_size=1024,
        duration=120,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return video


@pytest.mark.asyncio
class TestVideoLibraryService:
    """Test VideoLibraryService methods."""

    async def test_upload_to_library_success(
        self,
        library_service,
        mock_db,
        mock_upload_file
    ):
        """Test successful video upload to library."""
        user_id = uuid4()
        
        # Mock metadata extraction
        mock_metadata = VideoFileMetadata(
            duration=120,
            resolution="1920x1080",
            width=1920,
            height=1080,
            frame_rate=30.0,
            bitrate=5000,
            codec="h264",
            format="mp4",
            file_size=1024000
        )
        
        with patch.object(
            library_service.metadata_extractor,
            'extract_metadata',
            new_callable=AsyncMock,
            return_value=mock_metadata
        ), patch.object(
            library_service.metadata_extractor,
            'generate_thumbnail',
            new_callable=AsyncMock
        ), patch.object(
            library_service.storage,
            'save_video',
            new_callable=AsyncMock,
            return_value=("videos/user/video.mp4", 1024000)
        ), patch.object(
            library_service.storage,
            'save_thumbnail',
            new_callable=AsyncMock,
            return_value="thumbnails/video.jpg"
        ), patch('builtins.open', create=True), patch('pathlib.Path.unlink'):
            
            video = await library_service.upload_to_library(
                user_id=user_id,
                file=mock_upload_file,
                title="Test Video",
                description="Test description"
            )
            
            # Verify video was added to database
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    async def test_upload_to_library_invalid_format(
        self,
        library_service
    ):
        """Test upload with invalid file format."""
        user_id = uuid4()
        
        # Create file with invalid extension
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"content")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await library_service.upload_to_library(
                user_id=user_id,
                file=file,
                title="Test"
            )
        
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail

    async def test_upload_to_library_no_filename(
        self,
        library_service
    ):
        """Test upload without filename."""
        user_id = uuid4()
        
        file = UploadFile(
            filename=None,
            file=BytesIO(b"content")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await library_service.upload_to_library(
                user_id=user_id,
                file=file,
                title="Test"
            )
        
        assert exc_info.value.status_code == 400

    async def test_get_library_videos_with_filters(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test getting library videos with filters."""
        user_id = uuid4()
        
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_video]
        mock_result.scalar.return_value = 1
        
        mock_db.execute.return_value = mock_result
        
        filters = VideoFilters(
            status=VideoStatus.IN_LIBRARY.value,
            is_favorite=True,
            search="test"
        )
        pagination = Pagination(page=1, limit=20)
        
        videos, total = await library_service.get_library_videos(
            user_id=user_id,
            filters=filters,
            pagination=pagination
        )
        
        assert len(videos) == 1
        assert total == 1
        mock_db.execute.assert_called()

    async def test_get_library_videos_pagination(
        self,
        library_service,
        mock_db
    ):
        """Test pagination parameters."""
        user_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result
        
        # Test page 2 with limit 10
        pagination = Pagination(page=2, limit=10)
        assert pagination.offset == 10
        assert pagination.limit == 10
        
        # Test max limit enforcement
        pagination = Pagination(page=1, limit=200)
        assert pagination.limit == 100  # Max limit

    async def test_get_video_by_id_success(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test getting video by ID."""
        user_id = mock_video.user_id
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        video = await library_service.get_video_by_id(
            video_id=mock_video.id,
            user_id=user_id
        )
        
        assert video == mock_video

    async def test_get_video_by_id_not_found(
        self,
        library_service,
        mock_db
    ):
        """Test getting non-existent video."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await library_service.get_video_by_id(
                video_id=uuid4(),
                user_id=uuid4()
            )
        
        assert exc_info.value.status_code == 404

    async def test_update_metadata_success(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test updating video metadata."""
        user_id = mock_video.user_id
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        updated_video = await library_service.update_metadata(
            video_id=mock_video.id,
            user_id=user_id,
            title="Updated Title",
            description="Updated description",
            tags=["tag1", "tag2"]
        )
        
        assert mock_video.title == "Updated Title"
        assert mock_video.description == "Updated description"
        assert mock_video.tags == ["tag1", "tag2"]
        mock_db.commit.assert_called_once()

    async def test_update_metadata_partial(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test partial metadata update."""
        user_id = mock_video.user_id
        original_title = mock_video.title
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Only update description
        await library_service.update_metadata(
            video_id=mock_video.id,
            user_id=user_id,
            description="New description"
        )
        
        # Title should remain unchanged
        assert mock_video.title == original_title
        assert mock_video.description == "New description"

    async def test_delete_from_library_success(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test deleting video from library."""
        user_id = mock_video.user_id
        mock_video.is_used_for_streaming = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with patch.object(
            library_service.storage,
            'delete_video',
            new_callable=AsyncMock,
            return_value=True
        ), patch.object(
            library_service.storage,
            'delete_thumbnail',
            new_callable=AsyncMock,
            return_value=True
        ):
            await library_service.delete_from_library(
                video_id=mock_video.id,
                user_id=user_id
            )
            
            mock_db.delete.assert_called_once_with(mock_video)
            mock_db.commit.assert_called_once()

    async def test_delete_from_library_in_use(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test deleting video that is in use."""
        user_id = mock_video.user_id
        mock_video.is_used_for_streaming = True
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await library_service.delete_from_library(
                video_id=mock_video.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "streaming" in exc_info.value.detail

    async def test_toggle_favorite(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test toggling favorite status."""
        user_id = mock_video.user_id
        mock_video.is_favorite = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Toggle to True
        await library_service.toggle_favorite(
            video_id=mock_video.id,
            user_id=user_id
        )
        assert mock_video.is_favorite is True
        
        # Toggle back to False
        await library_service.toggle_favorite(
            video_id=mock_video.id,
            user_id=user_id
        )
        assert mock_video.is_favorite is False

    async def test_move_to_folder_success(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test moving video to folder."""
        user_id = mock_video.user_id
        folder_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Mock folder validation
        with patch.object(
            library_service,
            '_validate_folder_access',
            new_callable=AsyncMock
        ):
            await library_service.move_to_folder(
                video_id=mock_video.id,
                user_id=user_id,
                folder_id=folder_id
            )
            
            assert mock_video.folder_id == folder_id
            mock_db.commit.assert_called_once()

    async def test_move_to_root_folder(
        self,
        library_service,
        mock_db,
        mock_video
    ):
        """Test moving video to root (no folder)."""
        user_id = mock_video.user_id
        mock_video.folder_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        await library_service.move_to_folder(
            video_id=mock_video.id,
            user_id=user_id,
            folder_id=None
        )
        
        assert mock_video.folder_id is None

    async def test_validate_file_valid_formats(self, library_service):
        """Test file validation with valid formats."""
        valid_formats = ["mp4", "mov", "avi", "mkv", "webm"]
        
        for fmt in valid_formats:
            file = UploadFile(
                filename=f"test.{fmt}",
                file=BytesIO(b"content")
            )
            # Should not raise exception
            library_service._validate_file(file)

    async def test_validate_file_invalid_format(self, library_service):
        """Test file validation with invalid format."""
        file = UploadFile(
            filename="test.exe",
            file=BytesIO(b"content")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            library_service._validate_file(file)
        
        assert exc_info.value.status_code == 400

    async def test_video_filters_defaults(self):
        """Test VideoFilters default values."""
        filters = VideoFilters()
        
        assert filters.folder_id is None
        assert filters.status is None
        assert filters.search is None
        assert filters.tags is None
        assert filters.is_favorite is None
        assert filters.sort_by == "created_at"
        assert filters.sort_order == "desc"

    async def test_pagination_bounds(self):
        """Test Pagination boundary conditions."""
        # Test minimum page
        pagination = Pagination(page=0, limit=20)
        assert pagination.page == 1
        
        # Test negative page
        pagination = Pagination(page=-5, limit=20)
        assert pagination.page == 1
        
        # Test minimum limit
        pagination = Pagination(page=1, limit=0)
        assert pagination.limit == 1
        
        # Test maximum limit
        pagination = Pagination(page=1, limit=500)
        assert pagination.limit == 100
