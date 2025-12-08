"""AI services module.

Provides AI-powered content optimization including:
- Title generation
- Description generation
- Tag suggestions
- Thumbnail generation and optimization

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4, 15.5
"""

from app.modules.ai.service import AIService, AIServiceError
from app.modules.ai.openai_client import OpenAIClient, OpenAIClientError, get_openai_client
from app.modules.ai.thumbnail import (
    ThumbnailOptimizer,
    ThumbnailOptimizationError,
    optimize_thumbnail,
    YOUTUBE_THUMBNAIL_WIDTH,
    YOUTUBE_THUMBNAIL_HEIGHT,
)

__all__ = [
    "AIService",
    "AIServiceError",
    "OpenAIClient",
    "OpenAIClientError",
    "get_openai_client",
    "ThumbnailOptimizer",
    "ThumbnailOptimizationError",
    "optimize_thumbnail",
    "YOUTUBE_THUMBNAIL_WIDTH",
    "YOUTUBE_THUMBNAIL_HEIGHT",
]
