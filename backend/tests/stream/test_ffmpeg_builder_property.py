"""Property-based tests for FFmpeg Command Builder and Output Parser.

**Feature: video-streaming, Property: FFmpeg Command Builder**
**Validates: Requirements 3.1, 3.4, 3.5, 10.1, 10.2, 10.3, 10.4**
"""

import uuid
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.stream_job_models import (
    StreamJob,
    LoopMode,
    EncodingMode,
    Resolution,
)
from app.modules.stream.ffmpeg_builder import (
    FFmpegCommandBuilder,
    FFmpegOutputParser,
    FFmpegMetrics,
    PlaylistConcatBuilder,
    FFmpegPlaylistCommandBuilder,
    validate_ffmpeg_command,
    RESOLUTION_SCALE,
)


# ============================================
# Strategies for generating test data
# ============================================

bitrate_strategy = st.integers(min_value=1000, max_value=10000)
fps_strategy = st.sampled_from([24, 30, 60])
resolution_strategy = st.sampled_from([r.value for r in Resolution])
loop_mode_strategy = st.sampled_from([m.value for m in LoopMode])
encoding_mode_strategy = st.sampled_from([m.value for m in EncodingMode])
loop_count_strategy = st.integers(min_value=1, max_value=100)


def create_test_job(
    loop_mode: str = LoopMode.NONE.value,
    loop_count: int = None,
    resolution: str = Resolution.RES_1080P.value,
    target_bitrate: int = 6000,
    target_fps: int = 30,
    encoding_mode: str = EncodingMode.CBR.value,
    stream_key: str = "test-stream-key",
) -> StreamJob:
    """Create a test StreamJob with given parameters."""
    job = StreamJob(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        video_path="/test/video.mp4",
        title="Test Stream",
        loop_mode=loop_mode,
        loop_count=loop_count,
        resolution=resolution,
        target_bitrate=target_bitrate,
        target_fps=target_fps,
        encoding_mode=encoding_mode,
        rtmp_url="rtmp://a.rtmp.youtube.com/live2",
    )
    job.stream_key = stream_key
    return job


# ============================================
# Property Tests for FFmpeg Command Builder
# ============================================


class TestFFmpegCommandBuilder:
    """Property tests for FFmpeg command generation.
    
    **Property 6: FFmpeg Command Contains Required Parameters**
    **Validates: Requirements 3.1**
    """

    @given(
        resolution=resolution_strategy,
        bitrate=bitrate_strategy,
        fps=fps_strategy,
        encoding_mode=encoding_mode_strategy,
    )
    @settings(max_examples=50)
    def test_command_contains_required_parameters(
        self,
        resolution: str,
        bitrate: int,
        fps: int,
        encoding_mode: str,
    ) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        Generated FFmpeg command SHALL contain all required parameters.
        """
        job = create_test_job(
            resolution=resolution,
            target_bitrate=bitrate,
            target_fps=fps,
            encoding_mode=encoding_mode,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        # Required parameters
        assert "-c:v" in cmd_str, "Missing video codec parameter"
        assert "libx264" in cmd_str, "Missing H.264 codec"
        assert "-c:a" in cmd_str, "Missing audio codec parameter"
        assert "aac" in cmd_str, "Missing AAC codec"
        assert "-f" in cmd_str, "Missing output format"
        assert "flv" in cmd_str, "Missing FLV format"
        assert "-re" in cmd_str, "Missing real-time flag"
        assert "-i" in cmd_str, "Missing input flag"

    @given(
        resolution=resolution_strategy,
        bitrate=bitrate_strategy,
    )
    @settings(max_examples=30)
    def test_command_contains_bitrate_settings(
        self,
        resolution: str,
        bitrate: int,
    ) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        Generated command SHALL contain bitrate configuration.
        Requirements: 10.2
        """
        job = create_test_job(
            resolution=resolution,
            target_bitrate=bitrate,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        # Bitrate should be in command
        assert f"{bitrate}k" in cmd_str, f"Missing bitrate {bitrate}k in command"
        assert "-b:v" in cmd_str, "Missing video bitrate flag"

    @given(fps=fps_strategy)
    @settings(max_examples=10)
    def test_command_contains_fps_setting(self, fps: int) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        Generated command SHALL contain FPS configuration.
        Requirements: 10.4
        """
        job = create_test_job(target_fps=fps)
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        assert f"-r {fps}" in cmd_str, f"Missing FPS setting -r {fps}"

    @given(resolution=resolution_strategy)
    @settings(max_examples=10)
    def test_command_contains_resolution_scale(self, resolution: str) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        Generated command SHALL contain resolution scaling.
        Requirements: 10.1
        """
        job = create_test_job(resolution=resolution)
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        expected_scale = RESOLUTION_SCALE.get(resolution, "1920:1080")
        assert expected_scale in cmd_str, (
            f"Missing resolution scale {expected_scale} for {resolution}"
        )

    def test_cbr_mode_has_constant_bitrate(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        CBR mode SHALL set minrate = maxrate = target bitrate.
        Requirements: 10.3
        """
        job = create_test_job(
            encoding_mode=EncodingMode.CBR.value,
            target_bitrate=6000,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        assert "-minrate 6000k" in cmd_str, "CBR should have minrate"
        assert "-maxrate 6000k" in cmd_str, "CBR should have maxrate equal to bitrate"

    def test_vbr_mode_has_variable_bitrate(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Command**
        
        VBR mode SHALL set maxrate > target bitrate.
        Requirements: 10.3
        """
        job = create_test_job(
            encoding_mode=EncodingMode.VBR.value,
            target_bitrate=6000,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        cmd_str = " ".join(cmd)
        
        # VBR should have maxrate = 1.5x bitrate
        assert "-maxrate 9000k" in cmd_str, "VBR should have maxrate > bitrate"
        assert "-minrate" not in cmd_str, "VBR should not have minrate"


# ============================================
# Property Tests for Loop Configuration
# ============================================


class TestLoopConfiguration:
    """Property tests for loop mode in FFmpeg commands.
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    def test_infinite_loop_uses_minus_one(self) -> None:
        """**Feature: video-streaming, Property: Loop Mode**
        
        INFINITE mode SHALL use -stream_loop -1.
        Requirements: 2.1
        """
        job = create_test_job(loop_mode=LoopMode.INFINITE.value)
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        
        # Find stream_loop index
        loop_idx = cmd.index("-stream_loop")
        assert cmd[loop_idx + 1] == "-1", "Infinite loop should use -1"

    @given(loop_count=loop_count_strategy)
    @settings(max_examples=50)
    def test_count_loop_uses_n_minus_one(self, loop_count: int) -> None:
        """**Feature: video-streaming, Property: Loop Mode**
        
        COUNT mode with N loops SHALL use -stream_loop (N-1).
        Requirements: 2.2
        """
        job = create_test_job(
            loop_mode=LoopMode.COUNT.value,
            loop_count=loop_count,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        
        loop_idx = cmd.index("-stream_loop")
        expected = str(loop_count - 1)
        assert cmd[loop_idx + 1] == expected, (
            f"Count loop {loop_count} should use {expected}, got {cmd[loop_idx + 1]}"
        )

    def test_none_loop_uses_zero(self) -> None:
        """**Feature: video-streaming, Property: Loop Mode**
        
        NONE mode SHALL use -stream_loop 0.
        Requirements: 2.3
        """
        job = create_test_job(loop_mode=LoopMode.NONE.value)
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        
        loop_idx = cmd.index("-stream_loop")
        assert cmd[loop_idx + 1] == "0", "None loop should use 0"


# ============================================
# Property Tests for FFmpeg Output Parser
# ============================================


class TestFFmpegOutputParser:
    """Property tests for FFmpeg output parsing.
    
    **Property 7: FFmpeg Output Parsing Extracts All Metrics**
    **Validates: Requirements 3.4, 3.5**
    """

    @given(
        frame=st.integers(min_value=0, max_value=1000000),
        fps=st.floats(min_value=0.1, max_value=120.0, allow_nan=False),
        bitrate=st.floats(min_value=100, max_value=50000, allow_nan=False),
        speed=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_parse_progress_line(
        self,
        frame: int,
        fps: float,
        bitrate: float,
        speed: float,
    ) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        Parser SHALL extract frame, fps, bitrate, speed from progress line.
        """
        # Build a realistic FFmpeg progress line
        line = (
            f"frame={frame:5d} fps={fps:5.1f} q=28.0 size=   1234kB "
            f"time=00:01:23.45 bitrate={bitrate:7.1f}kbits/s speed={speed:.2f}x"
        )
        
        parser = FFmpegOutputParser()
        metrics = parser.parse_line(line)
        
        assert metrics is not None, f"Failed to parse line: {line}"
        assert metrics.frame_count == frame, f"Frame mismatch: {metrics.frame_count} != {frame}"
        assert abs(metrics.fps - fps) < 0.2, f"FPS mismatch: {metrics.fps} != {fps}"
        # Bitrate is converted from kbits/s to bps
        expected_bitrate = int(bitrate * 1000)
        assert abs(metrics.bitrate - expected_bitrate) < 1000, (
            f"Bitrate mismatch: {metrics.bitrate} != {expected_bitrate}"
        )

    def test_parse_simple_progress_line(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        Parser SHALL handle simple progress format.
        """
        line = "frame=  100 fps= 30 bitrate=6000.0kbits/s speed=1.00x"
        
        parser = FFmpegOutputParser()
        metrics = parser.parse_line(line)
        
        assert metrics is not None
        assert metrics.frame_count == 100
        assert metrics.fps == 30.0
        assert metrics.bitrate == 6000000  # 6000 kbits/s = 6000000 bps

    def test_parse_returns_none_for_non_progress_line(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        Parser SHALL return None for non-progress lines.
        """
        non_progress_lines = [
            "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':",
            "Duration: 00:10:00.00, start: 0.000000, bitrate: 5000 kb/s",
            "Stream #0:0(und): Video: h264 (High)",
            "",
            "Some random text",
        ]
        
        parser = FFmpegOutputParser()
        
        for line in non_progress_lines:
            metrics = parser.parse_line(line)
            assert metrics is None, f"Should return None for: {line}"

    @given(
        hours=st.integers(min_value=0, max_value=23),
        minutes=st.integers(min_value=0, max_value=59),
        seconds=st.floats(min_value=0, max_value=59.99, allow_nan=False),
    )
    @settings(max_examples=50)
    def test_time_to_seconds_conversion(
        self,
        hours: int,
        minutes: int,
        seconds: float,
    ) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        time_to_seconds() SHALL correctly convert time string to seconds.
        """
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"
        
        parser = FFmpegOutputParser()
        result = parser.time_to_seconds(time_str)
        
        expected = hours * 3600 + minutes * 60 + seconds
        assert abs(result - expected) < 0.01, (
            f"Time conversion failed: {time_str} -> {result} != {expected}"
        )

    def test_detect_connection_error(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        Parser SHALL detect connection errors.
        """
        error_lines = [
            "Connection refused",
            "Connection timed out",
            "Connection reset by peer",
            "Network is unreachable",
        ]
        
        parser = FFmpegOutputParser()
        
        for line in error_lines:
            assert parser.is_connection_error(line) is True, (
                f"Should detect connection error: {line}"
            )

    def test_detect_input_error(self) -> None:
        """**Feature: video-streaming, Property: FFmpeg Output Parsing**
        
        Parser SHALL detect input file errors.
        """
        error_lines = [
            "No such file or directory",
            "Invalid data found when processing input",
            "File does not exist",
            "Permission denied",
        ]
        
        parser = FFmpegOutputParser()
        
        for line in error_lines:
            assert parser.is_input_error(line) is True, (
                f"Should detect input error: {line}"
            )


# ============================================
# Property Tests for Loop Detection
# ============================================


class TestLoopDetection:
    """Property tests for video loop detection."""

    @given(
        previous_seconds=st.floats(min_value=100, max_value=3600, allow_nan=False),
        current_seconds=st.floats(min_value=0, max_value=50, allow_nan=False),
    )
    @settings(max_examples=50)
    def test_detect_loop_on_time_reset(
        self,
        previous_seconds: float,
        current_seconds: float,
    ) -> None:
        """**Feature: video-streaming, Property: Loop Detection**
        
        Loop SHALL be detected when time resets significantly.
        """
        assume(previous_seconds > current_seconds + 10)
        
        def seconds_to_time(s: float) -> str:
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            sec = s % 60
            return f"{h:02d}:{m:02d}:{sec:05.2f}"
        
        previous_time = seconds_to_time(previous_seconds)
        current_time = seconds_to_time(current_seconds)
        
        parser = FFmpegOutputParser()
        is_loop = parser.detect_loop_completion(
            current_time=current_time,
            previous_time=previous_time,
            video_duration=previous_seconds + 100,
        )
        
        assert is_loop is True, (
            f"Should detect loop: {previous_time} -> {current_time}"
        )


# ============================================
# Property Tests for Command Validation
# ============================================


class TestCommandValidation:
    """Property tests for FFmpeg command validation."""

    @given(
        resolution=resolution_strategy,
        bitrate=bitrate_strategy,
        fps=fps_strategy,
    )
    @settings(max_examples=30)
    def test_generated_command_is_valid(
        self,
        resolution: str,
        bitrate: int,
        fps: int,
    ) -> None:
        """**Feature: video-streaming, Property: Command Validation**
        
        Generated FFmpeg command SHALL pass validation.
        """
        job = create_test_job(
            resolution=resolution,
            target_bitrate=bitrate,
            target_fps=fps,
        )
        
        builder = FFmpegCommandBuilder()
        cmd = builder.build_streaming_command(job)
        
        is_valid, error = validate_ffmpeg_command(cmd)
        
        assert is_valid is True, f"Command validation failed: {error}"

    def test_invalid_command_fails_validation(self) -> None:
        """**Feature: video-streaming, Property: Command Validation**
        
        Invalid command SHALL fail validation with error message.
        """
        invalid_cmd = ["ffmpeg", "-i", "input.mp4", "output.mp4"]
        
        is_valid, error = validate_ffmpeg_command(invalid_cmd)
        
        assert is_valid is False
        assert error is not None


# ============================================
# Property Tests for Playlist Concat Builder
# ============================================


class TestPlaylistConcatBuilder:
    """Property tests for playlist concat file builder.
    
    **Property 17: Playlist Order Preservation**
    **Validates: Requirements 11.1**
    """

    @given(
        video_count=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=30)
    def test_concat_file_preserves_order(self, video_count: int) -> None:
        """**Feature: video-streaming, Property: Playlist Order**
        
        Concat file SHALL preserve video order from input list.
        """
        import os
        import tempfile
        
        video_paths = [f"/videos/video_{i}.mp4" for i in range(video_count)]
        job_id = str(uuid.uuid4())
        
        builder = PlaylistConcatBuilder(temp_dir=tempfile.gettempdir())
        concat_path = builder.build_concat_file(video_paths, job_id)
        
        try:
            with open(concat_path, "r") as f:
                lines = f.readlines()
            
            # Each video should have one line
            assert len(lines) == video_count, (
                f"Expected {video_count} lines, got {len(lines)}"
            )
            
            # Order should be preserved
            for i, line in enumerate(lines):
                expected_path = video_paths[i]
                assert expected_path in line, (
                    f"Video {i} should be {expected_path}, got {line}"
                )
        finally:
            # Cleanup
            if os.path.exists(concat_path):
                os.remove(concat_path)

    def test_concat_file_escapes_quotes(self) -> None:
        """**Feature: video-streaming, Property: Playlist Concat**
        
        Concat file SHALL escape single quotes in paths.
        """
        import os
        import tempfile
        
        video_paths = ["/videos/video's_name.mp4"]
        job_id = str(uuid.uuid4())
        
        builder = PlaylistConcatBuilder(temp_dir=tempfile.gettempdir())
        concat_path = builder.build_concat_file(video_paths, job_id)
        
        try:
            with open(concat_path, "r") as f:
                content = f.read()
            
            # Single quote should be escaped
            assert "'\\''" in content or "video's_name" not in content.replace("'\\''", ""), (
                "Single quotes should be escaped"
            )
        finally:
            if os.path.exists(concat_path):
                os.remove(concat_path)

    def test_cleanup_removes_concat_file(self) -> None:
        """**Feature: video-streaming, Property: Playlist Concat**
        
        cleanup_concat_file() SHALL remove the concat file.
        """
        import os
        import tempfile
        
        video_paths = ["/videos/video.mp4"]
        job_id = str(uuid.uuid4())
        
        builder = PlaylistConcatBuilder(temp_dir=tempfile.gettempdir())
        concat_path = builder.build_concat_file(video_paths, job_id)
        
        assert os.path.exists(concat_path), "Concat file should exist"
        
        result = builder.cleanup_concat_file(job_id)
        
        assert result is True, "Cleanup should return True"
        assert not os.path.exists(concat_path), "Concat file should be removed"
