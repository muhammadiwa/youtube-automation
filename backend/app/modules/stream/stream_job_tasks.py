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
from app.core.datetime_utils import utcnow, to_naive_utc
from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobHealth,
    StreamJobStatus,
)
from app.modules.stream.stream_job_repository import (
    StreamJobRepository,
    StreamJobHealthRepository,
)


def _run_async(coro):
    """Run async coroutine in Celery task context.
    
    Uses asyncio.run() which creates a fresh event loop for each task.
    Combined with NullPool in celery_session_maker, this avoids
    connection pool conflicts across different event loops.
    """
    return asyncio.run(coro)
from app.modules.stream.ffmpeg_builder import (
    FFmpegCommandBuilder,
    FFmpegOutputParser,
    FFmpegMetrics,
    FFmpegPlaylistCommandBuilder,
)


logger = logging.getLogger(__name__)

# Global storage for log file paths (in-memory, per worker)
log_file_paths: dict[str, str] = {}


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
        return _run_async(_start_ffmpeg_worker_async(job_id))
    except Exception as e:
        logger.error(f"Failed to start FFmpeg worker for job {job_id}: {e}")
        # Update job status to failed
        _run_async(_update_job_status(job_id, StreamJobStatus.FAILED, str(e)))
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
            
            # Log encoder info
            encoder_info = playlist_builder.get_encoder_info()
            logger.info(f"Using encoder: {encoder_info['encoder']} (hardware: {encoder_info['is_hardware']})")
            logger.info(f"FFmpeg playlist command for {len(video_paths)} videos")
        else:
            # Build single video command
            builder = FFmpegCommandBuilder()
            cmd = builder.build_streaming_command(job)
            
            # Log encoder info
            encoder_info = builder.get_encoder_info()
            logger.info(f"Using encoder: {encoder_info['encoder']} (hardware: {encoder_info['is_hardware']})")
        
        logger.info(f"FFmpeg command: {' '.join(cmd[:10])}...")
        
        # Create log file for FFmpeg output
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"ffmpeg_{job_id}.log")
        
        # Open log file for writing
        log_file = open(log_file_path, "w")
        
        # Start FFmpeg process with stderr redirected to log file
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            # Don't create new process group on Windows
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        
        # Update job with PID, status
        job.pid = process.pid
        job.status = StreamJobStatus.RUNNING.value
        job.actual_start_at = to_naive_utc(utcnow())
        await repo.update(job)
        
        # Store log file path for monitoring
        log_file_paths[str(job.id)] = log_file_path
        
        logger.info(f"FFmpeg process started with PID {process.pid} for job {job_id}")
        
        # Start monitoring task
        monitor_ffmpeg_worker.delay(job_id, process.pid)
        
        # Auto-start live chat moderation if this is a YouTube Live stream
        await _start_moderation_for_job(job)
        
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
        return _run_async(_stop_ffmpeg_worker_async(job_id))
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
                process = psutil.Process(job.pid)
                
                # Try graceful termination first (SIGTERM)
                process.terminate()
                
                # Wait up to 3 seconds for graceful shutdown
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # Force kill if still running
                    logger.warning(f"FFmpeg process {job.pid} did not terminate gracefully, killing")
                    process.kill()
                    try:
                        process.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        logger.error(f"FFmpeg process {job.pid} could not be killed")
                
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
        job.actual_end_at = to_naive_utc(utcnow())
        job.is_stream_key_locked = False
        job.update_total_duration()
        job.pid = None
        job.concat_file_path = None
        await repo.update(job)
        
        # Auto-stop live chat moderation
        await _stop_moderation_for_job(job)
        
        # Update video usage tracking if this job has a video_id
        if job.video_id:
            try:
                from app.modules.video.video_usage_tracker import VideoUsageTracker
                usage_tracker = VideoUsageTracker(session)
                
                # Calculate duration
                duration = job.get_duration_seconds()
                
                # Log streaming end
                await usage_tracker.log_streaming_end(
                    video_id=job.video_id,
                    stream_job_id=job.id,
                    duration=duration,
                    viewer_count=0
                )
                logger.info(f"Updated video usage tracking for job {job_id}, duration: {duration}s")
            except Exception as e:
                logger.error(f"Failed to update video usage tracking for job {job_id}: {e}")
        
        return {
            "status": "stopped",
            "job_id": job_id,
        }


# ============================================
# FFmpeg Monitoring Task
# ============================================


@celery_app.task(bind=True)
def monitor_ffmpeg_worker(self, job_id: str, pid: int) -> dict:
    """Initial setup for FFmpeg worker monitoring.
    
    This task only does initial setup. Actual monitoring is done by
    collect_health_metrics periodic task to avoid blocking the worker.
    
    Requirements: 3.4, 3.5, 3.6, 4.1
    
    Args:
        job_id: Stream job UUID string
        pid: FFmpeg process PID
        
    Returns:
        dict: Setup status
    """
    logger.info(f"Setting up monitoring for FFmpeg worker {pid} (job {job_id})")
    
    # Just verify the process exists and return
    # Actual monitoring is done by collect_health_metrics periodic task
    try:
        process = psutil.Process(pid)
        if process.is_running():
            logger.info(f"FFmpeg process {pid} is running, monitoring via periodic task")
            return {
                "status": "monitoring_setup",
                "pid": pid,
                "job_id": job_id,
            }
        else:
            logger.warning(f"FFmpeg process {pid} is not running")
            return {
                "status": "process_not_running",
                "pid": pid,
                "job_id": job_id,
            }
    except psutil.NoSuchProcess:
        logger.warning(f"FFmpeg process {pid} not found")
        return {
            "status": "process_not_found",
            "pid": pid,
            "job_id": job_id,
        }


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
        _run_async(_update_job_status(job_id, StreamJobStatus.STARTING))
        
        # Start worker
        return start_ffmpeg_worker(job_id)
    except Exception as e:
        logger.error(f"Failed to restart FFmpeg worker for job {job_id}: {e}")
        
        # Mark as failed after max retries
        _run_async(_update_job_status(
            job_id, StreamJobStatus.FAILED, f"Failed to restart: {e}"
        ))
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
    
    return _run_async(_check_scheduled_streams_async())


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
    
    # Use asyncio.run() for fresh event loop - avoids event loop conflicts
    return asyncio.run(_collect_health_metrics_async())


async def _collect_health_metrics_async() -> dict:
    """Async implementation of health metrics collection.
    
    Also handles process termination detection and auto-restart.
    Parses FFmpeg log files to extract real-time metrics.
    
    Returns:
        dict: Number of streams checked
    """
    checked_count = 0
    parser = FFmpegOutputParser()
    
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        health_repo = StreamJobHealthRepository(session)
        
        # Get all active jobs
        active_jobs = await repo.get_active_jobs()
        logger.debug(f"Found {len(active_jobs)} active stream jobs to check")
        
        for job in active_jobs:
            try:
                cpu_percent = 0.0
                memory_mb = 0.0
                process_running = False
                
                # Parse FFmpeg metrics from log file
                bitrate = 0
                fps = None
                speed = None
                frame_count = 0
                
                if job.pid:
                    try:
                        process = psutil.Process(job.pid)
                        
                        if process.is_running():
                            process_running = True
                            cpu_percent = process.cpu_percent(interval=0.1)
                            memory_info = process.memory_info()
                            memory_mb = memory_info.rss / (1024 * 1024)
                            
                            # Parse FFmpeg log for metrics
                            log_path = _get_ffmpeg_log_path(str(job.id))
                            metrics = _parse_ffmpeg_log_tail(log_path, parser)
                            if metrics:
                                bitrate = metrics.bitrate
                                fps = metrics.fps
                                speed = metrics.speed
                                frame_count = metrics.frame_count
                                
                                # Update job with latest metrics
                                await repo.update_metrics(
                                    job_id=str(job.id),
                                    bitrate=bitrate,
                                    fps=fps,
                                    speed=speed,
                                    frame_count=frame_count,
                                )
                        else:
                            logger.warning(f"Process {job.pid} for job {job.id} is not running")
                            
                    except psutil.NoSuchProcess:
                        logger.warning(f"Process {job.pid} not found for job {job.id}")
                else:
                    logger.warning(f"Job {job.id} has no PID but status is {job.status}")
                
                # Handle process termination for running jobs
                if job.status == StreamJobStatus.RUNNING.value and not process_running:
                    logger.warning(f"FFmpeg process terminated unexpectedly for job {job.id}")
                    
                    # Check if should auto-restart
                    if job.can_restart():
                        logger.info(f"Auto-restarting job {job.id} (attempt {job.restart_count + 1}/{job.max_restarts})")
                        
                        # Calculate backoff delay
                        delay = min(300, 5 * (2 ** job.restart_count))
                        
                        # Increment restart count
                        await repo.increment_restart_count(str(job.id))
                        
                        # Schedule restart
                        restart_ffmpeg_worker.apply_async(args=[str(job.id)], countdown=delay)
                    else:
                        # Mark as failed
                        await repo.update_status(str(job.id), StreamJobStatus.FAILED, "FFmpeg process terminated unexpectedly")
                    
                    continue  # Skip health record for terminated process
                
                # Create health record for running processes
                if process_running:
                    health = StreamJobHealth(
                        stream_job_id=job.id,
                        bitrate=bitrate,
                        fps=fps,
                        speed=speed,
                        dropped_frames=job.dropped_frames,
                        dropped_frames_delta=0,
                        frame_count=frame_count,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                    )
                    
                    await health_repo.create(health)
                    checked_count += 1
                    logger.debug(f"Saved health metrics for job {job.id}: bitrate={bitrate}, fps={fps}, CPU={cpu_percent:.1f}%")
                        
            except Exception as e:
                logger.error(f"Error collecting metrics for job {job.id}: {e}")
    
    return {"checked": checked_count}


def _parse_ffmpeg_log_tail(log_path: str, parser: FFmpegOutputParser, lines: int = 50) -> Optional[FFmpegMetrics]:
    """Parse the last N lines of FFmpeg log file for metrics.
    
    Args:
        log_path: Path to FFmpeg log file
        parser: FFmpegOutputParser instance
        lines: Number of lines to read from end
        
    Returns:
        Optional[FFmpegMetrics]: Latest metrics or None
    """
    try:
        if not os.path.exists(log_path):
            return None
        
        # Read last N lines efficiently
        with open(log_path, 'rb') as f:
            # Seek to end
            f.seek(0, 2)
            file_size = f.tell()
            
            # Read last chunk (estimate ~200 bytes per line)
            chunk_size = min(file_size, lines * 200)
            f.seek(max(0, file_size - chunk_size))
            
            content = f.read().decode('utf-8', errors='ignore')
        
        # Parse lines from end to find latest metrics
        log_lines = content.split('\n')
        
        for line in reversed(log_lines):
            metrics = parser.parse_line(line)
            if metrics:
                return metrics
        
        return None
        
    except Exception as e:
        logger.debug(f"Error parsing FFmpeg log {log_path}: {e}")
        return None


# ============================================
# Helper Functions
# ============================================


def _get_ffmpeg_log_path(job_id: str) -> str:
    """Get FFmpeg log file path for a job.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        str: Path to log file
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage", "logs")
    return os.path.join(log_dir, f"ffmpeg_{job_id}.log")


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
    """Get video file paths/URLs from a playlist.
    
    For local storage: returns absolute file paths
    For cloud storage (R2/S3): returns presigned URLs (FFmpeg supports HTTP input)
    
    Requirements: 11.1
    
    Args:
        session: Database session
        playlist_id: Playlist UUID string
        
    Returns:
        list[str]: List of video file paths/URLs in order
    """
    from app.modules.stream.repository import StreamPlaylistRepository
    from app.modules.video.repository import VideoRepository
    from app.core.storage import get_file_url_for_ffmpeg, is_cloud_storage, get_storage
    
    playlist_repo = StreamPlaylistRepository(session)
    video_repo = VideoRepository(session)
    
    playlist = await playlist_repo.get_by_id(playlist_id)
    if not playlist:
        return []
    
    video_paths = []
    storage = get_storage()
    
    for item in sorted(playlist.items, key=lambda x: x.position):
        if item.video_id:
            video = await video_repo.get_by_id(item.video_id)
            if video and video.file_path:
                # Get path/URL that FFmpeg can use
                ffmpeg_path = get_file_url_for_ffmpeg(video.file_path, expires_in=86400)
                
                # Validate file exists
                if ffmpeg_path.startswith("http"):
                    # For HTTP URLs, check storage exists
                    if storage.exists(video.file_path):
                        video_paths.append(ffmpeg_path)
                elif os.path.exists(ffmpeg_path):
                    video_paths.append(ffmpeg_path)
                    
        elif item.video_url:
            # Direct URL or path provided
            if item.video_url.startswith("http"):
                video_paths.append(item.video_url)
            elif os.path.exists(item.video_url):
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


# ============================================
# Moderation Integration
# ============================================


async def _start_moderation_for_job(job: StreamJob) -> None:
    """Start live chat moderation for a stream job.
    
    This is called automatically when a stream starts.
    Will auto-detect broadcast_id if not provided.
    
    Only starts moderation if:
    - Stream is going to YouTube Live
    - enable_chat_moderation is True
    - broadcast_id is provided OR can be auto-detected
    
    Args:
        job: Stream job instance
    """
    try:
        # Check if moderation is enabled for this job
        if not getattr(job, 'enable_chat_moderation', True):
            logger.debug(f"Chat moderation disabled for job {job.id}")
            return
        
        # Check if this is a YouTube Live stream
        if not job.rtmp_url or ("youtube.com" not in job.rtmp_url.lower() and "rtmp.youtube.com" not in job.rtmp_url.lower()):
            logger.debug(f"Skipping moderation for job {job.id} - not a YouTube stream")
            return
        
        # Get broadcast_id - either from job or schedule auto-detect
        broadcast_id = getattr(job, 'youtube_broadcast_id', None)
        
        if broadcast_id:
            # We have broadcast_id, start moderation immediately
            await _start_moderation_with_broadcast_id(job, broadcast_id)
        else:
            # Schedule auto-detect task (runs in background with delay)
            # This gives YouTube time to recognize the incoming stream
            logger.info(f"Scheduling broadcast auto-detection for job {job.id}")
            auto_detect_and_start_moderation.apply_async(
                args=[str(job.id)],
                countdown=10,  # Wait 10 seconds before first attempt
            )
                
    except Exception as e:
        logger.error(f"Failed to start moderation for job {job.id}: {e}")
        # Don't fail the stream start if moderation fails


async def _start_moderation_with_broadcast_id(job: StreamJob, broadcast_id: str) -> None:
    """Start moderation with a known broadcast_id.
    
    Args:
        job: Stream job instance
        broadcast_id: YouTube broadcast ID
    """
    from app.modules.moderation.chat_worker import start_moderation_for_broadcast
    
    logger.info(f"Starting chat moderation for job {job.id}, broadcast {broadcast_id}")
    
    await start_moderation_for_broadcast(
        account_id=job.account_id,
        broadcast_id=broadcast_id,
        session_id=None,
    )
    
    logger.info(f"Chat moderation started for job {job.id}")


@celery_app.task(bind=True, max_retries=5)
def auto_detect_and_start_moderation(self, job_id: str) -> dict:
    """Background task to auto-detect broadcast_id and start moderation.
    
    This task runs with retries to give YouTube time to recognize the stream.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status
    """
    logger.info(f"Auto-detecting broadcast for job {job_id} (attempt {self.request.retries + 1})")
    
    try:
        result = _run_async(_auto_detect_and_start_moderation_async(job_id))
        
        if result.get("status") == "not_found":
            # Retry with exponential backoff
            retry_delay = min(60, 10 * (2 ** self.request.retries))  # 10, 20, 40, 60, 60
            logger.info(f"Broadcast not found for job {job_id}, retrying in {retry_delay}s")
            raise self.retry(countdown=retry_delay)
        
        return result
        
    except Exception as e:
        if self.request.retries >= self.max_retries:
            logger.warning(f"Max retries reached for broadcast detection on job {job_id}")
            return {"status": "max_retries", "job_id": job_id}
        raise


async def _auto_detect_and_start_moderation_async(job_id: str) -> dict:
    """Async implementation of auto-detect and start moderation.
    
    Args:
        job_id: Stream job UUID string
        
    Returns:
        dict: Result with status and broadcast_id if found
    """
    from app.modules.account.repository import YouTubeAccountRepository
    from app.modules.stream.youtube_api import YouTubeLiveStreamingClient
    
    async with celery_session_maker() as session:
        repo = StreamJobRepository(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            return {"status": "job_not_found", "job_id": job_id}
        
        # Check if job is still running
        if job.status != StreamJobStatus.RUNNING.value:
            logger.info(f"Job {job_id} is no longer running, skipping moderation")
            return {"status": "job_not_running", "job_id": job_id}
        
        # Check if broadcast_id was already set (maybe manually)
        if job.youtube_broadcast_id:
            logger.info(f"Broadcast ID already set for job {job_id}")
            return {"status": "already_set", "job_id": job_id, "broadcast_id": job.youtube_broadcast_id}
        
        # Get account
        account_repo = YouTubeAccountRepository(session)
        account = await account_repo.get_by_id(str(job.account_id))
        
        if not account or not account.access_token:
            logger.warning(f"No valid account/token for job {job_id}")
            return {"status": "no_account", "job_id": job_id}
        
        # Create YouTube API client
        client = YouTubeLiveStreamingClient(account.access_token)
        
        # Try to find broadcast by stream key
        stream_key = job.stream_key
        broadcast = None
        
        if stream_key:
            broadcast = await client.find_active_broadcast_by_stream_key(stream_key)
        
        # Fallback: get any active broadcast
        if not broadcast:
            broadcast = await client.get_any_active_broadcast()
        
        if not broadcast:
            return {"status": "not_found", "job_id": job_id}
        
        broadcast_id = broadcast.get("id")
        
        # Save broadcast_id to job
        job.youtube_broadcast_id = broadcast_id
        await repo.update(job)
        
        logger.info(f"Auto-detected broadcast ID {broadcast_id} for job {job_id}")
        
        # Start moderation
        await _start_moderation_with_broadcast_id(job, broadcast_id)
        
        return {"status": "started", "job_id": job_id, "broadcast_id": broadcast_id}


async def _stop_moderation_for_job(job: StreamJob) -> None:
    """Stop live chat moderation for a stream job.
    
    This is called automatically when a stream stops.
    
    Args:
        job: Stream job instance
    """
    try:
        from app.modules.moderation.chat_worker import stop_moderation_for_broadcast, get_active_workers
        
        # Find and stop any active moderation workers for this account
        active_workers = get_active_workers()
        
        for key, worker in list(active_workers.items()):
            if str(worker.account_id) == str(job.account_id):
                logger.info(f"Stopping moderation worker for account {job.account_id}")
                await stop_moderation_for_broadcast(
                    account_id=job.account_id,
                    broadcast_id=worker.broadcast_id,
                )
                
    except Exception as e:
        logger.error(f"Failed to stop moderation for job {job.id}: {e}")
        # Don't fail the stream stop if moderation stop fails
