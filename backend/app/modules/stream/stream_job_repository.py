"""Stream Job Repository for database operations.

Implements CRUD operations for StreamJob and StreamJobHealth models.
Requirements: 1.1, 1.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import utcnow, to_naive_utc
from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobHealth,
    StreamJobStatus,
    LoopMode,
)


class StreamJobRepository:
    """Repository for StreamJob database operations.
    
    Requirements: 1.1, 1.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ============================================
    # Create Operations
    # ============================================

    async def create(self, stream_job: StreamJob) -> StreamJob:
        """Create a new stream job.
        
        Args:
            stream_job: StreamJob instance to create
            
        Returns:
            StreamJob: Created stream job with ID
        """
        self.session.add(stream_job)
        await self.session.commit()
        await self.session.refresh(stream_job)
        return stream_job

    # ============================================
    # Read Operations
    # ============================================

    async def get_by_id(
        self, 
        job_id: uuid.UUID,
        include_health: bool = False
    ) -> Optional[StreamJob]:
        """Get stream job by ID.
        
        Args:
            job_id: Stream job UUID
            include_health: Whether to include health logs
            
        Returns:
            Optional[StreamJob]: Stream job or None
        """
        query = select(StreamJob).where(StreamJob.id == job_id)
        
        if include_health:
            query = query.options(selectinload(StreamJob.health_logs))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[StreamJob], int]:
        """Get stream jobs for a user with pagination.
        
        Args:
            user_id: User UUID
            status: Optional status filter
            account_id: Optional account filter
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJob], int]: Jobs and total count
        """
        # Build base query
        query = select(StreamJob).where(StreamJob.user_id == user_id)
        count_query = select(func.count(StreamJob.id)).where(StreamJob.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.where(StreamJob.status == status)
            count_query = count_query.where(StreamJob.status == status)
        
        if account_id:
            query = query.where(StreamJob.account_id == account_id)
            count_query = count_query.where(StreamJob.account_id == account_id)
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(StreamJob.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        jobs = result.scalars().all()
        
        return jobs, total

    async def get_active_jobs(self, user_id: Optional[uuid.UUID] = None) -> Sequence[StreamJob]:
        """Get all active stream jobs (starting, running, stopping).
        
        Args:
            user_id: Optional user filter
            
        Returns:
            Sequence[StreamJob]: Active stream jobs
        """
        active_statuses = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
            StreamJobStatus.STOPPING.value,
        ]
        
        query = select(StreamJob).where(StreamJob.status.in_(active_statuses))
        
        if user_id:
            query = query.where(StreamJob.user_id == user_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_scheduled_jobs(self, before: Optional[datetime] = None) -> Sequence[StreamJob]:
        """Get scheduled stream jobs that should start.
        
        Args:
            before: Get jobs scheduled before this time (default: now)
            
        Returns:
            Sequence[StreamJob]: Scheduled stream jobs ready to start
        """
        if before is None:
            before = to_naive_utc(utcnow())
        
        query = select(StreamJob).where(
            and_(
                StreamJob.status == StreamJobStatus.SCHEDULED.value,
                StreamJob.scheduled_start_at <= before,
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_jobs_to_stop(self) -> Sequence[StreamJob]:
        """Get running jobs that should stop based on scheduled end time.
        
        Returns:
            Sequence[StreamJob]: Jobs that should stop
        """
        now = to_naive_utc(utcnow())
        
        query = select(StreamJob).where(
            and_(
                StreamJob.status == StreamJobStatus.RUNNING.value,
                StreamJob.scheduled_end_at.isnot(None),
                StreamJob.scheduled_end_at <= now,
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_active_by_user(self, user_id: uuid.UUID) -> int:
        """Count active stream jobs for a user (for slot management).
        
        Args:
            user_id: User UUID
            
        Returns:
            int: Number of active jobs
        """
        active_statuses = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
            StreamJobStatus.STOPPING.value,
        ]
        
        query = select(func.count(StreamJob.id)).where(
            and_(
                StreamJob.user_id == user_id,
                StreamJob.status.in_(active_statuses),
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_by_stream_key(self, stream_key: str) -> Optional[StreamJob]:
        """Get active stream job using a specific stream key.
        
        Used to check if stream key is already in use.
        
        Args:
            stream_key: Stream key to check
            
        Returns:
            Optional[StreamJob]: Active job using this key or None
        """
        active_statuses = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
        ]
        
        # Note: We need to check encrypted keys, so we get all active jobs
        # and check in Python. This is not ideal but necessary for encrypted data.
        query = select(StreamJob).where(
            and_(
                StreamJob.status.in_(active_statuses),
                StreamJob.is_stream_key_locked == True,
            )
        )
        
        result = await self.session.execute(query)
        jobs = result.scalars().all()
        
        for job in jobs:
            if job.stream_key == stream_key:
                return job
        
        return None

    # ============================================
    # Update Operations
    # ============================================

    async def update(self, stream_job: StreamJob) -> StreamJob:
        """Update a stream job.
        
        Args:
            stream_job: StreamJob instance to update
            
        Returns:
            StreamJob: Updated stream job
        """
        await self.session.commit()
        await self.session.refresh(stream_job)
        return stream_job

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: StreamJobStatus,
        error: Optional[str] = None,
    ) -> Optional[StreamJob]:
        """Update stream job status.
        
        Args:
            job_id: Stream job UUID
            status: New status
            error: Optional error message
            
        Returns:
            Optional[StreamJob]: Updated job or None
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        job.status = status.value
        if error:
            job.last_error = error
        
        # Update timing based on status
        now = to_naive_utc(utcnow())
        if status == StreamJobStatus.RUNNING:
            job.actual_start_at = now
            job.is_stream_key_locked = True
        elif status in [
            StreamJobStatus.STOPPED,
            StreamJobStatus.COMPLETED,
            StreamJobStatus.FAILED,
        ]:
            job.actual_end_at = now
            job.is_stream_key_locked = False
            job.update_total_duration()
        
        return await self.update(job)

    async def update_metrics(
        self,
        job_id: uuid.UUID,
        bitrate: Optional[int] = None,
        fps: Optional[float] = None,
        speed: Optional[str] = None,
        dropped_frames: Optional[int] = None,
        frame_count: Optional[int] = None,
    ) -> Optional[StreamJob]:
        """Update stream job metrics from FFmpeg output.
        
        Args:
            job_id: Stream job UUID
            bitrate: Current bitrate in bps
            fps: Current FPS
            speed: Current speed (e.g., "1.0x")
            dropped_frames: Total dropped frames
            frame_count: Total frame count
            
        Returns:
            Optional[StreamJob]: Updated job or None
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        if bitrate is not None:
            job.current_bitrate = bitrate
        if fps is not None:
            job.current_fps = fps
        if speed is not None:
            job.current_speed = speed
        if dropped_frames is not None:
            job.dropped_frames = dropped_frames
        if frame_count is not None:
            job.frame_count = frame_count
        
        return await self.update(job)

    async def increment_loop(self, job_id: uuid.UUID) -> Optional[StreamJob]:
        """Increment loop counter for a stream job.
        
        Args:
            job_id: Stream job UUID
            
        Returns:
            Optional[StreamJob]: Updated job or None
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        job.increment_loop()
        return await self.update(job)

    async def increment_restart_count(self, job_id: uuid.UUID) -> Optional[StreamJob]:
        """Increment restart counter for a stream job.
        
        Args:
            job_id: Stream job UUID
            
        Returns:
            Optional[StreamJob]: Updated job or None
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        job.restart_count += 1
        return await self.update(job)

    # ============================================
    # Delete Operations
    # ============================================

    async def delete(self, job_id: uuid.UUID) -> bool:
        """Delete a stream job.
        
        Args:
            job_id: Stream job UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        job = await self.get_by_id(job_id)
        if not job:
            return False
        
        await self.session.delete(job)
        await self.session.commit()
        return True


class StreamJobHealthRepository:
    """Repository for StreamJobHealth database operations.
    
    Requirements: 4.2, 4.7
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ============================================
    # Create Operations
    # ============================================

    async def create(self, health: StreamJobHealth) -> StreamJobHealth:
        """Create a new health record.
        
        Args:
            health: StreamJobHealth instance to create
            
        Returns:
            StreamJobHealth: Created health record
        """
        # Evaluate health thresholds before saving
        health.evaluate_health()
        
        self.session.add(health)
        await self.session.commit()
        await self.session.refresh(health)
        return health

    # ============================================
    # Read Operations
    # ============================================

    async def get_latest(self, job_id: uuid.UUID) -> Optional[StreamJobHealth]:
        """Get latest health record for a stream job.
        
        Args:
            job_id: Stream job UUID
            
        Returns:
            Optional[StreamJobHealth]: Latest health record or None
        """
        query = (
            select(StreamJobHealth)
            .where(StreamJobHealth.stream_job_id == job_id)
            .order_by(StreamJobHealth.collected_at.desc())
            .limit(1)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_history(
        self,
        job_id: uuid.UUID,
        hours: int = 24,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[Sequence[StreamJobHealth], int]:
        """Get health history for a stream job.
        
        Args:
            job_id: Stream job UUID
            hours: Number of hours to look back
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJobHealth], int]: Health records and total count
        """
        since = to_naive_utc(utcnow()) - timedelta(hours=hours)
        
        # Build base query
        base_filter = and_(
            StreamJobHealth.stream_job_id == job_id,
            StreamJobHealth.collected_at >= since,
        )
        
        # Get total count
        count_query = select(func.count(StreamJobHealth.id)).where(base_filter)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = (
            select(StreamJobHealth)
            .where(base_filter)
            .order_by(StreamJobHealth.collected_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        return records, total

    async def get_alerts(
        self,
        job_id: uuid.UUID,
        unacknowledged_only: bool = False,
    ) -> Sequence[StreamJobHealth]:
        """Get health records with alerts for a stream job.
        
        Args:
            job_id: Stream job UUID
            unacknowledged_only: Only return unacknowledged alerts
            
        Returns:
            Sequence[StreamJobHealth]: Health records with alerts
        """
        query = select(StreamJobHealth).where(
            and_(
                StreamJobHealth.stream_job_id == job_id,
                StreamJobHealth.alert_type.isnot(None),
            )
        )
        
        if unacknowledged_only:
            query = query.where(StreamJobHealth.is_alert_acknowledged == False)
        
        query = query.order_by(StreamJobHealth.collected_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()

    # ============================================
    # Update Operations
    # ============================================

    async def acknowledge_alert(self, health_id: uuid.UUID) -> Optional[StreamJobHealth]:
        """Acknowledge a health alert.
        
        Args:
            health_id: Health record UUID
            
        Returns:
            Optional[StreamJobHealth]: Updated record or None
        """
        query = select(StreamJobHealth).where(StreamJobHealth.id == health_id)
        result = await self.session.execute(query)
        health = result.scalar_one_or_none()
        
        if not health:
            return None
        
        health.is_alert_acknowledged = True
        await self.session.commit()
        await self.session.refresh(health)
        return health

    # ============================================
    # Delete Operations
    # ============================================

    async def delete_old_records(self, days: int = 30) -> int:
        """Delete health records older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            int: Number of deleted records
        """
        cutoff = to_naive_utc(utcnow()) - timedelta(days=days)
        
        # Get count first
        count_query = select(func.count(StreamJobHealth.id)).where(
            StreamJobHealth.collected_at < cutoff
        )
        count_result = await self.session.execute(count_query)
        count = count_result.scalar() or 0
        
        # Delete old records
        from sqlalchemy import delete
        delete_query = delete(StreamJobHealth).where(
            StreamJobHealth.collected_at < cutoff
        )
        await self.session.execute(delete_query)
        await self.session.commit()
        
        return count

    async def get_statistics_for_job(
        self,
        job_id: uuid.UUID,
    ) -> dict:
        """Get aggregated statistics for a stream job.
        
        Requirements: 12.1
        
        Args:
            job_id: Stream job UUID
            
        Returns:
            dict: Aggregated statistics
        """
        query = select(
            func.avg(StreamJobHealth.bitrate).label("avg_bitrate"),
            func.avg(StreamJobHealth.fps).label("avg_fps"),
            func.max(StreamJobHealth.dropped_frames).label("total_dropped_frames"),
            func.max(StreamJobHealth.cpu_percent).label("peak_cpu"),
            func.max(StreamJobHealth.memory_mb).label("peak_memory"),
            func.count(StreamJobHealth.id).label("record_count"),
        ).where(StreamJobHealth.stream_job_id == job_id)
        
        result = await self.session.execute(query)
        row = result.one_or_none()
        
        if not row:
            return {
                "avg_bitrate_kbps": 0,
                "avg_fps": 0,
                "total_dropped_frames": 0,
                "peak_cpu_percent": 0,
                "peak_memory_mb": 0,
            }
        
        return {
            "avg_bitrate_kbps": (row.avg_bitrate or 0) / 1000,
            "avg_fps": row.avg_fps or 0,
            "total_dropped_frames": row.total_dropped_frames or 0,
            "peak_cpu_percent": row.peak_cpu or 0,
            "peak_memory_mb": row.peak_memory or 0,
        }


class StreamJobAnalyticsRepository:
    """Repository for stream job analytics and history.
    
    Requirements: 12.1, 12.2, 12.3, 12.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_history(
        self,
        user_id: uuid.UUID,
        days: int = 30,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[StreamJob], int]:
        """Get stream job history for a user.
        
        Requirements: 12.2
        
        Args:
            user_id: User UUID
            days: Number of days to look back
            page: Page number
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJob], int]: Jobs and total count
        """
        since = to_naive_utc(utcnow()) - timedelta(days=days)
        
        # Only get completed/stopped/failed jobs
        finished_statuses = [
            StreamJobStatus.STOPPED.value,
            StreamJobStatus.COMPLETED.value,
            StreamJobStatus.FAILED.value,
        ]
        
        base_filter = and_(
            StreamJob.user_id == user_id,
            StreamJob.status.in_(finished_statuses),
            StreamJob.actual_end_at >= since,
        )
        
        # Get total count
        count_query = select(func.count(StreamJob.id)).where(base_filter)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = (
            select(StreamJob)
            .where(base_filter)
            .order_by(StreamJob.actual_end_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(query)
        jobs = result.scalars().all()
        
        return jobs, total

    async def get_analytics_summary(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> dict:
        """Get analytics summary for a user.
        
        Requirements: 12.5
        
        Args:
            user_id: User UUID
            days: Number of days to analyze
            
        Returns:
            dict: Analytics summary
        """
        since = to_naive_utc(utcnow()) - timedelta(days=days)
        
        # Get aggregate statistics
        query = select(
            func.count(StreamJob.id).label("total_streams"),
            func.sum(StreamJob.total_duration_seconds).label("total_duration"),
            func.sum(StreamJob.current_loop).label("total_loops"),
            func.avg(StreamJob.total_duration_seconds).label("avg_duration"),
            func.avg(StreamJob.current_bitrate).label("avg_bitrate"),
        ).where(
            and_(
                StreamJob.user_id == user_id,
                StreamJob.created_at >= since,
            )
        )
        
        result = await self.session.execute(query)
        row = result.one_or_none()
        
        total_streams = row.total_streams or 0 if row else 0
        total_duration = row.total_duration or 0 if row else 0
        total_loops = row.total_loops or 0 if row else 0
        avg_duration = row.avg_duration or 0 if row else 0
        avg_bitrate = row.avg_bitrate or 0 if row else 0
        
        # Calculate data transferred (bitrate * duration)
        total_data_gb = (avg_bitrate * total_duration) / (8 * 1024 * 1024 * 1024) if avg_bitrate else 0
        
        # Get streams by day
        streams_by_day = await self._get_streams_by_day(user_id, days)
        duration_by_day = await self._get_duration_by_day(user_id, days)
        
        return {
            "total_streams": total_streams,
            "total_duration_hours": total_duration / 3600,
            "total_loops_completed": total_loops,
            "avg_stream_duration_minutes": avg_duration / 60,
            "avg_bitrate_kbps": avg_bitrate / 1000 if avg_bitrate else 0,
            "total_data_transferred_gb": total_data_gb,
            "streams_by_day": streams_by_day,
            "duration_by_day": duration_by_day,
        }

    async def _get_streams_by_day(
        self,
        user_id: uuid.UUID,
        days: int,
    ) -> list[dict]:
        """Get stream count by day.
        
        Args:
            user_id: User UUID
            days: Number of days
            
        Returns:
            list[dict]: [{date, count}]
        """
        since = to_naive_utc(utcnow()) - timedelta(days=days)
        
        query = select(
            func.date(StreamJob.created_at).label("date"),
            func.count(StreamJob.id).label("count"),
        ).where(
            and_(
                StreamJob.user_id == user_id,
                StreamJob.created_at >= since,
            )
        ).group_by(func.date(StreamJob.created_at)).order_by(func.date(StreamJob.created_at))
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [{"date": str(row.date), "count": row.count} for row in rows]

    async def _get_duration_by_day(
        self,
        user_id: uuid.UUID,
        days: int,
    ) -> list[dict]:
        """Get total duration by day.
        
        Args:
            user_id: User UUID
            days: Number of days
            
        Returns:
            list[dict]: [{date, hours}]
        """
        since = to_naive_utc(utcnow()) - timedelta(days=days)
        
        query = select(
            func.date(StreamJob.created_at).label("date"),
            func.sum(StreamJob.total_duration_seconds).label("duration"),
        ).where(
            and_(
                StreamJob.user_id == user_id,
                StreamJob.created_at >= since,
            )
        ).group_by(func.date(StreamJob.created_at)).order_by(func.date(StreamJob.created_at))
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [{"date": str(row.date), "hours": (row.duration or 0) / 3600} for row in rows]

    async def export_to_csv_data(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> list[dict]:
        """Get stream job data for CSV export.
        
        Requirements: 12.4
        
        Args:
            user_id: User UUID
            days: Number of days
            
        Returns:
            list[dict]: List of job data for CSV
        """
        since = to_naive_utc(utcnow()) - timedelta(days=days)
        
        query = (
            select(StreamJob)
            .where(
                and_(
                    StreamJob.user_id == user_id,
                    StreamJob.created_at >= since,
                )
            )
            .order_by(StreamJob.created_at.desc())
        )
        
        result = await self.session.execute(query)
        jobs = result.scalars().all()
        
        return [
            {
                "id": str(job.id),
                "title": job.title,
                "status": job.status,
                "loop_mode": job.loop_mode,
                "resolution": job.resolution,
                "target_bitrate_kbps": job.target_bitrate,
                "target_fps": job.target_fps,
                "total_loops": job.current_loop,
                "total_duration_seconds": job.total_duration_seconds,
                "total_duration_hours": job.total_duration_seconds / 3600,
                "dropped_frames": job.dropped_frames,
                "restart_count": job.restart_count,
                "actual_start_at": job.actual_start_at.isoformat() if job.actual_start_at else "",
                "actual_end_at": job.actual_end_at.isoformat() if job.actual_end_at else "",
                "created_at": job.created_at.isoformat() if job.created_at else "",
            }
            for job in jobs
        ]
