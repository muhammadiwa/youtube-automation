"""FastAPI router for AI endpoints.

Provides REST API endpoints for AI-powered content optimization.
Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.ai.service import AIService, AIServiceError
from app.modules.ai.schemas import (
    TitleGenerationRequest,
    TitleGenerationResponse,
    DescriptionGenerationRequest,
    DescriptionGenerationResponse,
    TagSuggestionRequest,
    TagSuggestionResponse,
    ThumbnailGenerationRequest,
    ThumbnailGenerationResponse,
    AIFeedbackRequest,
    AIFeedbackResponse,
    AIPreferences,
    AIPreferencesResponse,
)

router = APIRouter(prefix="/ai", tags=["AI"])


def get_ai_service(session: AsyncSession = Depends(get_session)) -> AIService:
    """Dependency to get AI service instance."""
    return AIService(session=session)


@router.post("/titles/generate", response_model=TitleGenerationResponse)
async def generate_titles(
    request: TitleGenerationRequest,
    user_id: Optional[uuid.UUID] = None,  # Would come from auth in production
    service: AIService = Depends(get_ai_service),
) -> TitleGenerationResponse:
    """Generate AI-powered title suggestions.

    Returns exactly 5 title variations with confidence scores.
    """
    try:
        return await service.generate_titles(request, user_id)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/descriptions/generate", response_model=DescriptionGenerationResponse)
async def generate_description(
    request: DescriptionGenerationRequest,
    user_id: Optional[uuid.UUID] = None,
    service: AIService = Depends(get_ai_service),
) -> DescriptionGenerationResponse:
    """Generate AI-powered video description.

    Returns SEO-optimized description with keywords and CTAs.
    """
    try:
        return await service.generate_description(request, user_id)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/tags/suggest", response_model=TagSuggestionResponse)
async def suggest_tags(
    request: TagSuggestionRequest,
    user_id: Optional[uuid.UUID] = None,
    service: AIService = Depends(get_ai_service),
) -> TagSuggestionResponse:
    """Generate AI-powered tag suggestions.

    Returns relevant tags sorted by relevance score.
    """
    try:
        return await service.suggest_tags(request, user_id)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/thumbnails/generate", response_model=ThumbnailGenerationResponse)
async def generate_thumbnails(
    request: ThumbnailGenerationRequest,
    user_id: Optional[uuid.UUID] = None,
    service: AIService = Depends(get_ai_service),
) -> ThumbnailGenerationResponse:
    """Generate AI-powered thumbnail designs.

    Returns exactly 3 thumbnail variations with design elements.
    """
    try:
        return await service.generate_thumbnails(request, user_id)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/feedback", response_model=AIFeedbackResponse)
async def record_feedback(
    request: AIFeedbackRequest,
    user_id: uuid.UUID,  # Would come from auth in production
    service: AIService = Depends(get_ai_service),
) -> AIFeedbackResponse:
    """Record user feedback on AI suggestions.

    Used for personalization and improving recommendations.
    """
    try:
        return await service.record_feedback(user_id, request)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/preferences/{user_id}", response_model=AIPreferencesResponse)
async def get_preferences(
    user_id: uuid.UUID,
    service: AIService = Depends(get_ai_service),
) -> AIPreferencesResponse:
    """Get user AI preferences."""
    try:
        return await service.get_preferences(user_id)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/preferences/{user_id}", response_model=AIPreferencesResponse)
async def update_preferences(
    user_id: uuid.UUID,
    preferences: AIPreferences,
    service: AIService = Depends(get_ai_service),
) -> AIPreferencesResponse:
    """Update user AI preferences."""
    try:
        return await service.update_preferences(user_id, preferences)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
