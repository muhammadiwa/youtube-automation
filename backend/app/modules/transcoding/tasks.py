"""Celery tasks for transcoding service.

Implements FFmpeg worker with Celery and job distribution based on load.
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import uuid
import os
from datetime import datetime
from typing import Optional

from celery import Task

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.modules.job.tasks import BaseTaskWithRetry, RetryConfig, RETRY_CONFIGS
from app.modules.transcoding.models import (
    TranscodeJob,
    TranscodeWorker,
    TranscodeStatus,
    Resolution,
    LatencyMode,
    RESOLUTION_DIMENSIONS,
)
from app.modules.transcoding.repository import (
    TranscodeJobRepository,
    TranscodeWorkerRepository,
    TranscodedOutputRepository,
)
from app.modules.transcoding.ffmpeg import (
    FFmpegTranscoder,
    FFmpegConfig,
    ABRTranscoder,
    validate_resolution_output,
    get_expected_dimensions,
)
from app.modules.transcoding.schemas import ABRConfig, get_recommended_bitrate


# Transcoding-specific retry configuration
TRANSCODE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=10.0,
    max_delay=120.0,
    backoff_multiplier=2.0,
)

# Add to global retry configs
RETRY_CONFIGS["transcode"] = TRANSCODE_RETRY_CONFIG


class TranscodeTask(Task):
    """Base task for transcoding operations.
    
    Requirements: 10.1, 10.2
    """
    abstract = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = args[0] if args else kwargs.get("job_id")
        if job_id:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                self._mark_job_failed(job_id, str(exc))
            )

    async def _mark_job_failed(self, job_id: str, error: str):
        """Mark job as failed in database."""
        async with async_session_maker() as session:
            repo = TranscodeJobRepository(session)
            job = await repo.get_by_id(uuid.UUID(job_id))
            if job:
                await repo.fail_job(job, error)
                await session.commit()


class WorkerLoadBalancer:
    """Distributes jobs to workers based on load.
    
    Requirements: 10.2 - Distribute to FFmpeg worker cluster based on load.
    """

    @staticmethod
    async def select_worker(
        session,
        requires_4k: bool = False,
    ) -> Optional[TranscodeWorker]:
        """Select the best worker for a job.
        
        Args:
            session: Database session
            requires_4k: Whether job requires 4K support
            
        Returns:
            Selected worker or None
        """
        repo = TranscodeWorkerRepository(session)
        return await repo.select_worker_by_load(requires_4k=requires_4k)

    @staticmethod
    def requires_4k_support(resolution: Resolution) -> bool:
        """Check if resolution requires 4K support."""
        return resolution == Resolution.RES_4K


@celery_app.task(bind=True, base=TranscodeTask)
def transcode_video_task(
    self: TranscodeTask,
    job_id: str,
) -> dict:
    """Transcode a video to target resolution.
    
    Requirements: 10.1 - Transcode to configured resolution.
    
    Args:
        job_id: UUID of the transcode job
        
    Returns:
        dict: Transcoding result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _transcode_video_async(job_id)
    )


async def _transcode_video_async(job_id: str) -> dict:
    """Async implementation of video transcoding."""
    async with async_session_maker() as session:
        job_repo = TranscodeJobRepository(session)
        worker_repo = TranscodeWorkerRepository(session)
        
        # Get job
        job = await job_repo.get_by_id(uuid.UUID(job_id))
        if not job:
            return {"success": False, "error": "Job not found"}
        
        # Check if already processing
        if job.status == TranscodeStatus.PROCESSING:
            return {"success": False, "error": "Job already processing"}
        
        # Select worker based on load
        requires_4k = WorkerLoadBalancer.requires_4k_support(job.target_resolution)
        worker = await WorkerLoadBalancer.select_worker(session, requires_4k=requires_4k)
        
        if not worker:
            # No worker available, will retry
            return {"success": False, "error": "No available workers", "retry": True}
        
        # Assign job to worker
        await job_repo.assign_to_worker(job, str(worker.id), worker.current_load)
        await worker_repo.increment_job_count(worker)
        await session.commit()
        
        try:
            # Perform transcoding
            transcoder = FFmpegTranscoder()
            
            # Generate output path
            output_dir = os.path.dirname(job.source_file_path)
            output_filename = f"transcoded_{job.id}_{job.target_resolution.value}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            # Get bitrate
            bitrate = job.target_bitrate or get_recommended_bitrate(
                job.target_resolution, job.latency_mode
            )
            
            config = FFmpegConfig(
                input_path=job.source_file_path,
                output_path=output_path,
                resolution=job.target_resolution,
                bitrate=bitrate,
                latency_mode=job.latency_mode,
            )
            
            # Transcode
            result = transcoder.transcode(config)
            
            if result.success:
                # Validate output dimensions
                expected_width, expected_height = get_expected_dimensions(job.target_resolution)
                is_valid = validate_resolution_output(
                    result.width, result.height, job.target_resolution
                )
                
                if not is_valid:
                    await job_repo.fail_job(
                        job,
                        f"Output dimensions {result.width}x{result.height} do not match "
                        f"expected {expected_width}x{expected_height}"
                    )
                    return {
                        "success": False,
                        "error": "Dimension validation failed",
                        "actual_width": result.width,
                        "actual_height": result.height,
                        "expected_width": expected_width,
                        "expected_height": expected_height,
                    }
                
                # Complete job
                await job_repo.complete_job(
                    job,
                    output_file_path=result.output_path,
                    output_width=result.width,
                    output_height=result.height,
                    output_file_size=result.file_size,
                )
                
                await session.commit()
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "output_path": result.output_path,
                    "width": result.width,
                    "height": result.height,
                    "file_size": result.file_size,
                    "duration": result.duration,
                    "bitrate": result.bitrate,
                }
            else:
                await job_repo.fail_job(job, result.error_message or "Transcoding failed")
                await session.commit()
                
                return {
                    "success": False,
                    "error": result.error_message,
                }
                
        finally:
            # Decrement worker job count
            await worker_repo.decrement_job_count(worker)
            await session.commit()


@celery_app.task(bind=True, base=TranscodeTask)
def transcode_abr_task(
    self: TranscodeTask,
    job_id: str,
    resolutions: list[str],
    bitrates: Optional[list[int]] = None,
) -> dict:
    """Transcode video to multiple resolutions for ABR.
    
    Requirements: 10.3 - Support adaptive bitrate (ABR).
    
    Args:
        job_id: UUID of the transcode job
        resolutions: List of resolution strings
        bitrates: Optional list of bitrates
        
    Returns:
        dict: ABR transcoding result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _transcode_abr_async(job_id, resolutions, bitrates)
    )


async def _transcode_abr_async(
    job_id: str,
    resolutions: list[str],
    bitrates: Optional[list[int]],
) -> dict:
    """Async implementation of ABR transcoding."""
    async with async_session_maker() as session:
        job_repo = TranscodeJobRepository(session)
        
        job = await job_repo.get_by_id(uuid.UUID(job_id))
        if not job:
            return {"success": False, "error": "Job not found"}
        
        # Convert resolution strings to enum
        resolution_enums = [Resolution(r) for r in resolutions]
        
        # Create ABR config
        abr_config = ABRConfig(
            resolutions=resolution_enums,
            bitrates=bitrates or [],
        )
        
        # Perform ABR transcoding
        transcoder = ABRTranscoder()
        output_dir = os.path.dirname(job.source_file_path)
        
        results = transcoder.transcode_abr(
            input_path=job.source_file_path,
            output_dir=output_dir,
            config=abr_config,
            latency_mode=job.latency_mode,
        )
        
        # Check results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if successful:
            # Use first successful result for job completion
            first_success = successful[0]
            await job_repo.complete_job(
                job,
                output_file_path=first_success.output_path,
                output_width=first_success.width,
                output_height=first_success.height,
                output_file_size=first_success.file_size,
            )
        else:
            await job_repo.fail_job(job, "All ABR transcodes failed")
        
        await session.commit()
        
        return {
            "success": len(successful) > 0,
            "job_id": job_id,
            "total_resolutions": len(resolutions),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "outputs": [
                {
                    "resolution": resolutions[i],
                    "success": results[i].success,
                    "output_path": results[i].output_path if results[i].success else None,
                    "error": results[i].error_message if not results[i].success else None,
                }
                for i in range(len(results))
            ],
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def dispatch_transcode_job(
    self: BaseTaskWithRetry,
    job_id: str,
) -> dict:
    """Dispatch a transcode job to an available worker.
    
    Requirements: 10.2 - Distribute to FFmpeg worker cluster based on load.
    
    Args:
        job_id: UUID of the transcode job
        
    Returns:
        dict: Dispatch result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _dispatch_job_async(job_id)
    )


async def _dispatch_job_async(job_id: str) -> dict:
    """Async implementation of job dispatch."""
    async with async_session_maker() as session:
        job_repo = TranscodeJobRepository(session)
        worker_repo = TranscodeWorkerRepository(session)
        
        job = await job_repo.get_by_id(uuid.UUID(job_id))
        if not job:
            return {"success": False, "error": "Job not found"}
        
        # Select worker based on load
        requires_4k = WorkerLoadBalancer.requires_4k_support(job.target_resolution)
        worker = await worker_repo.select_worker_by_load(requires_4k=requires_4k)
        
        if not worker:
            return {
                "success": False,
                "error": "No available workers",
                "job_id": job_id,
            }
        
        # Dispatch to worker
        transcode_video_task.delay(job_id)
        
        return {
            "success": True,
            "job_id": job_id,
            "worker_id": str(worker.id),
            "worker_hostname": worker.hostname,
            "worker_load": worker.current_load,
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def process_queued_transcode_jobs(self: BaseTaskWithRetry) -> dict:
    """Process queued transcode jobs.
    
    Periodic task to dispatch queued jobs to available workers.
    
    Returns:
        dict: Processing result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _process_queued_jobs_async()
    )


async def _process_queued_jobs_async() -> dict:
    """Async implementation of queued job processing."""
    dispatched = []
    errors = []
    
    async with async_session_maker() as session:
        job_repo = TranscodeJobRepository(session)
        worker_repo = TranscodeWorkerRepository(session)
        
        # Get queued jobs
        jobs = await job_repo.get_queued_jobs(limit=10)
        
        for job in jobs:
            # Check for available worker
            requires_4k = WorkerLoadBalancer.requires_4k_support(job.target_resolution)
            worker = await worker_repo.select_worker_by_load(requires_4k=requires_4k)
            
            if worker:
                # Dispatch job
                transcode_video_task.delay(str(job.id))
                dispatched.append(str(job.id))
            else:
                errors.append({
                    "job_id": str(job.id),
                    "error": "No available workers",
                })
    
    return {
        "processed_at": datetime.utcnow().isoformat(),
        "dispatched_count": len(dispatched),
        "dispatched_jobs": dispatched,
        "errors": errors,
    }


@celery_app.task
def worker_heartbeat_task(
    hostname: str,
    current_jobs: int,
    current_load: float,
) -> dict:
    """Update worker heartbeat.
    
    Args:
        hostname: Worker hostname
        current_jobs: Current job count
        current_load: Current load percentage
        
    Returns:
        dict: Heartbeat result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _worker_heartbeat_async(hostname, current_jobs, current_load)
    )


async def _worker_heartbeat_async(
    hostname: str,
    current_jobs: int,
    current_load: float,
) -> dict:
    """Async implementation of worker heartbeat."""
    async with async_session_maker() as session:
        repo = TranscodeWorkerRepository(session)
        worker = await repo.heartbeat(hostname, current_jobs, current_load)
        
        if worker:
            await session.commit()
            return {
                "success": True,
                "worker_id": str(worker.id),
                "hostname": hostname,
            }
        else:
            return {
                "success": False,
                "error": "Worker not found",
            }
