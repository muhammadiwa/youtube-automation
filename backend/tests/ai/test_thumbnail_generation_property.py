"""Property-based tests for AI thumbnail generation.

**Feature: youtube-automation, Property 21: Thumbnail Generation Count**
**Validates: Requirements 15.1**

Tests that thumbnail generation always returns exactly 3 thumbnail variations.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import AsyncMock, MagicMock

from app.modules.ai.service import AIService
from app.modules.ai.schemas import ThumbnailGenerationRequest


# Strategy for generating valid video titles
video_title_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))
).filter(lambda x: len(x.strip()) >= 1)

# Strategy for video content
video_content_strategy = st.one_of(
    st.none(),
    st.text(min_size=10, max_size=500, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")))
)

# Strategy for thumbnail styles
style_strategy = st.sampled_from(["modern", "minimalist", "bold", "professional", "gaming"])

# Strategy for include_text
include_text_strategy = st.booleans()

# Strategy for text content
text_content_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")))
)

# Strategy for brand colors
brand_colors_strategy = st.one_of(
    st.none(),
    st.lists(
        st.from_regex(r"#[0-9A-Fa-f]{6}", fullmatch=True),
        min_size=1,
        max_size=3,
    )
)


def create_mock_thumbnail_response(num_thumbnails: int = 3) -> dict:
    """Create a mock OpenAI response with the specified number of thumbnails."""
    thumbnails = []
    for i in range(num_thumbnails):
        thumbnails.append({
            "id": f"thumb_{i + 1}",
            "description": f"Thumbnail design {i + 1}",
            "style": "modern",
            "elements": [
                {
                    "element_type": "text",
                    "position": {"x": 100, "y": 50},
                    "size": {"width": 400, "height": 100},
                    "content": f"Text {i + 1}",
                    "style": {"font": "bold", "color": "#FFFFFF"},
                }
            ],
            "color_palette": ["#FF0000", "#FFFFFF"],
            "mood": "exciting",
        })
    return {"thumbnails": thumbnails}


class TestThumbnailGenerationCount:
    """Property tests for thumbnail generation count.

    **Feature: youtube-automation, Property 21: Thumbnail Generation Count**
    **Validates: Requirements 15.1**
    """

    @given(
        video_title=video_title_strategy,
        video_content=video_content_strategy,
        style=style_strategy,
        include_text=include_text_strategy,
        text_content=text_content_strategy,
        brand_colors=brand_colors_strategy,
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_thumbnail_generation_returns_exactly_three_thumbnails(
        self,
        video_title: str,
        video_content: str,
        style: str,
        include_text: bool,
        text_content: str,
        brand_colors: list[str],
    ):
        """
        **Feature: youtube-automation, Property 21: Thumbnail Generation Count**
        **Validates: Requirements 15.1**

        For any valid thumbnail generation request, the system SHALL return
        exactly 3 thumbnail variations.
        """
        # Create mock OpenAI client
        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=create_mock_thumbnail_response(3))

        # Create service with mock client
        service = AIService(session=None, openai_client=mock_client)

        # Create request
        request = ThumbnailGenerationRequest(
            video_title=video_title.strip() or "Test Title",
            video_content=video_content,
            style=style,
            include_text=include_text,
            text_content=text_content,
            brand_colors=brand_colors,
        )

        # Generate thumbnails
        response = await service.generate_thumbnails(request)

        # Property: Must return exactly 3 thumbnails
        assert len(response.thumbnails) == 3, (
            f"Expected exactly 3 thumbnails, got {len(response.thumbnails)}"
        )

        # Property: Each thumbnail must have required fields
        for i, thumbnail in enumerate(response.thumbnails):
            assert thumbnail.id, f"Thumbnail {i} missing id"
            assert thumbnail.image_url, f"Thumbnail {i} missing image_url"
            assert thumbnail.style, f"Thumbnail {i} missing style"
            assert isinstance(thumbnail.elements, list), f"Thumbnail {i} elements not a list"
            assert thumbnail.width == 1280, f"Thumbnail {i} width not 1280"
            assert thumbnail.height == 720, f"Thumbnail {i} height not 720"

    @given(
        video_title=video_title_strategy,
        num_api_thumbnails=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_thumbnail_generation_pads_to_three_when_api_returns_fewer(
        self,
        video_title: str,
        num_api_thumbnails: int,
    ):
        """
        **Feature: youtube-automation, Property 21: Thumbnail Generation Count**
        **Validates: Requirements 15.1**

        For any API response with fewer than 3 thumbnails, the system SHALL
        pad the response to exactly 3 thumbnails.
        """
        # Create mock OpenAI client with variable number of thumbnails
        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(
            return_value=create_mock_thumbnail_response(num_api_thumbnails)
        )

        # Create service with mock client
        service = AIService(session=None, openai_client=mock_client)

        # Create request
        request = ThumbnailGenerationRequest(
            video_title=video_title.strip() or "Test Title",
            video_content=None,
            style="modern",
            include_text=True,
            text_content=None,
            brand_colors=None,
        )

        # Generate thumbnails
        response = await service.generate_thumbnails(request)

        # Property: Must always return exactly 3 thumbnails regardless of API response
        assert len(response.thumbnails) == 3, (
            f"Expected exactly 3 thumbnails when API returned {num_api_thumbnails}, "
            f"got {len(response.thumbnails)}"
        )

    @given(
        video_title=video_title_strategy,
        style=style_strategy,
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_thumbnail_generation_has_correct_dimensions(
        self,
        video_title: str,
        style: str,
    ):
        """
        **Feature: youtube-automation, Property 21: Thumbnail Generation Count**
        **Validates: Requirements 15.1**

        For any thumbnail generation, all thumbnails SHALL have dimensions 1280x720.
        """
        mock_client = MagicMock()
        mock_client.generate_json = AsyncMock(return_value=create_mock_thumbnail_response(3))

        service = AIService(session=None, openai_client=mock_client)

        request = ThumbnailGenerationRequest(
            video_title=video_title.strip() or "Test Title",
            video_content=None,
            style=style,
            include_text=True,
            text_content=None,
            brand_colors=None,
        )

        response = await service.generate_thumbnails(request)

        # Property: All thumbnails must have correct dimensions
        for i, thumbnail in enumerate(response.thumbnails):
            assert thumbnail.width == 1280, (
                f"Thumbnail {i} width {thumbnail.width} != 1280"
            )
            assert thumbnail.height == 720, (
                f"Thumbnail {i} height {thumbnail.height} != 720"
            )
