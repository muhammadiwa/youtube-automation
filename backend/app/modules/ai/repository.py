"""Repository for AI module database operations.

Handles CRUD operations for AI feedback and preferences.
Requirements: 14.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AIFeedback, AIUserPreferences, ThumbnailLibrary


class AIFeedbackRepository:
    """Repository for AI feedback operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        suggestion_type: str,
        suggestion_id: str,
        was_selected: bool,
        user_modification: Optional[str] = None,
        rating: Optional[int] = None,
    ) -> AIFeedback:
        """Create a new feedback record.

        Args:
            user_id: User UUID
            suggestion_type: Type of suggestion (title, description, tags, thumbnail)
            suggestion_id: ID of the suggestion
            was_selected: Whether the suggestion was selected
            user_modification: User's modification to the suggestion
            rating: User rating (1-5)

        Returns:
            AIFeedback: Created feedback record
        """
        feedback = AIFeedback(
            user_id=user_id,
            suggestion_type=suggestion_type,
            suggestion_id=suggestion_id,
            was_selected=was_selected,
            user_modification=user_modification,
            rating=rating,
        )
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        suggestion_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[AIFeedback]:
        """Get feedback records for a user.

        Args:
            user_id: User UUID
            suggestion_type: Optional filter by type
            limit: Maximum records to return

        Returns:
            list[AIFeedback]: List of feedback records
        """
        query = select(AIFeedback).where(AIFeedback.user_id == user_id)
        if suggestion_type:
            query = query.where(AIFeedback.suggestion_type == suggestion_type)
        query = query.order_by(AIFeedback.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AIPreferencesRepository:
    """Repository for AI user preferences operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_user(self, user_id: uuid.UUID) -> Optional[AIUserPreferences]:
        """Get preferences for a user.

        Args:
            user_id: User UUID

        Returns:
            Optional[AIUserPreferences]: User preferences or None
        """
        query = select(AIUserPreferences).where(AIUserPreferences.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: uuid.UUID,
        preferred_title_style: Optional[str] = None,
        preferred_description_length: Optional[int] = None,
        preferred_tag_count: Optional[int] = None,
        preferred_thumbnail_style: Optional[str] = None,
        brand_colors: Optional[list[str]] = None,
        brand_keywords: Optional[list[str]] = None,
        avoid_keywords: Optional[list[str]] = None,
    ) -> AIUserPreferences:
        """Create or update user preferences.

        Args:
            user_id: User UUID
            preferred_title_style: Preferred title style
            preferred_description_length: Preferred description length
            preferred_tag_count: Preferred number of tags
            preferred_thumbnail_style: Preferred thumbnail style
            brand_colors: Brand colors
            brand_keywords: Brand keywords
            avoid_keywords: Keywords to avoid

        Returns:
            AIUserPreferences: Created or updated preferences
        """
        existing = await self.get_by_user(user_id)

        if existing:
            if preferred_title_style is not None:
                existing.preferred_title_style = preferred_title_style
            if preferred_description_length is not None:
                existing.preferred_description_length = preferred_description_length
            if preferred_tag_count is not None:
                existing.preferred_tag_count = preferred_tag_count
            if preferred_thumbnail_style is not None:
                existing.preferred_thumbnail_style = preferred_thumbnail_style
            if brand_colors is not None:
                existing.brand_colors = brand_colors
            if brand_keywords is not None:
                existing.brand_keywords = brand_keywords
            if avoid_keywords is not None:
                existing.avoid_keywords = avoid_keywords
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing

        preferences = AIUserPreferences(
            user_id=user_id,
            preferred_title_style=preferred_title_style,
            preferred_description_length=preferred_description_length,
            preferred_tag_count=preferred_tag_count,
            preferred_thumbnail_style=preferred_thumbnail_style,
            brand_colors=brand_colors,
            brand_keywords=brand_keywords,
            avoid_keywords=avoid_keywords,
        )
        self.session.add(preferences)
        await self.session.flush()
        return preferences


class ThumbnailLibraryRepository:
    """Repository for thumbnail library operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        image_url: str,
        width: int = 1280,
        height: int = 720,
        video_id: Optional[uuid.UUID] = None,
        style: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        elements: Optional[list] = None,
        tags: Optional[list[str]] = None,
        is_generated: bool = True,
    ) -> ThumbnailLibrary:
        """Create a new thumbnail record.

        Args:
            user_id: User UUID
            image_url: URL to the thumbnail image
            width: Image width
            height: Image height
            video_id: Optional associated video UUID
            style: Thumbnail style
            file_size_bytes: File size in bytes
            elements: Thumbnail elements metadata
            tags: Tags for searching
            is_generated: Whether AI generated

        Returns:
            ThumbnailLibrary: Created thumbnail record
        """
        thumbnail = ThumbnailLibrary(
            user_id=user_id,
            video_id=video_id,
            image_url=image_url,
            style=style,
            width=width,
            height=height,
            file_size_bytes=file_size_bytes,
            elements=elements,
            tags=tags,
            is_generated=is_generated,
        )
        self.session.add(thumbnail)
        await self.session.flush()
        return thumbnail

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ThumbnailLibrary]:
        """Get thumbnails for a user.

        Args:
            user_id: User UUID
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            list[ThumbnailLibrary]: List of thumbnails
        """
        query = (
            select(ThumbnailLibrary)
            .where(ThumbnailLibrary.user_id == user_id)
            .order_by(ThumbnailLibrary.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, thumbnail_id: uuid.UUID) -> Optional[ThumbnailLibrary]:
        """Get thumbnail by ID.

        Args:
            thumbnail_id: Thumbnail UUID

        Returns:
            Optional[ThumbnailLibrary]: Thumbnail or None
        """
        query = select(ThumbnailLibrary).where(ThumbnailLibrary.id == thumbnail_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, thumbnail: ThumbnailLibrary) -> None:
        """Delete a thumbnail.

        Args:
            thumbnail: Thumbnail to delete
        """
        await self.session.delete(thumbnail)
        await self.session.flush()
