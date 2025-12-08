"""Video management module."""

from app.modules.video.models import (
    Video,
    VideoStatus,
    VideoVisibility,
    MetadataVersion,
    VideoTemplate,
)
from app.modules.video.repository import VideoRepository, VideoTemplateRepository
from app.modules.video.service import (
    VideoService,
    VideoServiceError,
    VideoNotFoundError,
    InvalidFileError,
    TemplateNotFoundError,
    validate_video_file,
    parse_csv_for_bulk_upload,
    create_bulk_upload_jobs,
)
from app.modules.video.tasks import (
    upload_video_task,
    process_bulk_upload_task,
    check_scheduled_publishes,
    UPLOAD_RETRY_CONFIG,
    calculate_upload_retry_delay,
    should_retry_upload,
)

__all__ = [
    # Models
    "Video",
    "VideoStatus",
    "VideoVisibility",
    "MetadataVersion",
    "VideoTemplate",
    # Repositories
    "VideoRepository",
    "VideoTemplateRepository",
    # Service
    "VideoService",
    "VideoServiceError",
    "VideoNotFoundError",
    "InvalidFileError",
    "TemplateNotFoundError",
    "validate_video_file",
    "parse_csv_for_bulk_upload",
    "create_bulk_upload_jobs",
    # Tasks
    "upload_video_task",
    "process_bulk_upload_task",
    "check_scheduled_publishes",
    "UPLOAD_RETRY_CONFIG",
    "calculate_upload_retry_delay",
    "should_retry_upload",
]
