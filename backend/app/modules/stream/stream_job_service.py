"""Stream Job Service for Video-to-Live streaming business logic.

Implements stream job management, slot checking, and stream control.
Requirements: 1.1, 1.2, 1.3, 1.5, 5.5, 6.1, 6.2, 6.3, 6.4
"""

import os
import uuid
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow, ensure_utc, to_naive_utc, is_in_future
from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobHealth,
    StreamJobStatus,
    LoopMode,
)
from app.modules.stream.stream_job_repository import (
    StreamJobRepository,
    StreamJobHealthRepository,
    StreamJobAnalyticsRepository,
)
from app.modules.stream.stream_job_schemas import (
    CreateStreamJobRequest,
    UpdateStreamJobRequest,
    StreamJobResponse,
    SlotStatusResponse,
    ResourceUsageResponse,
    StreamResourceResponse,
    ResourceDashboardResponse,
)


# ============================================
# Custom Exceptions
# ============================================


class StreamJobServiceError(Exception):
    """Base exception for stream job service errors."""
    pass


class StreamJobNotFoundError(StreamJobServiceError):
    """Raised when stream job is not found."""
    pass


class VideoNotFoundError(StreamJobServiceError):
    """Raised when video file is not found."""
    pass


class AccountNotFoundError(StreamJobServiceError):
    """Raised when YouTube account is not found."""
    pass


class SlotLimitExceededError(StreamJobServiceError):
    """Raised when user has reached stream slot limit."""
    pass


class StreamKeyInUseError(StreamJobServiceError):
    """Raised when stream key is already in use."""
    pass


class InvalidStatusTransitionError(StreamJobServiceError):
    """Raised when status transition is invalid."""
    pass


class StreamNotRunningError(StreamJobServiceError):
    """Raised when trying to stop a non-running stream."""
    pass


class StreamAlreadyRunningError(StreamJobServiceError):
    """Raised when trying to start an already running stream."""
    pass


# ============================================
# Stream Job Service
# ============================================


class StreamJobService:
    """Service for stream job management operations.
    
    Requirements: 1.1, 1.2, 1.3, 1.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.job_repo = StreamJobRepository(session)
        self.health_repo = StreamJobHealthRepository(session)
        self.analytics_repo = StreamJobAnalyticsRepository(session)

    # ============================================
    # Create Operations
    # ============================================

    async def create_stream_job(
        self,
        user_id: uuid.UUID,
        request: CreateStreamJobRequest,
    ) -> StreamJob:
        """Create a new stream job.
        
        Requirements: 1.1
        
        Args:
            user_id: User UUID
            request: Create request data
            
        Returns:
            StreamJob: Created stream job
            
        Raises:
            VideoNotFoundError: If video file doesn't exist
            AccountNotFoundError: If YouTube account not found
        """
        # Convert relative path to absolute path or presigned URL
        video_path = self._resolve_video_path(request.video_path)
        
        # Validate video file/URL exists
        if not self._validate_video_source(video_path, request.video_path):
            raise VideoNotFoundError(f"Video file not found: {request.video_path}")
        
        # Validate YouTube account exists
        await self._validate_account(request.account_id, user_id)
        
        # Determine initial status
        initial_status = StreamJobStatus.PENDING.value
        if request.scheduled_start_at:
            # Use timezone-aware comparison
            if is_in_future(request.scheduled_start_at):
                initial_status = StreamJobStatus.SCHEDULED.value
        
        # Create stream job
        job = StreamJob(
            user_id=user_id,
            account_id=request.account_id,
            video_id=request.video_id,
            video_path=video_path,  # Use resolved absolute path
            playlist_id=request.playlist_id,
            rtmp_url=request.rtmp_url,
            title=request.title,
            description=request.description,
            loop_mode=request.loop_mode,
            loop_count=request.loop_count,
            resolution=request.resolution,
            target_bitrate=request.target_bitrate,
            encoding_mode=request.encoding_mode,
            target_fps=request.target_fps,
            scheduled_start_at=request.scheduled_start_at,
            scheduled_end_at=request.scheduled_end_at,
            enable_auto_restart=request.enable_auto_restart,
            max_restarts=request.max_restarts,
            status=initial_status,
            youtube_broadcast_id=getattr(request, 'youtube_broadcast_id', None),
            enable_chat_moderation=getattr(request, 'enable_chat_moderation', True),
        )
        
        # Set encrypted stream key
        job.stream_key = request.stream_key
        
        return await self.job_repo.create(job)

    # ============================================
    # Read Operations
    # ============================================

    async def get_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> StreamJob:
        """Get stream job by ID.
        
        Requirements: 1.5
        
        Args:
            job_id: Stream job UUID
            user_id: Optional user filter for authorization
            
        Returns:
            StreamJob: Stream job instance
            
        Raises:
            StreamJobNotFoundError: If job not found
        """
        job = await self.job_repo.get_by_id(job_id)
        
        if not job:
            raise StreamJobNotFoundError(f"Stream job {job_id} not found")
        
        if user_id and job.user_id != user_id:
            raise StreamJobNotFoundError(f"Stream job {job_id} not found")
        
        return job

    async def list_stream_jobs(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[StreamJob], int]:
        """List stream jobs for a user.
        
        Requirements: 1.5
        
        Args:
            user_id: User UUID
            status: Optional status filter
            account_id: Optional account filter
            page: Page number
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJob], int]: Jobs and total count
        """
        return await self.job_repo.get_by_user(
            user_id=user_id,
            status=status,
            account_id=account_id,
            page=page,
            page_size=page_size,
        )

    async def get_active_jobs(
        self,
        user_id: Optional[uuid.UUID] = None,
    ) -> Sequence[StreamJob]:
        """Get all active stream jobs.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            Sequence[StreamJob]: Active stream jobs
        """
        return await self.job_repo.get_active_jobs(user_id)

    # ============================================
    # Update Operations
    # ============================================

    async def update_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        request: UpdateStreamJobRequest,
    ) -> StreamJob:
        """Update a stream job.
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            request: Update request data
            
        Returns:
            StreamJob: Updated stream job
            
        Raises:
            StreamJobNotFoundError: If job not found
            InvalidStatusTransitionError: If job is running
        """
        job = await self.get_stream_job(job_id, user_id)
        
        # Cannot update running jobs (except certain fields)
        if job.is_active():
            # Only allow updating auto-restart settings while running
            if request.enable_auto_restart is not None:
                job.enable_auto_restart = request.enable_auto_restart
            if request.max_restarts is not None:
                job.max_restarts = request.max_restarts
            return await self.job_repo.update(job)
        
        # Update all fields
        if request.title is not None:
            job.title = request.title
        if request.description is not None:
            job.description = request.description
        if request.loop_mode is not None:
            job.loop_mode = request.loop_mode
        if request.loop_count is not None:
            job.loop_count = request.loop_count
        if request.resolution is not None:
            job.resolution = request.resolution
        if request.target_bitrate is not None:
            job.target_bitrate = request.target_bitrate
        if request.encoding_mode is not None:
            job.encoding_mode = request.encoding_mode
        if request.target_fps is not None:
            job.target_fps = request.target_fps
        if request.scheduled_start_at is not None:
            job.scheduled_start_at = request.scheduled_start_at
        if request.scheduled_end_at is not None:
            job.scheduled_end_at = request.scheduled_end_at
        if request.enable_auto_restart is not None:
            job.enable_auto_restart = request.enable_auto_restart
        if request.max_restarts is not None:
            job.max_restarts = request.max_restarts
        
        return await self.job_repo.update(job)

    # ============================================
    # Delete Operations
    # ============================================

    async def delete_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a stream job.
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            
        Returns:
            bool: True if deleted
            
        Raises:
            StreamJobNotFoundError: If job not found
            InvalidStatusTransitionError: If job is running
        """
        job = await self.get_stream_job(job_id, user_id)
        
        # Cannot delete running or starting jobs (but allow stopping/stopped)
        if job.status in [StreamJobStatus.RUNNING.value, StreamJobStatus.STARTING.value]:
            raise InvalidStatusTransitionError(
                "Cannot delete a running stream job. Stop it first."
            )
        
        # If job is in "stopping" status, try to kill the process first
        if job.status == StreamJobStatus.STOPPING.value and job.pid:
            try:
                import psutil
                process = psutil.Process(job.pid)
                process.kill()
            except Exception:
                pass  # Process may already be dead
        
        return await self.job_repo.delete(job_id)

    # ============================================
    # Stream Control Operations
    # ============================================

    async def start_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> StreamJob:
        """Start a stream job.
        
        Requirements: 1.2, 5.5, 6.1, 6.2
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            
        Returns:
            StreamJob: Updated stream job
            
        Raises:
            StreamJobNotFoundError: If job not found
            SlotLimitExceededError: If slot limit reached
            StreamKeyInUseError: If stream key is in use
            StreamAlreadyRunningError: If already running
        """
        job = await self.get_stream_job(job_id, user_id)
        
        # Check if can start
        if not job.can_start():
            raise StreamAlreadyRunningError(
                f"Stream job is in '{job.status}' status and cannot be started"
            )
        
        # Check concurrent streams limit from database Plan
        from app.modules.billing.feature_gate import FeatureGateService, LimitExceededError
        feature_gate = FeatureGateService(self.session)
        try:
            await feature_gate.check_concurrent_streams_limit(user_id, raise_on_exceed=True)
        except LimitExceededError as e:
            raise SlotLimitExceededError(e.message)
        
        # Check stream key not in use (Requirements: 8.4)
        existing = await self.job_repo.get_by_stream_key(job.stream_key)
        if existing and existing.id != job.id:
            raise StreamKeyInUseError(
                "Stream key is already in use by another active stream"
            )
        
        # Update status to starting
        job.status = StreamJobStatus.STARTING.value
        job.is_stream_key_locked = True
        job.last_error = None
        job.actual_start_at = None  # Reset for fresh duration calculation
        job.actual_end_at = None
        
        # Queue the FFmpeg worker task
        from app.modules.stream.stream_job_tasks import start_ffmpeg_worker
        start_ffmpeg_worker.delay(str(job.id))
        
        return await self.job_repo.update(job)

    async def stop_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> StreamJob:
        """Stop a stream job.
        
        Requirements: 1.3, 6.3
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            
        Returns:
            StreamJob: Updated stream job
            
        Raises:
            StreamJobNotFoundError: If job not found
            StreamNotRunningError: If not running
        """
        job = await self.get_stream_job(job_id, user_id)
        
        # Check if can stop
        if not job.can_stop():
            raise StreamNotRunningError(
                f"Stream job is in '{job.status}' status and cannot be stopped"
            )
        
        # Update status to stopping
        job.status = StreamJobStatus.STOPPING.value
        
        # Queue the stop task
        from app.modules.stream.stream_job_tasks import stop_ffmpeg_worker
        stop_ffmpeg_worker.delay(str(job.id))
        
        return await self.job_repo.update(job)

    async def restart_stream_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> StreamJob:
        """Restart a stream job.
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            
        Returns:
            StreamJob: Updated stream job
        """
        job = await self.get_stream_job(job_id, user_id)
        
        # If running or stopping, force stop first
        if job.is_active() or job.status == StreamJobStatus.STOPPING.value:
            # Kill process directly if PID exists
            if job.pid:
                try:
                    import psutil
                    process = psutil.Process(job.pid)
                    process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass  # Process may already be dead
            
            # Force status to stopped
            job.status = StreamJobStatus.STOPPED.value
            job.pid = None
            job.is_stream_key_locked = False
            await self.job_repo.update(job)
        
        # Reset restart count and actual_start_at for manual restart
        job.restart_count = 0
        job.actual_start_at = None  # Reset so duration starts fresh
        job.actual_end_at = None
        await self.job_repo.update(job)
        
        # Start again
        return await self.start_stream_job(job_id, user_id)

    # ============================================
    # Slot Management (Requirements: 6.1, 6.2, 6.3, 6.4)
    # ============================================

    async def get_slot_status(self, user_id: uuid.UUID) -> SlotStatusResponse:
        """Get stream slot status for a user.
        
        Requirements: 6.4
        
        Args:
            user_id: User UUID
            
        Returns:
            SlotStatusResponse: Slot status
        """
        # Get user's plan limits from database
        from app.modules.billing.feature_gate import FeatureGateService
        feature_gate = FeatureGateService(self.session)
        
        try:
            plan, subscription = await feature_gate.get_user_plan(user_id)
            total_slots = plan.concurrent_streams
            plan_name = plan.slug
        except Exception:
            # Fallback to default if plan not found
            total_slots = 1
            plan_name = "free"
        
        # Count active streams
        used_slots = await self.job_repo.count_active_by_user(user_id)
        
        # Handle unlimited (-1)
        if total_slots == -1:
            return SlotStatusResponse(
                used_slots=used_slots,
                total_slots=-1,
                available_slots=999,  # Effectively unlimited
                plan=plan_name,
            )
        
        return SlotStatusResponse(
            used_slots=used_slots,
            total_slots=total_slots,
            available_slots=max(0, total_slots - used_slots),
            plan=plan_name,
        )

    async def check_slot_available(self, user_id: uuid.UUID) -> bool:
        """Check if user has available stream slots.
        
        Requirements: 5.5, 6.1
        
        Args:
            user_id: User UUID
            
        Returns:
            bool: True if slot available
        """
        slot_status = await self.get_slot_status(user_id)
        return slot_status.available_slots > 0

    # ============================================
    # Resource Monitoring (Requirements: 9.1, 9.2, 9.3, 9.4, 9.5)
    # ============================================

    async def get_resource_usage(
        self,
        user_id: Optional[uuid.UUID] = None,
    ) -> ResourceDashboardResponse:
        """Get resource usage dashboard.
        
        Requirements: 9.1, 9.5
        
        Args:
            user_id: Optional user filter
            
        Returns:
            ResourceDashboardResponse: Resource dashboard
        """
        # Get active jobs
        active_jobs = await self.job_repo.get_active_jobs(user_id)
        
        # Aggregate metrics
        total_cpu = 0.0
        total_memory = 0.0
        total_bandwidth = 0.0
        streams = []
        
        for job in active_jobs:
            # Get latest health for this job
            health = await self.health_repo.get_latest(job.id)
            
            cpu = health.cpu_percent if health else 0.0
            memory = health.memory_mb if health else 0.0
            bitrate = (health.bitrate / 1000) if health else 0.0  # Convert to kbps
            
            total_cpu += cpu or 0
            total_memory += memory or 0
            total_bandwidth += bitrate or 0
            
            streams.append(StreamResourceResponse(
                stream_job_id=job.id,
                title=job.title,
                status=job.status,
                cpu_percent=cpu,
                memory_mb=memory,
                bitrate_kbps=bitrate,
            ))
        
        # Calculate remaining capacity
        # Estimate: 1 stream ≈ 0.7% CPU, 30MB RAM
        avg_cpu_per_stream = 0.7
        avg_memory_per_stream = 30
        
        if len(active_jobs) > 0:
            avg_cpu_per_stream = total_cpu / len(active_jobs) if total_cpu > 0 else 0.7
            avg_memory_per_stream = total_memory / len(active_jobs) if total_memory > 0 else 30
        
        # Assume 100% CPU and 8GB RAM available
        remaining_by_cpu = int((100 - total_cpu) / avg_cpu_per_stream) if avg_cpu_per_stream > 0 else 100
        remaining_by_memory = int((8192 - total_memory) / avg_memory_per_stream) if avg_memory_per_stream > 0 else 100
        estimated_remaining = min(remaining_by_cpu, remaining_by_memory, 100)
        
        # Warning if usage > 80%
        is_warning = total_cpu > 80 or total_memory > 6553  # 80% of 8GB
        
        aggregate = ResourceUsageResponse(
            total_cpu_percent=total_cpu,
            total_memory_mb=total_memory,
            total_bandwidth_kbps=total_bandwidth,
            active_streams=len(active_jobs),
            estimated_remaining_slots=max(0, estimated_remaining),
            is_warning=is_warning,
        )
        
        return ResourceDashboardResponse(
            aggregate=aggregate,
            streams=streams,
        )

    # ============================================
    # Health Operations
    # ============================================

    async def get_health_latest(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[StreamJobHealth]:
        """Get latest health record for a stream job.
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            
        Returns:
            Optional[StreamJobHealth]: Latest health record
        """
        # Verify access
        await self.get_stream_job(job_id, user_id)
        return await self.health_repo.get_latest(job_id)

    async def get_health_history(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        hours: int = 24,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[Sequence[StreamJobHealth], int]:
        """Get health history for a stream job.
        
        Args:
            job_id: Stream job UUID
            user_id: User UUID for authorization
            hours: Hours to look back
            page: Page number
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJobHealth], int]: Health records and total
        """
        # Verify access
        await self.get_stream_job(job_id, user_id)
        return await self.health_repo.get_history(
            job_id=job_id,
            hours=hours,
            page=page,
            page_size=page_size,
        )

    async def acknowledge_alert(
        self,
        health_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[StreamJobHealth]:
        """Acknowledge a health alert.
        
        Args:
            health_id: Health record UUID
            user_id: User UUID for authorization
            
        Returns:
            Optional[StreamJobHealth]: Updated health record
        """
        return await self.health_repo.acknowledge_alert(health_id)

    # ============================================
    # Helper Methods
    # ============================================

    async def _validate_account(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Validate YouTube account exists and belongs to user.
        
        Args:
            account_id: YouTube account UUID
            user_id: User UUID
            
        Raises:
            AccountNotFoundError: If account not found or unauthorized
        """
        from app.modules.account.repository import YouTubeAccountRepository
        
        account_repo = YouTubeAccountRepository(self.session)
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise AccountNotFoundError(f"YouTube account {account_id} not found")
        
        if account.user_id != user_id:
            raise AccountNotFoundError(f"YouTube account {account_id} not found")

    async def _get_user_plan(self, user_id: uuid.UUID) -> str:
        """Get user's subscription plan.
        
        Args:
            user_id: User UUID
            
        Returns:
            str: Plan name
        """
        # TODO: Integrate with actual subscription system
        # For now, return default plan
        try:
            from app.modules.subscription.repository import SubscriptionRepository
            sub_repo = SubscriptionRepository(self.session)
            subscription = await sub_repo.get_active_by_user(user_id)
            if subscription:
                return subscription.plan
        except ImportError:
            pass
        
        return DEFAULT_PLAN

    def _resolve_video_path(self, video_path: str) -> str:
        """Resolve video path to a path/URL that FFmpeg can use.
        
        Supports:
        - Absolute local paths (returned as-is)
        - Relative storage keys (converted to absolute path or presigned URL)
        - HTTP/HTTPS URLs (returned as-is, FFmpeg supports HTTP input)
        
        Args:
            video_path: Video path (can be relative, absolute, or HTTP URL)
            
        Returns:
            str: Path or URL that FFmpeg can read
        """
        from pathlib import Path
        from app.core.config import settings
        from app.core.storage import get_file_url_for_ffmpeg, is_cloud_storage
        
        # If it's already an HTTP URL, return as-is (FFmpeg supports HTTP input)
        if video_path.startswith("http://") or video_path.startswith("https://"):
            return video_path
        
        # If already absolute local path, return as-is
        if os.path.isabs(video_path):
            return video_path
        
        # It's a relative storage key - get appropriate path/URL
        return get_file_url_for_ffmpeg(video_path, expires_in=86400)  # 24 hours for long streams

    def _validate_video_source(self, resolved_path: str, original_path: str) -> bool:
        """Validate that video source exists and is accessible.
        
        Supports:
        - Local file paths (checks os.path.exists)
        - HTTP/HTTPS URLs (assumes valid if it's a presigned URL)
        - Storage keys (checks via storage.exists)
        
        Args:
            resolved_path: Resolved path/URL from _resolve_video_path
            original_path: Original path provided by user
            
        Returns:
            bool: True if video source is valid
        """
        from app.core.storage import get_storage, is_cloud_storage
        
        # If it's an HTTP URL (presigned URL from R2/S3), assume valid
        # The presigned URL was just generated, so it should be valid
        if resolved_path.startswith("http://") or resolved_path.startswith("https://"):
            # For cloud storage, verify the file exists in storage
            if is_cloud_storage() and not os.path.isabs(original_path):
                storage = get_storage()
                return storage.exists(original_path)
            return True
        
        # For local paths, check if file exists
        return os.path.exists(resolved_path)

    # ============================================
    # History & Analytics Operations (Requirements: 12.1, 12.2, 12.4, 12.5)
    # ============================================

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
            days: Days to look back
            page: Page number
            page_size: Items per page
            
        Returns:
            tuple[Sequence[StreamJob], int]: Jobs and total count
        """
        return await self.analytics_repo.get_history(
            user_id=user_id,
            days=days,
            page=page,
            page_size=page_size,
        )

    async def get_analytics_summary(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> dict:
        """Get analytics summary for a user.
        
        Requirements: 12.5
        
        Args:
            user_id: User UUID
            days: Days to analyze
            
        Returns:
            dict: Analytics summary
        """
        return await self.analytics_repo.get_analytics_summary(
            user_id=user_id,
            days=days,
        )

    async def export_to_csv(
        self,
        user_id: uuid.UUID,
        days: int = 30,
    ) -> list[dict]:
        """Export stream job data for CSV.
        
        Requirements: 12.4
        
        Args:
            user_id: User UUID
            days: Days to export
            
        Returns:
            list[dict]: Data for CSV export
        """
        return await self.analytics_repo.export_to_csv_data(
            user_id=user_id,
            days=days,
        )
