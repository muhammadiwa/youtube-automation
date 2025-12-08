"""AI service for content optimization.

Implements AI-powered title, description, tag, and thumbnail generation.
Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4, 15.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.openai_client import OpenAIClient, get_openai_client, OpenAIClientError
from app.modules.ai.prompts import (
    TITLE_GENERATION_SYSTEM,
    TITLE_GENERATION_USER,
    DESCRIPTION_GENERATION_SYSTEM,
    DESCRIPTION_GENERATION_USER,
    TAG_SUGGESTION_SYSTEM,
    TAG_SUGGESTION_USER,
    THUMBNAIL_GENERATION_SYSTEM,
    THUMBNAIL_GENERATION_USER,
)
from app.modules.ai.repository import (
    AIFeedbackRepository,
    AIPreferencesRepository,
    ThumbnailLibraryRepository,
)
from app.modules.ai.schemas import (
    TitleGenerationRequest,
    TitleGenerationResponse,
    TitleSuggestion,
    DescriptionGenerationRequest,
    DescriptionGenerationResponse,
    DescriptionSuggestion,
    TagSuggestionRequest,
    TagSuggestionResponse,
    TagSuggestion,
    ThumbnailGenerationRequest,
    ThumbnailGenerationResponse,
    ThumbnailResult,
    ThumbnailElement,
    AIFeedbackRequest,
    AIFeedbackResponse,
    AIPreferences,
    AIPreferencesResponse,
)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIService:
    """Service for AI-powered content optimization."""

    REQUIRED_TITLE_COUNT = 5
    REQUIRED_THUMBNAIL_COUNT = 3

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        openai_client: Optional[OpenAIClient] = None,
    ):
        """Initialize AI service.

        Args:
            session: Optional database session for feedback/preferences
            openai_client: Optional OpenAI client (uses singleton if not provided)
        """
        self.session = session
        self._openai_client = openai_client

        if session:
            self.feedback_repo = AIFeedbackRepository(session)
            self.preferences_repo = AIPreferencesRepository(session)
            self.thumbnail_repo = ThumbnailLibraryRepository(session)
        else:
            self.feedback_repo = None
            self.preferences_repo = None
            self.thumbnail_repo = None

    @property
    def openai_client(self) -> OpenAIClient:
        """Get OpenAI client."""
        if self._openai_client is None:
            self._openai_client = get_openai_client()
        return self._openai_client

    async def generate_titles(
        self,
        request: TitleGenerationRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> TitleGenerationResponse:
        """Generate title suggestions for a video.

        Args:
            request: Title generation request
            user_id: Optional user ID for personalization

        Returns:
            TitleGenerationResponse: Generated title suggestions

        Raises:
            AIServiceError: If generation fails
        """
        # Get user preferences if available
        preferences = None
        if user_id and self.preferences_repo:
            preferences = await self.preferences_repo.get_by_user(user_id)

        # Build prompt
        keywords_str = ", ".join(request.keywords) if request.keywords else "None specified"
        style = request.style
        if preferences and preferences.preferred_title_style:
            style = preferences.preferred_title_style

        user_prompt = TITLE_GENERATION_USER.format(
            video_content=request.video_content,
            keywords=keywords_str,
            style=style,
            max_length=request.max_length,
        )

        try:
            response = await self.openai_client.generate_json(
                system_prompt=TITLE_GENERATION_SYSTEM,
                user_prompt=user_prompt,
                temperature=0.8,
            )

            suggestions = []
            for item in response.get("suggestions", [])[:self.REQUIRED_TITLE_COUNT]:
                suggestions.append(
                    TitleSuggestion(
                        title=item.get("title", "")[:request.max_length],
                        confidence_score=min(1.0, max(0.0, item.get("confidence_score", 0.5))),
                        reasoning=item.get("reasoning", ""),
                        keywords=item.get("keywords", []),
                    )
                )

            # Ensure exactly 5 suggestions
            while len(suggestions) < self.REQUIRED_TITLE_COUNT:
                suggestions.append(
                    TitleSuggestion(
                        title=f"Video Title Option {len(suggestions) + 1}",
                        confidence_score=0.3,
                        reasoning="Fallback suggestion",
                        keywords=[],
                    )
                )

            return TitleGenerationResponse(
                suggestions=suggestions[:self.REQUIRED_TITLE_COUNT],
                generated_at=datetime.utcnow(),
            )

        except OpenAIClientError as e:
            raise AIServiceError(f"Title generation failed: {str(e)}") from e

    async def generate_description(
        self,
        request: DescriptionGenerationRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> DescriptionGenerationResponse:
        """Generate description for a video.

        Args:
            request: Description generation request
            user_id: Optional user ID for personalization

        Returns:
            DescriptionGenerationResponse: Generated description

        Raises:
            AIServiceError: If generation fails
        """
        # Get user preferences if available
        preferences = None
        if user_id and self.preferences_repo:
            preferences = await self.preferences_repo.get_by_user(user_id)

        max_length = request.max_length
        if preferences and preferences.preferred_description_length:
            max_length = preferences.preferred_description_length

        keywords_str = ", ".join(request.keywords) if request.keywords else "None specified"

        user_prompt = DESCRIPTION_GENERATION_USER.format(
            video_title=request.video_title,
            video_content=request.video_content,
            keywords=keywords_str,
            include_timestamps=request.include_timestamps,
            include_cta=request.include_cta,
            max_length=max_length,
        )

        try:
            response = await self.openai_client.generate_json(
                system_prompt=DESCRIPTION_GENERATION_SYSTEM,
                user_prompt=user_prompt,
                temperature=0.7,
            )

            suggestion = DescriptionSuggestion(
                description=response.get("description", "")[:max_length],
                seo_score=min(1.0, max(0.0, response.get("seo_score", 0.5))),
                keywords_used=response.get("keywords_used", []),
                has_cta=response.get("has_cta", False),
                estimated_read_time=response.get("estimated_read_time", 30),
            )

            return DescriptionGenerationResponse(
                suggestion=suggestion,
                generated_at=datetime.utcnow(),
            )

        except OpenAIClientError as e:
            raise AIServiceError(f"Description generation failed: {str(e)}") from e

    async def suggest_tags(
        self,
        request: TagSuggestionRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> TagSuggestionResponse:
        """Suggest tags for a video.

        Args:
            request: Tag suggestion request
            user_id: Optional user ID for personalization

        Returns:
            TagSuggestionResponse: Suggested tags

        Raises:
            AIServiceError: If suggestion fails
        """
        # Get user preferences if available
        preferences = None
        if user_id and self.preferences_repo:
            preferences = await self.preferences_repo.get_by_user(user_id)

        max_tags = request.max_tags
        if preferences and preferences.preferred_tag_count:
            max_tags = preferences.preferred_tag_count

        existing_tags_str = ", ".join(request.existing_tags) if request.existing_tags else "None"

        user_prompt = TAG_SUGGESTION_USER.format(
            video_title=request.video_title,
            video_description=request.video_description or "Not provided",
            video_content=request.video_content or "Not provided",
            existing_tags=existing_tags_str,
            max_tags=max_tags,
        )

        try:
            response = await self.openai_client.generate_json(
                system_prompt=TAG_SUGGESTION_SYSTEM,
                user_prompt=user_prompt,
                temperature=0.6,
            )

            suggestions = []
            for item in response.get("suggestions", [])[:max_tags]:
                category = item.get("category", "secondary")
                if category not in ["primary", "secondary", "trending", "long_tail"]:
                    category = "secondary"

                suggestions.append(
                    TagSuggestion(
                        tag=item.get("tag", ""),
                        relevance_score=min(1.0, max(0.0, item.get("relevance_score", 0.5))),
                        category=category,
                    )
                )

            return TagSuggestionResponse(
                suggestions=suggestions,
                generated_at=datetime.utcnow(),
            )

        except OpenAIClientError as e:
            raise AIServiceError(f"Tag suggestion failed: {str(e)}") from e

    async def generate_thumbnails(
        self,
        request: ThumbnailGenerationRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> ThumbnailGenerationResponse:
        """Generate thumbnail designs for a video.

        Args:
            request: Thumbnail generation request
            user_id: Optional user ID for personalization

        Returns:
            ThumbnailGenerationResponse: Generated thumbnail designs

        Raises:
            AIServiceError: If generation fails
        """
        # Get user preferences if available
        preferences = None
        if user_id and self.preferences_repo:
            preferences = await self.preferences_repo.get_by_user(user_id)

        style = request.style
        if preferences and preferences.preferred_thumbnail_style:
            style = preferences.preferred_thumbnail_style

        brand_colors = request.brand_colors
        if preferences and preferences.brand_colors:
            brand_colors = preferences.brand_colors

        brand_colors_str = ", ".join(brand_colors) if brand_colors else "Not specified"

        user_prompt = THUMBNAIL_GENERATION_USER.format(
            video_title=request.video_title,
            video_content=request.video_content or "Not provided",
            style=style,
            include_text=request.include_text,
            text_content=request.text_content or "None",
            brand_colors=brand_colors_str,
        )

        try:
            response = await self.openai_client.generate_json(
                system_prompt=THUMBNAIL_GENERATION_SYSTEM,
                user_prompt=user_prompt,
                temperature=0.9,
            )

            thumbnails = []
            for i, item in enumerate(response.get("thumbnails", [])[:self.REQUIRED_THUMBNAIL_COUNT]):
                elements = []
                for elem in item.get("elements", []):
                    elements.append(
                        ThumbnailElement(
                            element_type=elem.get("element_type", "text"),
                            position=elem.get("position", {"x": 0, "y": 0}),
                            size=elem.get("size", {"width": 100, "height": 50}),
                            content=elem.get("content"),
                            style=elem.get("style"),
                        )
                    )

                thumbnails.append(
                    ThumbnailResult(
                        id=item.get("id", f"thumb_{i + 1}"),
                        image_url=f"placeholder://thumbnail/{i + 1}",  # Placeholder URL
                        style=item.get("style", style),
                        elements=elements,
                        width=1280,
                        height=720,
                    )
                )

            # Ensure exactly 3 thumbnails
            while len(thumbnails) < self.REQUIRED_THUMBNAIL_COUNT:
                thumbnails.append(
                    ThumbnailResult(
                        id=f"thumb_{len(thumbnails) + 1}",
                        image_url=f"placeholder://thumbnail/{len(thumbnails) + 1}",
                        style=style,
                        elements=[],
                        width=1280,
                        height=720,
                    )
                )

            return ThumbnailGenerationResponse(
                thumbnails=thumbnails[:self.REQUIRED_THUMBNAIL_COUNT],
                generated_at=datetime.utcnow(),
            )

        except OpenAIClientError as e:
            raise AIServiceError(f"Thumbnail generation failed: {str(e)}") from e

    async def record_feedback(
        self,
        user_id: uuid.UUID,
        request: AIFeedbackRequest,
    ) -> AIFeedbackResponse:
        """Record user feedback on AI suggestions.

        Args:
            user_id: User UUID
            request: Feedback request

        Returns:
            AIFeedbackResponse: Recorded feedback

        Raises:
            AIServiceError: If recording fails
        """
        if not self.feedback_repo:
            raise AIServiceError("Database session required for feedback")

        feedback = await self.feedback_repo.create(
            user_id=user_id,
            suggestion_type=request.suggestion_type,
            suggestion_id=request.suggestion_id,
            was_selected=request.was_selected,
            user_modification=request.user_modification,
            rating=request.rating,
        )

        return AIFeedbackResponse(
            feedback_id=feedback.id,
            recorded_at=feedback.created_at,
        )

    async def get_preferences(self, user_id: uuid.UUID) -> AIPreferencesResponse:
        """Get user AI preferences.

        Args:
            user_id: User UUID

        Returns:
            AIPreferencesResponse: User preferences

        Raises:
            AIServiceError: If retrieval fails
        """
        if not self.preferences_repo:
            raise AIServiceError("Database session required for preferences")

        prefs = await self.preferences_repo.get_by_user(user_id)

        if prefs:
            preferences = AIPreferences(
                preferred_title_style=prefs.preferred_title_style,
                preferred_description_length=prefs.preferred_description_length,
                preferred_tag_count=prefs.preferred_tag_count,
                preferred_thumbnail_style=prefs.preferred_thumbnail_style,
                brand_colors=prefs.brand_colors,
                brand_keywords=prefs.brand_keywords,
                avoid_keywords=prefs.avoid_keywords,
            )
            updated_at = prefs.updated_at
        else:
            preferences = AIPreferences()
            updated_at = datetime.utcnow()

        return AIPreferencesResponse(
            user_id=user_id,
            preferences=preferences,
            updated_at=updated_at,
        )

    async def update_preferences(
        self,
        user_id: uuid.UUID,
        preferences: AIPreferences,
    ) -> AIPreferencesResponse:
        """Update user AI preferences.

        Args:
            user_id: User UUID
            preferences: New preferences

        Returns:
            AIPreferencesResponse: Updated preferences

        Raises:
            AIServiceError: If update fails
        """
        if not self.preferences_repo:
            raise AIServiceError("Database session required for preferences")

        prefs = await self.preferences_repo.create_or_update(
            user_id=user_id,
            preferred_title_style=preferences.preferred_title_style,
            preferred_description_length=preferences.preferred_description_length,
            preferred_tag_count=preferences.preferred_tag_count,
            preferred_thumbnail_style=preferences.preferred_thumbnail_style,
            brand_colors=preferences.brand_colors,
            brand_keywords=preferences.brand_keywords,
            avoid_keywords=preferences.avoid_keywords,
        )

        return AIPreferencesResponse(
            user_id=user_id,
            preferences=preferences,
            updated_at=prefs.updated_at,
        )
