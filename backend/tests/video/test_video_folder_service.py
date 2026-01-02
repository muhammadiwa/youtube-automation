"""Unit tests for VideoFolderService.

Tests folder management operations with mocked database.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.video_folder_service import VideoFolderService
from app.modules.video.models import VideoFolder


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
def folder_service(mock_db):
    """Create VideoFolderService instance."""
    return VideoFolderService(mock_db)


@pytest.fixture
def mock_folder():
    """Create mock VideoFolder object."""
    folder = VideoFolder(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Folder",
        parent_id=None,
        description="Test description",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return folder


@pytest.mark.asyncio
class TestVideoFolderService:
    """Test VideoFolderService methods."""

    async def test_create_folder_success(
        self,
        folder_service,
        mock_db
    ):
        """Test successful folder creation."""
        user_id = uuid4()
        
        # Mock folder count check
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock duplicate check (no duplicate)
        mock_dup_result = MagicMock()
        mock_dup_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_count_result,
            mock_dup_result
        ]
        
        folder = await folder_service.create_folder(
            user_id=user_id,
            name="New Folder",
            description="Test folder"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_folder_with_parent(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test creating folder with parent."""
        user_id = mock_folder.user_id
        parent_id = mock_folder.id
        
        # Mock folder count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock parent folder lookup
        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock depth check
        mock_depth_result = MagicMock()
        mock_depth_result.scalar_one_or_none.return_value = None
        
        # Mock duplicate check (no duplicate)
        mock_dup_result = MagicMock()
        mock_dup_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_count_result,  # Folder count
            mock_parent_result,  # Parent lookup
            mock_depth_result,  # Depth check
            mock_dup_result,  # Duplicate check
        ]
        
        await folder_service.create_folder(
            user_id=user_id,
            name="Child Folder",
            parent_id=parent_id
        )
        
        mock_db.add.assert_called_once()

    async def test_create_folder_limit_exceeded(
        self,
        folder_service,
        mock_db
    ):
        """Test folder creation when limit exceeded."""
        user_id = uuid4()
        
        # Mock folder count at limit
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.create_folder(
                user_id=user_id,
                name="New Folder"
            )
        
        assert exc_info.value.status_code == 400
        assert "limit" in exc_info.value.detail.lower()

    async def test_create_folder_max_depth_exceeded(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test folder creation when max depth exceeded."""
        user_id = mock_folder.user_id
        parent_id = mock_folder.id
        
        # Mock folder count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock parent folder
        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock depth at max (5 levels) - simulate 5 parent folders
        # Each iteration returns a parent_id until we reach root (None)
        mock_depth_results = []
        for i in range(6):  # Need 6 to reach depth 5
            mock_result = MagicMock()
            # Return parent_id for first 5, then None for root
            mock_result.scalar_one_or_none.return_value = uuid4() if i < 5 else None
            mock_depth_results.append(mock_result)
        
        mock_db.execute.side_effect = [
            mock_count_result,  # Folder count check
            mock_parent_result,  # Parent lookup
        ] + mock_depth_results  # Depth checks (will reach 5 and raise error)
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.create_folder(
                user_id=user_id,
                name="Deep Folder",
                parent_id=parent_id
            )
        
        assert exc_info.value.status_code == 400
        assert "depth" in exc_info.value.detail.lower()

    async def test_create_folder_duplicate_name(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test folder creation with duplicate name."""
        user_id = mock_folder.user_id
        
        # Mock folder count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock duplicate check
        mock_dup_result = MagicMock()
        mock_dup_result.scalar_one_or_none.return_value = mock_folder
        
        mock_db.execute.side_effect = [
            mock_count_result,
            mock_dup_result
        ]
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.create_folder(
                user_id=user_id,
                name=mock_folder.name
            )
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    async def test_update_folder_success(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test successful folder update."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_folder
        mock_db.execute.return_value = mock_result
        
        updated = await folder_service.update_folder(
            folder_id=mock_folder.id,
            user_id=user_id,
            description="Updated description",
            color="#FF0000"
        )
        
        assert mock_folder.description == "Updated description"
        assert mock_folder.color == "#FF0000"
        mock_db.commit.assert_called_once()

    async def test_update_folder_name(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test updating folder name."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock duplicate check
        mock_dup_result = MagicMock()
        mock_dup_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_dup_result
        ]
        
        await folder_service.update_folder(
            folder_id=mock_folder.id,
            user_id=user_id,
            name="New Name"
        )
        
        assert mock_folder.name == "New Name"

    async def test_delete_folder_success(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test successful folder deletion."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock video count (0)
        mock_video_count = MagicMock()
        mock_video_count.scalar.return_value = 0
        
        # Mock subfolder count (0)
        mock_subfolder_count = MagicMock()
        mock_subfolder_count.scalar.return_value = 0
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_video_count,
            mock_subfolder_count
        ]
        
        await folder_service.delete_folder(
            folder_id=mock_folder.id,
            user_id=user_id
        )
        
        mock_db.delete.assert_called_once_with(mock_folder)
        mock_db.commit.assert_called_once()

    async def test_delete_folder_with_videos(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test deleting folder with videos."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock video count (has videos)
        mock_video_count = MagicMock()
        mock_video_count.scalar.return_value = 5
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_video_count
        ]
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.delete_folder(
                folder_id=mock_folder.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "videos" in exc_info.value.detail.lower()

    async def test_delete_folder_with_subfolders(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test deleting folder with subfolders."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock video count (0)
        mock_video_count = MagicMock()
        mock_video_count.scalar.return_value = 0
        
        # Mock subfolder count (has subfolders)
        mock_subfolder_count = MagicMock()
        mock_subfolder_count.scalar.return_value = 3
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_video_count,
            mock_subfolder_count
        ]
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.delete_folder(
                folder_id=mock_folder.id,
                user_id=user_id
            )
        
        assert exc_info.value.status_code == 400
        assert "subfolders" in exc_info.value.detail.lower()

    async def test_get_folder_tree(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test getting folder tree."""
        user_id = mock_folder.user_id
        
        # Mock folder query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_folder]
        mock_db.execute.return_value = mock_result
        
        folders = await folder_service.get_folder_tree(user_id)
        
        assert len(folders) == 1
        assert folders[0] == mock_folder

    async def test_get_folder_with_stats(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test getting folder with statistics."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock video count
        mock_video_count = MagicMock()
        mock_video_count.scalar.return_value = 10
        
        # Mock subfolder count
        mock_subfolder_count = MagicMock()
        mock_subfolder_count.scalar.return_value = 3
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_video_count,
            mock_subfolder_count
        ]
        
        result = await folder_service.get_folder_with_stats(
            folder_id=mock_folder.id,
            user_id=user_id
        )
        
        assert result["folder"] == mock_folder
        assert result["video_count"] == 10
        assert result["subfolder_count"] == 3

    async def test_move_folder_to_root(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test moving folder to root."""
        user_id = mock_folder.user_id
        mock_folder.parent_id = uuid4()
        
        # Mock folder lookup
        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = mock_folder
        
        # Mock duplicate check
        mock_dup_result = MagicMock()
        mock_dup_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_folder_result,
            mock_dup_result
        ]
        
        await folder_service.move_folder(
            folder_id=mock_folder.id,
            user_id=user_id,
            new_parent_id=None
        )
        
        assert mock_folder.parent_id is None
        mock_db.commit.assert_called_once()

    async def test_move_folder_into_itself(
        self,
        folder_service,
        mock_db,
        mock_folder
    ):
        """Test moving folder into itself."""
        user_id = mock_folder.user_id
        
        # Mock folder lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_folder
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service.move_folder(
                folder_id=mock_folder.id,
                user_id=user_id,
                new_parent_id=mock_folder.id
            )
        
        assert exc_info.value.status_code == 400
        assert "itself" in exc_info.value.detail.lower()

    async def test_get_folder_not_found(
        self,
        folder_service,
        mock_db
    ):
        """Test getting non-existent folder."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await folder_service._get_folder(
                folder_id=uuid4(),
                user_id=uuid4()
            )
        
        assert exc_info.value.status_code == 404
