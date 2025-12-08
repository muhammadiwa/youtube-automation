"""Repository for transcoding service database operations.

Requirements: 10.1, 10.2, 10.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transcoding.models import (
    TranscodeJob,
    TranscodeWorker,
    TranscodedOutput,
    TranscodeStatus,
    Resolution,
    LatencyMode,
)


class TranscodeJobRepository:
    """Repository for TranscodeJob operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        source_file_path: str,
        target_resolution: Resolution,
        target_bitrate: Optional[int] = None,
        latency_mode: LatencyMode = LatencyMode.NORMAL,
        enable_abr: bool = False,
        account_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        live_event_id: Optional[uuid.UUID] = None,
    ) -> TranscodeJob:
        """Create a new transcoding job.
        
        Args:
            source_file_path: Path to source video file
            target_resolution: Target output resolution
            target_bitrate: Target bitrate in bps
            latency_mode: Latency optimization mode
            enable_abr: Enable adaptive bitrate
            account_id: Associated YouTube account
            video_id: Associated video
            live_event_id: Associated live event
            
        Returns:
            Created TranscodeJob
        """
        job = TranscodeJob(
            source_file_path=source_file_path,
            target_resolution=target_resolution,
            target_bitrate=target_bitrate,
            latency_mode=latency_mode,
            enable_abr=enable_abr,
            account_id=account_id,
            video_id=video_id,
            live_event_id=live_event_id,
            status=TranscodeStatus.QUEUED,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[TranscodeJob]:
        """Get a transcoding job by ID."""
        result = await self.session.execute(
            select(TranscodeJob).where(TranscodeJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_queued_jobs(self, limit: int = 10) -> list[TranscodeJob]:
        """Get queued jobs ready for processing."""
        result = await self.session.execute(
            select(TranscodeJob)
            .where(TranscodeJob.status == TranscodeStatus.QUEUED)
            .order_by(TranscodeJob.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def assign_to_worker(
        self,
        job: TranscodeJob,
        worker_id: str,
        worker_load: float,
    ) -> None:
        """Assign a job to a worker.
        
        Args:
            job: The job to assign
            worker_id: Worker identifier
            worker_load: Worker load at assignment time
        """
        job.assigned_worker_id = worker_id
        job.worker_load_at_assignment = worker_load
        job.status = TranscodeStatus.PROCESSING
        job.started_at = datetime.utcnow()

    async def update_progress(
        self,
        job: TranscodeJob,
        progress: float,
    ) -> None:
        """Update job progress.
        
        Args:
            job: The job to update
            progress: Progress percentage (0-100)
        """
        job.progress = min(100.0, max(0.0, progress))

    async def complete_job(
        self,
        job: TranscodeJob,
        output_file_path: str,
        output_width: int,
        output_height: int,
        output_file_size: int,
        cdn_url: Optional[str] = None,
    ) -> None:
        """Mark a job as completed.
        
        Args:
            job: The job to complete
            output_file_path: Path to output file
            output_width: Output video width
            output_height: Output video height
            output_file_size: Output file size in bytes
            cdn_url: CDN URL if uploaded
        """
        job.status = TranscodeStatus.COMPLETED
        job.progress = 100.0
        job.output_file_path = output_file_path
        job.output_width = output_width
        job.output_height = output_height
        job.output_file_size = output_file_size
        job.cdn_url = cdn_url
        job.completed_at = datetime.utcnow()

    async def fail_job(
        self,
        job: TranscodeJob,
        error_message: str,
    ) -> None:
        """Mark a job as failed.
        
        Args:
            job: The job to fail
            error_message: Error description
        """
        job.status = TranscodeStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()


class TranscodeWorkerRepository:
    """Repository for TranscodeWorker operations.
    
    Requirements: 10.2 - Distribute to FFmpeg worker cluster based on load.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # Heartbeat timeout in seconds
    HEARTBEAT_TIMEOUT = 60

    async def register(
        self,
        hostname: str,
        ip_address: Optional[str] = None,
        max_concurrent_jobs: int = 2,
        supports_4k: bool = True,
        supports_hardware_encoding: bool = False,
        gpu_type: Optional[str] = None,
    ) -> TranscodeWorker:
        """Register a new worker or update existing.
        
        Args:
            hostname: Worker hostname
            ip_address: Worker IP address
            max_concurrent_jobs: Maximum concurrent jobs
            supports_4k: Whether worker supports 4K
            supports_hardware_encoding: Whether worker has GPU encoding
            gpu_type: GPU type if available
            
        Returns:
            Registered TranscodeWorker
        """
        # Check if worker already exists
        result = await self.session.execute(
            select(TranscodeWorker).where(TranscodeWorker.hostname == hostname)
        )
        worker = result.scalar_one_or_none()

        if worker:
            # Update existing worker
            worker.ip_address = ip_address
            worker.max_concurrent_jobs = max_concurrent_jobs
            worker.supports_4k = supports_4k
            worker.supports_hardware_encoding = supports_hardware_encoding
            worker.gpu_type = gpu_type
            worker.is_healthy = True
            worker.last_heartbeat = datetime.utcnow()
        else:
            # Create new worker
            worker = TranscodeWorker(
                hostname=hostname,
                ip_address=ip_address,
                max_concurrent_jobs=max_concurrent_jobs,
                supports_4k=supports_4k,
                supports_hardware_encoding=supports_hardware_encoding,
                gpu_type=gpu_type,
            )
            self.session.add(worker)

        await self.session.flush()
        return worker

    async def get_by_id(self, worker_id: uuid.UUID) -> Optional[TranscodeWorker]:
        """Get a worker by ID."""
        result = await self.session.execute(
            select(TranscodeWorker).where(TranscodeWorker.id == worker_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hostname(self, hostname: str) -> Optional[TranscodeWorker]:
        """Get a worker by hostname."""
        result = await self.session.execute(
            select(TranscodeWorker).where(TranscodeWorker.hostname == hostname)
        )
        return result.scalar_one_or_none()

    async def heartbeat(
        self,
        hostname: str,
        current_jobs: int,
        current_load: float,
    ) -> Optional[TranscodeWorker]:
        """Update worker heartbeat.
        
        Args:
            hostname: Worker hostname
            current_jobs: Current number of jobs
            current_load: Current load percentage
            
        Returns:
            Updated worker or None if not found
        """
        result = await self.session.execute(
            select(TranscodeWorker).where(TranscodeWorker.hostname == hostname)
        )
        worker = result.scalar_one_or_none()

        if worker:
            worker.current_jobs = current_jobs
            worker.current_load = current_load
            worker.last_heartbeat = datetime.utcnow()
            worker.is_healthy = True

        return worker

    async def get_healthy_workers(self) -> list[TranscodeWorker]:
        """Get all healthy workers."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.HEARTBEAT_TIMEOUT)
        result = await self.session.execute(
            select(TranscodeWorker)
            .where(
                and_(
                    TranscodeWorker.is_healthy == True,
                    TranscodeWorker.last_heartbeat >= cutoff,
                )
            )
        )
        return list(result.scalars().all())

    async def get_available_workers(self, requires_4k: bool = False) -> list[TranscodeWorker]:
        """Get workers that can accept new jobs.
        
        Args:
            requires_4k: Whether job requires 4K support
            
        Returns:
            List of available workers
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.HEARTBEAT_TIMEOUT)
        
        query = select(TranscodeWorker).where(
            and_(
                TranscodeWorker.is_healthy == True,
                TranscodeWorker.last_heartbeat >= cutoff,
            )
        )
        
        if requires_4k:
            query = query.where(TranscodeWorker.supports_4k == True)
        
        result = await self.session.execute(query)
        workers = list(result.scalars().all())
        
        # Filter to only available workers
        return [w for w in workers if w.is_available()]

    async def select_worker_by_load(
        self,
        requires_4k: bool = False,
    ) -> Optional[TranscodeWorker]:
        """Select the worker with lowest load.
        
        Requirements: 10.2 - Distribute based on load.
        
        Args:
            requires_4k: Whether job requires 4K support
            
        Returns:
            Worker with lowest load or None
        """
        workers = await self.get_available_workers(requires_4k=requires_4k)
        
        if not workers:
            return None
        
        # Sort by load and return lowest
        workers.sort(key=lambda w: w.current_load)
        return workers[0]

    async def increment_job_count(self, worker: TranscodeWorker) -> None:
        """Increment worker's current job count."""
        worker.current_jobs += 1
        worker.current_load = (worker.current_jobs / worker.max_concurrent_jobs) * 100

    async def decrement_job_count(self, worker: TranscodeWorker) -> None:
        """Decrement worker's current job count."""
        worker.current_jobs = max(0, worker.current_jobs - 1)
        worker.current_load = (worker.current_jobs / worker.max_concurrent_jobs) * 100

    async def mark_unhealthy(self, worker: TranscodeWorker) -> None:
        """Mark a worker as unhealthy."""
        worker.is_healthy = False


class TranscodedOutputRepository:
    """Repository for TranscodedOutput operations.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        transcode_job_id: uuid.UUID,
        resolution: Resolution,
        width: int,
        height: int,
        bitrate: int,
        file_size: int,
        duration: float,
        storage_bucket: str,
        storage_key: str,
        cdn_url: str,
        expires_at: Optional[datetime] = None,
    ) -> TranscodedOutput:
        """Create a transcoded output record.
        
        Args:
            transcode_job_id: Associated job ID
            resolution: Output resolution
            width: Video width
            height: Video height
            bitrate: Video bitrate
            file_size: File size in bytes
            duration: Duration in seconds
            storage_bucket: S3 bucket name
            storage_key: S3 object key
            cdn_url: CDN URL
            expires_at: Expiration time
            
        Returns:
            Created TranscodedOutput
        """
        output = TranscodedOutput(
            transcode_job_id=transcode_job_id,
            resolution=resolution,
            width=width,
            height=height,
            bitrate=bitrate,
            file_size=file_size,
            duration=duration,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            cdn_url=cdn_url,
            expires_at=expires_at,
        )
        self.session.add(output)
        await self.session.flush()
        return output

    async def get_by_job_id(self, job_id: uuid.UUID) -> list[TranscodedOutput]:
        """Get all outputs for a job."""
        result = await self.session.execute(
            select(TranscodedOutput)
            .where(TranscodedOutput.transcode_job_id == job_id)
        )
        return list(result.scalars().all())
