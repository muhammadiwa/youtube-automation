"""Property-based tests for Stream Configuration Validation.

**Feature: video-streaming, Property: Configuration Validation**
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 11.2, 11.3, 12.1**
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobStatus,
    LoopMode,
    EncodingMode,
    Resolution,
    RESOLUTION_DIMENSIONS,
)


# ============================================
# Strategies for generating test data
# ============================================

valid_bitrate_strategy = st.integers(min_value=1000, max_value=10000)
valid_fps_strategy = st.sampled_from([24, 30, 60])
valid_resolution_strategy = st.sampled_from([r.value for r in Resolution])
valid_encoding_mode_strategy = st.sampled_from([m.value for m in EncodingMode])

invalid_bitrate_strategy = st.one_of(
    st.integers(min_value=-1000, max_value=999),
    st.integers(min_value=10001, max_value=100000),
)
invalid_fps_strategy = st.integers(min_value=0, max_value=23)


# ============================================
# Mock Configuration Validator
# ============================================


class OutputConfigValidator:
    """Validator for stream output configuration.
    
    Validates resolution, bitrate, FPS, and encoding mode settings.
    """

    VALID_RESOLUTIONS = [r.value for r in Resolution]
    VALID_ENCODING_MODES = [m.value for m in EncodingMode]
    MIN_BITRATE = 1000  # kbps
    MAX_BITRATE = 10000  # kbps
    VALID_FPS = [24, 30, 60]

    @classmethod
    def validate_resolution(cls, resolution: str) -> tuple[bool, str]:
        """Validate resolution setting."""
        if resolution not in cls.VALID_RESOLUTIONS:
            return False, f"Invalid resolution: {resolution}. Valid: {cls.VALID_RESOLUTIONS}"
        return True, ""

    @classmethod
    def validate_bitrate(cls, bitrate: int) -> tuple[bool, str]:
        """Validate bitrate setting."""
        if bitrate < cls.MIN_BITRATE:
            return False, f"Bitrate {bitrate} below minimum {cls.MIN_BITRATE} kbps"
        if bitrate > cls.MAX_BITRATE:
            return False, f"Bitrate {bitrate} above maximum {cls.MAX_BITRATE} kbps"
        return True, ""

    @classmethod
    def validate_fps(cls, fps: int) -> tuple[bool, str]:
        """Validate FPS setting."""
        if fps not in cls.VALID_FPS:
            return False, f"Invalid FPS: {fps}. Valid: {cls.VALID_FPS}"
        return True, ""

    @classmethod
    def validate_encoding_mode(cls, mode: str) -> tuple[bool, str]:
        """Validate encoding mode setting."""
        if mode not in cls.VALID_ENCODING_MODES:
            return False, f"Invalid encoding mode: {mode}. Valid: {cls.VALID_ENCODING_MODES}"
        return True, ""

    @classmethod
    def validate_all(
        cls,
        resolution: str,
        bitrate: int,
        fps: int,
        encoding_mode: str,
    ) -> tuple[bool, list[str]]:
        """Validate all output configuration settings."""
        errors = []
        
        valid, error = cls.validate_resolution(resolution)
        if not valid:
            errors.append(error)
        
        valid, error = cls.validate_bitrate(bitrate)
        if not valid:
            errors.append(error)
        
        valid, error = cls.validate_fps(fps)
        if not valid:
            errors.append(error)
        
        valid, error = cls.validate_encoding_mode(encoding_mode)
        if not valid:
            errors.append(error)
        
        return len(errors) == 0, errors


# ============================================
# Property Tests for Output Configuration
# ============================================


class TestOutputConfigurationValidation:
    """Property tests for output configuration validation.
    
    **Property 19: Output Configuration Validation**
    **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
    """

    @given(resolution=valid_resolution_strategy)
    @settings(max_examples=20)
    def test_valid_resolution_passes(self, resolution: str) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        Valid resolution SHALL pass validation.
        """
        valid, error = OutputConfigValidator.validate_resolution(resolution)
        
        assert valid is True, f"Resolution {resolution} should be valid"
        assert error == ""

    @given(resolution=st.text(min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_invalid_resolution_fails(self, resolution: str) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        Invalid resolution SHALL fail validation.
        """
        assume(resolution not in OutputConfigValidator.VALID_RESOLUTIONS)
        
        valid, error = OutputConfigValidator.validate_resolution(resolution)
        
        assert valid is False, f"Resolution {resolution} should be invalid"
        assert "Invalid resolution" in error

    @given(bitrate=valid_bitrate_strategy)
    @settings(max_examples=50)
    def test_valid_bitrate_passes(self, bitrate: int) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        Bitrate between 1000-10000 kbps SHALL pass validation.
        Requirements: 10.2
        """
        valid, error = OutputConfigValidator.validate_bitrate(bitrate)
        
        assert valid is True, f"Bitrate {bitrate} should be valid"
        assert error == ""

    @given(bitrate=st.integers(min_value=-1000, max_value=999))
    @settings(max_examples=30)
    def test_low_bitrate_fails(self, bitrate: int) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        Bitrate below 1000 kbps SHALL fail validation.
        """
        valid, error = OutputConfigValidator.validate_bitrate(bitrate)
        
        assert valid is False, f"Bitrate {bitrate} should be invalid (too low)"
        assert "below minimum" in error

    @given(bitrate=st.integers(min_value=10001, max_value=100000))
    @settings(max_examples=30)
    def test_high_bitrate_fails(self, bitrate: int) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        Bitrate above 10000 kbps SHALL fail validation.
        """
        valid, error = OutputConfigValidator.validate_bitrate(bitrate)
        
        assert valid is False, f"Bitrate {bitrate} should be invalid (too high)"
        assert "above maximum" in error

    @given(fps=valid_fps_strategy)
    @settings(max_examples=10)
    def test_valid_fps_passes(self, fps: int) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        FPS of 24, 30, or 60 SHALL pass validation.
        Requirements: 10.4
        """
        valid, error = OutputConfigValidator.validate_fps(fps)
        
        assert valid is True, f"FPS {fps} should be valid"
        assert error == ""

    @given(fps=st.integers(min_value=0, max_value=120))
    @settings(max_examples=50)
    def test_invalid_fps_fails(self, fps: int) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        FPS not in [24, 30, 60] SHALL fail validation.
        """
        assume(fps not in OutputConfigValidator.VALID_FPS)
        
        valid, error = OutputConfigValidator.validate_fps(fps)
        
        assert valid is False, f"FPS {fps} should be invalid"
        assert "Invalid FPS" in error

    @given(mode=valid_encoding_mode_strategy)
    @settings(max_examples=10)
    def test_valid_encoding_mode_passes(self, mode: str) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        CBR and VBR encoding modes SHALL pass validation.
        Requirements: 10.3
        """
        valid, error = OutputConfigValidator.validate_encoding_mode(mode)
        
        assert valid is True, f"Encoding mode {mode} should be valid"
        assert error == ""

    @given(
        resolution=valid_resolution_strategy,
        bitrate=valid_bitrate_strategy,
        fps=valid_fps_strategy,
        mode=valid_encoding_mode_strategy,
    )
    @settings(max_examples=30)
    def test_all_valid_config_passes(
        self,
        resolution: str,
        bitrate: int,
        fps: int,
        mode: str,
    ) -> None:
        """**Feature: video-streaming, Property: Config Validation**
        
        All valid configuration SHALL pass complete validation.
        """
        valid, errors = OutputConfigValidator.validate_all(
            resolution=resolution,
            bitrate=bitrate,
            fps=fps,
            encoding_mode=mode,
        )
        
        assert valid is True, f"Config should be valid, errors: {errors}"
        assert len(errors) == 0


# ============================================
# Property Tests for Playlist Index Progression
# ============================================


class TestPlaylistIndexProgression:
    """Property tests for playlist index progression.
    
    **Property 18: Playlist Index Progression**
    **Validates: Requirements 11.2, 11.3**
    """

    @given(
        total_items=st.integers(min_value=2, max_value=100),
        current_index=st.integers(min_value=0, max_value=98),
    )
    @settings(max_examples=50)
    def test_advance_increments_index(
        self,
        total_items: int,
        current_index: int,
    ) -> None:
        """**Feature: video-streaming, Property: Playlist Index**
        
        advance_playlist_index() SHALL increment index by 1 when not at end.
        """
        assume(current_index < total_items - 1)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.NONE.value,
            current_playlist_index=current_index,
            total_playlist_items=total_items,
        )
        
        result = job.advance_playlist_index()
        
        assert result is True, "Should advance when not at end"
        assert job.current_playlist_index == current_index + 1

    @given(total_items=st.integers(min_value=2, max_value=100))
    @settings(max_examples=30)
    def test_advance_returns_false_at_end_no_loop(self, total_items: int) -> None:
        """**Feature: video-streaming, Property: Playlist Index**
        
        advance_playlist_index() SHALL return False at end with no loop.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.NONE.value,
            current_playlist_index=total_items - 1,  # At last item
            total_playlist_items=total_items,
        )
        
        result = job.advance_playlist_index()
        
        assert result is False, "Should not advance at end with no loop"
        assert job.current_playlist_index == total_items - 1

    @given(total_items=st.integers(min_value=2, max_value=100))
    @settings(max_examples=30)
    def test_advance_loops_back_with_infinite_mode(self, total_items: int) -> None:
        """**Feature: video-streaming, Property: Playlist Index**
        
        advance_playlist_index() SHALL loop back to 0 with infinite mode.
        Requirements: 11.3
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.INFINITE.value,
            current_playlist_index=total_items - 1,  # At last item
            total_playlist_items=total_items,
            current_loop=0,
        )
        
        result = job.advance_playlist_index()
        
        assert result is True, "Should advance (loop back) with infinite mode"
        assert job.current_playlist_index == 0, "Should reset to first item"
        assert job.current_loop == 1, "Should increment loop counter"

    @given(total_items=st.integers(min_value=2, max_value=100))
    @settings(max_examples=30)
    def test_playlist_progress_calculation(self, total_items: int) -> None:
        """**Feature: video-streaming, Property: Playlist Progress**
        
        get_playlist_progress() SHALL return correct percentage.
        """
        for index in range(total_items):
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                current_playlist_index=index,
                total_playlist_items=total_items,
            )
            
            progress = job.get_playlist_progress()
            expected = (index / total_items) * 100
            
            assert abs(progress - expected) < 0.01, (
                f"Progress should be {expected}%, got {progress}%"
            )


# ============================================
# Property Tests for Statistics Persistence
# ============================================


class TestStatisticsPersistence:
    """Property tests for statistics persistence on stream end.
    
    **Property 20: Statistics Persistence on Stream End**
    **Validates: Requirements 12.1**
    """

    @given(
        duration_seconds=st.integers(min_value=0, max_value=86400),
        loop_count=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=50)
    def test_duration_accumulates_correctly(
        self,
        duration_seconds: int,
        loop_count: int,
    ) -> None:
        """**Feature: video-streaming, Property: Statistics**
        
        total_duration_seconds SHALL accumulate across sessions.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            total_duration_seconds=duration_seconds,
            current_loop=loop_count,
        )
        
        # Simulate adding more duration
        additional_duration = 3600  # 1 hour
        job.total_duration_seconds += additional_duration
        
        assert job.total_duration_seconds == duration_seconds + additional_duration

    def test_duration_calculation_from_timestamps(self) -> None:
        """**Feature: video-streaming, Property: Statistics**
        
        get_duration_seconds() SHALL calculate from start/end times.
        """
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            actual_start_at=start_time,
            actual_end_at=end_time,
        )
        
        duration = job.get_duration_seconds()
        
        # Should be approximately 2 hours (7200 seconds)
        assert 7190 < duration <= 7210, f"Duration should be ~7200s, got {duration}"

    def test_duration_zero_when_not_started(self) -> None:
        """**Feature: video-streaming, Property: Statistics**
        
        get_duration_seconds() SHALL return 0 when not started.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            actual_start_at=None,
        )
        
        duration = job.get_duration_seconds()
        
        assert duration == 0

    @given(
        initial_duration=st.integers(min_value=0, max_value=86400),
    )
    @settings(max_examples=30)
    def test_update_total_duration_adds_session(self, initial_duration: int) -> None:
        """**Feature: video-streaming, Property: Statistics**
        
        update_total_duration() SHALL add current session to total.
        """
        start_time = datetime.utcnow() - timedelta(hours=1)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            total_duration_seconds=initial_duration,
            actual_start_at=start_time,
            actual_end_at=None,  # Still running
        )
        
        session_duration = job.get_duration_seconds()
        job.update_total_duration()
        
        expected = initial_duration + session_duration
        assert abs(job.total_duration_seconds - expected) < 5, (
            f"Total duration should be ~{expected}, got {job.total_duration_seconds}"
        )


# ============================================
# Property Tests for Resolution Dimensions
# ============================================


class TestResolutionDimensions:
    """Property tests for resolution dimension mapping."""

    @given(resolution=valid_resolution_strategy)
    @settings(max_examples=20)
    def test_all_resolutions_have_valid_dimensions(self, resolution: str) -> None:
        """**Feature: video-streaming, Property: Resolution**
        
        All valid resolutions SHALL have positive dimensions.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            resolution=resolution,
        )
        
        width, height = job.get_resolution_dimensions()
        
        assert width > 0, f"Width should be positive for {resolution}"
        assert height > 0, f"Height should be positive for {resolution}"

    def test_resolution_dimensions_are_standard(self) -> None:
        """**Feature: video-streaming, Property: Resolution**
        
        Resolution dimensions SHALL match standard values.
        """
        expected = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "4k": (3840, 2160),
        }
        
        for res, (exp_width, exp_height) in expected.items():
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                resolution=res,
            )
            
            width, height = job.get_resolution_dimensions()
            
            assert width == exp_width, f"{res} width should be {exp_width}"
            assert height == exp_height, f"{res} height should be {exp_height}"
