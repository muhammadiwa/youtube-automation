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
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import utcnow, to_naive_utc
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
    UploadJobResponse,
    CreateStreamFromVideoRequest
)

router = APIRouter(prefix="/videos/library", tags=["video-library"])


def _create_video_response(video, video_id: uuid.UUID = None) -> VideoResponse:
    """Create VideoResponse with stream_url and thumbnail_url populated.
    
    Args:
        video: Video model instance
        video_id: Optional video ID (uses video.id if not provided)
        
    Returns:
        VideoResponse with stream_url and thumbnail_url set based on storage configuration
    """
    from app.core.storage import get_storage, is_cloud_storage, get_public_url
    
    # Generate stream URL based on storage configuration
    stream_url = None
    if video.file_path:
        if is_cloud_storage():
            # For cloud storage, return direct CDN/presigned URL
            storage = get_storage()
            stream_url = storage.get_url(video.file_path, expires_in=3600)
        else:
            # For local storage, return stream endpoint URL
            vid = video_id or video.id
            stream_url = f"/api/v1/videos/library/{vid}/stream"
    
    # Generate thumbnail URL
    # Priority: thumbnail_url (YouTube) > local_thumbnail_path (generated)
    thumbnail_url = video.thumbnail_url
    if not thumbnail_url and video.local_thumbnail_path:
        thumbnail_url = get_public_url(video.local_thumbnail_path, expires_in=3600)
    
    # Create response with stream_url and thumbnail_url
    response = VideoResponse.model_validate(video)
    response.stream_url = stream_url
    if thumbnail_url:
        response.thumbnail_url = thumbnail_url
    
    return response


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
    
    Only checks storage limit (not video count per month).
    Video count limit is enforced when uploading to YouTube.
    """
    from app.modules.billing.feature_gate import FeatureGateService, LimitExceededError
    
    user_id = current_user.id
    feature_gate = FeatureGateService(db)
    
    # Check storage limit (estimate from content-length if available)
    if file.size:
        try:
            await feature_gate.check_storage_limit(
                user_id, 
                additional_bytes=file.size, 
                raise_on_exceed=True
            )
        except LimitExceededError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message,
            )
    
    service = VideoLibraryService(db)
    
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
    
    return _create_video_response(video)


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
        items=[_create_video_response(v) for v in videos],
        total=total,
        page=page,
        pageSize=limit,
        totalPages=total_pages
    )


# ============================================
# STATIC ROUTES (must be before {video_id})
# ============================================

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
) -> None:
    """Delete folder (must be empty)."""
    service = VideoFolderService(db)
    user_id = current_user.id
    
    await service.delete_folder(
        folder_id=folder_id,
        user_id=user_id
    )


# Bulk Operations

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


# ============================================
# DYNAMIC ROUTES (with {video_id} parameter)
# ============================================

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video_details(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get video details by ID.
    
    Returns video details including stream_url for video preview.
    The stream_url is generated based on storage configuration:
    - For cloud storage with CDN: returns public CDN URL
    - For local storage: returns stream endpoint URL
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    return _create_video_response(video, video_id)


@router.get("/{video_id}/processing-status")
async def get_processing_status(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get video processing status.
    
    Use this endpoint to poll for upload processing progress.
    Returns status, progress percentage, and any errors.
    
    Uses existing columns:
    - status: processing_upload → in_library (ready) or failed
    - upload_progress: 0-100
    - last_upload_error: Error message if failed
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    status = await service.get_processing_status(
        video_id=video_id,
        user_id=user_id
    )
    
    return status


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
    
    return _create_video_response(video, video_id)


@router.post("/{video_id}/thumbnail", response_model=VideoResponse)
async def upload_thumbnail(
    video_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload custom thumbnail for video.
    
    Accepts JPEG, PNG, or WebP images. Max size 2MB.
    Replaces any existing custom thumbnail.
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.upload_thumbnail(
        video_id=video_id,
        user_id=user_id,
        file=file
    )
    
    return _create_video_response(video, video_id)


@router.delete("/{video_id}/thumbnail", response_model=VideoResponse)
async def delete_thumbnail(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete custom thumbnail and revert to auto-generated one.
    
    If video has an auto-generated thumbnail, it will be used.
    Otherwise, thumbnail will be empty.
    """
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    video = await service.delete_thumbnail(
        video_id=video_id,
        user_id=user_id
    )
    
    return _create_video_response(video, video_id)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete video from library."""
    service = VideoLibraryService(db)
    user_id = current_user.id
    
    await service.delete_from_library(
        video_id=video_id,
        user_id=user_id
    )


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
    
    return _create_video_response(video, video_id)


@router.post("/{video_id}/move")
async def move_to_folder(
    video_id: uuid.UUID,
    folder_id: Optional[uuid.UUID] = Query(None, description="Target folder ID (null for root)"),
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
    
    return _create_video_response(video, video_id)


@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(
    video_id: uuid.UUID,
    token: Optional[str] = Query(None, description="Auth token for thumbnail access"),
    db: AsyncSession = Depends(get_db),
):
    """Get video thumbnail.
    
    - For local storage: serves thumbnail file directly
    - For cloud storage (R2/S3): redirects to presigned URL
    
    Accepts auth token via query parameter for img element compatibility.
    """
    import os
    import logging
    from fastapi.responses import FileResponse, RedirectResponse
    from app.core.config import settings
    from app.core.storage import get_storage, is_cloud_storage
    from app.modules.auth.jwt import validate_token
    
    logger = logging.getLogger(__name__)
    
    # Verify token from query parameter
    if not token:
        logger.warning("Thumbnail request without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide token as query parameter."
        )
    
    # Validate token
    payload = validate_token(token, expected_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user_id from payload
    try:
        user_id = uuid.UUID(payload.sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    service = VideoLibraryService(db)
    
    # Get video to verify ownership and get thumbnail path
    video = await service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Check for thumbnail - prefer local_thumbnail_path, then thumbnail_url
    thumbnail_key = video.local_thumbnail_path or video.thumbnail_url
    
    if not thumbnail_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found for this video"
        )
    
    # If thumbnail_url is a full URL (e.g., YouTube thumbnail), redirect to it
    if thumbnail_key.startswith(('http://', 'https://')):
        return RedirectResponse(url=thumbnail_key, status_code=302)
    
    storage = get_storage()
    
    # Check if using cloud storage (R2/S3)
    if is_cloud_storage():
        # For cloud storage, redirect to presigned URL
        presigned_url = storage.get_url(thumbnail_key, expires_in=3600)
        logger.info(f"Redirecting to cloud storage URL for thumbnail {video_id}")
        return RedirectResponse(url=presigned_url, status_code=302)
    
    # For local storage, serve the file directly
    file_path = thumbnail_key
    
    # If it's a relative path (storage key), prepend the local storage path
    if not os.path.isabs(file_path):
        local_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        file_path = os.path.join(local_storage_path, file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail file not found on disk"
        )
    
    # Determine content type based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    content_type = content_types.get(ext, 'image/jpeg')
    
    return FileResponse(
        path=file_path,
        media_type=content_type
    )


@router.get("/{video_id}/stream")
async def stream_video_preview(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Stream video file for preview.
    
    Returns the actual video file for streaming.
    - For cloud storage with public CDN: redirects to public CDN URL
    - For local storage or private cloud: serves file with authentication
    
    Authentication is required to verify video ownership.
    """
    import os
    import logging
    from fastapi.responses import FileResponse, RedirectResponse
    from app.core.config import settings
    from app.core.storage import get_storage, is_cloud_storage
    
    logger = logging.getLogger(__name__)
    
    # Get user_id from current_user
    user_id = current_user.id
    
    logger.info(f"Stream request for video {video_id} by user {user_id}")
    
    service = VideoLibraryService(db)
    
    # Get video to verify ownership and get file_path
    video = await service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Check if video has a file path
    if not video.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found. This video may have been imported from YouTube without a local file."
        )
    
    storage = get_storage()
    
    # Check if using cloud storage (R2/S3)
    if is_cloud_storage():
        # For cloud storage, get the URL (CDN or presigned)
        # If CDN is enabled and bucket is public, this returns CDN URL
        # Otherwise, returns presigned URL
        video_url = storage.get_url(video.file_path, expires_in=3600)
        logger.info(f"Redirecting to cloud storage URL for video {video_id}")
        
        # Redirect to cloud URL - browser will fetch directly
        return RedirectResponse(url=video_url, status_code=302)
    
    # For local storage, serve the file directly
    # The file_path could be a relative path or absolute path
    file_path = video.file_path
    
    # If it's a relative path (storage key), prepend the local storage path
    if not os.path.isabs(file_path):
        local_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        file_path = os.path.join(local_storage_path, file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found on disk"
        )
    
    # Determine content type based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
    }
    content_type = content_types.get(ext, 'video/mp4')
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=f"{video.title}{ext}"
    )


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


# Streaming Integration Endpoints

@router.post("/{video_id}/create-stream")
async def create_stream_from_video(
    video_id: uuid.UUID,
    request: CreateStreamFromVideoRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a stream job from library video.
    
    Creates a 24/7 looping stream using the video from library.
    Uses the stream key stored in the YouTube account.
    Tracks video usage for streaming.
    
    For cloud storage: uses presigned URL that FFmpeg can read directly.
    """
    from app.modules.stream.stream_job_service import StreamJobService
    from app.modules.stream.stream_job_schemas import CreateStreamJobRequest
    from app.core.config import settings
    from app.core.storage import get_file_url_for_ffmpeg
    from datetime import datetime
    
    user_id = current_user.id
    
    # Get video from library
    library_service = VideoLibraryService(db)
    video = await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get video file path - use storage key, let stream_job_service resolve it
    if not video.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file not found"
        )
    
    # Use storage key directly - stream_job_service will resolve to URL/path for FFmpeg
    video_path = video.file_path
    
    # Parse scheduled start time
    scheduled_start = None
    if request.scheduled_start_at:
        scheduled_start = datetime.fromisoformat(request.scheduled_start_at.replace('Z', '+00:00'))
    
    # Parse scheduled end time
    scheduled_end = None
    if request.scheduled_end_at:
        scheduled_end = datetime.fromisoformat(request.scheduled_end_at.replace('Z', '+00:00'))
    
    # Get account and verify ownership
    from app.modules.account.repository import YouTubeAccountRepository
    account_repo = YouTubeAccountRepository(db)
    account = await account_repo.get_by_id(request.account_id)
    
    if not account or account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube account not found"
        )
    
    # Determine stream key - use request value if provided, otherwise use account's key
    stream_key = request.stream_key if request.stream_key else account.stream_key
    rtmp_url = request.rtmp_url if request.rtmp_url else (account.rtmp_url or "rtmp://a.rtmp.youtube.com/live2")
    
    # Check if we have a stream key
    if not stream_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No stream key provided. Please enter a stream key or sync from YouTube."
        )
    
    # Create stream job
    stream_service = StreamJobService(db)
    
    # Create stream job request
    stream_request = CreateStreamJobRequest(
        account_id=request.account_id,
        video_id=video_id,
        video_path=video_path,
        rtmp_url=rtmp_url,
        stream_key=stream_key,
        title=request.title or video.title,
        description=video.description,
        loop_mode=request.loop_mode,
        loop_count=request.loop_count,
        resolution=request.resolution,
        target_bitrate=request.target_bitrate,
        target_fps=request.target_fps,
        encoding_mode=request.encoding_mode,
        enable_chat_moderation=request.enable_chat_moderation,
        enable_auto_restart=request.enable_auto_restart,
        max_restarts=request.max_restarts,
        scheduled_start_at=scheduled_start,
        scheduled_end_at=scheduled_end
    )
    
    stream_job = await stream_service.create_stream_job(
        user_id=user_id,
        request=stream_request
    )
    
    # Track video usage
    usage_tracker = VideoUsageTracker(db)
    await usage_tracker.log_streaming_start(
        video_id=video_id,
        stream_job_id=stream_job.id
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
    include_logs: bool = True,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics for a video.
    
    Returns YouTube upload and streaming usage stats with optional usage logs.
    """
    user_id = current_user.id
    
    # Verify video ownership
    library_service = VideoLibraryService(db)
    video = await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Get usage stats with logs
    usage_tracker = VideoUsageTracker(db)
    stats = await usage_tracker.get_usage_stats(
        video_id=video_id,
        include_logs=include_logs
    )
    
    # Check if video is currently in use
    is_in_use = await usage_tracker.is_video_in_use(video_id=video_id)
    
    # Format usage logs for response
    usage_logs = []
    if include_logs and stats.usage_logs:
        for log in stats.usage_logs:
            usage_logs.append({
                "id": str(log.id),
                "usageType": log.usage_type,
                "startedAt": log.started_at.isoformat() if log.started_at else None,
                "endedAt": log.ended_at.isoformat() if log.ended_at else None,
                "usageMetadata": log.usage_metadata or {}
            })
    
    return {
        "videoId": str(video_id),
        "title": video.title,
        "usageStats": {
            "youtubeUploads": stats.youtube_uploads,
            "streamingSessions": stats.streaming_sessions,
            "totalStreamingDuration": stats.total_streaming_duration,
            "lastUsedAt": stats.last_used_at.isoformat() if stats.last_used_at else None
        },
        "usageLogs": usage_logs,
        "isCurrentlyInUse": is_in_use,
        "youtubeId": video.youtube_id,
        "isUsedForStreaming": video.is_used_for_streaming,
        "streamingCount": video.streaming_count,
        "totalStreamingDuration": video.total_streaming_duration
    }



@router.post("/{video_id}/fix-usage-logs")
async def fix_video_usage_logs(
    video_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fix unclosed usage logs for a video.
    
    Closes any streaming usage logs that don't have an ended_at timestamp
    by looking up the corresponding stream job's actual_end_at.
    """
    from sqlalchemy import select, update
    from app.modules.video.models import VideoUsageLog, Video
    from app.modules.stream.stream_job_models import StreamJob
    from datetime import datetime
    
    user_id = current_user.id
    
    # Verify video ownership
    library_service = VideoLibraryService(db)
    video = await library_service.get_video_by_id(
        video_id=video_id,
        user_id=user_id
    )
    
    # Find unclosed usage logs for this video
    query = select(VideoUsageLog).where(
        VideoUsageLog.video_id == video_id,
        VideoUsageLog.usage_type == "live_stream",
        VideoUsageLog.ended_at.is_(None)
    )
    result = await db.execute(query)
    unclosed_logs = result.scalars().all()
    
    fixed_count = 0
    total_duration_added = 0
    
    for log in unclosed_logs:
        # Try to find the stream job from metadata
        stream_job_id = None
        if log.usage_metadata and "stream_job_id" in log.usage_metadata:
            stream_job_id = log.usage_metadata["stream_job_id"]
        
        if stream_job_id:
            # Get stream job to find actual end time
            job_query = select(StreamJob).where(StreamJob.id == uuid.UUID(stream_job_id))
            job_result = await db.execute(job_query)
            stream_job = job_result.scalar_one_or_none()
            
            if stream_job and stream_job.actual_end_at:
                # Calculate duration
                start = log.started_at.replace(tzinfo=None) if log.started_at.tzinfo else log.started_at
                end = stream_job.actual_end_at.replace(tzinfo=None) if stream_job.actual_end_at.tzinfo else stream_job.actual_end_at
                duration = int((end - start).total_seconds())
                
                # Update usage log
                log.ended_at = stream_job.actual_end_at
                if log.usage_metadata is None:
                    log.usage_metadata = {}
                log.usage_metadata["stream_duration"] = duration
                log.usage_metadata["fixed_at"] = utcnow().isoformat()
                
                total_duration_added += duration
                fixed_count += 1
            elif stream_job and stream_job.status in ["stopped", "failed", "error"]:
                # Stream job ended but no actual_end_at, use now
                now = to_naive_utc(utcnow())
                duration = int((now - log.started_at.replace(tzinfo=None)).total_seconds())
                log.ended_at = now
                if log.usage_metadata is None:
                    log.usage_metadata = {}
                log.usage_metadata["stream_duration"] = duration
                log.usage_metadata["fixed_at"] = utcnow().isoformat()
                log.usage_metadata["estimated"] = True
                
                total_duration_added += duration
                fixed_count += 1
        else:
            # No stream job ID, close with estimated duration
            now = to_naive_utc(utcnow())
            duration = int((now - log.started_at.replace(tzinfo=None)).total_seconds())
            log.ended_at = now
            if log.usage_metadata is None:
                log.usage_metadata = {}
            log.usage_metadata["stream_duration"] = duration
            log.usage_metadata["fixed_at"] = utcnow().isoformat()
            log.usage_metadata["estimated"] = True
            
            total_duration_added += duration
            fixed_count += 1
    
    # Update video total streaming duration
    if total_duration_added > 0:
        video.total_streaming_duration += total_duration_added
        video.is_used_for_streaming = False  # No longer actively streaming
    
    await db.commit()
    
    return {
        "videoId": str(video_id),
        "fixedLogs": fixed_count,
        "totalDurationAdded": total_duration_added,
        "message": f"Fixed {fixed_count} unclosed usage logs, added {total_duration_added} seconds to total duration"
    }
