"""Property-based tests for transcoding resolution accuracy.

**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
**Validates: Requirements 10.1**
"""

import sys
from unittest.mock import MagicMock

# Mock celery_app before importing transcoding modules
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.transcoding.models import Resolution, RESOLUTION_DIMENSIONS
from app.modules.transcoding.ffmpeg import (
    get_expected_dimensions,
    validate_resolution_output,
)
from app.modules.transcoding.schemas import (
    get_resolution_dimensions,
    get_recommended_bitrate,
)


# Strategy for generating valid resolutions
resolution_strategy = st.sampled_from(list(Resolution))


class TestResolutionDimensions:
    """Property tests for resolution dimension mapping.
    
    Requirements 10.1: Support 720p, 1080p, 2K, 4K output.
    """

    @given(resolution=resolution_strategy)
    @settings(max_examples=100)
    def test_resolution_has_valid_dimensions(self, resolution: Resolution) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any supported resolution, the system SHALL return valid positive dimensions.
        """
        width, height = get_expected_dimensions(resolution)
        
        assert width > 0, f"Width must be positive for {resolution}"
        assert height > 0, f"Height must be positive for {resolution}"

    @given(resolution=resolution_strategy)
    @settings(max_examples=100)
    def test_resolution_dimensions_are_consistent(self, resolution: Resolution) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, get_expected_dimensions and get_resolution_dimensions
        SHALL return identical values.
        """
        expected = get_expected_dimensions(resolution)
        actual = get_resolution_dimensions(resolution)
        
        assert expected == actual, f"Dimension functions disagree for {resolution}"

    @given(resolution=resolution_strategy)
    @settings(max_examples=100)
    def test_resolution_width_greater_than_height(self, resolution: Resolution) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution (landscape format), width SHALL be greater than height.
        """
        width, height = get_expected_dimensions(resolution)
        
        assert width > height, f"Width should be > height for landscape {resolution}"

    def test_all_resolutions_have_dimensions(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        All defined resolutions SHALL have dimension mappings.
        """
        for resolution in Resolution:
            assert resolution in RESOLUTION_DIMENSIONS, f"Missing dimensions for {resolution}"
            width, height = RESOLUTION_DIMENSIONS[resolution]
            assert width > 0 and height > 0

    def test_720p_dimensions(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        720p resolution SHALL have dimensions 1280x720.
        """
        width, height = get_expected_dimensions(Resolution.RES_720P)
        assert width == 1280
        assert height == 720

    def test_1080p_dimensions(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        1080p resolution SHALL have dimensions 1920x1080.
        """
        width, height = get_expected_dimensions(Resolution.RES_1080P)
        assert width == 1920
        assert height == 1080

    def test_2k_dimensions(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        2K resolution SHALL have dimensions 2560x1440.
        """
        width, height = get_expected_dimensions(Resolution.RES_2K)
        assert width == 2560
        assert height == 1440

    def test_4k_dimensions(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        4K resolution SHALL have dimensions 3840x2160.
        """
        width, height = get_expected_dimensions(Resolution.RES_4K)
        assert width == 3840
        assert height == 2160


class TestResolutionValidation:
    """Property tests for output dimension validation.
    
    Requirements 10.1: Validate output dimensions.
    """

    @given(resolution=resolution_strategy)
    @settings(max_examples=100)
    def test_exact_match_is_valid(self, resolution: Resolution) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, exact dimension match SHALL be valid.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width,
            actual_height=expected_height,
            target_resolution=resolution,
        )
        
        assert is_valid is True, f"Exact match should be valid for {resolution}"

    @given(
        resolution=resolution_strategy,
        width_delta=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_oversized_width_is_invalid(
        self,
        resolution: Resolution,
        width_delta: int,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, output wider than expected SHALL be invalid.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width + width_delta,
            actual_height=expected_height,
            target_resolution=resolution,
        )
        
        assert is_valid is False, f"Oversized width should be invalid for {resolution}"

    @given(
        resolution=resolution_strategy,
        height_delta=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_oversized_height_is_invalid(
        self,
        resolution: Resolution,
        height_delta: int,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, output taller than expected SHALL be invalid.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width,
            actual_height=expected_height + height_delta,
            target_resolution=resolution,
        )
        
        assert is_valid is False, f"Oversized height should be invalid for {resolution}"

    @given(
        resolution=resolution_strategy,
        width_reduction=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_letterboxed_output_is_valid(
        self,
        resolution: Resolution,
        width_reduction: int,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, letterboxed output (reduced width, exact height) SHALL be valid.
        This allows for aspect ratio preservation.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        # Ensure we don't reduce width below a reasonable minimum
        assume(expected_width - width_reduction > 100)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width - width_reduction,
            actual_height=expected_height,
            target_resolution=resolution,
        )
        
        assert is_valid is True, f"Letterboxed output should be valid for {resolution}"

    @given(
        resolution=resolution_strategy,
        height_reduction=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_pillarboxed_output_is_valid(
        self,
        resolution: Resolution,
        height_reduction: int,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, pillarboxed output (exact width, reduced height) SHALL be valid.
        This allows for aspect ratio preservation.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        # Ensure we don't reduce height below a reasonable minimum
        assume(expected_height - height_reduction > 100)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width,
            actual_height=expected_height - height_reduction,
            target_resolution=resolution,
        )
        
        assert is_valid is True, f"Pillarboxed output should be valid for {resolution}"

    @given(
        resolution=resolution_strategy,
        width_reduction=st.integers(min_value=1, max_value=50),
        height_reduction=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_both_dimensions_reduced_is_invalid(
        self,
        resolution: Resolution,
        width_reduction: int,
        height_reduction: int,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, output with both dimensions reduced SHALL be invalid.
        At least one dimension must match exactly.
        """
        expected_width, expected_height = get_expected_dimensions(resolution)
        
        is_valid = validate_resolution_output(
            actual_width=expected_width - width_reduction,
            actual_height=expected_height - height_reduction,
            target_resolution=resolution,
        )
        
        assert is_valid is False, f"Both dimensions reduced should be invalid for {resolution}"


class TestBitrateRecommendations:
    """Property tests for bitrate recommendations."""

    @given(resolution=resolution_strategy)
    @settings(max_examples=100)
    def test_bitrate_is_positive(self, resolution: Resolution) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any resolution, recommended bitrate SHALL be positive.
        """
        from app.modules.transcoding.models import LatencyMode
        
        bitrate = get_recommended_bitrate(resolution)
        assert bitrate > 0, f"Bitrate must be positive for {resolution}"

    @given(
        resolution1=resolution_strategy,
        resolution2=resolution_strategy,
    )
    @settings(max_examples=100)
    def test_higher_resolution_has_higher_bitrate(
        self,
        resolution1: Resolution,
        resolution2: Resolution,
    ) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        For any two resolutions, higher resolution SHALL have >= bitrate.
        """
        from app.modules.transcoding.models import LatencyMode
        
        width1, height1 = get_expected_dimensions(resolution1)
        width2, height2 = get_expected_dimensions(resolution2)
        
        bitrate1 = get_recommended_bitrate(resolution1)
        bitrate2 = get_recommended_bitrate(resolution2)
        
        pixels1 = width1 * height1
        pixels2 = width2 * height2
        
        if pixels1 > pixels2:
            assert bitrate1 >= bitrate2, "Higher resolution should have higher bitrate"
        elif pixels1 < pixels2:
            assert bitrate1 <= bitrate2, "Lower resolution should have lower bitrate"


class TestResolutionOrdering:
    """Property tests for resolution ordering."""

    def test_resolutions_are_ordered_by_size(self) -> None:
        """**Feature: youtube-automation, Property 16: Transcoding Resolution Accuracy**
        
        Resolutions SHALL be ordered from smallest to largest.
        """
        resolutions = [
            Resolution.RES_720P,
            Resolution.RES_1080P,
            Resolution.RES_2K,
            Resolution.RES_4K,
        ]
        
        prev_pixels = 0
        for resolution in resolutions:
            width, height = get_expected_dimensions(resolution)
            pixels = width * height
            assert pixels > prev_pixels, f"{resolution} should have more pixels than previous"
            prev_pixels = pixels
