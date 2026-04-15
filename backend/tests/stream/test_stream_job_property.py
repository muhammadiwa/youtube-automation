"""Property-based tests for StreamJob model.

**Feature: video-streaming, Property: Stream Job Model**
**Validates: Requirements 1.1, 1.6, 1.7, 2.2, 2.4, 2.5, 8.1, 8.2, 8.3**
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

stream_key_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=4,
    max_size=64,
)

loop_count_strategy = st.integers(min_value=1, max_value=1000)

status_strategy = st.sampled_from([s.value for s in StreamJobStatus])

loop_mode_strategy = st.sampled_from([m.value for m in LoopMode])

resolution_strategy = st.sampled_from([r.value for r in Resolution])


# ============================================
# Property Tests for Stream Key Encryption
# ============================================


class TestStreamKeyEncryption:
    """Property tests for stream key encryption round-trip.
    
    **Property 2: Stream Key Encryption Round-Trip**
    **Validates: Requirements 8.1, 8.3**
    """

    @given(stream_key=stream_key_strategy)
    @settings(max_examples=100)
    def test_stream_key_encryption_round_trip(self, stream_key: str) -> None:
        """**Feature: video-streaming, Property: Stream Key Encryption**
        
        For any stream key, encrypting and decrypting SHALL return
        the original value.
        """
        assume(len(stream_key) >= 4)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        # Set stream key (triggers encryption)
        job.stream_key = stream_key
        
        # Get stream key (triggers decryption)
        decrypted = job.stream_key
        
        assert decrypted == stream_key, (
            f"Stream key round-trip failed: {stream_key} != {decrypted}"
        )

    @given(stream_key=stream_key_strategy)
    @settings(max_examples=100)
    def test_stream_key_is_encrypted_in_storage(self, stream_key: str) -> None:
        """**Feature: video-streaming, Property: Stream Key Encryption**
        
        For any stream key, the stored value SHALL be encrypted
        (different from original).
        """
        assume(len(stream_key) >= 4)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        job.stream_key = stream_key
        
        # Internal storage should be encrypted (different from original)
        assert job._stream_key != stream_key, (
            "Stream key should be encrypted in storage"
        )

    def test_none_stream_key_returns_none(self) -> None:
        """**Feature: video-streaming, Property: Stream Key Encryption**
        
        Setting stream key to None SHALL return None on get.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        job.stream_key = None
        
        assert job.stream_key is None
        assert job._stream_key is None


# ============================================
# Property Tests for Stream Key Masking
# ============================================


class TestStreamKeyMasking:
    """Property tests for stream key masking.
    
    **Property 14: Stream Key Masking**
    **Validates: Requirements 8.2**
    """

    @given(stream_key=stream_key_strategy)
    @settings(max_examples=100)
    def test_masked_key_shows_only_last_4_chars(self, stream_key: str) -> None:
        """**Feature: video-streaming, Property: Stream Key Masking**
        
        For any stream key with length > 4, masked version SHALL show
        only the last 4 characters.
        """
        assume(len(stream_key) > 4)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        job.stream_key = stream_key
        masked = job.get_masked_stream_key()
        
        # Last 4 chars should match
        assert masked[-4:] == stream_key[-4:], (
            f"Last 4 chars should match: {masked[-4:]} != {stream_key[-4:]}"
        )
        
        # Rest should be asterisks
        expected_asterisks = "*" * (len(stream_key) - 4)
        assert masked[:-4] == expected_asterisks, (
            f"Prefix should be asterisks: {masked[:-4]} != {expected_asterisks}"
        )

    @given(stream_key=st.text(min_size=1, max_size=4))
    @settings(max_examples=50)
    def test_short_key_fully_masked(self, stream_key: str) -> None:
        """**Feature: video-streaming, Property: Stream Key Masking**
        
        For stream keys with length <= 4, entire key SHALL be masked.
        """
        assume(len(stream_key) >= 1)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        job.stream_key = stream_key
        masked = job.get_masked_stream_key()
        
        assert masked == "*" * len(stream_key), (
            f"Short key should be fully masked: {masked}"
        )

    def test_none_key_returns_none_masked(self) -> None:
        """**Feature: video-streaming, Property: Stream Key Masking**
        
        None stream key SHALL return None when masked.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        
        job.stream_key = None
        
        assert job.get_masked_stream_key() is None


# ============================================
# Property Tests for Status Transitions
# ============================================


class TestStatusTransitions:
    """Property tests for stream job status transitions.
    
    **Property 3: Stream Job Status Transitions**
    **Validates: Requirements 1.2, 1.3, 1.4**
    """

    def test_can_start_from_valid_states(self) -> None:
        """**Feature: video-streaming, Property: Status Transitions**
        
        Stream job SHALL be startable from pending, scheduled, stopped, failed.
        """
        valid_start_states = [
            StreamJobStatus.PENDING.value,
            StreamJobStatus.SCHEDULED.value,
            StreamJobStatus.STOPPED.value,
            StreamJobStatus.FAILED.value,
        ]
        
        for status in valid_start_states:
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                status=status,
            )
            
            assert job.can_start() is True, (
                f"Should be able to start from {status}"
            )

    def test_cannot_start_from_invalid_states(self) -> None:
        """**Feature: video-streaming, Property: Status Transitions**
        
        Stream job SHALL NOT be startable from starting, running, stopping, completed, cancelled.
        """
        invalid_start_states = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
            StreamJobStatus.STOPPING.value,
            StreamJobStatus.COMPLETED.value,
            StreamJobStatus.CANCELLED.value,
        ]
        
        for status in invalid_start_states:
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                status=status,
            )
            
            assert job.can_start() is False, (
                f"Should NOT be able to start from {status}"
            )

    def test_can_stop_from_active_states(self) -> None:
        """**Feature: video-streaming, Property: Status Transitions**
        
        Stream job SHALL be stoppable from starting, running.
        """
        stoppable_states = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
        ]
        
        for status in stoppable_states:
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                status=status,
            )
            
            assert job.can_stop() is True, (
                f"Should be able to stop from {status}"
            )

    def test_is_active_for_active_states(self) -> None:
        """**Feature: video-streaming, Property: Status Transitions**
        
        is_active() SHALL return True for starting, running, stopping.
        """
        active_states = [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
            StreamJobStatus.STOPPING.value,
        ]
        
        for status in active_states:
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                status=status,
            )
            
            assert job.is_active() is True, (
                f"Should be active for {status}"
            )

    def test_is_finished_for_terminal_states(self) -> None:
        """**Feature: video-streaming, Property: Status Transitions**
        
        is_finished() SHALL return True for stopped, completed, failed, cancelled.
        """
        finished_states = [
            StreamJobStatus.STOPPED.value,
            StreamJobStatus.COMPLETED.value,
            StreamJobStatus.FAILED.value,
            StreamJobStatus.CANCELLED.value,
        ]
        
        for status in finished_states:
            job = StreamJob(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                account_id=uuid.uuid4(),
                video_path="/test/video.mp4",
                title="Test Stream",
                status=status,
            )
            
            assert job.is_finished() is True, (
                f"Should be finished for {status}"
            )


# ============================================
# Property Tests for Loop Count
# ============================================


class TestLoopCount:
    """Property tests for loop count consistency.
    
    **Property 4: Loop Count Consistency**
    **Property 5: Infinite Loop Counter Increment**
    **Validates: Requirements 2.1, 2.2, 2.4, 2.5**
    """

    @given(loop_count=loop_count_strategy)
    @settings(max_examples=100)
    def test_loop_complete_when_current_reaches_target(self, loop_count: int) -> None:
        """**Feature: video-streaming, Property: Loop Count**
        
        For COUNT mode, is_loop_complete() SHALL return True when
        current_loop >= loop_count.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.COUNT.value,
            loop_count=loop_count,
            current_loop=loop_count,
        )
        
        assert job.is_loop_complete() is True, (
            f"Should be complete when current_loop ({loop_count}) >= loop_count ({loop_count})"
        )

    @given(
        loop_count=loop_count_strategy,
        current=st.integers(min_value=0, max_value=999),
    )
    @settings(max_examples=100)
    def test_loop_not_complete_when_current_less_than_target(
        self, loop_count: int, current: int
    ) -> None:
        """**Feature: video-streaming, Property: Loop Count**
        
        For COUNT mode, is_loop_complete() SHALL return False when
        current_loop < loop_count.
        """
        assume(current < loop_count)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.COUNT.value,
            loop_count=loop_count,
            current_loop=current,
        )
        
        assert job.is_loop_complete() is False, (
            f"Should NOT be complete when current_loop ({current}) < loop_count ({loop_count})"
        )

    @given(current_loop=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_infinite_loop_never_complete(self, current_loop: int) -> None:
        """**Feature: video-streaming, Property: Infinite Loop**
        
        For INFINITE mode, is_loop_complete() SHALL always return False.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.INFINITE.value,
            current_loop=current_loop,
        )
        
        assert job.is_loop_complete() is False, (
            f"Infinite loop should never be complete (current_loop={current_loop})"
        )

    @given(initial_loop=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_increment_loop_increases_by_one(self, initial_loop: int) -> None:
        """**Feature: video-streaming, Property: Loop Counter**
        
        increment_loop() SHALL increase current_loop by exactly 1.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            current_loop=initial_loop,
        )
        
        job.increment_loop()
        
        assert job.current_loop == initial_loop + 1, (
            f"Loop should increment by 1: {initial_loop} -> {job.current_loop}"
        )

    def test_should_loop_for_infinite_mode(self) -> None:
        """**Feature: video-streaming, Property: Loop Mode**
        
        For INFINITE mode, should_loop() SHALL always return True.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.INFINITE.value,
        )
        
        assert job.should_loop() is True

    def test_should_not_loop_for_none_mode(self) -> None:
        """**Feature: video-streaming, Property: Loop Mode**
        
        For NONE mode, should_loop() SHALL always return False.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
            loop_mode=LoopMode.NONE.value,
        )
        
        assert job.should_loop() is False


# ============================================
# Property Tests for Serialization
# ============================================


class TestSerialization:
    """Property tests for StreamJob serialization.
    
    **Property 1: Stream Job Serialization Round-Trip**
    **Validates: Requirements 1.6, 1.7**
    """

    @given(
        title=st.text(min_size=1, max_size=100),
        loop_mode=loop_mode_strategy,
        resolution=resolution_strategy,
        target_bitrate=st.integers(min_value=1000, max_value=10000),
        target_fps=st.sampled_from([24, 30, 60]),
    )
    @settings(max_examples=50)
    def test_to_dict_contains_all_fields(
        self,
        title: str,
        loop_mode: str,
        resolution: str,
        target_bitrate: int,
        target_fps: int,
    ) -> None:
        """**Feature: video-streaming, Property: Serialization**
        
        to_dict() SHALL contain all required fields.
        """
        assume(len(title.strip()) > 0)
        
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title=title,
            loop_mode=loop_mode,
            resolution=resolution,
            target_bitrate=target_bitrate,
            target_fps=target_fps,
        )
        
        result = job.to_dict()
        
        # Check required fields exist
        required_fields = [
            "id", "user_id", "account_id", "video_path", "title",
            "loop_mode", "resolution", "target_bitrate", "target_fps",
            "status", "current_loop", "enable_auto_restart",
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        # Check values match
        assert result["title"] == title
        assert result["loop_mode"] == loop_mode
        assert result["resolution"] == resolution
        assert result["target_bitrate"] == target_bitrate
        assert result["target_fps"] == target_fps

    def test_to_dict_masks_stream_key(self) -> None:
        """**Feature: video-streaming, Property: Serialization**
        
        to_dict() SHALL include masked stream key, not plain text.
        """
        job = StreamJob(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            video_path="/test/video.mp4",
            title="Test Stream",
        )
        job.stream_key = "my-secret-stream-key-12345"
        
        result = job.to_dict()
        
        assert "stream_key_masked" in result
        assert result["stream_key_masked"].endswith("2345")
        assert "my-secret" not in result["stream_key_masked"]


# ============================================
# Property Tests for Resolution
# ============================================


class TestResolution:
    """Property tests for resolution handling."""

    @given(resolution=resolution_strategy)
    @settings(max_examples=20)
    def test_resolution_dimensions_valid(self, resolution: str) -> None:
        """**Feature: video-streaming, Property: Resolution**
        
        get_resolution_dimensions() SHALL return valid width and height.
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
        
        assert width > 0, f"Width should be positive: {width}"
        assert height > 0, f"Height should be positive: {height}"
        assert width >= height, f"Width should be >= height for landscape: {width}x{height}"

    def test_all_resolutions_have_dimensions(self) -> None:
        """**Feature: video-streaming, Property: Resolution**
        
        All Resolution enum values SHALL have defined dimensions.
        """
        for res in Resolution:
            assert res in RESOLUTION_DIMENSIONS, (
                f"Resolution {res} missing from RESOLUTION_DIMENSIONS"
            )
            width, height = RESOLUTION_DIMENSIONS[res]
            assert width > 0 and height > 0
