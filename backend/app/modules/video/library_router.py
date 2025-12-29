"""Video Library API router.

Implements REST endpoints for video library management.
Requirements: 1.1, 1.2, 1.3
"""

import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
    Response
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.jwt import get_current_user
from app.modules.video.video_library_service import (
    VideoLibraryService,
    VideoFilters,
    Pagination
)
from app.modules.video.video_folder_service import VideoFolderService
from app.modules.video.youtube_upload_service import YouTubeUploadService
from app.modules.video.video_usage_tracker import VideoUsageTracker
from app.modules.video.schemas import (
    VideoResponse,
    VideoMetadataUpdate,
    PaginatedVideoResponse,
    VideoFolderResponse,
    VideoFolderCreate,
    VideoFolderUpdate,
    YouTubeUploadRequest,
    UploadProgressResponse,
    UploadJobResponse
)

router = APIRouter(prefix="/videos/library", tags=["video-library"])


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_to_library(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    folder_id: Optional[uuid.UUID] = Form(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload video to library.
    
    Uploads video file to storage and extracts metadata.
    Does not upload to YouTube - that's a separate action.
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    video = await service.upload_to_library(
        user_id=user_id,
        file=file,
        title=title,
        description=description,
        tags=tag_list,
        folder_id=folder_id
    )
    
    return VideoResponse.from_orm(video)


@router.get("", response_model=PaginatedVideoResponse)
async def get_library_videos(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    folder_id: Optional[uuid.UUID] = Query(None, description="Filter by folder"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get library videos with filters and pagination."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # Build filters
    filters = VideoFilters(
        folder_id=folder_id,
        status=status,
        search=search,
        tags=tag_list,
        is_favorite=is_favorite,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    pagination = Pagination(page=page, limit=limit)
    
    videos, total = await service.get_library_videos(
        user_id=user_id,
        filters=filters,
        pagination=pagination
    )
    
    import math
    total_pages = math.ceil(total / limit) if total > 0 else 0
    
    return PaginatedVideoResponse(
        items=[VideoResponse.from_orm(v) for v in videos],
        total=total,
        page=page,
        pageSize=limit,
        totalPages=total_pages
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video_details(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get video details by ID."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    return VideoResponse.from_orm(video)


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video_metadata(
    video_id: uuid.UUID,
    metadata: VideoMetadataUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update video metadata."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.update_metadata(
        video_id=video_id,
        user_id=user_id,
        title=metadata.title,
        description=metadata.description,
        tags=metadata.tags,
        notes=metadata.notes if hasattr(metadata, 'notes') else None
    )
    
    return VideoResponse.from_orm(video)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete video from library."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    await service.delete_from_library(
        video_id=video_id,
        user_id=user_id
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{video_id}/favorite", response_model=VideoResponse)
async def toggle_favorite(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle video favorite status."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.toggle_favorite(
        video_id=video_id,
        user_id=user_id
    )
    
    return VideoResponse.from_orm(video)


@router.post("/{video_id}/move")
async def move_to_folder(
    video_id: uuid.UUID,
    folder_id: Optional[uuid.UUID] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move video to folder (or root if folder_id is None)."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.move_to_folder(
        video_id=video_id,
        user_id=user_id,
        folder_id=folder_id
    )
    
    return VideoResponse.from_orm(video)


@router.get("/{video_id}/stream")
async def stream_video_preview(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream video for preview.
    
    Returns video file URL for streaming.
    Note: Actual streaming is handled by storage service (S3/MinIO).
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    # Get video to verify ownership
    video = await service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get streaming URL from storage
    from app.modules.video.video_storage_service import VideoStorageService
    from app.core.storage import get_storage_service
    
    storage_service = VideoStorageService(get_storage_service())
    stream_url = await storage_service.get_video_url(
        video_id=video_id,
        user_id=user_id,
        expiry_seconds=3600  # 1 hour
    )
    
    return {"stream_url": stream_url}


# Folder Management Endpoints

@router.get("/folders/all", response_model=list[VideoFolderResponse])
async def get_all_folders(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all folders for user (tree structure)."""
    service = VideoFolderService(db)
    user_id = current_user.id
    
    folders = await service.get_folder_tree(user_id=user_id)
    
    return [VideoFolderResponse.from_orm(f) for f in folders]


@router.post("/folders", response_model=VideoFolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder: VideoFolderCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new folder."""
    service = VideoFolderService(db)
    user_id = current_user.id
    
    new_folder = await service.create_folder(
        user_id=user_id,
        name=folder.name,
        parent_id=folder.parent_id,
        description=folder.description,
        color=folder.color,
        icon=folder.icon
    )
    
    return VideoFolderResponse.from_orm(new_folder)


@router.patch("/folders/{folder_id}", response_model=VideoFolderResponse)
async def update_folder(
    folder_id: uuid.UUID,
    folder: VideoFolderUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update folder."""
    service = VideoFolderService(db)
    user_id = current_user.id
    
    updated_folder = await service.update_folder(
        folder_id=folder_id,
        user_id=user_id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        icon=folder.icon
    )
    
    return VideoFolderResponse.from_orm(updated_folder)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete folder (must be empty)."""
    service = VideoFolderService(db)
    user_id = current_user.id
    
    await service.delete_folder(
        folder_id=folder_id,
        user_id=user_id
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# YouTube Upload Endpoints

@router.post("/{video_id}/upload-to-youtube")
async def upload_to_youtube(
    video_id: uuid.UUID,
    upload_request: YouTubeUploadRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload library video to YouTube."""
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    result = await service.upload_to_youtube(
        video_id=video_id,
        user_id=user_id,
        account_id=upload_request.account_id,
        title=upload_request.title,
        description=upload_request.description,
        tags=upload_request.tags,
        category_id=upload_request.category_id,
        visibility=upload_request.visibility,
        scheduled_publish_at=upload_request.scheduled_publish_at
    )
    
    return result


@router.get("/{video_id}/upload-progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get YouTube upload progress."""
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    progress = await service.get_upload_progress(
        video_id=video_id,
        user_id=user_id
    )
    
    return UploadProgressResponse(**progress)


@router.post("/{video_id}/retry-upload")
async def retry_youtube_upload(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry failed YouTube upload."""
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    result = await service.retry_upload(
        video_id=video_id,
        user_id=user_id
    )
    
    return result


@router.post("/{video_id}/cancel-upload")
async def cancel_youtube_upload(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel ongoing YouTube upload."""
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    result = await service.cancel_upload(
        video_id=video_id,
        user_id=user_id
    )
    
    return result


@router.get("/{video_id}/youtube-info")
async def get_youtube_video_info(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get YouTube video information and statistics."""
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    info = await service.get_youtube_video_info(
        video_id=video_id,
        user_id=user_id
    )
    
    return info


@router.post("/bulk-upload-to-youtube")
async def bulk_upload_to_youtube(
    video_ids: list[uuid.UUID],
    account_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk upload multiple library videos to YouTube.
    
    Uploads multiple videos to the same YouTube account.
    Each video uses its existing metadata from the library.
    """
    service = YouTubeUploadService(db)
    user_id = current_user.id
    
    jobs = []
    errors = []
    
    for video_id in video_ids:
        try:
            result = await service.upload_to_youtube(
                video_id=video_id,
                user_id=user_id,
                account_id=account_id,
                # Use existing metadata from library
                title=None,
                description=None,
                tags=None,
                category_id=None,
                visibility=None,
                scheduled_publish_at=None
            )
            jobs.append(UploadJobResponse(
                job_id=result.get("job_id", ""),
                video_id=video_id,
                status=result.get("status", "queued"),
                progress=0,
                message=result.get("message")
            ))
        except Exception as e:
            errors.append(f"Video {video_id}: {str(e)}")
    
    return {
        "total_videos": len(video_ids),
        "jobs_created": len(jobs),
        "jobs": jobs,
        "errors": errors
    }


# Streaming Integration Endpoints

@router.post("/{video_id}/create-stream")
async def create_stream_from_video(
    video_id: uuid.UUID,
    account_id: uuid.UUID,
    title: Optional[str] = None,
    loop_mode: str = "infinite",
    loop_count: Optional[int] = None,
    resolution: str = "1080p",
    target_bitrate: int = 6000,
    target_fps: int = 30,
    scheduled_start_at: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a stream job from library video.
    
    Creates a 24/7 looping stream using the video from library.
    Tracks video usage for streaming.
    """
    from app.modules.stream.stream_job_service import StreamJobService
    from app.modules.stream.stream_job_schemas import CreateStreamJobRequest
    from app.modules.video.video_storage_service import VideoStorageService
    from app.core.storage import get_storage_service
    from datetime import datetime
    
    user_id = current_user.id
    
    # Get video from library
    library_service = VideoLibraryService(db)
    video = await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get video file path from storage
    storage_service = VideoStorageService(get_storage_service())
    video_path = await storage_service.get_video_url(
        video_id=video_id,
        user_id=user_id,
        expiry_seconds=86400 * 365  # 1 year for streaming
    )
    
    # Parse scheduled start time
    scheduled_start = None
    if scheduled_start_at:
        scheduled_start = datetime.fromisoformat(scheduled_start_at.replace('Z', '+00:00'))
    
    # Create stream job
    stream_service = StreamJobService(db)
    
    # Get stream key from account
    from app.modules.account.repository import YouTubeAccountRepository
    account_repo = YouTubeAccountRepository(db)
    account = await account_repo.get_by_id(account_id)
    
    if not account or account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube account not found"
        )
    
    # Create stream job request
    stream_request = CreateStreamJobRequest(
        account_id=account_id,
        video_id=video_id,
        video_path=video_path,
        rtmp_url="rtmp://a.rtmp.youtube.com/live2",
        stream_key=account.stream_key if hasattr(account, 'stream_key') else "",
        title=title or video.title,
        description=video.description,
        loop_mode=loop_mode,
        loop_count=loop_count,
        resolution=resolution,
        target_bitrate=target_bitrate,
        target_fps=target_fps,
        scheduled_start_at=scheduled_start
    )
    
    stream_job = await stream_service.create_stream_job(
        user_id=user_id,
        request=stream_request
    )
    
    # Track video usage
    usage_tracker = VideoUsageTracker(db)
    await usage_tracker.log_streaming_start(
        video_id=video_id,
        stream_job_id=stream_job.id,
        metadata={
            "resolution": resolution,
            "bitrate": target_bitrate,
            "fps": target_fps,
            "loop_mode": loop_mode
        }
    )
    
    return {
        "stream_job_id": str(stream_job.id),
        "video_id": str(video_id),
        "status": stream_job.status,
        "title": stream_job.title,
        "message": "Stream job created successfully"
    }


@router.get("/{video_id}/streaming-history")
async def get_streaming_history(
    video_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get streaming history for a video.
    
    Returns all streaming sessions for this video.
    """
    user_id = current_user.id
    
    # Verify video ownership
    library_service = VideoLibraryService(db)
    await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get streaming history
    usage_tracker = VideoUsageTracker(db)
    history = await usage_tracker.get_streaming_history(
        video_id=video_id,
        page=page,
        limit=limit
    )
    
    return {
        "video_id": str(video_id),
        "history": history,
        "page": page,
        "limit": limit
    }


@router.get("/{video_id}/usage")
async def get_video_usage_stats(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics for a video.
    
    Returns YouTube upload and streaming usage stats.
    """
    user_id = current_user.id
    
    # Verify video ownership
    library_service = VideoLibraryService(db)
    video = await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get usage stats
    usage_tracker = VideoUsageTracker(db)
    stats = await usage_tracker.get_usage_stats(video_id=video_id)
    
    # Check if video is currently in use
    is_in_use = await usage_tracker.is_video_in_use(video_id=video_id)
    
    return {
        "video_id": str(video_id),
        "title": video.title,
        "usage_stats": stats,
        "is_currently_in_use": is_in_use,
        "youtube_id": video.youtube_id,
        "is_used_for_streaming": video.is_used_for_streaming,
        "streaming_count": video.streaming_count,
        "total_streaming_duration": video.total_streaming_duration
    }

