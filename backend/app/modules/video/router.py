"""Video API router.

Implements REST endpoints for video management.
Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.video.models import VideoStatus
from app.modules.video.schemas import (
    VideoUploadRequest,
    VideoMetadataUpdate,
    BulkMetadataUpdate,
    SchedulePublishRequest,
    VideoResponse,
    MetadataVersionResponse,
    UploadJobResponse,
    UploadProgressResponse,
    BulkUploadResponse,
    VideoTemplateRequest,
    VideoTemplateResponse,
    ApplyTemplateRequest,
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


@router.post("", response_model=UploadJobResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    account_id: uuid.UUID = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    category_id: Optional[str] = Form(None),
    visibility: str = Form("private"),
    scheduled_publish_at: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file.

    Requirements: 3.1, 3.2
    """
    service = VideoService(db)

    try:
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Parse scheduled time
        scheduled_at = None
        if scheduled_publish_at:
            from datetime import datetime

            scheduled_at = datetime.fromisoformat(scheduled_publish_at)

        # Create upload request
        from app.modules.video.models import VideoVisibility

        request = VideoUploadRequest(
            title=title,
            description=description,
            tags=tag_list,
            category_id=category_id,
            visibility=VideoVisibility(visibility),
            scheduled_publish_at=scheduled_at,
        )

        # Save file (in production, this would go to S3/storage)
        file_path = f"/tmp/uploads/{file.filename}"
        file_size = file.size or 0

        # Create video and upload job
        video = await service.create_video(
            account_id=account_id,
            request=request,
            file_path=file_path,
            file_size=file_size,
        )

        job = await service.create_upload_job(video)
        return job

    except InvalidFileError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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


@router.get("/{video_id}/versions", response_model=list[MetadataVersionResponse])
async def get_metadata_versions(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get metadata version history.

    Requirements: 4.5
    """
    service = VideoService(db)

    try:
        versions = await service.get_metadata_versions(video_id)
        return versions
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{video_id}/rollback/{version_number}", response_model=VideoResponse)
async def rollback_metadata(
    video_id: uuid.UUID,
    version_number: int,
    db: AsyncSession = Depends(get_db),
):
    """Rollback metadata to a specific version.

    Requirements: 4.5
    """
    service = VideoService(db)

    try:
        video = await service.rollback_metadata(video_id, version_number)
        return video
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    """Delete a video."""
    service = VideoService(db)

    try:
        await service.delete_video(video_id)
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Template endpoints
template_router = APIRouter(prefix="/templates", tags=["video-templates"])


@template_router.post("", response_model=VideoTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    user_id: uuid.UUID,  # In production, get from auth
    request: VideoTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a video template.

    Requirements: 4.2
    """
    service = VideoService(db)

    template = await service.create_template(
        user_id=user_id,
        name=request.name,
        description_template=request.description_template,
        tags=request.tags,
        category_id=request.category_id,
        visibility=request.visibility.value,
    )
    return template


@template_router.get("", response_model=list[VideoTemplateResponse])
async def get_templates(
    user_id: uuid.UUID,  # In production, get from auth
    db: AsyncSession = Depends(get_db),
):
    """Get all templates for a user.

    Requirements: 4.2
    """
    service = VideoService(db)
    templates = await service.get_templates(user_id)
    return templates
