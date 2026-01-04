"""Video Library Integration for Stream Jobs.

Integrates stream job creation with video library system.
Requirements: 3.1, 3.2, 3.3, 4.2
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.datetime_utils import utcnow, to_naive_utc
from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
from app.modules.stream.stream_job_service import StreamJobService
from app.modules.stream.stream_job_schemas import CreateStreamJobRequest
from app.modules.video.models import Video, VideoStatus
from app.modules.video.video_usage_tracker import VideoUsageTracker
from app.core.storage import get_storage


class VideoLibraryStreamIntegration:
    """Integration service for creating streams from video library.
    
    Requirements: 3.1, 3.2, 3.3
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize integration service.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.stream_service = StreamJobService(session)
        self.usage_tracker = VideoUsageTracker(session)
        self.storage = get_storage()
    
    async def create_stream_from_video(
        self,
        user_id: uuid.UUID,
        video_id: uuid.UUID,
        request: CreateStreamJobRequest,
    ) -> StreamJob:
        """Create a stream job from a video in the library.
        
        Requirements: 3.1
        
        Args:
            user_id: User UUID
            video_id: Video UUID from library
            request: Stream job creation request
            
        Returns:
            StreamJob: Created stream job
            
        Raises:
            ValueError: If video not found or not accessible
        """
        # Get video from library
        video = await self._get_video(video_id, user_id)
        
        if not video:
            raise ValueError(f"Video {video_id} not found or not accessible")
        
        if not video.file_path:
            raise ValueError(f"Video {video_id} has no file path")
        
        # Get actual file path from storage
        video_path = await self._get_video_file_path(video)
        
        # Update request with video information
        request.video_id = video_id
        request.video_path = video_path
        
        # If title not provided, use video title
        if not request.title:
            request.title = f"Stream: {video.title}"
        
        # Create stream job
        stream_job = await self.stream_service.create_stream_job(
            user_id=user_id,
            request=request,
        )
        
        # Track video usage
        await self.usage_tracker.log_streaming_start(
            video_id=video_id,
            stream_job_id=stream_job.id,
        )
        
        # Update video status
        await self._update_video_streaming_status(video, is_streaming=True)
        
        return stream_job
    
    async def on_stream_start(
        self,
        stream_job: StreamJob,
    ) -> None:
        """Handle stream start event.
        
        Requirements: 3.2, 4.2
        
        Args:
            stream_job: Stream job that started
        """
        if not stream_job.video_id:
            return
        
        # Get video
        video = await self._get_video(stream_job.video_id, stream_job.user_id)
        if not video:
            return
        
        # Update video streaming status
        await self._update_video_streaming_status(video, is_streaming=True)
        
        # Update last streamed timestamp
        video.last_streamed_at = to_naive_utc(utcnow())
        await self.session.commit()
    
    async def on_stream_stop(
        self,
        stream_job: StreamJob,
    ) -> None:
        """Handle stream stop event.
        
        Requirements: 3.2, 4.2
        
        Args:
            stream_job: Stream job that stopped
        """
        if not stream_job.video_id:
            return
        
        # Get video
        video = await self._get_video(stream_job.video_id, stream_job.user_id)
        if not video:
            return
        
        # Calculate duration
        duration = stream_job.get_duration_seconds()
        
        # Log streaming end
        await self.usage_tracker.log_streaming_end(
            video_id=stream_job.video_id,
            stream_job_id=stream_job.id,
            duration=duration,
            viewer_count=0,  # TODO: Get from YouTube API if available
        )
        
        # Check if video has other active streams
        has_other_streams = await self._has_other_active_streams(
            video.id,
            exclude_job_id=stream_job.id,
        )
        
        # Update video streaming status
        if not has_other_streams:
            await self._update_video_streaming_status(video, is_streaming=False)
        
        # Update streaming count and duration
        video.streaming_count += 1
        video.total_streaming_duration += duration
        await self.session.commit()
    
    async def get_video_streaming_status(
        self,
        video_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Get streaming status for a video.
        
        Requirements: 3.3
        
        Args:
            video_id: Video UUID
            user_id: User UUID
            
        Returns:
            dict: Streaming status information
        """
        video = await self._get_video(video_id, user_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Get active streams for this video
        active_streams = await self._get_active_streams_for_video(video_id)
        
        # Get usage stats
        usage_stats = await self.usage_tracker.get_usage_stats(video_id)
        
        return {
            "video_id": str(video_id),
            "is_used_for_streaming": video.is_used_for_streaming,
            "streaming_count": video.streaming_count,
            "last_streamed_at": video.last_streamed_at.isoformat() if video.last_streamed_at else None,
            "total_streaming_duration": video.total_streaming_duration,
            "active_streams": [
                {
                    "id": str(stream.id),
                    "title": stream.title,
                    "status": stream.status,
                    "started_at": stream.actual_start_at.isoformat() if stream.actual_start_at else None,
                }
                for stream in active_streams
            ],
            "usage_stats": usage_stats,
        }
    
    # ============================================
    # Private Helper Methods
    # ============================================
    
    async def _get_video(
        self,
        video_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Video]:
        """Get video by ID with user authorization.
        
        Args:
            video_id: Video UUID
            user_id: User UUID
            
        Returns:
            Optional[Video]: Video if found and accessible
        """
        result = await self.session.execute(
            select(Video)
            .where(Video.id == video_id)
            .where(Video.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_video_file_path(self, video: Video) -> str:
        """Get actual file path for video.
        
        Args:
            video: Video instance
            
        Returns:
            str: Actual file path
            
        Raises:
            ValueError: If file path cannot be determined
        """
        if not video.file_path:
            raise ValueError(f"Video {video.id} has no file path")
        
        # If using cloud storage, get presigned URL or download path
        # For now, assume local storage
        return video.file_path
    
    async def _update_video_streaming_status(
        self,
        video: Video,
        is_streaming: bool,
    ) -> None:
        """Update video streaming status.
        
        Args:
            video: Video instance
            is_streaming: Whether video is currently streaming
        """
        video.is_used_for_streaming = is_streaming
        
        # Update video status
        if is_streaming:
            if video.status == VideoStatus.IN_LIBRARY.value:
                video.status = VideoStatus.STREAMING.value
        else:
            # Check if video was uploaded to YouTube
            if video.youtube_id:
                video.status = VideoStatus.PUBLISHED.value
            else:
                video.status = VideoStatus.IN_LIBRARY.value
        
        await self.session.commit()
    
    async def _has_other_active_streams(
        self,
        video_id: uuid.UUID,
        exclude_job_id: uuid.UUID,
    ) -> bool:
        """Check if video has other active streams.
        
        Args:
            video_id: Video UUID
            exclude_job_id: Stream job ID to exclude
            
        Returns:
            bool: True if video has other active streams
        """
        result = await self.session.execute(
            select(StreamJob)
            .where(StreamJob.video_id == video_id)
            .where(StreamJob.id != exclude_job_id)
            .where(StreamJob.status.in_([
                StreamJobStatus.STARTING.value,
                StreamJobStatus.RUNNING.value,
                StreamJobStatus.STOPPING.value,
            ]))
        )
        active_streams = result.scalars().all()
        return len(active_streams) > 0
    
    async def _get_active_streams_for_video(
        self,
        video_id: uuid.UUID,
    ) -> list[StreamJob]:
        """Get all active streams for a video.
        
        Args:
            video_id: Video UUID
            
        Returns:
            list[StreamJob]: List of active stream jobs
        """
        result = await self.session.execute(
            select(StreamJob)
            .where(StreamJob.video_id == video_id)
            .where(StreamJob.status.in_([
                StreamJobStatus.STARTING.value,
                StreamJobStatus.RUNNING.value,
                StreamJobStatus.STOPPING.value,
            ]))
        )
        return list(result.scalars().all())
