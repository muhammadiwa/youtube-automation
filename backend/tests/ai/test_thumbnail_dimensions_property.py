"""Property-based tests for thumbnail dimension compliance.

**Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
**Validates: Requirements 15.3**

Tests that all optimized thumbnails have exactly 1280x720 dimensions.
"""

import io
from datetime import timedelta
import pytest
from hypothesis import given, strategies as st, settings
from PIL import Image

from app.modules.ai.thumbnail import (
    ThumbnailOptimizer,
    optimize_thumbnail,
    YOUTUBE_THUMBNAIL_WIDTH,
    YOUTUBE_THUMBNAIL_HEIGHT,
)


# Strategy for generating image dimensions
width_strategy = st.integers(min_value=100, max_value=4000)
height_strategy = st.integers(min_value=100, max_value=4000)

# Strategy for image modes
mode_strategy = st.sampled_from(["RGB", "RGBA", "L", "P"])

# Strategy for enhance quality flag
enhance_strategy = st.booleans()


def create_test_image(width: int, height: int, mode: str = "RGB") -> bytes:
    """Create a test image with specified dimensions.

    Args:
        width: Image width
        height: Image height
        mode: Image mode (RGB, RGBA, etc.)

    Returns:
        bytes: Image data as bytes
    """
    # Create image with solid color
    if mode == "P":
        # Palette mode needs special handling
        image = Image.new("P", (width, height))
        image.putpalette([i for i in range(256)] * 3)
    else:
        image = Image.new(mode, (width, height), color=(128, 128, 128) if mode == "RGB" else 128)

    # Save to bytes
    output = io.BytesIO()
    if mode in ("RGBA", "P"):
        image.save(output, format="PNG")
    else:
        image.save(output, format="JPEG", quality=85)
    return output.getvalue()


class TestThumbnailDimensionCompliance:
    """Property tests for thumbnail dimension compliance.

    **Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
    **Validates: Requirements 15.3**
    """

    @given(
        input_width=width_strategy,
        input_height=height_strategy,
        enhance_quality=enhance_strategy,
    )
    @settings(max_examples=100, deadline=timedelta(seconds=5))
    def test_optimized_thumbnail_has_exact_dimensions(
        self,
        input_width: int,
        input_height: int,
        enhance_quality: bool,
    ):
        """
        **Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
        **Validates: Requirements 15.3**

        For any input image of any dimensions, the optimized output SHALL have
        exactly 1280x720 dimensions.
        """
        # Create test image with arbitrary dimensions
        image_data = create_test_image(input_width, input_height, "RGB")

        # Optimize the image
        optimized_data, metadata = optimize_thumbnail(
            image_data,
            target_width=YOUTUBE_THUMBNAIL_WIDTH,
            target_height=YOUTUBE_THUMBNAIL_HEIGHT,
            enhance_quality=enhance_quality,
        )

        # Verify output dimensions
        output_image = Image.open(io.BytesIO(optimized_data))
        output_width, output_height = output_image.size

        # Property: Output must be exactly 1280x720
        assert output_width == YOUTUBE_THUMBNAIL_WIDTH, (
            f"Output width {output_width} != {YOUTUBE_THUMBNAIL_WIDTH} "
            f"(input was {input_width}x{input_height})"
        )
        assert output_height == YOUTUBE_THUMBNAIL_HEIGHT, (
            f"Output height {output_height} != {YOUTUBE_THUMBNAIL_HEIGHT} "
            f"(input was {input_width}x{input_height})"
        )

        # Verify metadata matches
        assert metadata["final_dimensions"]["width"] == YOUTUBE_THUMBNAIL_WIDTH
        assert metadata["final_dimensions"]["height"] == YOUTUBE_THUMBNAIL_HEIGHT

    @given(
        input_width=width_strategy,
        input_height=height_strategy,
        mode=mode_strategy,
    )
    @settings(max_examples=100, deadline=timedelta(seconds=5))
    def test_optimized_thumbnail_dimensions_regardless_of_input_mode(
        self,
        input_width: int,
        input_height: int,
        mode: str,
    ):
        """
        **Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
        **Validates: Requirements 15.3**

        For any input image mode (RGB, RGBA, L, P), the optimized output SHALL
        have exactly 1280x720 dimensions.
        """
        # Create test image with specified mode
        image_data = create_test_image(input_width, input_height, mode)

        # Optimize the image
        optimized_data, metadata = optimize_thumbnail(
            image_data,
            target_width=YOUTUBE_THUMBNAIL_WIDTH,
            target_height=YOUTUBE_THUMBNAIL_HEIGHT,
            enhance_quality=True,
        )

        # Verify output dimensions
        output_image = Image.open(io.BytesIO(optimized_data))
        output_width, output_height = output_image.size

        # Property: Output must be exactly 1280x720 regardless of input mode
        assert output_width == YOUTUBE_THUMBNAIL_WIDTH, (
            f"Output width {output_width} != {YOUTUBE_THUMBNAIL_WIDTH} "
            f"(input mode was {mode})"
        )
        assert output_height == YOUTUBE_THUMBNAIL_HEIGHT, (
            f"Output height {output_height} != {YOUTUBE_THUMBNAIL_HEIGHT} "
            f"(input mode was {mode})"
        )

    @given(
        input_width=width_strategy,
        input_height=height_strategy,
    )
    @settings(max_examples=100, deadline=timedelta(seconds=5))
    def test_thumbnail_optimizer_validate_dimensions(
        self,
        input_width: int,
        input_height: int,
    ):
        """
        **Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
        **Validates: Requirements 15.3**

        For any optimized image, validate_dimensions SHALL return True
        and correct dimensions.
        """
        # Create and optimize image
        image_data = create_test_image(input_width, input_height, "RGB")
        optimizer = ThumbnailOptimizer()
        optimized_data, _ = optimizer.optimize(image_data)

        # Validate dimensions
        is_valid, dimensions = optimizer.validate_dimensions(optimized_data)

        # Property: Optimized images must pass validation
        assert is_valid is True, (
            f"Optimized image failed validation with dimensions {dimensions}"
        )
        assert dimensions["width"] == YOUTUBE_THUMBNAIL_WIDTH
        assert dimensions["height"] == YOUTUBE_THUMBNAIL_HEIGHT

    @given(
        aspect_ratio=st.floats(min_value=0.5, max_value=3.0),
        base_size=st.integers(min_value=200, max_value=2000),
    )
    @settings(max_examples=100, deadline=timedelta(seconds=5))
    def test_thumbnail_handles_various_aspect_ratios(
        self,
        aspect_ratio: float,
        base_size: int,
    ):
        """
        **Feature: youtube-automation, Property 22: Thumbnail Dimension Compliance**
        **Validates: Requirements 15.3**

        For any input aspect ratio, the optimized output SHALL have
        exactly 1280x720 dimensions (16:9 aspect ratio).
        """
        # Calculate dimensions based on aspect ratio
        input_width = base_size
        input_height = int(base_size / aspect_ratio)

        # Ensure minimum dimensions
        if input_height < 100:
            input_height = 100

        # Create test image
        image_data = create_test_image(input_width, input_height, "RGB")

        # Optimize the image
        optimized_data, metadata = optimize_thumbnail(image_data)

        # Verify output dimensions
        output_image = Image.open(io.BytesIO(optimized_data))
        output_width, output_height = output_image.size

        # Property: Output must be exactly 1280x720 regardless of input aspect ratio
        assert output_width == YOUTUBE_THUMBNAIL_WIDTH, (
            f"Output width {output_width} != {YOUTUBE_THUMBNAIL_WIDTH} "
            f"(input aspect ratio was {aspect_ratio:.2f})"
        )
        assert output_height == YOUTUBE_THUMBNAIL_HEIGHT, (
            f"Output height {output_height} != {YOUTUBE_THUMBNAIL_HEIGHT} "
            f"(input aspect ratio was {aspect_ratio:.2f})"
        )

        # Verify output aspect ratio is 16:9
        output_ratio = output_width / output_height
        expected_ratio = 16 / 9
        assert abs(output_ratio - expected_ratio) < 0.01, (
            f"Output aspect ratio {output_ratio:.4f} != {expected_ratio:.4f}"
        )
