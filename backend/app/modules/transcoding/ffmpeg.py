"""FFmpeg transcoding utilities.

Implements video transcoding with FFmpeg for multiple resolutions and ABR.
Requirements: 10.1, 10.3, 10.4
"""

import os
import subprocess
import json
from dataclasses import dataclass
from typing import Optional, Callable

from app.modules.transcoding.models import Resolution, LatencyMode, RESOLUTION_DIMENSIONS
from app.modules.transcoding.schemas import (
    get_resolution_dimensions,
    get_recommended_bitrate,
    ABRConfig,
    LowLatencyConfig,
)


@dataclass
class FFmpegConfig:
    """Configuration for FFmpeg transcoding."""
    input_path: str
    output_path: str
    resolution: Resolution
    bitrate: Optional[int] = None
    latency_mode: LatencyMode = LatencyMode.NORMAL
    preset: str = "medium"
    crf: int = 23
    audio_bitrate: int = 128000  # 128 kbps
    keyframe_interval: int = 2  # seconds


@dataclass
class TranscodeOutput:
    """Result of transcoding operation."""
    success: bool
    output_path: str
    width: int
    height: int
    file_size: int
    duration: float
    bitrate: int
    error_message: Optional[str] = None


class FFmpegTranscoder:
    """FFmpeg-based video transcoder.
    
    Requirements: 10.1 - Support 720p, 1080p, 2K, 4K output.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """Initialize transcoder.
        
        Args:
            ffmpeg_path: Path to ffmpeg binary
            ffprobe_path: Path to ffprobe binary
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def get_video_info(self, input_path: str) -> dict:
        """Get video information using ffprobe.
        
        Args:
            input_path: Path to input video
            
        Returns:
            Video information dict
        """
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            input_path,
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return {"error": str(e)}

    def build_transcode_command(self, config: FFmpegConfig) -> list[str]:
        """Build FFmpeg command for transcoding.
        
        Args:
            config: Transcoding configuration
            
        Returns:
            FFmpeg command as list of arguments
        """
        width, height = get_resolution_dimensions(config.resolution)
        bitrate = config.bitrate or get_recommended_bitrate(config.resolution, config.latency_mode)
        
        # Get preset based on latency mode
        preset = self._get_preset_for_latency(config.latency_mode)
        tune = self._get_tune_for_latency(config.latency_mode)
        
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-i", config.input_path,
            # Video settings
            "-c:v", "libx264",
            "-preset", preset,
            "-b:v", str(bitrate),
            "-maxrate", str(int(bitrate * 1.5)),
            "-bufsize", str(int(bitrate * 2)),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-g", str(config.keyframe_interval * 30),  # Keyframe interval in frames (assuming 30fps)
            # Audio settings
            "-c:a", "aac",
            "-b:a", str(config.audio_bitrate),
            "-ar", "48000",
            "-ac", "2",
            # Output format
            "-movflags", "+faststart",
            "-f", "mp4",
        ]
        
        # Add tune option for low latency
        if tune:
            cmd.extend(["-tune", tune])
        
        cmd.append(config.output_path)
        
        return cmd

    def _get_preset_for_latency(self, latency_mode: LatencyMode) -> str:
        """Get FFmpeg preset based on latency mode.
        
        Requirements: 10.4 - Optimize for low latency mode.
        """
        presets = {
            LatencyMode.NORMAL: "medium",
            LatencyMode.LOW: "fast",
            LatencyMode.ULTRA_LOW: "ultrafast",
        }
        return presets.get(latency_mode, "medium")

    def _get_tune_for_latency(self, latency_mode: LatencyMode) -> Optional[str]:
        """Get FFmpeg tune option based on latency mode.
        
        Requirements: 10.4 - Optimize for low latency mode.
        """
        if latency_mode in [LatencyMode.LOW, LatencyMode.ULTRA_LOW]:
            return "zerolatency"
        return None

    def transcode(
        self,
        config: FFmpegConfig,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> TranscodeOutput:
        """Transcode video to target resolution.
        
        Requirements: 10.1 - Transcode to configured resolution.
        
        Args:
            config: Transcoding configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            TranscodeOutput with result
        """
        width, height = get_resolution_dimensions(config.resolution)
        
        # Build command
        cmd = self.build_transcode_command(config)
        
        try:
            # Run FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                return TranscodeOutput(
                    success=False,
                    output_path=config.output_path,
                    width=width,
                    height=height,
                    file_size=0,
                    duration=0,
                    bitrate=0,
                    error_message=stderr,
                )
            
            # Get output file info
            file_size = os.path.getsize(config.output_path) if os.path.exists(config.output_path) else 0
            
            # Get actual output dimensions and duration
            output_info = self.get_video_info(config.output_path)
            actual_width = width
            actual_height = height
            duration = 0.0
            bitrate = config.bitrate or get_recommended_bitrate(config.resolution, config.latency_mode)
            
            if "streams" in output_info:
                for stream in output_info["streams"]:
                    if stream.get("codec_type") == "video":
                        actual_width = stream.get("width", width)
                        actual_height = stream.get("height", height)
                        break
            
            if "format" in output_info:
                duration = float(output_info["format"].get("duration", 0))
                bitrate = int(output_info["format"].get("bit_rate", bitrate))
            
            return TranscodeOutput(
                success=True,
                output_path=config.output_path,
                width=actual_width,
                height=actual_height,
                file_size=file_size,
                duration=duration,
                bitrate=bitrate,
            )
            
        except Exception as e:
            return TranscodeOutput(
                success=False,
                output_path=config.output_path,
                width=width,
                height=height,
                file_size=0,
                duration=0,
                bitrate=0,
                error_message=str(e),
            )

    def validate_output_dimensions(
        self,
        output_path: str,
        expected_resolution: Resolution,
    ) -> tuple[bool, int, int]:
        """Validate that output has correct dimensions.
        
        Requirements: 10.1 - Validate output dimensions.
        
        Args:
            output_path: Path to output video
            expected_resolution: Expected resolution
            
        Returns:
            Tuple of (is_valid, actual_width, actual_height)
        """
        expected_width, expected_height = get_resolution_dimensions(expected_resolution)
        
        info = self.get_video_info(output_path)
        
        if "error" in info or "streams" not in info:
            return False, 0, 0
        
        for stream in info["streams"]:
            if stream.get("codec_type") == "video":
                actual_width = stream.get("width", 0)
                actual_height = stream.get("height", 0)
                
                # Allow for aspect ratio preservation (one dimension matches)
                is_valid = (
                    (actual_width == expected_width and actual_height <= expected_height) or
                    (actual_height == expected_height and actual_width <= expected_width)
                )
                
                return is_valid, actual_width, actual_height
        
        return False, 0, 0


class ABRTranscoder:
    """Transcoder for Adaptive Bitrate streaming.
    
    Requirements: 10.3 - Support adaptive bitrate (ABR).
    """

    def __init__(self, base_transcoder: Optional[FFmpegTranscoder] = None):
        """Initialize ABR transcoder.
        
        Args:
            base_transcoder: Base FFmpeg transcoder
        """
        self.transcoder = base_transcoder or FFmpegTranscoder()

    def transcode_abr(
        self,
        input_path: str,
        output_dir: str,
        config: ABRConfig,
        latency_mode: LatencyMode = LatencyMode.NORMAL,
    ) -> list[TranscodeOutput]:
        """Transcode video to multiple resolutions for ABR.
        
        Args:
            input_path: Path to input video
            output_dir: Directory for output files
            config: ABR configuration
            latency_mode: Latency mode
            
        Returns:
            List of TranscodeOutput for each resolution
        """
        outputs = []
        
        for i, resolution in enumerate(config.resolutions):
            bitrate = config.bitrates[i] if i < len(config.bitrates) else None
            
            output_path = os.path.join(
                output_dir,
                f"output_{resolution.value}.mp4"
            )
            
            ffmpeg_config = FFmpegConfig(
                input_path=input_path,
                output_path=output_path,
                resolution=resolution,
                bitrate=bitrate,
                latency_mode=latency_mode,
            )
            
            result = self.transcoder.transcode(ffmpeg_config)
            outputs.append(result)
        
        return outputs


def get_expected_dimensions(resolution: Resolution) -> tuple[int, int]:
    """Get expected dimensions for a resolution.
    
    This is the core function used for property testing.
    
    Args:
        resolution: Target resolution
        
    Returns:
        Tuple of (width, height)
    """
    return RESOLUTION_DIMENSIONS[resolution]


def validate_resolution_output(
    actual_width: int,
    actual_height: int,
    target_resolution: Resolution,
) -> bool:
    """Validate that output dimensions match target resolution.
    
    Requirements: 10.1 - Validate output dimensions.
    
    Args:
        actual_width: Actual output width
        actual_height: Actual output height
        target_resolution: Target resolution
        
    Returns:
        True if dimensions match
    """
    expected_width, expected_height = get_expected_dimensions(target_resolution)
    
    # Exact match
    if actual_width == expected_width and actual_height == expected_height:
        return True
    
    # Allow for aspect ratio preservation (letterboxing/pillarboxing)
    # One dimension should match exactly, other should be <= expected
    if actual_width == expected_width and actual_height <= expected_height:
        return True
    if actual_height == expected_height and actual_width <= expected_width:
        return True
    
    return False
