"""Video Usage Tracker for tracking video usage.

Tracks how videos are used (YouTube uploads, streaming sessions).
Requirements: 1.3, 4.2
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import VideoUsageLog, Video


class VideoUsageStats:
    """Video usage statistics."""
    
    def __init__(
        self,
        youtube_uploads: int = 0,
        streaming_sessions: int = 0,
        total_streaming_duration: int = 0,
        last_used_at: Optional[datetime] = None,
        usage_logs: list[VideoUsageLog] = None
    ):
        self.youtube_uploads = youtube_uploads
        self.streaming_sessions = streaming_sessions
        self.total_streaming_duration = total_streaming_duration
        self.last_used_at = last_used_at
        self.usage_logs = usage_logs or []


class VideoUsageTracker:
    """Service for tracking video usage.
    
    Handles:
    - Logging YouTube uploads
    - Logging streaming sessions
    - Getting usage statistics
    - Updating video usage counters
    """

    def __init__(self, db: AsyncSession):
        """Initialize video usage tracker.
        
        Args:
            db: Database session
        """
        self.db = db

    async def log_youtube_upload(
        self,
        video_id: UUID,
        youtube_id: str,
        account_id: UUID,
        duration: int
    ) -> VideoUsageLog:
        """Log YouTube upload.
        
        Args:
            video_id: Video identifier
            youtube_id: YouTube video ID
            account_id: YouTube account used
            duration: Upload duration in seconds
            
        Returns:
            VideoUsageLog: Created usage log
        """
        # Create usage log
        usage_log = VideoUsageLog(
            video_id=video_id,
            usage_type="youtube_upload",
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
            usage_metadata={
                "youtube_id": youtube_id,
                "account_id": str(account_id),
                "upload_duration": duration
            }
        )
        
        self.db.add(usage_log)
        
        # Update video statistics
        query = select(Video).where(Video.id == video_id)
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if video:
            video.last_accessed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        return usage_log

    async def log_streaming_start(
        self,
        video_id: UUID,
        stream_job_id: UUID
    ) -> VideoUsageLog:
        """Log streaming session start.
        
        Args:
            video_id: Video identifier
            stream_job_id: Stream job identifier
            
        Returns:
            VideoUsageLog: Created usage log
        """
        # Create usage log
        usage_log = VideoUsageLog(
            video_id=video_id,
            usage_type="live_stream",
            started_at=datetime.utcnow(),
            ended_at=None,  # Will be set when stream ends
            usage_metadata={
                "stream_job_id": str(stream_job_id)
            }
        )
        
        self.db.add(usage_log)
        
        # Update video statistics
        query = select(Video).where(Video.id == video_id)
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if video:
            video.is_used_for_streaming = True
            video.streaming_count += 1
            video.last_streamed_at = datetime.utcnow()
            video.last_accessed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        return usage_log

    async def log_streaming_end(
        self,
        log_id: UUID,
        duration: int,
        viewer_count: int = 0
    ) -> VideoUsageLog:
        """Log streaming session end.
        
        Args:
            log_id: Usage log identifier
            duration: Stream duration in seconds
            viewer_count: Total viewer count
            
        Returns:
            VideoUsageLog: Updated usage log
        """
        # Get usage log
        query = select(VideoUsageLog).where(VideoUsageLog.id == log_id)
        result = await self.db.execute(query)
        usage_log = result.scalar_one_or_none()
        
        if not usage_log:
            raise ValueError(f"Usage log {log_id} not found")
        
        # Update usage log
        usage_log.ended_at = datetime.utcnow()
        if usage_log.usage_metadata is None:
            usage_log.usage_metadata = {}
        usage_log.usage_metadata["stream_duration"] = duration
        usage_log.usage_metadata["viewer_count"] = viewer_count
        
        # Update video statistics
        query = select(Video).where(Video.id == usage_log.video_id)
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if video:
            video.total_streaming_duration += duration
            video.last_accessed_at = datetime.utcnow()
            
            # Check if video is still being used for streaming
            # (check if there are other active streaming sessions)
            active_query = select(func.count()).select_from(VideoUsageLog).where(
                VideoUsageLog.video_id == video.id,
                VideoUsageLog.usage_type == "live_stream",
                VideoUsageLog.ended_at.is_(None),
                VideoUsageLog.id != log_id
            )
            active_result = await self.db.execute(active_query)
            active_count = active_result.scalar() or 0
            
            if active_count == 0:
                video.is_used_for_streaming = False
        
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        return usage_log

    async def get_usage_stats(
        self,
        video_id: UUID,
        include_logs: bool = False
    ) -> VideoUsageStats:
        """Get usage statistics for video.
        
        Args:
            video_id: Video identifier
            include_logs: Whether to include usage logs
            
        Returns:
            VideoUsageStats: Usage statistics
        """
        # Count YouTube uploads
        youtube_query = select(func.count()).select_from(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "youtube_upload"
        )
        youtube_result = await self.db.execute(youtube_query)
        youtube_uploads = youtube_result.scalar() or 0
        
        # Count streaming sessions
        streaming_query = select(func.count()).select_from(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "live_stream"
        )
        streaming_result = await self.db.execute(streaming_query)
        streaming_sessions = streaming_result.scalar() or 0
        
        # Get video for total streaming duration
        video_query = select(Video).where(Video.id == video_id)
        video_result = await self.db.execute(video_query)
        video = video_result.scalar_one_or_none()
        
        total_streaming_duration = video.total_streaming_duration if video else 0
        
        # Get last used timestamp
        last_used_query = select(VideoUsageLog.started_at).where(
            VideoUsageLog.video_id == video_id
        ).order_by(VideoUsageLog.started_at.desc()).limit(1)
        last_used_result = await self.db.execute(last_used_query)
        last_used_at = last_used_result.scalar_one_or_none()
        
        # Get usage logs if requested
        usage_logs = []
        if include_logs:
            logs_query = select(VideoUsageLog).where(
                VideoUsageLog.video_id == video_id
            ).order_by(VideoUsageLog.started_at.desc())
            logs_result = await self.db.execute(logs_query)
            usage_logs = list(logs_result.scalars().all())
        
        return VideoUsageStats(
            youtube_uploads=youtube_uploads,
            streaming_sessions=streaming_sessions,
            total_streaming_duration=total_streaming_duration,
            last_used_at=last_used_at,
            usage_logs=usage_logs
        )

    async def get_streaming_history(
        self,
        video_id: UUID,
        limit: int = 10
    ) -> list[VideoUsageLog]:
        """Get streaming history for video.
        
        Args:
            video_id: Video identifier
            limit: Maximum number of logs to return
            
        Returns:
            list[VideoUsageLog]: Streaming usage logs
        """
        query = select(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "live_stream"
        ).order_by(VideoUsageLog.started_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs)

    async def get_youtube_upload_history(
        self,
        video_id: UUID,
        limit: int = 10
    ) -> list[VideoUsageLog]:
        """Get YouTube upload history for video.
        
        Args:
            video_id: Video identifier
            limit: Maximum number of logs to return
            
        Returns:
            list[VideoUsageLog]: YouTube upload usage logs
        """
        query = select(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "youtube_upload"
        ).order_by(VideoUsageLog.started_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs)

    async def is_video_in_use(self, video_id: UUID) -> bool:
        """Check if video is currently being used for streaming.
        
        Args:
            video_id: Video identifier
            
        Returns:
            bool: True if video is in use
        """
        # Check for active streaming sessions
        query = select(func.count()).select_from(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "live_stream",
            VideoUsageLog.ended_at.is_(None)
        )
        
        result = await self.db.execute(query)
        active_count = result.scalar() or 0
        
        return active_count > 0
