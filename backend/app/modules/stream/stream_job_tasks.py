"""Celery tasks for Stream Job FFmpeg worker management.

Implements FFmpeg subprocess management, health monitoring, and scheduling.
Requirements: 1.2, 1.3, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 7.2
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Optional

import psutil
from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import celery_session_maker
from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobHealth,
    StreamJobStatus,
)
from app.modules.stream.stream_job_repository import (
    StreamJobRepository,
    StreamJobHealthRepository,
)
from app.modules.stream.ffmpeg_builder import (
    FFmpegCommandBuilder,
    FFmpegOutputParser,
    FFmpegMetrics,
    FFmpegPlaylistCommandBuilder,
)


logger = logging.getLogger(__name__)


# ============================================
# FFmpeg Worker Management Tasks
# ============================================


@celery_app.task(bind=True, max_retries=3)
def start_ffmpeg_worker(self, job_id: str) -> dict:
    """Start FFmpeg worker process for a stream job.
    
    Requirements: 1.2, 3.2
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status and PID
    """
    logger.info(f"Starting FFmpeg worker for job {job_id}")
    
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_start_ffmpeg_worker_async(job_id))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Failed to start FFmpeg worker for job {job_id}: {e}")
        # Update job status to failed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_update_job_status(job_id, StreamJobStatus.FAILED, str(e)))
        loop.close()
        raise


async def _start_ffmpeg_worker_async(job_id: str) -> dict:
    """Async implementation of FFmpeg worker start.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status and PID
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            raise ValueError(f"Stream job {job_id} not found")
        
        concat_path = None
        
        # Check if this is a playlist stream
        if job.playlist_id:
            # Get playlist items
            video_paths = await _get_playlist_video_paths(session, job.playlist_id)
            
            if not video_paths:
                raise ValueError(f"No videos found in playlist {job.playlist_id}")
            
            # Build playlist command
            playlist_builder = FFmpegPlaylistCommandBuilder()
            cmd, concat_path = playlist_builder.build_playlist_command(job, video_paths)
            
            # Update job with playlist info
            job.total_playlist_items = len(video_paths)
            job.concat_file_path = concat_path
            
            logger.info(f"FFmpeg playlist command for {len(video_paths)} videos")
        else:
            # Build single video command
            builder = FFmpegCommandBuilder()
            cmd = builder.build_streaming_command(job)
        
        logger.info(f"FFmpeg command: {' '.join(cmd[:10])}...")
        
        # Start FFmpeg process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            # Don't create new process group on Windows
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        
        # Update job with PID and status
        job.pid = process.pid
        job.status = StreamJobStatus.RUNNING.value
        job.actual_start_at = datetime.utcnow()
        await repo.update(job)
        
        logger.info(f"FFmpeg process started with PID {process.pid} for job {job_id}")
        
        # Start monitoring task
        monitor_ffmpeg_worker.delay(job_id, process.pid)
        
        return {
            "status": "started",
            "pid": process.pid,
            "job_id": job_id,
        }


@celery_app.task(bind=True)
def stop_ffmpeg_worker(self, job_id: str) -> dict:
    """Stop FFmpeg worker process for a stream job.
    
    Requirements: 1.3, 3.2
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status
    """
    logger.info(f"Stopping FFmpeg worker for job {job_id}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_stop_ffmpeg_worker_async(job_id))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Failed to stop FFmpeg worker for job {job_id}: {e}")
        raise


async def _stop_ffmpeg_worker_async(job_id: str) -> dict:
    """Async implementation of FFmpeg worker stop.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            raise ValueError(f"Stream job {job_id} not found")
        
        if job.pid:
            try:
                # Try graceful termination first (SIGTERM)
                process = psutil.Process(job.pid)
                process.terminate()
                
                # Wait up to 10 seconds for graceful shutdown
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if still running
                    logger.warning(f"FFmpeg process {job.pid} did not terminate gracefully, killing")
                    process.kill()
                    process.wait(timeout=5)
                
                logger.info(f"FFmpeg process {job.pid} terminated for job {job_id}")
                
            except psutil.NoSuchProcess:
                logger.info(f"FFmpeg process {job.pid} already terminated for job {job_id}")
            except Exception as e:
                logger.error(f"Error terminating FFmpeg process {job.pid}: {e}")
        
        # Cleanup concat file if exists
        if job.concat_file_path:
            await _cleanup_concat_file(str(job.id))
        
        # Update job status
        job.status = StreamJobStatus.STOPPED.value
        job.actual_end_at = datetime.utcnow()
        job.is_stream_key_locked = False
        job.update_total_duration()
        job.pid = None
        job.concat_file_path = None
        await repo.update(job)
        
        return {
            "status": "stopped",
            "job_id": job_id,
        }


# ============================================
# FFmpeg Monitoring Task
# ============================================


@celery_app.task(bind=True)
def monitor_ffmpeg_worker(self, job_id: str, pid: int) -> dict:
    """Monitor FFmpeg worker process and collect metrics.
    
    Requirements: 3.4, 3.5, 3.6, 4.1
    
    Args:
        job_id: Stream job UUID string
        pid: FFmpeg process PID
        
    Returns:
        dict: Final status
    """
    logger.info(f"Starting monitoring for FFmpeg worker {pid} (job {job_id})")
    
    parser = FFmpegOutputParser()
    last_metrics: Optional[FFmpegMetrics] = None
    last_dropped_frames = 0
    last_time = ""
    
    try:
        process = psutil.Process(pid)
        
        while True:
            # Check if process is still running
            if not process.is_running():
                logger.info(f"FFmpeg process {pid} has terminated")
                break
            
            # Get process resource usage
            try:
                cpu_percent = process.cpu_percent(interval=1)
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
            except psutil.NoSuchProcess:
                break
            
            # Read stderr for metrics (non-blocking)
            # Note: In production, use async I/O for better performance
            try:
                # Get FFmpeg stderr output
                # This is a simplified version - in production, use async readers
                stderr_line = _read_ffmpeg_stderr(pid)
                if stderr_line:
                    metrics = parser.parse_line(stderr_line)
                    if metrics:
                        last_metrics = metrics
                        
                        # Check for loop completion
                        if last_time and metrics.time:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            job = loop.run_until_complete(_get_job(job_id))
                            loop.close()
                            
                            if job and parser.detect_loop_completion(
                                metrics.time, last_time, 0  # TODO: Get video duration
                            ):
                                # Increment loop counter
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(_increment_loop(job_id))
                                loop.close()
                        
                        last_time = metrics.time or last_time
            except Exception as e:
                logger.debug(f"Error reading FFmpeg stderr: {e}")
            
            # Save health metrics
            if last_metrics:
                dropped_delta = last_metrics.frame_count - last_dropped_frames if last_dropped_frames else 0
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_save_health_metrics(
                    job_id=job_id,
                    bitrate=last_metrics.bitrate,
                    fps=last_metrics.fps,
                    speed=last_metrics.speed,
                    dropped_frames=0,  # FFmpeg doesn't report this directly
                    dropped_frames_delta=max(0, dropped_delta),
                    frame_count=last_metrics.frame_count,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                ))
                loop.close()
                
                # Update job metrics
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_update_job_metrics(
                    job_id=job_id,
                    bitrate=last_metrics.bitrate,
                    fps=last_metrics.fps,
                    speed=last_metrics.speed,
                    frame_count=last_metrics.frame_count,
                ))
                loop.close()
            
            # Wait before next check
            time.sleep(10)
        
        # Process ended - check exit status
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        job = loop.run_until_complete(_get_job(job_id))
        loop.close()
        
        if job and job.status == StreamJobStatus.RUNNING.value:
            # Unexpected termination
            logger.warning(f"FFmpeg process {pid} terminated unexpectedly for job {job_id}")
            
            # Check if should auto-restart
            if job.can_restart():
                logger.info(f"Auto-restarting job {job_id} (attempt {job.restart_count + 1}/{job.max_restarts})")
                
                # Calculate backoff delay
                delay = min(300, 5 * (2 ** job.restart_count))
                
                # Schedule restart
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_increment_restart_count(job_id))
                loop.close()
                
                restart_ffmpeg_worker.apply_async(args=[job_id], countdown=delay)
            else:
                # Mark as failed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_update_job_status(
                    job_id, StreamJobStatus.FAILED, "FFmpeg process terminated unexpectedly"
                ))
                loop.close()
        
        return {"status": "monitoring_ended", "job_id": job_id}
        
    except psutil.NoSuchProcess:
        logger.info(f"FFmpeg process {pid} no longer exists")
        return {"status": "process_not_found", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error monitoring FFmpeg worker {pid}: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def restart_ffmpeg_worker(self, job_id: str) -> dict:
    """Restart FFmpeg worker with exponential backoff.
    
    Requirements: 3.3
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status
    """
    logger.info(f"Restarting FFmpeg worker for job {job_id}")
    
    try:
        # Update status to starting
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_update_job_status(job_id, StreamJobStatus.STARTING))
        loop.close()
        
        # Start worker
        return start_ffmpeg_worker(job_id)
    except Exception as e:
        logger.error(f"Failed to restart FFmpeg worker for job {job_id}: {e}")
        
        # Mark as failed after max retries
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_update_job_status(
            job_id, StreamJobStatus.FAILED, f"Failed to restart: {e}"
        ))
        loop.close()
        raise


# ============================================
# Scheduling Tasks (Requirements: 7.2)
# ============================================


@celery_app.task
def check_scheduled_streams() -> dict:
    """Check and start scheduled streams.
    
    Requirements: 7.2
    
    This task runs periodically (every 10 seconds) via Celery Beat.
    
    Returns:
        dict: Number of streams started
    """
    logger.debug("Checking scheduled streams")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_check_scheduled_streams_async())
    loop.close()
    
    return result


async def _check_scheduled_streams_async() -> dict:
    """Async implementation of scheduled stream check.
    
    Returns:
        dict: Number of streams started
    """
    started_count = 0
    
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        
        # Get scheduled jobs that should start
        jobs = await repo.get_scheduled_jobs()
        
        for job in jobs:
            if job.should_start_now():
                logger.info(f"Starting scheduled stream job {job.id}")
                
                # Update status and start
                job.status = StreamJobStatus.STARTING.value
                await repo.update(job)
                
                # Queue start task
                start_ffmpeg_worker.delay(str(job.id))
                started_count += 1
        
        # Check for jobs that should stop
        jobs_to_stop = await repo.get_jobs_to_stop()
        
        for job in jobs_to_stop:
            logger.info(f"Stopping scheduled stream job {job.id} (end time reached)")
            
            job.status = StreamJobStatus.STOPPING.value
            await repo.update(job)
            
            stop_ffmpeg_worker.delay(str(job.id))
    
    return {"started": started_count, "stopped": len(jobs_to_stop)}


@celery_app.task
def collect_health_metrics() -> dict:
    """Collect health metrics for all active streams.
    
    Requirements: 4.1
    
    This task runs periodically (every 10 seconds) via Celery Beat.
    
    Returns:
        dict: Number of streams checked
    """
    logger.debug("Collecting health metrics for active streams")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_collect_health_metrics_async())
    loop.close()
    
    return result


async def _collect_health_metrics_async() -> dict:
    """Async implementation of health metrics collection.
    
    Returns:
        dict: Number of streams checked
    """
    checked_count = 0
    
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        health_repo = StreamJobHealthRepository(session)
        
        # Get all active jobs
        active_jobs = await repo.get_active_jobs()
        
        for job in active_jobs:
            if job.pid:
                try:
                    process = psutil.Process(job.pid)
                    
                    if process.is_running():
                        cpu_percent = process.cpu_percent(interval=0.1)
                        memory_info = process.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)
                        
                        # Create health record
                        health = StreamJobHealth(
                            stream_job_id=job.id,
                            bitrate=job.current_bitrate or 0,
                            fps=job.current_fps,
                            speed=job.current_speed,
                            dropped_frames=job.dropped_frames,
                            dropped_frames_delta=0,
                            frame_count=job.frame_count,
                            cpu_percent=cpu_percent,
                            memory_mb=memory_mb,
                        )
                        
                        await health_repo.create(health)
                        checked_count += 1
                        
                except psutil.NoSuchProcess:
                    logger.warning(f"Process {job.pid} not found for job {job.id}")
                except Exception as e:
                    logger.error(f"Error collecting metrics for job {job.id}: {e}")
    
    return {"checked": checked_count}


# ============================================
# Helper Functions
# ============================================


def _read_ffmpeg_stderr(pid: int) -> Optional[str]:
    """Read FFmpeg stderr output (simplified version).
    
    In production, use async I/O with proper buffering.
    
    Args:
        pid: FFmpeg process PID
        
    Returns:
        Optional[str]: Latest stderr line or None
    """
    # This is a placeholder - in production, implement proper stderr reading
    # using async subprocess or file-based logging
    return None


async def _get_job(job_id: str) -> Optional[StreamJob]:
    """Get stream job by ID.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        Optional[StreamJob]: Stream job or None
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        return await repo.get_by_id(job_id)


async def _update_job_status(
    job_id: str,
    status: StreamJobStatus,
    error: Optional[str] = None,
) -> None:
    """Update stream job status.
    
    Args:
        job_id: Stream job UUID string
        status: New status
        error: Optional error message
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        await repo.update_status(job_id, status, error)


async def _update_job_metrics(
    job_id: str,
    bitrate: Optional[int] = None,
    fps: Optional[float] = None,
    speed: Optional[str] = None,
    frame_count: Optional[int] = None,
) -> None:
    """Update stream job metrics.
    
    Args:
        job_id: Stream job UUID string
        bitrate: Current bitrate
        fps: Current FPS
        speed: Current speed
        frame_count: Frame count
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        await repo.update_metrics(
            job_id=job_id,
            bitrate=bitrate,
            fps=fps,
            speed=speed,
            frame_count=frame_count,
        )


async def _increment_loop(job_id: str) -> None:
    """Increment loop counter for a stream job.
    
    Args:
        job_id: Stream job UUID string
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        job = await repo.increment_loop(job_id)
        
        # Check if loop complete
        if job and job.is_loop_complete():
            logger.info(f"Loop complete for job {job_id}, stopping stream")
            job.status = StreamJobStatus.COMPLETED.value
            await repo.update(job)
            
            # Stop the FFmpeg process
            if job.pid:
                stop_ffmpeg_worker.delay(str(job_id))


async def _increment_restart_count(job_id: str) -> None:
    """Increment restart counter for a stream job.
    
    Args:
        job_id: Stream job UUID string
    """
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        await repo.increment_restart_count(job_id)


async def _get_playlist_video_paths(session, playlist_id: str) -> list[str]:
    """Get video file paths from a playlist.
    
    Requirements: 11.1
    
    Args:
        session: Database session
        playlist_id: Playlist UUID string
        
    Returns:
        list[str]: List of video file paths in order
    """
    from app.modules.stream.repository import StreamPlaylistRepository
    from app.modules.video.repository import VideoRepository
    
    playlist_repo = StreamPlaylistRepository(session)
    video_repo = VideoRepository(session)
    
    playlist = await playlist_repo.get_by_id(playlist_id)
    if not playlist:
        return []
    
    video_paths = []
    for item in sorted(playlist.items, key=lambda x: x.position):
        if item.video_id:
            video = await video_repo.get_by_id(item.video_id)
            if video and video.local_path and os.path.exists(video.local_path):
                video_paths.append(video.local_path)
        elif item.video_url and os.path.exists(item.video_url):
            video_paths.append(item.video_url)
    
    return video_paths


async def _cleanup_concat_file(job_id: str) -> None:
    """Cleanup concat file for a job.
    
    Args:
        job_id: Stream job UUID string
    """
    from app.modules.stream.ffmpeg_builder import FFmpegPlaylistCommandBuilder
    
    builder = FFmpegPlaylistCommandBuilder()
    builder.cleanup(job_id)


async def _save_health_metrics(
    job_id: str,
    bitrate: int,
    fps: Optional[float],
    speed: Optional[str],
    dropped_frames: int,
    dropped_frames_delta: int,
    frame_count: int,
    cpu_percent: float,
    memory_mb: float,
) -> None:
    """Save health metrics for a stream job.
    
    Args:
        job_id: Stream job UUID string
        bitrate: Current bitrate in bps
        fps: Current FPS
        speed: Current speed
        dropped_frames: Total dropped frames
        dropped_frames_delta: Dropped frames since last check
        frame_count: Total frame count
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in MB
    """
    async with celery_session_maker() as session:
        health_repo = StreamJobHealthRepository(session)
        
        health = StreamJobHealth(
            stream_job_id=job_id,
            bitrate=bitrate,
            fps=fps,
            speed=speed,
            dropped_frames=dropped_frames,
            dropped_frames_delta=dropped_frames_delta,
            frame_count=frame_count,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
        )
        
        await health_repo.create(health)
