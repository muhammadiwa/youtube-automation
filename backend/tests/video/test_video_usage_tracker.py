"""Unit tests for VideoUsageTracker.

Tests video usage tracking operations with mocked dependencies.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.video_usage_tracker import (
    VideoUsageTracker,
    VideoUsageStats
)
from app.modules.video.models import VideoUsageLog, Video, VideoStatus


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def usage_tracker(mock_db):
    """Create VideoUsageTracker instance."""
    return VideoUsageTracker(mock_db)


@pytest.fixture
def mock_video():
    """Create mock Video object."""
    video = Video(
        id=uuid4(),
        user_id=uuid4(),
        title="Test Video",
        status=VideoStatus.IN_LIBRARY.value,
        file_path="videos/user/video.mp4",
        file_size=1024,
        duration=120,
        streaming_count=0,
        total_streaming_duration=0,
        is_used_for_streaming=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return video


@pytest.fixture
def mock_usage_log():
    """Create mock VideoUsageLog object."""
    log = VideoUsageLog(
        id=uuid4(),
        video_id=uuid4(),
        usage_type="live_stream",
        started_at=datetime.utcnow(),
        ended_at=None,
        usage_metadata={"stream_job_id": str(uuid4())}
    )
    return log


@pytest.mark.asyncio
class TestVideoUsageTracker:
    """Test VideoUsageTracker methods."""

    async def test_log_youtube_upload_success(
        self,
        usage_tracker,
        mock_db,
        mock_video
    ):
        """Test logging YouTube upload."""
        video_id = mock_video.id
        youtube_id = "abc123"
        account_id = uuid4()
        duration = 300
        
        # Mock video query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        usage_log = await usage_tracker.log_youtube_upload(
            video_id=video_id,
            youtube_id=youtube_id,
            account_id=account_id,
            duration=duration
        )
        
        # Verify usage log was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify video last_accessed_at was updated
        assert mock_video.last_accessed_at is not None

    async def test_log_youtube_upload_metadata(
        self,
        usage_tracker,
        mock_db,
        mock_video
    ):
        """Test YouTube upload log metadata."""
        video_id = mock_video.id
        youtube_id = "xyz789"
        account_id = uuid4()
        duration = 180
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        # Capture the usage log that was added
        added_log = None
        def capture_add(obj):
            nonlocal added_log
            if isinstance(obj, VideoUsageLog):
                added_log = obj
        
        mock_db.add.side_effect = capture_add
        
        await usage_tracker.log_youtube_upload(
            video_id=video_id,
            youtube_id=youtube_id,
            account_id=account_id,
            duration=duration
        )
        
        # Verify metadata
        assert added_log is not None
        assert added_log.usage_type == "youtube_upload"
        assert added_log.usage_metadata["youtube_id"] == youtube_id
        assert added_log.usage_metadata["account_id"] == str(account_id)
        assert added_log.usage_metadata["upload_duration"] == duration

    async def test_log_streaming_start_success(
        self,
        usage_tracker,
        mock_db,
        mock_video
    ):
        """Test logging streaming session start."""
        video_id = mock_video.id
        stream_job_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        usage_log = await usage_tracker.log_streaming_start(
            video_id=video_id,
            stream_job_id=stream_job_id
        )
        
        # Verify usage log was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify video statistics were updated
        assert mock_video.is_used_for_streaming is True
        assert mock_video.streaming_count == 1
        assert mock_video.last_streamed_at is not None
        assert mock_video.last_accessed_at is not None

    async def test_log_streaming_start_increments_count(
        self,
        usage_tracker,
        mock_db,
        mock_video
    ):
        """Test streaming count increments correctly."""
        video_id = mock_video.id
        stream_job_id = uuid4()
        
        # Set initial count
        mock_video.streaming_count = 5
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        mock_db.execute.return_value = mock_result
        
        await usage_tracker.log_streaming_start(
            video_id=video_id,
            stream_job_id=stream_job_id
        )
        
        # Verify count was incremented
        assert mock_video.streaming_count == 6

    async def test_log_streaming_end_success(
        self,
        usage_tracker,
        mock_db,
        mock_video,
        mock_usage_log
    ):
        """Test logging streaming session end."""
        log_id = mock_usage_log.id
        duration = 3600
        viewer_count = 150
        
        # Mock usage log query
        mock_log_result = MagicMock()
        mock_log_result.scalar_one_or_none.return_value = mock_usage_log
        
        # Mock video query
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = mock_video
        
        # Mock active sessions count query (no other active sessions)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [
            mock_log_result,
            mock_video_result,
            mock_count_result
        ]
        
        usage_log = await usage_tracker.log_streaming_end(
            log_id=log_id,
            duration=duration,
            viewer_count=viewer_count
        )
        
        # Verify usage log was updated
        assert mock_usage_log.ended_at is not None
        assert mock_usage_log.usage_metadata["stream_duration"] == duration
        assert mock_usage_log.usage_metadata["viewer_count"] == viewer_count
        
        # Verify video statistics were updated
        assert mock_video.total_streaming_duration == duration
        assert mock_video.is_used_for_streaming is False  # No other active sessions

    async def test_log_streaming_end_with_active_sessions(
        self,
        usage_tracker,
        mock_db,
        mock_video,
        mock_usage_log
    ):
        """Test ending stream when other sessions are active."""
        log_id = mock_usage_log.id
        duration = 1800
        
        # Set initial state - video is currently being used for streaming
        mock_video.is_used_for_streaming = True
        
        mock_log_result = MagicMock()
        mock_log_result.scalar_one_or_none.return_value = mock_usage_log
        
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = mock_video
        
        # Mock active sessions count (2 other active sessions)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        
        mock_db.execute.side_effect = [
            mock_log_result,
            mock_video_result,
            mock_count_result
        ]
        
        await usage_tracker.log_streaming_end(
            log_id=log_id,
            duration=duration
        )
        
        # Video should still be marked as in use
        assert mock_video.is_used_for_streaming is True

    async def test_log_streaming_end_not_found(
        self,
        usage_tracker,
        mock_db
    ):
        """Test ending non-existent streaming session."""
        log_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError) as exc_info:
            await usage_tracker.log_streaming_end(
                log_id=log_id,
                duration=100
            )
        
        assert "not found" in str(exc_info.value)

    async def test_log_streaming_end_updates_total_duration(
        self,
        usage_tracker,
        mock_db,
        mock_video,
        mock_usage_log
    ):
        """Test total streaming duration accumulation."""
        log_id = mock_usage_log.id
        duration = 2400
        
        # Set initial duration
        mock_video.total_streaming_duration = 1000
        
        mock_log_result = MagicMock()
        mock_log_result.scalar_one_or_none.return_value = mock_usage_log
        
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = mock_video
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [
            mock_log_result,
            mock_video_result,
            mock_count_result
        ]
        
        await usage_tracker.log_streaming_end(
            log_id=log_id,
            duration=duration
        )
        
        # Verify duration was added
        assert mock_video.total_streaming_duration == 3400

    async def test_get_usage_stats_success(
        self,
        usage_tracker,
        mock_db,
        mock_video
    ):
        """Test getting usage statistics."""
        video_id = mock_video.id
        
        # Mock YouTube uploads count
        mock_youtube_result = MagicMock()
        mock_youtube_result.scalar.return_value = 3
        
        # Mock streaming sessions count
        mock_streaming_result = MagicMock()
        mock_streaming_result.scalar.return_value = 5
        
        # Mock video query
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = mock_video
        
        # Mock last used timestamp
        last_used = datetime.utcnow()
        mock_last_used_result = MagicMock()
        mock_last_used_result.scalar_one_or_none.return_value = last_used
        
        mock_db.execute.side_effect = [
            mock_youtube_result,
            mock_streaming_result,
            mock_video_result,
            mock_last_used_result
        ]
        
        stats = await usage_tracker.get_usage_stats(
            video_id=video_id,
            include_logs=False
        )
        
        assert stats.youtube_uploads == 3
        assert stats.streaming_sessions == 5
        assert stats.total_streaming_duration == mock_video.total_streaming_duration
        assert stats.last_used_at == last_used
        assert len(stats.usage_logs) == 0

    async def test_get_usage_stats_with_logs(
        self,
        usage_tracker,
        mock_db,
        mock_video,
        mock_usage_log
    ):
        """Test getting usage statistics with logs."""
        video_id = mock_video.id
        
        mock_youtube_result = MagicMock()
        mock_youtube_result.scalar.return_value = 1
        
        mock_streaming_result = MagicMock()
        mock_streaming_result.scalar.return_value = 1
        
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = mock_video
        
        mock_last_used_result = MagicMock()
        mock_last_used_result.scalar_one_or_none.return_value = datetime.utcnow()
        
        # Mock logs query
        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value.all.return_value = [mock_usage_log]
        
        mock_db.execute.side_effect = [
            mock_youtube_result,
            mock_streaming_result,
            mock_video_result,
            mock_last_used_result,
            mock_logs_result
        ]
        
        stats = await usage_tracker.get_usage_stats(
            video_id=video_id,
            include_logs=True
        )
        
        assert len(stats.usage_logs) == 1
        assert stats.usage_logs[0] == mock_usage_log

    async def test_get_usage_stats_no_data(
        self,
        usage_tracker,
        mock_db
    ):
        """Test getting stats for video with no usage."""
        video_id = uuid4()
        
        mock_youtube_result = MagicMock()
        mock_youtube_result.scalar.return_value = 0
        
        mock_streaming_result = MagicMock()
        mock_streaming_result.scalar.return_value = 0
        
        mock_video_result = MagicMock()
        mock_video_result.scalar_one_or_none.return_value = None
        
        mock_last_used_result = MagicMock()
        mock_last_used_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_youtube_result,
            mock_streaming_result,
            mock_video_result,
            mock_last_used_result
        ]
        
        stats = await usage_tracker.get_usage_stats(
            video_id=video_id,
            include_logs=False
        )
        
        assert stats.youtube_uploads == 0
        assert stats.streaming_sessions == 0
        assert stats.total_streaming_duration == 0
        assert stats.last_used_at is None

    async def test_get_streaming_history(
        self,
        usage_tracker,
        mock_db,
        mock_usage_log
    ):
        """Test getting streaming history."""
        video_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_usage_log]
        mock_db.execute.return_value = mock_result
        
        logs = await usage_tracker.get_streaming_history(
            video_id=video_id,
            limit=10
        )
        
        assert len(logs) == 1
        assert logs[0] == mock_usage_log

    async def test_get_streaming_history_with_limit(
        self,
        usage_tracker,
        mock_db
    ):
        """Test streaming history respects limit."""
        video_id = uuid4()
        
        # Create multiple logs
        logs = [MagicMock(spec=VideoUsageLog) for _ in range(5)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = logs[:3]
        mock_db.execute.return_value = mock_result
        
        result = await usage_tracker.get_streaming_history(
            video_id=video_id,
            limit=3
        )
        
        assert len(result) == 3

    async def test_get_youtube_upload_history(
        self,
        usage_tracker,
        mock_db
    ):
        """Test getting YouTube upload history."""
        video_id = uuid4()
        
        log = VideoUsageLog(
            id=uuid4(),
            video_id=video_id,
            usage_type="youtube_upload",
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
            usage_metadata={"youtube_id": "abc123"}
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [log]
        mock_db.execute.return_value = mock_result
        
        logs = await usage_tracker.get_youtube_upload_history(
            video_id=video_id,
            limit=10
        )
        
        assert len(logs) == 1
        assert logs[0].usage_type == "youtube_upload"

    async def test_is_video_in_use_true(
        self,
        usage_tracker,
        mock_db
    ):
        """Test checking if video is in use (active sessions)."""
        video_id = uuid4()
        
        # Mock active sessions count (2 active)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute.return_value = mock_result
        
        in_use = await usage_tracker.is_video_in_use(video_id)
        
        assert in_use is True

    async def test_is_video_in_use_false(
        self,
        usage_tracker,
        mock_db
    ):
        """Test checking if video is not in use."""
        video_id = uuid4()
        
        # Mock no active sessions
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result
        
        in_use = await usage_tracker.is_video_in_use(video_id)
        
        assert in_use is False

    async def test_is_video_in_use_none_result(
        self,
        usage_tracker,
        mock_db
    ):
        """Test checking video usage with None result."""
        video_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result
        
        in_use = await usage_tracker.is_video_in_use(video_id)
        
        assert in_use is False


class TestVideoUsageStats:
    """Test VideoUsageStats data class."""

    def test_usage_stats_defaults(self):
        """Test default values."""
        stats = VideoUsageStats()
        
        assert stats.youtube_uploads == 0
        assert stats.streaming_sessions == 0
        assert stats.total_streaming_duration == 0
        assert stats.last_used_at is None
        assert stats.usage_logs == []

    def test_usage_stats_with_values(self):
        """Test with provided values."""
        last_used = datetime.utcnow()
        logs = [MagicMock(spec=VideoUsageLog)]
        
        stats = VideoUsageStats(
            youtube_uploads=5,
            streaming_sessions=10,
            total_streaming_duration=36000,
            last_used_at=last_used,
            usage_logs=logs
        )
        
        assert stats.youtube_uploads == 5
        assert stats.streaming_sessions == 10
        assert stats.total_streaming_duration == 36000
        assert stats.last_used_at == last_used
        assert len(stats.usage_logs) == 1
