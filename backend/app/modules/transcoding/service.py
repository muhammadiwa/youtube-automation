"""Service layer for transcoding operations.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transcoding.models import (
    TranscodeJob,
    TranscodeWorker,
    TranscodeStatus,
    Resolution,
    LatencyMode,
)
from app.modules.transcoding.repository import (
    TranscodeJobRepository,
    TranscodeWorkerRepository,
    TranscodedOutputRepository,
)
from app.modules.transcoding.schemas import (
    TranscodeJobCreate,
    TranscodeJobResponse,
    WorkerRegistration,
    WorkerStatus,
    WorkerSelection,
    ABRConfig,
    get_recommended_bitrate,
)
from app.modules.transcoding.tasks import (
    transcode_video_task,
    transcode_abr_task,
    dispatch_transcode_job,
)


class TranscodingService:
    """Service for managing transcoding operations.
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.job_repo = TranscodeJobRepository(session)
        self.worker_repo = TranscodeWorkerRepository(session)
        self.output_repo = TranscodedOutputRepository(session)

    async def create_transcode_job(
        self,
        data: TranscodeJobCreate,
        dispatch: bool = True,
    ) -> TranscodeJob:
        """Create a new transcoding job.
        
        Requirements: 10.1, 10.2
        
        Args:
            data: Job creation data
            dispatch: Whether to dispatch immediately
            
        Returns:
            Created TranscodeJob
        """
        # Set default bitrate if not provided
        bitrate = data.target_bitrate
        if bitrate is None:
            bitrate = get_recommended_bitrate(data.target_resolution, data.latency_mode)
        
        job = await self.job_repo.create(
            source_file_path=data.source_file_path,
            target_resolution=data.target_resolution,
            target_bitrate=bitrate,
            latency_mode=data.latency_mode,
            enable_abr=data.enable_abr,
            account_id=data.account_id,
            video_id=data.video_id,
            live_event_id=data.live_event_id,
        )
        
        await self.session.commit()
        
        # Dispatch job to worker
        if dispatch:
            dispatch_transcode_job.delay(str(job.id))
        
        return job

    async def create_abr_transcode_job(
        self,
        source_file_path: str,
        abr_config: ABRConfig,
        latency_mode: LatencyMode = LatencyMode.NORMAL,
        account_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
    ) -> TranscodeJob:
        """Create an ABR transcoding job.
        
        Requirements: 10.3 - Support adaptive bitrate (ABR).
        
        Args:
            source_file_path: Path to source video
            abr_config: ABR configuration
            latency_mode: Latency mode
            account_id: Associated account
            video_id: Associated video
            
        Returns:
            Created TranscodeJob
        """
        # Use highest resolution as primary
        primary_resolution = max(
            abr_config.resolutions,
            key=lambda r: r.value,
        )
        
        job = await self.job_repo.create(
            source_file_path=source_file_path,
            target_resolution=primary_resolution,
            latency_mode=latency_mode,
            enable_abr=True,
            account_id=account_id,
            video_id=video_id,
        )
        
        await self.session.commit()
        
        # Dispatch ABR job
        transcode_abr_task.delay(
            str(job.id),
            [r.value for r in abr_config.resolutions],
            abr_config.bitrates,
        )
        
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[TranscodeJob]:
        """Get a transcoding job by ID."""
        return await self.job_repo.get_by_id(job_id)

    async def get_job_status(self, job_id: uuid.UUID) -> Optional[TranscodeJobResponse]:
        """Get job status as response schema."""
        job = await self.job_repo.get_by_id(job_id)
        if job:
            return TranscodeJobResponse.model_validate(job)
        return None

    async def cancel_job(self, job_id: uuid.UUID) -> bool:
        """Cancel a queued job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False if not possible
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return False
        
        if job.status != TranscodeStatus.QUEUED:
            return False
        
        await self.job_repo.fail_job(job, "Cancelled by user")
        await self.session.commit()
        return True

    async def register_worker(
        self,
        data: WorkerRegistration,
    ) -> TranscodeWorker:
        """Register a new transcoding worker.
        
        Requirements: 10.2
        
        Args:
            data: Worker registration data
            
        Returns:
            Registered worker
        """
        worker = await self.worker_repo.register(
            hostname=data.hostname,
            ip_address=data.ip_address,
            max_concurrent_jobs=data.max_concurrent_jobs,
            supports_4k=data.supports_4k,
            supports_hardware_encoding=data.supports_hardware_encoding,
            gpu_type=data.gpu_type,
        )
        
        await self.session.commit()
        return worker

    async def get_worker_status(self, worker_id: uuid.UUID) -> Optional[WorkerStatus]:
        """Get worker status."""
        worker = await self.worker_repo.get_by_id(worker_id)
        if worker:
            return WorkerStatus.model_validate(worker)
        return None

    async def get_all_workers(self) -> list[WorkerStatus]:
        """Get all registered workers."""
        workers = await self.worker_repo.get_healthy_workers()
        return [WorkerStatus.model_validate(w) for w in workers]

    async def select_best_worker(
        self,
        requires_4k: bool = False,
    ) -> Optional[WorkerSelection]:
        """Select the best worker for a job.
        
        Requirements: 10.2 - Distribute based on load.
        
        Args:
            requires_4k: Whether job requires 4K support
            
        Returns:
            Worker selection result
        """
        worker = await self.worker_repo.select_worker_by_load(requires_4k=requires_4k)
        
        if worker:
            return WorkerSelection(
                worker_id=worker.id,
                hostname=worker.hostname,
                current_load=worker.current_load,
                reason="Lowest load among available workers",
            )
        return None

    async def get_queue_stats(self) -> dict:
        """Get transcoding queue statistics."""
        queued_jobs = await self.job_repo.get_queued_jobs(limit=1000)
        healthy_workers = await self.worker_repo.get_healthy_workers()
        available_workers = await self.worker_repo.get_available_workers()
        
        return {
            "queued_jobs": len(queued_jobs),
            "total_workers": len(healthy_workers),
            "available_workers": len(available_workers),
            "average_load": (
                sum(w.current_load for w in healthy_workers) / len(healthy_workers)
                if healthy_workers else 0
            ),
        }
