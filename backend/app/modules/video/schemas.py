"""Pydantic schemas for video module.

Defines request/response schemas for video upload and management.
Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.5
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.video.models import VideoStatus, VideoVisibility


# Allowed video file extensions and MIME types
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/x-ms-wmv",
}
MAX_FILE_SIZE = 128 * 1024 * 1024 * 1024  # 128 GB (YouTube limit)
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000
MAX_TAGS = 500


class VideoUploadRequest(BaseModel):
    """Request schema for video upload."""

    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    category_id: Optional[str] = None
    visibility: VideoVisibility = VideoVisibility.PRIVATE
    scheduled_publish_at: Optional[datetime] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        # Remove empty tags and duplicates
        cleaned = list(dict.fromkeys(tag.strip() for tag in v if tag.strip()))
        if len(cleaned) > MAX_TAGS:
            raise ValueError(f"Maximum {MAX_TAGS} tags allowed")
        return cleaned


class VideoMetadataUpdate(BaseModel):
    """Request schema for updating video metadata."""

    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    category_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    visibility: Optional[VideoVisibility] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        cleaned = list(dict.fromkeys(tag.strip() for tag in v if tag.strip()))
        if len(cleaned) > MAX_TAGS:
            raise ValueError(f"Maximum {MAX_TAGS} tags allowed")
        return cleaned


class BulkMetadataUpdate(BaseModel):
    """Request schema for bulk metadata update."""

    video_ids: list[uuid.UUID] = Field(..., min_length=1)
    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    category_id: Optional[str] = None
    visibility: Optional[VideoVisibility] = None


class SchedulePublishRequest(BaseModel):
    """Request schema for scheduling video publish."""

    publish_at: datetime


class VideoResponse(BaseModel):
    """Response schema for video."""

    id: uuid.UUID
    account_id: uuid.UUID = Field(alias="accountId", serialization_alias="accountId")
    youtube_id: Optional[str] = Field(alias="youtubeId", serialization_alias="youtubeId", default=None)
    title: str
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category_id: Optional[str] = Field(alias="categoryId", serialization_alias="categoryId", default=None)
    thumbnail_url: Optional[str] = Field(alias="thumbnailUrl", serialization_alias="thumbnailUrl", default=None)
    visibility: str
    scheduled_publish_at: Optional[datetime] = Field(alias="scheduledPublishAt", serialization_alias="scheduledPublishAt", default=None)
    published_at: Optional[datetime] = Field(alias="publishedAt", serialization_alias="publishedAt", default=None)
    view_count: int = Field(alias="viewCount", serialization_alias="viewCount", default=0)
    like_count: int = Field(alias="likeCount", serialization_alias="likeCount", default=0)
    comment_count: int = Field(alias="commentCount", serialization_alias="commentCount", default=0)
    status: str
    upload_progress: int = Field(alias="uploadProgress", serialization_alias="uploadProgress", default=0)
    created_at: datetime = Field(alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt", serialization_alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class MetadataVersionResponse(BaseModel):
    """Response schema for metadata version."""

    id: uuid.UUID
    video_id: uuid.UUID
    version_number: int
    title: str
    description: Optional[str]
    tags: Optional[list[str]]
    category_id: Optional[str]
    thumbnail_url: Optional[str]
    visibility: str
    changed_by: Optional[uuid.UUID]
    change_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UploadJobResponse(BaseModel):
    """Response schema for upload job."""

    job_id: str
    video_id: uuid.UUID
    status: str
    progress: int
    message: Optional[str] = None


class UploadProgressResponse(BaseModel):
    """Response schema for upload progress."""

    video_id: uuid.UUID
    job_id: Optional[str]
    status: str
    progress: int
    error: Optional[str] = None


class BulkUploadEntry(BaseModel):
    """Schema for a single entry in bulk upload CSV."""

    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[str] = None  # Comma-separated tags
    category_id: Optional[str] = None
    visibility: Optional[str] = None
    scheduled_publish_at: Optional[str] = None
    file_path: str


class BulkUploadResponse(BaseModel):
    """Response schema for bulk upload."""

    total_entries: int
    jobs_created: int
    jobs: list[UploadJobResponse]
    errors: list[str]


class VideoTemplateRequest(BaseModel):
    """Request schema for creating/updating video template."""

    name: str = Field(..., min_length=1, max_length=100)
    title_template: Optional[str] = Field(None, max_length=200)
    description_template: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    category_id: Optional[str] = None
    visibility: VideoVisibility = VideoVisibility.PRIVATE
    is_default: bool = False


class VideoTemplateResponse(BaseModel):
    """Response schema for video template."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    tags: Optional[list[str]] = None
    category_id: Optional[str] = None
    visibility: str
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplyTemplateRequest(BaseModel):
    """Request schema for applying template to video."""

    template_id: uuid.UUID


class PaginatedVideoResponse(BaseModel):
    """Response schema for paginated video list."""

    items: list[VideoResponse]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    class Config:
        from_attributes = True
        populate_by_name = True
