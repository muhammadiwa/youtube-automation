"""Pydantic schemas for AI module.

Defines request/response schemas for AI-powered content optimization.
Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4, 15.5
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# Title Generation
class TitleGenerationRequest(BaseModel):
    """Request schema for AI title generation."""

    video_content: str = Field(..., min_length=10, max_length=5000, description="Video content description or transcript")
    keywords: Optional[list[str]] = Field(None, max_length=20, description="Target keywords to include")
    style: Optional[Literal["engaging", "informative", "clickbait", "professional"]] = Field(
        "engaging", description="Title style preference"
    )
    max_length: int = Field(100, ge=20, le=100, description="Maximum title length")


class TitleSuggestion(BaseModel):
    """Schema for a single title suggestion."""

    title: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    keywords: list[str]


class TitleGenerationResponse(BaseModel):
    """Response schema for title generation."""

    suggestions: list[TitleSuggestion] = Field(..., min_length=5, max_length=5)
    generated_at: datetime


# Description Generation
class DescriptionGenerationRequest(BaseModel):
    """Request schema for AI description generation."""

    video_title: str = Field(..., min_length=1, max_length=100)
    video_content: str = Field(..., min_length=10, max_length=5000)
    keywords: Optional[list[str]] = Field(None, max_length=20)
    include_timestamps: bool = Field(False, description="Include timestamp placeholders")
    include_cta: bool = Field(True, description="Include call-to-action")
    max_length: int = Field(2000, ge=100, le=5000)


class DescriptionSuggestion(BaseModel):
    """Schema for description suggestion."""

    description: str
    seo_score: float = Field(..., ge=0.0, le=1.0)
    keywords_used: list[str]
    has_cta: bool
    estimated_read_time: int  # seconds


class DescriptionGenerationResponse(BaseModel):
    """Response schema for description generation."""

    suggestion: DescriptionSuggestion
    generated_at: datetime


# Tag Suggestion
class TagSuggestionRequest(BaseModel):
    """Request schema for AI tag suggestions."""

    video_title: str = Field(..., min_length=1, max_length=100)
    video_description: Optional[str] = Field(None, max_length=5000)
    video_content: Optional[str] = Field(None, max_length=5000)
    existing_tags: Optional[list[str]] = Field(None, max_length=50)
    max_tags: int = Field(30, ge=5, le=50)


class TagSuggestion(BaseModel):
    """Schema for a single tag suggestion."""

    tag: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    category: Literal["primary", "secondary", "trending", "long_tail"]


class TagSuggestionResponse(BaseModel):
    """Response schema for tag suggestions."""

    suggestions: list[TagSuggestion]
    generated_at: datetime


# Thumbnail Generation
class ThumbnailGenerationRequest(BaseModel):
    """Request schema for AI thumbnail generation."""

    video_title: str = Field(..., min_length=1, max_length=100)
    video_content: Optional[str] = Field(None, max_length=2000)
    style: Literal["modern", "minimalist", "bold", "professional", "gaming"] = Field("modern")
    include_text: bool = Field(True, description="Include text overlay on thumbnail")
    text_content: Optional[str] = Field(None, max_length=50, description="Text to display on thumbnail")
    brand_colors: Optional[list[str]] = Field(None, max_length=3, description="Brand colors in hex format")


class ThumbnailElement(BaseModel):
    """Schema for thumbnail element."""

    element_type: Literal["text", "image", "shape", "logo"]
    position: dict  # {"x": int, "y": int}
    size: dict  # {"width": int, "height": int}
    content: Optional[str] = None
    style: Optional[dict] = None


class ThumbnailResult(BaseModel):
    """Schema for a single thumbnail result."""

    id: str
    image_url: str
    style: str
    elements: list[ThumbnailElement]
    width: int = 1280
    height: int = 720


class ThumbnailGenerationResponse(BaseModel):
    """Response schema for thumbnail generation."""

    thumbnails: list[ThumbnailResult] = Field(..., min_length=3, max_length=3)
    generated_at: datetime


# Thumbnail Optimization
class ThumbnailOptimizationRequest(BaseModel):
    """Request schema for thumbnail optimization."""

    image_data: bytes = Field(..., description="Base64 encoded image data")
    target_width: int = Field(1280, ge=640, le=2560)
    target_height: int = Field(720, ge=360, le=1440)
    enhance_quality: bool = Field(True)
    apply_branding: bool = Field(False)
    brand_logo_url: Optional[str] = None


class ThumbnailOptimizationResponse(BaseModel):
    """Response schema for thumbnail optimization."""

    optimized_image_url: str
    original_dimensions: dict  # {"width": int, "height": int}
    final_dimensions: dict  # {"width": int, "height": int}
    file_size_bytes: int
    optimizations_applied: list[str]


# User Feedback
class AIFeedbackRequest(BaseModel):
    """Request schema for AI feedback."""

    suggestion_type: Literal["title", "description", "tags", "thumbnail"]
    suggestion_id: str
    was_selected: bool
    user_modification: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class AIFeedbackResponse(BaseModel):
    """Response schema for AI feedback."""

    feedback_id: uuid.UUID
    recorded_at: datetime


# User Preferences
class AIPreferences(BaseModel):
    """Schema for user AI preferences."""

    preferred_title_style: Optional[str] = None
    preferred_description_length: Optional[int] = None
    preferred_tag_count: Optional[int] = None
    preferred_thumbnail_style: Optional[str] = None
    brand_colors: Optional[list[str]] = None
    brand_keywords: Optional[list[str]] = None
    avoid_keywords: Optional[list[str]] = None


class AIPreferencesResponse(BaseModel):
    """Response schema for AI preferences."""

    user_id: uuid.UUID
    preferences: AIPreferences
    updated_at: datetime
