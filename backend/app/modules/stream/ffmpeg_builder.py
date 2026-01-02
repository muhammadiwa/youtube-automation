"""FFmpeg Command Builder and Output Parser for Video-to-Live Streaming.

Implements FFmpeg command generation and stderr output parsing for
real-time metrics extraction. Supports hardware encoding (NVENC, QSV, AMF)
with automatic detection and fallback to software encoding.

Requirements: 3.1, 3.4, 3.5, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3
"""

import os
import re
import subprocess
import tempfile
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple
from functools import lru_cache

from app.modules.stream.stream_job_models import (
    StreamJob,
    LoopMode,
    EncodingMode,
    Resolution,
    RESOLUTION_DIMENSIONS,
)

logger = logging.getLogger(__name__)


# ============================================
# Resolution Scale Mapping
# ============================================

RESOLUTION_SCALE = {
    Resolution.RES_720P.value: "1280:720",
    Resolution.RES_1080P.value: "1920:1080",
    Resolution.RES_1440P.value: "2560:1440",
    Resolution.RES_4K.value: "3840:2160",
    # Fallback for string values
    "720p": "1280:720",
    "1080p": "1920:1080",
    "1440p": "2560:1440",
    "4k": "3840:2160",
}


# ============================================
# Hardware Encoder Types
# ============================================


class HardwareEncoder(Enum):
    """Available hardware encoders."""
    NVENC = "h264_nvenc"      # NVIDIA GPU
    QSV = "h264_qsv"          # Intel Quick Sync
    AMF = "h264_amf"          # AMD AMF
    VIDEOTOOLBOX = "h264_videotoolbox"  # macOS
    SOFTWARE = "libx264"      # CPU fallback


# Hardware encoder configurations
HARDWARE_ENCODER_CONFIG = {
    HardwareEncoder.NVENC: {
        "codec": "h264_nvenc",
        "preset": "p4",  # Balanced quality/speed (p1=fastest, p7=slowest)
        "extra_args": ["-rc", "cbr", "-tune", "ll"],  # Low latency
        "profile": "high",
    },
    HardwareEncoder.QSV: {
        "codec": "h264_qsv",
        "preset": "faster",
        "extra_args": ["-look_ahead", "0"],  # Disable lookahead for low latency
        "profile": "high",
    },
    HardwareEncoder.AMF: {
        "codec": "h264_amf",
        "preset": "speed",  # speed, balanced, quality
        "extra_args": ["-rc", "cbr"],
        "profile": "high",
    },
    HardwareEncoder.VIDEOTOOLBOX: {
        "codec": "h264_videotoolbox",
        "preset": None,  # VideoToolbox doesn't use preset
        "extra_args": ["-realtime", "1"],
        "profile": "high",
    },
    HardwareEncoder.SOFTWARE: {
        "codec": "libx264",
        "preset": "ultrafast",
        "extra_args": [],
        "profile": "high",
    },
}


# ============================================
# Hardware Detection
# ============================================


@lru_cache(maxsize=1)
def detect_available_encoders(ffmpeg_path: str = "ffmpeg") -> List[HardwareEncoder]:
    """Detect available hardware encoders on the system.
    
    Uses FFmpeg to check which encoders are available.
    Results are cached for performance.
    
    Args:
        ffmpeg_path: Path to FFmpeg binary
        
    Returns:
        List[HardwareEncoder]: Available encoders in priority order
    """
    available = []
    
    # Check each hardware encoder
    encoder_checks = [
        (HardwareEncoder.NVENC, "h264_nvenc"),
        (HardwareEncoder.QSV, "h264_qsv"),
        (HardwareEncoder.AMF, "h264_amf"),
        (HardwareEncoder.VIDEOTOOLBOX, "h264_videotoolbox"),
    ]
    
    for encoder, codec_name in encoder_checks:
        if _check_encoder_available(ffmpeg_path, codec_name):
            available.append(encoder)
            logger.info(f"Hardware encoder detected: {encoder.value}")
    
    # Software encoder is always available as fallback
    available.append(HardwareEncoder.SOFTWARE)
    
    return available


def _check_encoder_available(ffmpeg_path: str, encoder_name: str) -> bool:
    """Check if a specific encoder is available in FFmpeg.
    
    Args:
        ffmpeg_path: Path to FFmpeg binary
        encoder_name: Name of encoder to check
        
    Returns:
        bool: True if encoder is available
    """
    try:
        # Run FFmpeg with encoder to check if it's available
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return encoder_name in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Error checking encoder {encoder_name}: {e}")
        return False


def _test_encoder_works(ffmpeg_path: str, encoder: HardwareEncoder) -> bool:
    """Test if encoder actually works (not just listed).
    
    Some systems list encoders but they don't work due to driver issues.
    
    Args:
        ffmpeg_path: Path to FFmpeg binary
        encoder: Encoder to test
        
    Returns:
        bool: True if encoder works
    """
    config = HARDWARE_ENCODER_CONFIG[encoder]
    
    try:
        # Try to initialize encoder with a null output
        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-f", "lavfi",
            "-i", "nullsrc=s=256x256:d=0.1",
            "-c:v", config["codec"],
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # Check if encoding succeeded (no error about encoder)
        if result.returncode == 0:
            return True
        
        # Check stderr for common hardware encoder errors
        stderr = result.stderr.lower()
        hardware_errors = [
            "no capable devices found",
            "device not found",
            "failed to initialize",
            "cannot load",
            "driver",
        ]
        
        return not any(err in stderr for err in hardware_errors)
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Error testing encoder {encoder.value}: {e}")
        return False


def get_best_encoder(ffmpeg_path: str = "ffmpeg", test_encoder: bool = True) -> HardwareEncoder:
    """Get the best available encoder for the system.
    
    Priority: NVENC > QSV > AMF > VideoToolbox > Software
    
    Args:
        ffmpeg_path: Path to FFmpeg binary
        test_encoder: Whether to test if encoder actually works
        
    Returns:
        HardwareEncoder: Best available encoder
    """
    available = detect_available_encoders(ffmpeg_path)
    
    if not test_encoder:
        return available[0]
    
    # Test each encoder to make sure it actually works
    for encoder in available:
        if encoder == HardwareEncoder.SOFTWARE:
            return encoder  # Software always works
        
        if _test_encoder_works(ffmpeg_path, encoder):
            logger.info(f"Using hardware encoder: {encoder.value}")
            return encoder
        else:
            logger.warning(f"Encoder {encoder.value} listed but not working, trying next...")
    
    logger.info("No working hardware encoder found, using software encoding")
    return HardwareEncoder.SOFTWARE


def clear_encoder_cache():
    """Clear the encoder detection cache.
    
    Call this if hardware configuration changes.
    """
    detect_available_encoders.cache_clear()


# ============================================
# FFmpeg Metrics Data Class
# ============================================


@dataclass
class FFmpegMetrics:
    """Parsed metrics from FFmpeg stderr output.
    
    Requirements: 3.4, 3.5
    """
    frame_count: int
    fps: float
    bitrate: int  # bps
    speed: str  # e.g., "1.0x"
    time: Optional[str] = None  # e.g., "00:01:23.45"
    size_kb: Optional[int] = None
    quality: Optional[float] = None  # q value
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "frame_count": self.frame_count,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "bitrate_kbps": self.bitrate / 1000 if self.bitrate else 0,
            "speed": self.speed,
            "time": self.time,
            "size_kb": self.size_kb,
            "quality": self.quality,
        }


# ============================================
# FFmpeg Command Builder
# ============================================


class FFmpegCommandBuilder:
    """Build FFmpeg commands for video-to-live streaming.
    
    Generates FFmpeg commands with proper encoding parameters for
    streaming pre-recorded videos to RTMP endpoints.
    Supports hardware encoding with automatic detection and fallback.
    
    Requirements: 3.1, 10.1, 10.2, 10.3, 10.4
    """

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        force_encoder: Optional[HardwareEncoder] = None,
    ):
        """Initialize command builder.
        
        Args:
            ffmpeg_path: Path to FFmpeg binary
            force_encoder: Force specific encoder (None = auto-detect)
        """
        self.ffmpeg_path = ffmpeg_path
        self._force_encoder = force_encoder
        self._detected_encoder: Optional[HardwareEncoder] = None

    @property
    def encoder(self) -> HardwareEncoder:
        """Get the encoder to use (cached after first detection)."""
        if self._force_encoder:
            return self._force_encoder
        
        if self._detected_encoder is None:
            self._detected_encoder = get_best_encoder(self.ffmpeg_path)
        
        return self._detected_encoder

    def get_encoder_info(self) -> dict:
        """Get information about the current encoder.
        
        Returns:
            dict: Encoder information
        """
        encoder = self.encoder
        config = HARDWARE_ENCODER_CONFIG[encoder]
        
        return {
            "encoder": encoder.value,
            "is_hardware": encoder != HardwareEncoder.SOFTWARE,
            "codec": config["codec"],
            "preset": config["preset"],
        }

    def build_streaming_command(self, job: StreamJob) -> List[str]:
        """Build FFmpeg command for streaming.
        
        Requirements: 3.1 - Generate FFmpeg command with all parameters.
        
        Args:
            job: StreamJob with configuration
            
        Returns:
            List[str]: FFmpeg command arguments
        """
        cmd = [self.ffmpeg_path]
        
        # Add loop configuration (Requirements: 2.1, 2.2, 2.3)
        loop_arg = self._get_loop_arg(job)
        cmd.extend(["-stream_loop", loop_arg])
        
        # Real-time mode - read input at native frame rate
        cmd.append("-re")
        
        # Input file
        cmd.extend(["-i", job.video_path])
        
        # Video encoding (Requirements: 10.1, 10.2, 10.3)
        cmd.extend(self._build_video_encoding(job))
        
        # Audio encoding
        cmd.extend(self._build_audio_encoding())
        
        # Output format and destination
        cmd.extend(self._build_output(job))
        
        return cmd

    def _get_loop_arg(self, job: StreamJob) -> str:
        """Get loop argument for FFmpeg.
        
        Requirements: 2.1, 2.2, 2.3
        
        Args:
            job: StreamJob with loop configuration
            
        Returns:
            str: Loop argument value
        """
        if job.loop_mode == LoopMode.INFINITE.value:
            return "-1"  # Infinite loop
        elif job.loop_mode == LoopMode.COUNT.value:
            # FFmpeg -stream_loop is 0-based (0 = play once, 1 = play twice)
            # So for N loops, we use N-1
            count = job.loop_count or 1
            return str(count - 1)
        else:
            return "0"  # No loop (play once)

    def _get_scale_filter(self, resolution: str) -> str:
        """Get scale filter for resolution.
        
        Requirements: 10.1
        
        Args:
            resolution: Target resolution string
            
        Returns:
            str: Scale filter value
        """
        return RESOLUTION_SCALE.get(resolution, "1920:1080")

    def _build_video_encoding(self, job: StreamJob) -> List[str]:
        """Build video encoding parameters.
        
        Requirements: 10.1, 10.2, 10.3, 10.4
        
        Args:
            job: StreamJob with encoding configuration
            
        Returns:
            List[str]: Video encoding arguments
        """
        args = []
        
        # Get encoder configuration
        encoder = self.encoder
        config = HARDWARE_ENCODER_CONFIG[encoder]
        
        # Video codec
        args.extend(["-c:v", config["codec"]])
        
        # Preset (if applicable)
        if config["preset"]:
            if encoder == HardwareEncoder.NVENC:
                args.extend(["-preset", config["preset"]])
            elif encoder == HardwareEncoder.QSV:
                args.extend(["-preset", config["preset"]])
            elif encoder == HardwareEncoder.AMF:
                args.extend(["-quality", config["preset"]])
            else:
                args.extend(["-preset", config["preset"]])
        
        # Profile and level for YouTube compatibility
        args.extend(["-profile:v", config["profile"]])
        args.extend(["-level:v", "4.1"])
        
        # Extra encoder-specific args
        args.extend(config["extra_args"])
        
        # Bitrate configuration (Requirements: 10.2, 10.3)
        bitrate_k = job.target_bitrate  # Already in kbps
        
        if encoder == HardwareEncoder.NVENC:
            # NVENC specific bitrate control
            if job.encoding_mode == EncodingMode.CBR.value:
                args.extend(["-b:v", f"{bitrate_k}k"])
                args.extend(["-maxrate", f"{bitrate_k}k"])
                args.extend(["-bufsize", f"{bitrate_k * 2}k"])
            else:
                args.extend(["-b:v", f"{bitrate_k}k"])
                args.extend(["-maxrate", f"{int(bitrate_k * 1.5)}k"])
                args.extend(["-bufsize", f"{bitrate_k * 2}k"])
        elif encoder == HardwareEncoder.QSV:
            # QSV specific bitrate control
            args.extend(["-b:v", f"{bitrate_k}k"])
            args.extend(["-maxrate", f"{bitrate_k}k"])
            args.extend(["-bufsize", f"{bitrate_k * 2}k"])
        elif encoder == HardwareEncoder.AMF:
            # AMF specific bitrate control
            args.extend(["-b:v", f"{bitrate_k}k"])
            args.extend(["-maxrate", f"{bitrate_k}k"])
            args.extend(["-bufsize", f"{bitrate_k * 2}k"])
        else:
            # Software encoding (libx264)
            if job.encoding_mode == EncodingMode.CBR.value:
                args.extend(["-b:v", f"{bitrate_k}k"])
                args.extend(["-minrate", f"{bitrate_k}k"])
                args.extend(["-maxrate", f"{bitrate_k}k"])
                args.extend(["-bufsize", f"{bitrate_k * 2}k"])
            else:
                args.extend(["-b:v", f"{bitrate_k}k"])
                args.extend(["-maxrate", f"{int(bitrate_k * 1.5)}k"])
                args.extend(["-bufsize", f"{bitrate_k * 2}k"])
        
        # Resolution scaling (Requirements: 10.1)
        scale = self._get_scale_filter(job.resolution)
        
        # Use appropriate scale filter for hardware encoders
        if encoder == HardwareEncoder.NVENC:
            # NVENC can use scale_cuda if available, fallback to scale
            args.extend(["-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale.replace(':', ':')}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"])
        elif encoder == HardwareEncoder.QSV:
            # QSV uses vpp_qsv for scaling, but scale works too
            args.extend(["-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale.replace(':', ':')}:(ow-iw)/2:(oh-ih)/2,format=nv12"])
        else:
            args.extend(["-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale.replace(':', ':')}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"])
        
        # Frame rate (Requirements: 10.4)
        args.extend(["-r", str(job.target_fps)])
        
        # Keyframe interval - every 2 seconds for streaming
        gop_size = job.target_fps * 2
        args.extend(["-g", str(gop_size)])
        
        # Software encoding specific options
        if encoder == HardwareEncoder.SOFTWARE:
            args.extend(["-keyint_min", str(gop_size)])
            args.extend(["-bf", "2"])  # B-frames
        
        # Pixel format (hardware encoders may need different format)
        if encoder not in [HardwareEncoder.QSV]:
            args.extend(["-pix_fmt", "yuv420p"])
        
        return args

    def _build_audio_encoding(self) -> List[str]:
        """Build audio encoding parameters.
        
        Returns:
            List[str]: Audio encoding arguments
        """
        return [
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
        ]

    def _build_output(self, job: StreamJob) -> List[str]:
        """Build output parameters.
        
        Args:
            job: StreamJob with RTMP configuration
            
        Returns:
            List[str]: Output arguments
        """
        # Get stream key (decrypted)
        stream_key = job.stream_key
        rtmp_url = job.rtmp_url.rstrip("/")
        
        return [
            "-f", "flv",
            f"{rtmp_url}/{stream_key}",
        ]

    def build_command_string(self, job: StreamJob) -> str:
        """Build FFmpeg command as a single string (for logging).
        
        Args:
            job: StreamJob with configuration
            
        Returns:
            str: FFmpeg command string (with masked stream key)
        """
        cmd = self.build_streaming_command(job)
        
        # Mask stream key in output
        cmd_str = " ".join(cmd)
        if job.stream_key:
            masked_key = job.get_masked_stream_key() or "****"
            cmd_str = cmd_str.replace(job.stream_key, masked_key)
        
        # Add encoder info
        encoder_info = self.get_encoder_info()
        encoder_note = f"[Encoder: {encoder_info['encoder']}]"
        
        return f"{encoder_note} {cmd_str}"


# ============================================
# FFmpeg Output Parser
# ============================================


class FFmpegOutputParser:
    """Parse FFmpeg stderr output for metrics extraction.
    
    Extracts real-time metrics from FFmpeg progress output lines.
    
    Requirements: 3.4, 3.5
    """

    # Pattern for FFmpeg progress line
    # Example: frame= 1234 fps= 30 q=28.0 size= 12345kB time=00:01:23.45 bitrate=1234.5kbits/s speed=1.00x
    PROGRESS_PATTERN = re.compile(
        r"frame=\s*(\d+)\s+"
        r"fps=\s*([\d.]+)\s+"
        r"(?:q=\s*([\d.-]+)\s+)?"
        r"(?:L?size=\s*(\d+)kB\s+)?"
        r"time=\s*([\d:.]+)\s+"
        r"bitrate=\s*([\d.]+)kbits/s\s+"
        r"(?:dup=\s*\d+\s+)?"
        r"(?:drop=\s*\d+\s+)?"
        r"speed=\s*([\d.]+)x"
    )

    # Alternative pattern for simpler output
    SIMPLE_PATTERN = re.compile(
        r"frame=\s*(\d+).*?"
        r"fps=\s*([\d.]+).*?"
        r"bitrate=\s*([\d.]+)kbits/s.*?"
        r"speed=\s*([\d.]+)x"
    )

    # Pattern to detect video completion (time resets)
    TIME_PATTERN = re.compile(r"time=\s*([\d:.]+)")

    # Pattern to detect errors
    ERROR_PATTERNS = [
        re.compile(r"Connection refused", re.IGNORECASE),
        re.compile(r"Connection timed out", re.IGNORECASE),
        re.compile(r"Connection reset", re.IGNORECASE),
        re.compile(r"Invalid data", re.IGNORECASE),
        re.compile(r"No such file", re.IGNORECASE),
        re.compile(r"Error", re.IGNORECASE),
        re.compile(r"Failed", re.IGNORECASE),
    ]

    def parse_line(self, line: str) -> Optional[FFmpegMetrics]:
        """Parse a single line of FFmpeg output.
        
        Requirements: 3.4, 3.5
        
        Args:
            line: FFmpeg stderr line
            
        Returns:
            Optional[FFmpegMetrics]: Parsed metrics or None
        """
        # Try full pattern first
        match = self.PROGRESS_PATTERN.search(line)
        if match:
            return FFmpegMetrics(
                frame_count=int(match.group(1)),
                fps=float(match.group(2)),
                quality=float(match.group(3)) if match.group(3) else None,
                size_kb=int(match.group(4)) if match.group(4) else None,
                time=match.group(5),
                bitrate=int(float(match.group(6)) * 1000),  # Convert kbits/s to bps
                speed=f"{match.group(7)}x",
            )
        
        # Try simple pattern
        match = self.SIMPLE_PATTERN.search(line)
        if match:
            return FFmpegMetrics(
                frame_count=int(match.group(1)),
                fps=float(match.group(2)),
                bitrate=int(float(match.group(3)) * 1000),  # Convert kbits/s to bps
                speed=f"{match.group(4)}x",
            )
        
        return None

    def parse_time(self, line: str) -> Optional[str]:
        """Extract time from FFmpeg output line.
        
        Args:
            line: FFmpeg stderr line
            
        Returns:
            Optional[str]: Time string or None
        """
        match = self.TIME_PATTERN.search(line)
        if match:
            return match.group(1)
        return None

    def time_to_seconds(self, time_str: str) -> float:
        """Convert FFmpeg time string to seconds.
        
        Args:
            time_str: Time string (e.g., "00:01:23.45")
            
        Returns:
            float: Time in seconds
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, IndexError):
            return 0.0

    def detect_loop_completion(
        self,
        current_time: str,
        previous_time: str,
        video_duration: float,
    ) -> bool:
        """Detect if video has looped (time reset).
        
        Requirements: 2.4
        
        Args:
            current_time: Current time string
            previous_time: Previous time string
            video_duration: Video duration in seconds
            
        Returns:
            bool: True if loop detected
        """
        current_seconds = self.time_to_seconds(current_time)
        previous_seconds = self.time_to_seconds(previous_time)
        
        # Loop detected if time resets (current < previous significantly)
        # Allow for small variations due to timing
        if previous_seconds > 10 and current_seconds < previous_seconds - 5:
            return True
        
        # Also detect if we've reached near the end of video
        if video_duration > 0 and previous_seconds >= video_duration - 1:
            if current_seconds < video_duration / 2:
                return True
        
        return False

    def detect_error(self, line: str) -> Optional[str]:
        """Detect error in FFmpeg output.
        
        Args:
            line: FFmpeg stderr line
            
        Returns:
            Optional[str]: Error type or None
        """
        for pattern in self.ERROR_PATTERNS:
            if pattern.search(line):
                return pattern.pattern
        return None

    def is_connection_error(self, line: str) -> bool:
        """Check if line indicates a connection error.
        
        Args:
            line: FFmpeg stderr line
            
        Returns:
            bool: True if connection error
        """
        connection_patterns = [
            "Connection refused",
            "Connection timed out",
            "Connection reset",
            "Network is unreachable",
        ]
        line_lower = line.lower()
        return any(p.lower() in line_lower for p in connection_patterns)

    def is_input_error(self, line: str) -> bool:
        """Check if line indicates an input file error.
        
        Args:
            line: FFmpeg stderr line
            
        Returns:
            bool: True if input error
        """
        input_patterns = [
            "No such file",
            "Invalid data",
            "does not exist",
            "Permission denied",
        ]
        line_lower = line.lower()
        return any(p.lower() in line_lower for p in input_patterns)


# ============================================
# Utility Functions
# ============================================


def get_resolution_dimensions(resolution: str) -> tuple[int, int]:
    """Get width and height for resolution string.
    
    Args:
        resolution: Resolution string (e.g., "1080p")
        
    Returns:
        tuple[int, int]: (width, height)
    """
    try:
        res = Resolution(resolution)
        return RESOLUTION_DIMENSIONS.get(res, (1920, 1080))
    except ValueError:
        # Try direct lookup
        scale = RESOLUTION_SCALE.get(resolution, "1920:1080")
        parts = scale.split(":")
        return (int(parts[0]), int(parts[1]))


# ============================================
# Playlist Concat File Builder
# ============================================


class PlaylistConcatBuilder:
    """Build FFmpeg concat demuxer file for playlist streaming.
    
    Creates a concat file that FFmpeg can use to seamlessly stream
    multiple videos in sequence.
    
    Requirements: 11.1, 11.2, 11.3
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize concat builder.
        
        Args:
            temp_dir: Directory for temporary concat files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def build_concat_file(
        self,
        video_paths: List[str],
        job_id: str,
        loop: bool = False,
    ) -> str:
        """Build concat demuxer file for playlist.
        
        Requirements: 11.1, 11.2
        
        Args:
            video_paths: List of video file paths in order
            job_id: Stream job ID for unique filename
            loop: Whether to loop the playlist
            
        Returns:
            str: Path to concat file
        """
        concat_path = os.path.join(self.temp_dir, f"concat_{job_id}.txt")
        
        with open(concat_path, "w") as f:
            for path in video_paths:
                # Escape single quotes in path
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        return concat_path

    def build_looping_concat_file(
        self,
        video_paths: List[str],
        job_id: str,
        loop_count: int = 1,
    ) -> str:
        """Build concat file with looping support.
        
        Requirements: 11.3
        
        Args:
            video_paths: List of video file paths
            job_id: Stream job ID
            loop_count: Number of times to loop (0 = infinite approximation)
            
        Returns:
            str: Path to concat file
        """
        concat_path = os.path.join(self.temp_dir, f"concat_{job_id}.txt")
        
        # For infinite loop, we'll repeat the playlist many times
        # FFmpeg will handle the actual looping via -stream_loop
        repeat_count = loop_count if loop_count > 0 else 1
        
        with open(concat_path, "w") as f:
            for _ in range(repeat_count):
                for path in video_paths:
                    escaped_path = path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
        
        return concat_path

    def cleanup_concat_file(self, job_id: str) -> bool:
        """Remove concat file for a job.
        
        Args:
            job_id: Stream job ID
            
        Returns:
            bool: True if file was removed
        """
        concat_path = os.path.join(self.temp_dir, f"concat_{job_id}.txt")
        try:
            if os.path.exists(concat_path):
                os.remove(concat_path)
                return True
        except OSError:
            pass
        return False


class FFmpegPlaylistCommandBuilder(FFmpegCommandBuilder):
    """Extended FFmpeg command builder for playlist streaming.
    
    Builds FFmpeg commands using concat demuxer for seamless
    multi-video streaming.
    
    Requirements: 11.1, 11.2, 11.3
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """Initialize playlist command builder.
        
        Args:
            ffmpeg_path: Path to FFmpeg binary
        """
        super().__init__(ffmpeg_path)
        self.concat_builder = PlaylistConcatBuilder()

    def build_playlist_command(
        self,
        job: StreamJob,
        video_paths: List[str],
    ) -> tuple[List[str], str]:
        """Build FFmpeg command for playlist streaming.
        
        Requirements: 11.1, 11.2
        
        Args:
            job: StreamJob with configuration
            video_paths: List of video file paths in playlist order
            
        Returns:
            tuple[List[str], str]: (FFmpeg command, concat file path)
        """
        # Build concat file
        concat_path = self.concat_builder.build_concat_file(
            video_paths=video_paths,
            job_id=str(job.id),
            loop=job.loop_mode == LoopMode.INFINITE.value,
        )
        
        cmd = [self.ffmpeg_path]
        
        # Add loop configuration for the concat input
        loop_arg = self._get_loop_arg(job)
        cmd.extend(["-stream_loop", loop_arg])
        
        # Real-time mode
        cmd.append("-re")
        
        # Use concat demuxer
        cmd.extend(["-f", "concat"])
        cmd.extend(["-safe", "0"])  # Allow absolute paths
        cmd.extend(["-i", concat_path])
        
        # Video encoding
        cmd.extend(self._build_video_encoding(job))
        
        # Audio encoding
        cmd.extend(self._build_audio_encoding())
        
        # Output
        cmd.extend(self._build_output(job))
        
        return cmd, concat_path

    def cleanup(self, job_id: str) -> None:
        """Cleanup temporary files for a job.
        
        Args:
            job_id: Stream job ID
        """
        self.concat_builder.cleanup_concat_file(job_id)


def validate_ffmpeg_command(cmd: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate FFmpeg command has required parameters.
    
    Requirements: 3.1
    
    Args:
        cmd: FFmpeg command arguments
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    cmd_str = " ".join(cmd)
    
    # Check for video codec (any supported encoder)
    valid_video_codecs = ["libx264", "h264_nvenc", "h264_qsv", "h264_amf", "h264_videotoolbox"]
    has_video_codec = any(codec in cmd_str for codec in valid_video_codecs)
    if not has_video_codec:
        return False, f"Missing video codec. Expected one of: {valid_video_codecs}"
    
    # Required parameters (codec-agnostic)
    required_params = [
        ("-c:a", "aac"),      # Audio codec
        ("-b:a", "128k"),     # Audio bitrate
        ("-ar", "44100"),     # Sample rate
        ("-f", "flv"),        # Output format
    ]
    
    for param, value in required_params:
        if param not in cmd_str:
            return False, f"Missing required parameter: {param}"
        if value and value not in cmd_str:
            return False, f"Missing required value for {param}: {value}"
    
    return True, None
