"""Video API router.

Implements REST endpoints for video management.
Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5
"""

import math
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.jwt import get_current_user
from app.modules.video.models import VideoStatus
from app.modules.video.schemas import (
    VideoUploadRequest,
    VideoMetadataUpdate,
    BulkMetadataUpdate,
    SchedulePublishRequest,
    VideoResponse,
    UploadJobResponse,
    UploadProgressResponse,
    BulkUploadResponse,
    VideoTemplateRequest,
    VideoTemplateResponse,
    ApplyTemplateRequest,
    PaginatedVideoResponse,
)
from app.modules.video.service import (
    VideoService,
    VideoNotFoundError,
    InvalidFileError,
    TemplateNotFoundError,
    parse_csv_for_bulk_upload,
    create_bulk_upload_jobs,
)

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=PaginatedVideoResponse)
async def get_videos(
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(20, ge=1, le=100, alias="pageSize", description="Items per page"),
    accountId: Optional[uuid.UUID] = Query(None, alias="accountId", description="Filter by account"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    sortBy: str = Query("date", alias="sortBy", description="Sort field"),
    sortOrder: str = Query("desc", alias="sortOrder", description="Sort order"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of videos for the current user.

    Returns all videos across all accounts owned by the authenticated user.
    """
    service = VideoService(db)
    user_id = current_user.id

    # Parse status filter
    video_status = None
    if status_filter:
        try:
            video_status = VideoStatus(status_filter)
        except ValueError:
            pass

    videos, total = await service.get_all_videos_paginated(
        user_id=user_id,
        account_id=accountId,
        status=video_status,
        visibility=visibility,
        search=search,
        sort_by=sortBy,
        sort_order=sortOrder,
        page=page,
        page_size=pageSize,
    )

    total_pages = math.ceil(total / pageSize) if total > 0 else 0

    return PaginatedVideoResponse(
        items=videos,
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
    )


@router.post("", response_model=UploadJobResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    account_id: uuid.UUID = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    category_id: Optional[str] = Form(None),
    visibility: str = Form("private"),
    scheduled_publish_at: Optional[str] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),  # Optional thumbnail
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file with streaming support.

    The file is streamed directly to disk without loading into memory,
    making it efficient for large video files. After saving, a background
    task handles the YouTube upload.

    Requirements: 3.1, 3.2
    """
    from app.modules.video.upload_handler import (
        stream_upload_to_disk,
        cleanup_upload,
        get_video_duration,
        FileTooLargeError,
        InvalidFileTypeError,
        UploadError,
    )
    from app.modules.video.models import VideoVisibility
    from datetime import datetime

    service = VideoService(db)
    file_path = None
    thumbnail_path = None

    try:
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Parse scheduled time
        scheduled_at = None
        if scheduled_publish_at:
            scheduled_at = datetime.fromisoformat(scheduled_publish_at)

        # Stream video file to disk (non-blocking for large files)
        upload_result = await stream_upload_to_disk(file)
        file_path = upload_result.file_path
        file_size = upload_result.file_size

        # Extract video duration using ffprobe
        duration = await get_video_duration(file_path)

        # Handle optional thumbnail upload
        if thumbnail and thumbnail.filename:
            import os
            import aiofiles
            from app.core.config import settings
            
            thumb_dir = getattr(settings, 'LOCAL_STORAGE_PATH', './storage') + "/thumbnails"
            os.makedirs(thumb_dir, exist_ok=True)
            
            thumb_ext = os.path.splitext(thumbnail.filename)[1] or ".jpg"
            thumbnail_path = os.path.join(thumb_dir, f"{uuid.uuid4()}{thumb_ext}")
            
            async with aiofiles.open(thumbnail_path, 'wb') as f:
                content = await thumbnail.read()
                await f.write(content)

        # Create upload request
        request = VideoUploadRequest(
            title=title,
            description=description,
            tags=tag_list,
            category_id=category_id,
            visibility=VideoVisibility(visibility),
            scheduled_publish_at=scheduled_at,
        )

        # Create video record and queue upload job
        video = await service.create_video(
            account_id=account_id,
            request=request,
            file_path=file_path,
            file_size=file_size,
            thumbnail_path=thumbnail_path,
            duration=duration,
        )

        await db.commit()
        job = await service.create_upload_job(video)
        await db.commit()
        return job

    except FileTooLargeError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))
    except UploadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidFileError as e:
        # Cleanup uploaded file on error
        if file_path:
            await cleanup_upload(file_path)
        if thumbnail_path:
            await cleanup_upload(thumbnail_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Cleanup uploaded file on error
        if file_path:
            await cleanup_upload(file_path)
        if thumbnail_path:
            await cleanup_upload(thumbnail_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk", response_model=BulkUploadResponse)
async def bulk_upload(
    account_id: uuid.UUID = Form(...),
    csv_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Bulk upload videos from CSV.

    Requirements: 3.5
    """
    service = VideoService(db)

    # Read CSV content
    content = await csv_file.read()
    csv_content = content.decode("utf-8")

    # Parse CSV
    entries, errors = parse_csv_for_bulk_upload(csv_content)

    if not entries and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "CSV parsing failed", "errors": errors},
        )

    # Create upload jobs
    result = await create_bulk_upload_jobs(service, account_id, entries)
    return result


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk delete."""
    videoIds: list[uuid.UUID]


class BulkDeleteResponse(BaseModel):
    """Response schema for bulk delete."""
    success: int
    failed: int
    results: list[dict]


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_videos(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bulk delete multiple videos and their associated files."""
    service = VideoService(db)
    
    success_count = 0
    failed_count = 0
    results = []
    
    for video_id in request.videoIds:
        try:
            await service.delete_video(video_id)
            success_count += 1
            results.append({"videoId": str(video_id), "success": True})
        except VideoNotFoundError:
            failed_count += 1
            results.append({"videoId": str(video_id), "success": False, "error": "Video not found"})
        except Exception as e:
            failed_count += 1
            results.append({"videoId": str(video_id), "success": False, "error": str(e)})
    
    await db.commit()
    return BulkDeleteResponse(success=success_count, failed=failed_count, results=results)


class BulkExtractDurationResponse(BaseModel):
    """Response schema for bulk duration extraction."""
    processed: int
    updated: int
    failed: int
    skipped: int
    results: list[dict]


@router.post("/bulk-extract-duration", response_model=BulkExtractDurationResponse)
async def bulk_extract_duration(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract duration for all videos that have local files but no duration.
    
    This is useful for migrating existing videos that were uploaded before
    duration extraction was implemented.
    """
    from app.modules.video.upload_handler import get_video_duration
    from sqlalchemy import select
    from app.modules.video.models import Video
    from app.modules.account.models import YouTubeAccount
    
    # Get all videos for this user that have file_path but no duration
    result = await db.execute(
        select(Video)
        .join(YouTubeAccount, Video.account_id == YouTubeAccount.id)
        .where(YouTubeAccount.user_id == current_user.id)
        .where(Video.file_path.isnot(None))
        .where(Video.duration.is_(None))
    )
    videos = result.scalars().all()
    
    processed = 0
    updated = 0
    failed = 0
    skipped = 0
    results = []
    
    for video in videos:
        processed += 1
        
        if not video.file_path or not os.path.exists(video.file_path):
            skipped += 1
            results.append({
                "videoId": str(video.id),
                "title": video.title,
                "status": "skipped",
                "reason": "File not found"
            })
            continue
        
        try:
            duration = await get_video_duration(video.file_path)
            if duration:
                video.duration = duration
                updated += 1
                results.append({
                    "videoId": str(video.id),
                    "title": video.title,
                    "status": "updated",
                    "duration": duration
                })
            else:
                failed += 1
                results.append({
                    "videoId": str(video.id),
                    "title": video.title,
                    "status": "failed",
                    "reason": "Could not extract duration"
                })
        except Exception as e:
            failed += 1
            results.append({
                "videoId": str(video.id),
                "title": video.title,
                "status": "failed",
                "reason": str(e)
            })
    
    await db.commit()
    
    return BulkExtractDurationResponse(
        processed=processed,
        updated=updated,
        failed=failed,
        skipped=skipped,
        results=results
    )


# Template endpoints - MUST be before /{video_id} routes
@router.get("/templates", response_model=list[VideoTemplateResponse])
async def get_templates(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all templates for current user."""
    service = VideoService(db)
    templates = await service.get_templates(current_user.id)
    return templates


@router.post("/templates", response_model=VideoTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: VideoTemplateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a video template."""
    service = VideoService(db)
    template = await service.create_template(
        user_id=current_user.id,
        name=request.name,
        title_template=request.title_template,
        description_template=request.description_template,
        tags=request.tags,
        category_id=request.category_id,
        visibility=request.visibility.value if request.visibility else "private",
        is_default=request.is_default,
    )
    await db.commit()
    return template


@router.get("/templates/{template_id}", response_model=VideoTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific template."""
    service = VideoService(db)
    template = await service.template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if str(template.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return template


@router.put("/templates/{template_id}", response_model=VideoTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    request: VideoTemplateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    service = VideoService(db)
    template = await service.template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if str(template.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if request.is_default and not template.is_default:
        await service.template_repo.unset_defaults(current_user.id)

    if request.name:
        template.name = request.name
    if request.title_template is not None:
        template.title_template = request.title_template
    if request.description_template is not None:
        template.description_template = request.description_template
    if request.tags is not None:
        template.tags = request.tags
    if request.category_id is not None:
        template.category_id = request.category_id
    if request.visibility:
        template.visibility = request.visibility.value
    template.is_default = request.is_default

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template."""
    service = VideoService(db)
    template = await service.template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if str(template.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(template)
    await db.commit()


# YouTube Sync endpoints - MUST be before /{video_id} routes
class YouTubeVideoItem(BaseModel):
    """YouTube video item from channel."""
    youtubeId: str
    title: str
    description: str
    thumbnailUrl: str
    publishedAt: str
    viewCount: int
    likeCount: int
    commentCount: int
    duration: str
    visibility: str
    isImported: bool


class YouTubeVideoListResponse(BaseModel):
    """Response for YouTube video list."""
    videos: list[YouTubeVideoItem]
    nextPageToken: Optional[str] = None


class YouTubeImportRequest(BaseModel):
    """Request to import a YouTube video."""
    account_id: uuid.UUID
    youtube_video_id: str


class YouTubeImportResponse(BaseModel):
    """Response for YouTube video import."""
    success: bool
    videoId: Optional[str] = None
    message: str


@router.get("/youtube/list", response_model=YouTubeVideoListResponse)
async def list_youtube_videos(
    account_id: uuid.UUID = Query(..., alias="account_id"),
    page_token: Optional[str] = Query(None, alias="pageToken"),
    max_results: int = Query(50, ge=1, le=50, alias="maxResults"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List videos from YouTube channel."""
    from app.modules.account.repository import AccountRepository
    from app.modules.video.youtube_upload_api import YouTubeUploadAPI

    account_repo = AccountRepository(db)
    account = await account_repo.get_by_id(account_id)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if str(account.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        youtube_api = YouTubeUploadAPI(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
        )
        videos_data = await youtube_api.list_channel_videos(
            max_results=max_results,
            page_token=page_token,
        )

        service = VideoService(db)
        imported_ids = await service.get_imported_youtube_ids(account_id)

        videos = []
        for item in videos_data.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            status_info = item.get("status", {})

            youtube_id = item.get("id")
            if isinstance(youtube_id, dict):
                youtube_id = youtube_id.get("videoId", "")

            videos.append(YouTubeVideoItem(
                youtubeId=youtube_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                thumbnailUrl=snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                publishedAt=snippet.get("publishedAt", ""),
                viewCount=int(statistics.get("viewCount", 0)),
                likeCount=int(statistics.get("likeCount", 0)),
                commentCount=int(statistics.get("commentCount", 0)),
                duration=content_details.get("duration", ""),
                visibility=status_info.get("privacyStatus", "private"),
                isImported=youtube_id in imported_ids,
            ))

        return YouTubeVideoListResponse(
            videos=videos,
            nextPageToken=videos_data.get("nextPageToken"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube videos: {str(e)}")


@router.post("/youtube/import", response_model=YouTubeImportResponse)
async def import_youtube_video(
    request: YouTubeImportRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import an existing YouTube video into the platform."""
    from app.modules.account.repository import AccountRepository
    from app.modules.video.youtube_upload_api import YouTubeUploadAPI
    from app.modules.video.models import VideoVisibility

    account_repo = AccountRepository(db)
    account = await account_repo.get_by_id(request.account_id)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if str(account.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        youtube_api = YouTubeUploadAPI(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
        )
        video_data = await youtube_api.get_video_details(request.youtube_video_id)

        if not video_data:
            raise HTTPException(status_code=404, detail="Video not found on YouTube")

        snippet = video_data.get("snippet", {})
        statistics = video_data.get("statistics", {})
        status_info = video_data.get("status", {})

        service = VideoService(db)
        visibility_map = {
            "public": VideoVisibility.PUBLIC,
            "unlisted": VideoVisibility.UNLISTED,
            "private": VideoVisibility.PRIVATE,
        }

        video = await service.import_youtube_video(
            account_id=request.account_id,
            youtube_id=request.youtube_video_id,
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            tags=snippet.get("tags", []),
            category_id=snippet.get("categoryId", "22"),
            visibility=visibility_map.get(status_info.get("privacyStatus", "private"), VideoVisibility.PRIVATE),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            published_at=snippet.get("publishedAt"),
        )

        await db.commit()
        return YouTubeImportResponse(
            success=True,
            videoId=str(video.id),
            message="Video imported successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import video: {str(e)}")


# Video by ID routes - MUST be after /templates and /youtube routes
@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get video by ID."""
    service = VideoService(db)

    try:
        video = await service.get_video(video_id)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{video_id}/progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get upload progress for a video.

    Requirements: 3.1
    """
    service = VideoService(db)

    try:
        progress = await service.get_upload_progress(video_id)
        return progress
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{video_id}/thumbnail")
async def upload_thumbnail(
    video_id: uuid.UUID,
    thumbnail: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload custom thumbnail for a video.

    Thumbnail will be uploaded to YouTube after video processing is complete.
    Supported formats: JPEG, PNG, GIF, BMP (max 2MB)
    """
    import os
    import tempfile
    from app.modules.video.tasks import upload_thumbnail_task

    service = VideoService(db)

    try:
        video = await service.get_video(video_id)

        if not video.youtube_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video must be uploaded to YouTube first",
            )

        # Validate thumbnail
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/bmp"]
        if thumbnail.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
            )

        max_size = 2 * 1024 * 1024  # 2MB
        content = await thumbnail.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thumbnail size exceeds 2MB limit",
            )

        # Save thumbnail temporarily
        ext = os.path.splitext(thumbnail.filename)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Queue thumbnail upload task
        task = upload_thumbnail_task.delay(str(video_id), tmp_path)

        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Thumbnail upload queued",
        }

    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/account/{account_id}", response_model=list[VideoResponse])
async def get_videos_by_account(
    account_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get all videos for an account."""
    service = VideoService(db)

    video_status = None
    if status:
        try:
            video_status = VideoStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )

    videos = await service.get_videos_by_account(
        account_id, video_status, limit, offset
    )
    return videos


@router.patch("/{video_id}/metadata", response_model=VideoResponse)
async def update_metadata(
    video_id: uuid.UUID,
    request: VideoMetadataUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update video metadata.

    Requirements: 4.1, 4.5
    """
    service = VideoService(db)

    try:
        video = await service.update_metadata(video_id, request)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/bulk-update", response_model=list[VideoResponse])
async def bulk_update_metadata(
    request: BulkMetadataUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Bulk update metadata for multiple videos.

    Requirements: 4.4
    """
    service = VideoService(db)
    videos = await service.bulk_update_metadata(request)
    return videos


@router.post("/{video_id}/apply-template", response_model=VideoResponse)
async def apply_template(
    video_id: uuid.UUID,
    request: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Apply template to video.

    Requirements: 4.2
    """
    service = VideoService(db)

    try:
        video = await service.apply_template(video_id, request.template_id)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{video_id}/sync-stats", response_model=VideoResponse)
async def sync_video_stats(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sync video statistics from YouTube.

    Fetches current view count, like count, and comment count from YouTube API.
    """
    service = VideoService(db)

    try:
        video = await service.sync_video_stats(video_id)
        await db.commit()
        await db.refresh(video)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{video_id}/extract-duration", response_model=VideoResponse)
async def extract_video_duration(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Extract and update video duration using ffprobe.

    Useful for videos that were uploaded before duration extraction was implemented.
    Only works for videos with local file_path.
    """
    from app.modules.video.upload_handler import get_video_duration

    service = VideoService(db)

    try:
        video = await service.get_video(video_id)
        
        if not video.file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video has no local file. Duration can only be extracted from uploaded videos.",
            )
        
        if not os.path.exists(video.file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video file not found on server.",
            )
        
        # Extract duration
        duration = await get_video_duration(video.file_path)
        
        if duration is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract duration. Make sure ffprobe is installed.",
            )
        
        # Update video
        video.duration = duration
        await db.commit()
        await db.refresh(video)
        
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{video_id}/schedule", response_model=VideoResponse)
async def schedule_publish(
    video_id: uuid.UUID,
    request: SchedulePublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """Schedule video for publishing.

    Requirements: 4.3
    """
    service = VideoService(db)

    try:
        video = await service.schedule_publish(video_id, request.publish_at)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{video_id}/publish", response_model=VideoResponse)
async def publish_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Publish video immediately.

    Requirements: 4.3
    """
    service = VideoService(db)

    try:
        video = await service.publish_video(video_id)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a video and its associated files."""
    service = VideoService(db)

    try:
        await service.delete_video(video_id)
        await db.commit()
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



