"""Stream Job Router for Video-to-Live streaming API endpoints.

Provides REST API endpoints for stream job management.
Requirements: 1.1, 1.2, 1.3, 1.5, 4.7, 6.4, 9.1
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import ensure_utc
from app.modules.auth.jwt import get_current_user
from app.modules.stream.stream_job_models import StreamJobStatus
from app.modules.stream.stream_job_schemas import (
    CreateStreamJobRequest,
    UpdateStreamJobRequest,
    StreamJobResponse,
    StreamJobListResponse,
    StreamJobHealthResponse,
    StreamJobHealthListResponse,
    SlotStatusResponse,
    ResourceDashboardResponse,
    StreamJobHistoryItem,
    StreamJobHistoryResponse,
    StreamAnalyticsSummary,
    BulkCreateStreamJobRequest,
    BulkCreateStreamJobResponse,
)
from app.modules.stream.stream_job_service import (
    StreamJobService,
    StreamJobNotFoundError,
    VideoNotFoundError,
    AccountNotFoundError,
    SlotLimitExceededError,
    StreamKeyInUseError,
    InvalidStatusTransitionError,
    StreamNotRunningError,
    StreamAlreadyRunningError,
)


router = APIRouter(prefix="/stream-jobs", tags=["stream-jobs"])


def get_stream_job_service(session: AsyncSession = Depends(get_db)) -> StreamJobService:
    """Dependency for getting stream job service."""
    return StreamJobService(session)


# ============================================
# Stream Job CRUD Endpoints (Requirements: 1.1, 1.5)
# ============================================


@router.post(
    "",
    response_model=StreamJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a stream job",
    description="Create a new Video-to-Live stream job.",
)
async def create_stream_job(
    request: CreateStreamJobRequest,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Create a new stream job.
    
    Requirements: 1.1
    
    Args:
        request: Stream job creation request
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Created stream job
    """
    try:
        job = await service.create_stream_job(
            user_id=current_user.id,
            request=request,
        )
        return StreamJobResponse.from_model(job)
    except VideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/bulk",
    response_model=BulkCreateStreamJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create stream jobs",
    description="Create multiple stream jobs with different schedules at once.",
)
async def bulk_create_stream_jobs(
    request: BulkCreateStreamJobRequest,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> BulkCreateStreamJobResponse:
    """Bulk create stream jobs with multiple schedules.
    
    Creates multiple stream jobs from a single video with different
    scheduled start/end times. Useful for recurring streams.
    
    Args:
        request: Bulk create request with schedules
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        BulkCreateStreamJobResponse: Results of bulk creation
    """
    from datetime import datetime, timezone, timedelta
    
    created_jobs = []
    errors = []
    
    # Create timezone from offset (offset is in minutes)
    # Note: timedelta uses opposite sign - if user is UTC+7, offset is +420
    # but we need to subtract to convert local to UTC
    tz_offset = timedelta(minutes=request.timezone_offset)
    user_tz = timezone(tz_offset)
    
    for schedule in request.schedules:
        try:
            # Parse date and times
            date_str = schedule.date
            start_time_str = schedule.start_time
            end_time_str = schedule.end_time
            
            # Create datetime objects in user's local timezone
            local_start = datetime.strptime(
                f"{date_str} {start_time_str}", 
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=user_tz)
            
            # Convert to UTC for storage
            scheduled_start = local_start.astimezone(timezone.utc)
            
            scheduled_end = None
            if end_time_str:
                local_end = datetime.strptime(
                    f"{date_str} {end_time_str}",
                    "%Y-%m-%d %H:%M"
                ).replace(tzinfo=user_tz)
                
                # Handle overnight streams (end time is next day)
                if local_end <= local_start:
                    local_end += timedelta(days=1)
                
                # Convert to UTC for storage
                scheduled_end = local_end.astimezone(timezone.utc)
            
            # Create stream job request
            job_request = CreateStreamJobRequest(
                account_id=request.account_id,
                video_id=request.video_id,
                video_path=request.video_path,
                title=f"{request.title} - {date_str}",
                description=request.description,
                rtmp_url=request.rtmp_url,
                stream_key=request.stream_key,
                loop_mode=request.loop_mode,
                loop_count=request.loop_count,
                resolution=request.resolution,
                target_bitrate=request.target_bitrate,
                encoding_mode=request.encoding_mode,
                target_fps=request.target_fps,
                enable_auto_restart=request.enable_auto_restart,
                max_restarts=request.max_restarts,
                enable_chat_moderation=request.enable_chat_moderation,
                scheduled_start_at=scheduled_start,
                scheduled_end_at=scheduled_end,
            )
            
            job = await service.create_stream_job(
                user_id=current_user.id,
                request=job_request,
            )
            
            created_jobs.append({
                "id": str(job.id),
                "title": job.title,
                "scheduled_start_at": scheduled_start.isoformat(),
                "scheduled_end_at": scheduled_end.isoformat() if scheduled_end else None,
                "status": job.status,
            })
            
        except Exception as e:
            errors.append(f"Failed to create job for {schedule.date}: {str(e)}")
    
    return BulkCreateStreamJobResponse(
        total_requested=len(request.schedules),
        total_created=len(created_jobs),
        created_jobs=created_jobs,
        errors=errors,
    )


@router.get(
    "",
    response_model=StreamJobListResponse,
    summary="List stream jobs",
    description="Get all stream jobs for the current user.",
)
async def list_stream_jobs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="page_size", description="Items per page"),
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobListResponse:
    """List stream jobs for the current user.
    
    Requirements: 1.5
    
    Args:
        status_filter: Optional status filter
        account_id: Optional account filter
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobListResponse: List of stream jobs with pagination
    """
    # Validate status filter
    if status_filter:
        try:
            StreamJobStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )
    
    jobs, total = await service.list_stream_jobs(
        user_id=current_user.id,
        status=status_filter,
        account_id=account_id,
        page=page,
        page_size=page_size,
    )
    
    return StreamJobListResponse(
        jobs=[StreamJobResponse.from_model(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# Static Routes (MUST be before /{job_id} routes)
# ============================================


@router.get(
    "/slots",
    response_model=SlotStatusResponse,
    summary="Get slot status",
    description="Get stream slot usage for the current user.",
)
async def get_slot_status(
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> SlotStatusResponse:
    """Get slot status for the current user.
    
    Requirements: 6.4
    """
    return await service.get_slot_status(current_user.id)


@router.get(
    "/resources",
    response_model=ResourceDashboardResponse,
    summary="Get resource usage",
    description="Get resource usage dashboard for active streams.",
)
async def get_resource_usage(
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> ResourceDashboardResponse:
    """Get resource usage dashboard.
    
    Requirements: 9.1, 9.5
    """
    return await service.get_resource_usage(current_user.id)


@router.get(
    "/history",
    response_model=StreamJobHistoryResponse,
    summary="Get stream history",
    description="Get completed stream job history for the current user.",
)
async def get_stream_history(
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="page_size", description="Items per page"),
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobHistoryResponse:
    """Get stream job history.
    
    Requirements: 12.2
    """
    jobs, total = await service.get_history(
        user_id=current_user.id,
        days=days,
        page=page,
        page_size=page_size,
    )
    
    items = [
        StreamJobHistoryItem(
            id=job.id,
            title=job.title,
            status=job.status,
            loop_mode=job.loop_mode,
            resolution=job.resolution,
            target_bitrate=job.target_bitrate,
            actual_start_at=ensure_utc(job.actual_start_at),
            actual_end_at=ensure_utc(job.actual_end_at),
            total_duration_seconds=job.total_duration_seconds,
            total_loops=job.current_loop,
            avg_bitrate_kbps=job.current_bitrate / 1000 if job.current_bitrate else None,
            total_dropped_frames=job.dropped_frames,
            created_at=ensure_utc(job.created_at),
        )
        for job in jobs
    ]
    
    return StreamJobHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/analytics",
    response_model=StreamAnalyticsSummary,
    summary="Get analytics summary",
    description="Get stream analytics summary for the current user.",
)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamAnalyticsSummary:
    """Get analytics summary.
    
    Requirements: 12.5
    """
    analytics = await service.get_analytics_summary(
        user_id=current_user.id,
        days=days,
    )
    
    return StreamAnalyticsSummary(**analytics)


@router.get(
    "/encoder/info",
    summary="Get encoder information",
    description="Get information about available video encoders.",
)
async def get_encoder_info(
    current_user=Depends(get_current_user),
) -> dict:
    """Get encoder information.
    
    Returns information about available hardware encoders and
    which encoder will be used for streaming.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Encoder information
    """
    from app.modules.stream.ffmpeg_builder import (
        FFmpegCommandBuilder,
        detect_available_encoders,
        HardwareEncoder,
        HARDWARE_ENCODER_CONFIG,
    )
    
    builder = FFmpegCommandBuilder()
    available = detect_available_encoders()
    
    return {
        "current_encoder": builder.get_encoder_info(),
        "available_encoders": [
            {
                "name": enc.value,
                "type": "hardware" if enc != HardwareEncoder.SOFTWARE else "software",
                "description": _get_encoder_description(enc),
            }
            for enc in available
        ],
        "hardware_acceleration": builder.encoder != HardwareEncoder.SOFTWARE,
    }


def _get_encoder_description(encoder) -> str:
    """Get human-readable description for encoder."""
    from app.modules.stream.ffmpeg_builder import HardwareEncoder
    
    descriptions = {
        HardwareEncoder.NVENC: "NVIDIA GPU (NVENC) - Very low CPU usage",
        HardwareEncoder.QSV: "Intel Quick Sync Video - Low CPU usage",
        HardwareEncoder.AMF: "AMD GPU (AMF) - Very low CPU usage",
        HardwareEncoder.VIDEOTOOLBOX: "Apple VideoToolbox - Low CPU usage (macOS)",
        HardwareEncoder.SOFTWARE: "CPU Software Encoding (libx264) - High CPU usage",
    }
    return descriptions.get(encoder, "Unknown encoder")


@router.get(
    "/export",
    summary="Export stream data",
    description="Export stream job data as CSV.",
)
async def export_stream_data(
    days: int = Query(30, ge=1, le=365, description="Days to export"),
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
):
    """Export stream data as CSV.
    
    Requirements: 12.4
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    data = await service.export_to_csv(
        user_id=current_user.id,
        days=days,
    )
    
    # Create CSV in memory
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=stream_jobs_export.csv"
        },
    )


# ============================================
# Dynamic Routes (with {job_id} parameter)
# ============================================


@router.get(
    "/{job_id}",
    response_model=StreamJobResponse,
    summary="Get a stream job",
    description="Get stream job details by ID.",
)
async def get_stream_job(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Get stream job by ID.
    
    Requirements: 1.5
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Stream job details
    """
    try:
        job = await service.get_stream_job(job_id, current_user.id)
        return StreamJobResponse.from_model(job)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/{job_id}",
    response_model=StreamJobResponse,
    summary="Update a stream job",
    description="Update stream job configuration.",
)
async def update_stream_job(
    job_id: uuid.UUID,
    request: UpdateStreamJobRequest,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Update a stream job.
    
    Args:
        job_id: Stream job UUID
        request: Update request
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Updated stream job
    """
    try:
        job = await service.update_stream_job(
            job_id=job_id,
            user_id=current_user.id,
            request=request,
        )
        return StreamJobResponse.from_model(job)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stream job",
    description="Delete a stream job.",
)
async def delete_stream_job(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> None:
    """Delete a stream job.
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
    """
    try:
        await service.delete_stream_job(job_id, current_user.id)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Stream Control Endpoints (Requirements: 1.2, 1.3)
# ============================================


@router.post(
    "/{job_id}/start",
    response_model=StreamJobResponse,
    summary="Start a stream job",
    description="Start streaming for a stream job.",
)
async def start_stream_job(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Start a stream job.
    
    Requirements: 1.2
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Updated stream job
    """
    try:
        job = await service.start_stream_job(job_id, current_user.id)
        return StreamJobResponse.from_model(job)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SlotLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        )
    except StreamKeyInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except StreamAlreadyRunningError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{job_id}/stop",
    response_model=StreamJobResponse,
    summary="Stop a stream job",
    description="Stop streaming for a stream job.",
)
async def stop_stream_job(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Stop a stream job.
    
    Requirements: 1.3
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Updated stream job
    """
    try:
        job = await service.stop_stream_job(job_id, current_user.id)
        return StreamJobResponse.from_model(job)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except StreamNotRunningError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{job_id}/restart",
    response_model=StreamJobResponse,
    summary="Restart a stream job",
    description="Restart streaming for a stream job.",
)
async def restart_stream_job(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobResponse:
    """Restart a stream job.
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobResponse: Updated stream job
    """
    try:
        job = await service.restart_stream_job(job_id, current_user.id)
        return StreamJobResponse.from_model(job)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (SlotLimitExceededError, StreamKeyInUseError) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


# ============================================
# Health Endpoints (Requirements: 4.7)
# ============================================


@router.get(
    "/{job_id}/health",
    response_model=StreamJobHealthListResponse,
    summary="Get health history",
    description="Get health metrics history for a stream job.",
)
async def get_health_history(
    job_id: uuid.UUID,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, alias="page_size", description="Items per page"),
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobHealthListResponse:
    """Get health history for a stream job.
    
    Requirements: 4.7
    
    Args:
        job_id: Stream job UUID
        hours: Hours to look back
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobHealthListResponse: Health history with pagination
    """
    try:
        records, total = await service.get_health_history(
            job_id=job_id,
            user_id=current_user.id,
            hours=hours,
            page=page,
            page_size=page_size,
        )
        
        return StreamJobHealthListResponse(
            records=[StreamJobHealthResponse.from_model(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
        )
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{job_id}/health/latest",
    response_model=StreamJobHealthResponse,
    summary="Get latest health",
    description="Get latest health metrics for a stream job.",
)
async def get_health_latest(
    job_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobHealthResponse:
    """Get latest health for a stream job.
    
    Requirements: 4.7
    
    Args:
        job_id: Stream job UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobHealthResponse: Latest health metrics
    """
    try:
        health = await service.get_health_latest(job_id, current_user.id)
        if not health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No health data available",
            )
        return StreamJobHealthResponse.from_model(health)
    except StreamJobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/health/{health_id}/acknowledge",
    response_model=StreamJobHealthResponse,
    summary="Acknowledge alert",
    description="Acknowledge a health alert.",
)
async def acknowledge_alert(
    health_id: uuid.UUID,
    current_user=Depends(get_current_user),
    service: StreamJobService = Depends(get_stream_job_service),
) -> StreamJobHealthResponse:
    """Acknowledge a health alert.
    
    Args:
        health_id: Health record UUID
        current_user: Current authenticated user
        service: Stream job service instance
        
    Returns:
        StreamJobHealthResponse: Updated health record
    """
    health = await service.acknowledge_alert(health_id, current_user.id)
    if not health:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health record not found",
        )
    return StreamJobHealthResponse.from_model(health)


# ============================================
# WebSocket Endpoint (Requirements: 4.6)
# ============================================


@router.websocket("/{job_id}/health/ws")
async def health_websocket(
    websocket: WebSocket,
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time health updates.
    
    Requirements: 4.6
    
    Args:
        websocket: WebSocket connection
        job_id: Stream job UUID
        session: Database session
    """
    await websocket.accept()
    
    service = StreamJobService(session)
    
    try:
        # Verify job exists (no user auth for WebSocket for simplicity)
        job = await service.job_repo.get_by_id(job_id)
        if not job:
            await websocket.close(code=4004, reason="Stream job not found")
            return
        
        # Send initial health data
        health = await service.health_repo.get_latest(job_id)
        if health:
            await websocket.send_json(health.to_dict())
        
        # Keep connection alive and send updates
        import asyncio
        while True:
            # Wait for 10 seconds
            await asyncio.sleep(10)
            
            # Get latest health
            health = await service.health_repo.get_latest(job_id)
            if health:
                await websocket.send_json(health.to_dict())
            
            # Check if job is still active
            job = await service.job_repo.get_by_id(job_id)
            if not job or not job.is_active():
                await websocket.send_json({
                    "type": "stream_ended",
                    "status": job.status if job else "unknown",
                })
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))


# ============================================
# Video Library Integration Endpoints (Requirements: 3.1, 3.2, 3.3)
# ============================================


@router.post(
    "/from-video/{video_id}",
    response_model=StreamJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create stream from video library",
    description="Create a stream job from a video in the library.",
)
async def create_stream_from_video(
    video_id: uuid.UUID,
    request: CreateStreamJobRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamJobResponse:
    """Create a stream job from a video in the library.
    
    Requirements: 3.1
    
    Args:
        video_id: Video UUID from library
        request: Stream job creation request
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        StreamJobResponse: Created stream job
    """
    from app.modules.stream.video_library_integration import VideoLibraryStreamIntegration
    
    try:
        integration = VideoLibraryStreamIntegration(session)
        job = await integration.create_stream_from_video(
            user_id=current_user.id,
            video_id=video_id,
            request=request,
        )
        return StreamJobResponse.from_model(job)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/video/{video_id}/status",
    summary="Get video streaming status",
    description="Get streaming status and usage for a video from library.",
)
async def get_video_streaming_status(
    video_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Get streaming status for a video.
    
    Requirements: 3.3
    
    Args:
        video_id: Video UUID
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Streaming status information
    """
    from app.modules.stream.video_library_integration import VideoLibraryStreamIntegration
    
    try:
        integration = VideoLibraryStreamIntegration(session)
        return await integration.get_video_streaming_status(
            video_id=video_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
