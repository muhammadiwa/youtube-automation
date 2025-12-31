"""Video Library Service for managing video library operations.

Provides library-first video management with storage, metadata extraction,
and organization features.
Requirements: 1.1, 1.2
"""

import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import Video, VideoFolder, VideoStatus
from app.modules.video.video_storage_service import video_storage_service
from app.modules.video.video_metadata_extractor import video_metadata_extractor


# Validation constants
ALLOWED_VIDEO_FORMATS = ["mp4", "mov", "avi", "mkv", "webm", "flv", "wmv"]
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB


class VideoFilters:
    """Filters for video library queries."""
    
    def __init__(
        self,
        folder_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
        is_favorite: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.folder_id = folder_id
        self.status = status
        self.search = search
        self.tags = tags
        self.is_favorite = is_favorite
        self.sort_by = sort_by
        self.sort_order = sort_order


class Pagination:
    """Pagination parameters."""
    
    def __init__(self, page: int = 1, limit: int = 20):
        self.page = max(1, page)
        self.limit = min(100, max(1, limit))
        self.offset = (self.page - 1) * self.limit


class VideoLibraryService:
    """Service for video library operations.
    
    Handles:
    - Uploading videos to library
    - Listing and filtering videos
    - Updating video metadata
    - Deleting videos
    - Organizing videos (favorites, folders)
    """

    def __init__(self, db: AsyncSession):
        """Initialize video library service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.storage = video_storage_service
        self.metadata_extractor = video_metadata_extractor

    async def upload_to_library(
        self,
        user_id: UUID,
        file: UploadFile,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        folder_id: Optional[UUID] = None,
        custom_tags: Optional[list[str]] = None,
        notes: Optional[str] = None
    ) -> Video:
        """Upload video to library.
        
        Args:
            user_id: Owner of the video
            file: Uploaded video file
            title: Video title
            description: Video description
            tags: YouTube tags
            folder_id: Folder to organize video
            custom_tags: Internal tags for organization
            notes: Internal notes
            
        Returns:
            Video: Created video object
            
        Raises:
            HTTPException: If validation fails or upload fails
        """
        # Validate file
        self._validate_file(file)
        
        # Validate folder if provided
        if folder_id:
            await self._validate_folder_access(user_id, folder_id)
        
        # Create video record first (to get video_id)
        video = Video(
            user_id=user_id,
            title=title,
            description=description,
            tags=tags or [],
            folder_id=folder_id,
            custom_tags=custom_tags or [],
            notes=notes,
            status=VideoStatus.IN_LIBRARY.value,
            is_favorite=False
        )
        self.db.add(video)
        await self.db.flush()  # Get video.id
        
        try:
            # Save file to temporary location for metadata extraction
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Reset file pointer for storage upload
            await file.seek(0)
            
            # Extract metadata
            try:
                metadata = await self.metadata_extractor.extract_metadata(tmp_file_path)
                
                # Update video with metadata
                video.duration = metadata.duration
                video.format = metadata.format
                video.resolution = metadata.resolution
                video.frame_rate = metadata.frame_rate
                video.bitrate = metadata.bitrate
                video.codec = metadata.codec
                video.file_size = metadata.file_size
                
                print(f"Metadata extracted successfully: duration={metadata.duration}, resolution={metadata.resolution}, format={metadata.format}")
                
            except Exception as e:
                # If metadata extraction fails, continue with upload
                # but log the error with full details
                import traceback
                print(f"Warning: Failed to extract metadata from {tmp_file_path}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
            
            # Generate thumbnail
            try:
                thumbnail_tmp_path = tmp_file_path + "_thumb.jpg"
                await self.metadata_extractor.generate_thumbnail(
                    tmp_file_path,
                    thumbnail_tmp_path,
                    timestamp=5
                )
                
                # Upload thumbnail to storage
                with open(thumbnail_tmp_path, "rb") as thumb_file:
                    thumb_content = thumb_file.read()
                    thumb_key = await self.storage.save_thumbnail(
                        video_id=video.id,
                        content=thumb_content,
                        custom=False
                    )
                    video.local_thumbnail_path = thumb_key
                
                # Clean up thumbnail temp file
                Path(thumbnail_tmp_path).unlink(missing_ok=True)
                
            except Exception as e:
                print(f"Warning: Failed to generate thumbnail: {e}")
            
            # Upload video to storage
            storage_key, file_size = await self.storage.save_video(
                user_id=user_id,
                video_id=video.id,
                file=file
            )
            
            video.file_path = storage_key
            if not video.file_size:  # If metadata extraction failed
                video.file_size = file_size
            
            # Clean up temp file
            Path(tmp_file_path).unlink(missing_ok=True)
            
            await self.db.commit()
            await self.db.refresh(video)
            
            return video
            
        except Exception as e:
            await self.db.rollback()
            # Clean up uploaded files if any
            if video.file_path:
                await self.storage.delete_video(video.file_path)
            if video.local_thumbnail_path:
                await self.storage.delete_thumbnail(video.local_thumbnail_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload video: {str(e)}"
            )

    async def get_library_videos(
        self,
        user_id: UUID,
        filters: VideoFilters,
        pagination: Pagination
    ) -> tuple[list[Video], int]:
        """Get user's library videos with filters and pagination.
        
        Args:
            user_id: Owner of videos
            filters: Filter criteria
            pagination: Pagination parameters
            
        Returns:
            tuple[list[Video], int]: (videos, total_count)
        """
        # Build query
        query = select(Video).where(Video.user_id == user_id)
        
        # Apply filters
        if filters.folder_id:
            query = query.where(Video.folder_id == filters.folder_id)
        
        if filters.status:
            query = query.where(Video.status == filters.status)
        
        if filters.is_favorite is not None:
            query = query.where(Video.is_favorite == filters.is_favorite)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Video.title.ilike(search_term),
                    Video.description.ilike(search_term),
                    Video.notes.ilike(search_term)
                )
            )
        
        if filters.tags:
            # Filter by custom tags
            for tag in filters.tags:
                query = query.where(Video.custom_tags.contains([tag]))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply sorting
        if filters.sort_order == "asc":
            query = query.order_by(getattr(Video, filters.sort_by).asc())
        else:
            query = query.order_by(getattr(Video, filters.sort_by).desc())
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        videos = result.scalars().all()
        
        return list(videos), total

    async def get_video_by_id(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> Video:
        """Get video by ID with access check.
        
        Args:
            video_id: Video identifier
            user_id: User requesting access
            
        Returns:
            Video: Video object
            
        Raises:
            HTTPException: If video not found or access denied
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        return video

    async def update_metadata(
        self,
        video_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        custom_tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
        category_id: Optional[str] = None,
        visibility: Optional[str] = None
    ) -> Video:
        """Update video metadata.
        
        Args:
            video_id: Video identifier
            user_id: User making the update
            title: New title
            description: New description
            tags: New YouTube tags
            custom_tags: New internal tags
            notes: New notes
            category_id: New category
            visibility: New visibility
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        # Update fields
        if title is not None:
            video.title = title
        if description is not None:
            video.description = description
        if tags is not None:
            video.tags = tags
        if custom_tags is not None:
            video.custom_tags = custom_tags
        if notes is not None:
            video.notes = notes
        if category_id is not None:
            video.category_id = category_id
        if visibility is not None:
            video.visibility = visibility
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def delete_from_library(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete video from library.
        
        Args:
            video_id: Video identifier
            user_id: User requesting deletion
            
        Raises:
            HTTPException: If video is in use or deletion fails
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        # Check if video is being used for streaming
        if video.is_used_for_streaming:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete video that is currently being used for streaming"
            )
        
        # Delete files from storage
        if video.file_path:
            await self.storage.delete_video(video.file_path)
        
        if video.local_thumbnail_path:
            await self.storage.delete_thumbnail(video.local_thumbnail_path)
        
        # Delete from database
        await self.db.delete(video)
        await self.db.commit()

    async def toggle_favorite(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> Video:
        """Toggle video favorite status.
        
        Args:
            video_id: Video identifier
            user_id: User making the change
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        video.is_favorite = not video.is_favorite
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def move_to_folder(
        self,
        video_id: UUID,
        user_id: UUID,
        folder_id: Optional[UUID]
    ) -> Video:
        """Move video to a folder.
        
        Args:
            video_id: Video identifier
            user_id: User making the change
            folder_id: Target folder (None for root)
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        # Validate folder if provided
        if folder_id:
            await self._validate_folder_access(user_id, folder_id)
        
        video.folder_id = folder_id
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file.
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Check file extension
        ext = Path(file.filename).suffix.lower().lstrip(".")
        if ext not in ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"File format not allowed. Allowed formats: {', '.join(ALLOWED_VIDEO_FORMATS)}"
            )
        
        # Note: File size validation should be done at the API level
        # using FastAPI's File size limits

    async def _validate_folder_access(
        self,
        user_id: UUID,
        folder_id: UUID
    ) -> VideoFolder:
        """Validate user has access to folder.
        
        Args:
            user_id: User identifier
            folder_id: Folder identifier
            
        Returns:
            VideoFolder: Folder object
            
        Raises:
            HTTPException: If folder not found or access denied
        """
        query = select(VideoFolder).where(
            VideoFolder.id == folder_id,
            VideoFolder.user_id == user_id
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise HTTPException(
                status_code=404,
                detail="Folder not found"
            )
        
        return folder
