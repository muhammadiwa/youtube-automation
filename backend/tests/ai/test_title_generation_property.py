"""Property-based tests for AI title generation.

**Feature: youtube-automation, Property 20: Title Generation Count**
**Validates: Requirements 14.1, 14.4**

Tests that title generation always returns exactly 5 title variations
with confidence scores and reasoning.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.modules.ai.service import AIService
from app.modules.ai.schemas import TitleGenerationRequest, TitleGenerationResponse


# Strategy for generating valid video content
video_content_strategy = st.text(
    min_size=10,
    max_size=500,
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))
).filter(lambda x: len(x.strip()) >= 10)

# Strategy for generating keywords
keywords_strategy = st.lists(
    st.text(min_size=2, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))),
    min_size=0,
    max_size=10,
)

# Strategy for title styles
style_strategy = st.sampled_from(["engaging", "informative", "clickbait", "professional"])

# Strategy for max length
max_length_strategy = st.integers(min_value=20, max_value=100)


def create_mock_openai_response(num_suggestions: int = 5) -> dict:
    """Create a mock OpenAI response with the specified number of suggestions."""
    suggestions = []
    for i in range(num_suggestions):
        suggestions.append({
            "title": f"Generated Title {i + 1}",
            "confidence_score": 0.8 - (i * 0.1),
            "reasoning": f"This title works because reason {i + 1}",
            "keywords": [f"keyword{i}", f"term{i}"],
        })
    return {"suggestions": suggestions}


class TestTitleGenerationCount:
    """Property tests for title generation count.

    **Feature: youtube-automation, Property 20: Title Generation Count**
    **Validates: Requirements 14.1, 14.4**
    """

    @given(
        video_content=video_content_strategy,
        keywords=keywords_strategy,
        style=style_strategy,
        max_length=max_length_strategy,
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_title_generation_returns_exactly_five_suggestions(
        self,
        video_content: str,
        keywords: list[str],
        style: str,
        max_length: int,
    ):
        """
        **Feature: youtube-automation, Property 20: Title Generation Count**
        **Validates: Requirements 14.1, 14.4**

        For any valid title generation request, the system SHALL return
        exactly 5 title variations with confidence scores.
        """
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=create_mock_openai_response(5))

        # Create service with mock client
        service = AIService(session=None, openai_client=mock_client)

        # Create request
        request = TitleGenerationRequest(
            video_content=video_content,
            keywords=keywords if keywords else None,
            style=style,
            max_length=max_length,
        )

        # Generate titles
        response = await service.generate_titles(request)

        # Property: Must return exactly 5 suggestions
        assert len(response.suggestions) == 5, (
            f"Expected exactly 5 title suggestions, got {len(response.suggestions)}"
        )

        # Property: Each suggestion must have required fields
        for i, suggestion in enumerate(response.suggestions):
            assert suggestion.title, f"Suggestion {i} missing title"
            assert 0.0 <= suggestion.confidence_score <= 1.0, (
                f"Suggestion {i} confidence score {suggestion.confidence_score} out of range [0, 1]"
            )
            assert suggestion.reasoning is not None, f"Suggestion {i} missing reasoning"
            assert isinstance(suggestion.keywords, list), f"Suggestion {i} keywords not a list"

    @given(
        video_content=video_content_strategy,
        num_api_suggestions=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_title_generation_pads_to_five_when_api_returns_fewer(
        self,
        video_content: str,
        num_api_suggestions: int,
    ):
        """
        **Feature: youtube-automation, Property 20: Title Generation Count**
        **Validates: Requirements 14.1, 14.4**

        For any API response with fewer than 5 suggestions, the system SHALL
        pad the response to exactly 5 suggestions.
        """
        # Create mock OpenAI client with variable number of suggestions
        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(
            return_value=create_mock_openai_response(num_api_suggestions)
        )

        # Create service with mock client
        service = AIService(session=None, openai_client=mock_client)

        # Create request
        request = TitleGenerationRequest(
            video_content=video_content,
            keywords=None,
            style="engaging",
            max_length=100,
        )

        # Generate titles
        response = await service.generate_titles(request)

        # Property: Must always return exactly 5 suggestions regardless of API response
        assert len(response.suggestions) == 5, (
            f"Expected exactly 5 title suggestions when API returned {num_api_suggestions}, "
            f"got {len(response.suggestions)}"
        )

    @given(
        video_content=video_content_strategy,
        max_length=max_length_strategy,
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_title_generation_respects_max_length(
        self,
        video_content: str,
        max_length: int,
    ):
        """
        **Feature: youtube-automation, Property 20: Title Generation Count**
        **Validates: Requirements 14.1, 14.4**

        For any max_length constraint, all generated titles SHALL be
        at most max_length characters.
        """
        # Create mock with long titles
        mock_response = {
            "suggestions": [
                {
                    "title": "A" * 200,  # Very long title
                    "confidence_score": 0.9,
                    "reasoning": "Test",
                    "keywords": [],
                }
                for _ in range(5)
            ]
        }

        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=mock_response)

        service = AIService(session=None, openai_client=mock_client)

        request = TitleGenerationRequest(
            video_content=video_content,
            keywords=None,
            style="engaging",
            max_length=max_length,
        )

        response = await service.generate_titles(request)

        # Property: All titles must respect max_length
        for i, suggestion in enumerate(response.suggestions):
            assert len(suggestion.title) <= max_length, (
                f"Suggestion {i} title length {len(suggestion.title)} exceeds max_length {max_length}"
            )

    @given(video_content=video_content_strategy)
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_title_generation_confidence_scores_in_valid_range(
        self,
        video_content: str,
    ):
        """
        **Feature: youtube-automation, Property 20: Title Generation Count**
        **Validates: Requirements 14.1, 14.4**

        For any title generation, all confidence scores SHALL be in range [0, 1].
        """
        # Create mock with out-of-range confidence scores
        mock_response = {
            "suggestions": [
                {
                    "title": f"Title {i}",
                    "confidence_score": 1.5 if i % 2 == 0 else -0.5,  # Invalid scores
                    "reasoning": "Test",
                    "keywords": [],
                }
                for i in range(5)
            ]
        }

        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=mock_response)

        service = AIService(session=None, openai_client=mock_client)

        request = TitleGenerationRequest(
            video_content=video_content,
            keywords=None,
            style="engaging",
            max_length=100,
        )

        response = await service.generate_titles(request)

        # Property: All confidence scores must be clamped to [0, 1]
        for i, suggestion in enumerate(response.suggestions):
            assert 0.0 <= suggestion.confidence_score <= 1.0, (
                f"Suggestion {i} confidence score {suggestion.confidence_score} not in [0, 1]"
            )
