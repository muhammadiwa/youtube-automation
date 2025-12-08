"""Adaptive Bitrate (ABR) streaming configuration and utilities.

Requirements: 10.3 - Support adaptive bitrate (ABR) for varying network conditions.
Requirements: 10.4 - Optimize encoding settings for minimal delay (low latency mode).
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from app.modules.transcoding.models import Resolution, LatencyMode, RESOLUTION_DIMENSIONS


class ABRProfile(str, Enum):
    """Predefined ABR profiles for different use cases."""
    STANDARD = "standard"  # Normal streaming
    LOW_LATENCY = "low_latency"  # Low latency streaming
    ULTRA_LOW_LATENCY = "ultra_low_latency"  # Ultra low latency
    HIGH_QUALITY = "high_quality"  # Maximum quality


@dataclass
class ABRVariant:
    """A single variant in an ABR ladder."""
    resolution: Resolution
    bitrate: int  # bps
    max_bitrate: int  # bps
    buffer_size: int  # bps
    profile: str = "main"
    level: str = "4.0"


@dataclass
class ABRLadder:
    """Complete ABR ladder configuration.
    
    Requirements: 10.3 - Support adaptive bitrate (ABR).
    """
    variants: list[ABRVariant] = field(default_factory=list)
    segment_duration: int = 4  # seconds
    keyframe_interval: int = 2  # seconds
    
    @classmethod
    def create_standard_ladder(cls) -> "ABRLadder":
        """Create standard ABR ladder for VOD/streaming."""
        return cls(
            variants=[
                ABRVariant(
                    resolution=Resolution.RES_720P,
                    bitrate=2500000,
                    max_bitrate=3000000,
                    buffer_size=5000000,
                    profile="main",
                    level="3.1",
                ),
                ABRVariant(
                    resolution=Resolution.RES_1080P,
                    bitrate=5000000,
                    max_bitrate=6000000,
                    buffer_size=10000000,
                    profile="high",
                    level="4.0",
                ),
                ABRVariant(
                    resolution=Resolution.RES_2K,
                    bitrate=10000000,
                    max_bitrate=12000000,
                    buffer_size=20000000,
                    profile="high",
                    level="4.1",
                ),
                ABRVariant(
                    resolution=Resolution.RES_4K,
                    bitrate=20000000,
                    max_bitrate=25000000,
                    buffer_size=40000000,
                    profile="high",
                    level="5.1",
                ),
            ],
            segment_duration=4,
            keyframe_interval=2,
        )
    
    @classmethod
    def create_low_latency_ladder(cls) -> "ABRLadder":
        """Create low latency ABR ladder.
        
        Requirements: 10.4 - Optimize for low latency mode.
        """
        return cls(
            variants=[
                ABRVariant(
                    resolution=Resolution.RES_720P,
                    bitrate=2000000,
                    max_bitrate=2500000,
                    buffer_size=2000000,
                    profile="main",
                    level="3.1",
                ),
                ABRVariant(
                    resolution=Resolution.RES_1080P,
                    bitrate=4000000,
                    max_bitrate=5000000,
                    buffer_size=4000000,
                    profile="high",
                    level="4.0",
                ),
            ],
            segment_duration=2,  # Shorter segments for lower latency
            keyframe_interval=1,  # More frequent keyframes
        )


@dataclass
class LowLatencySettings:
    """Settings optimized for low latency streaming.
    
    Requirements: 10.4 - Optimize encoding settings for minimal delay.
    """
    mode: LatencyMode
    preset: str
    tune: str
    keyframe_interval: int  # seconds
    buffer_size_ms: int
    lookahead: int  # frames
    b_frames: int
    
    @classmethod
    def for_mode(cls, mode: LatencyMode) -> "LowLatencySettings":
        """Get settings for a specific latency mode.
        
        Args:
            mode: Latency mode
            
        Returns:
            Optimized settings for the mode
        """
        if mode == LatencyMode.ULTRA_LOW:
            return cls(
                mode=mode,
                preset="ultrafast",
                tune="zerolatency",
                keyframe_interval=1,
                buffer_size_ms=500,
                lookahead=0,
                b_frames=0,
            )
        elif mode == LatencyMode.LOW:
            return cls(
                mode=mode,
                preset="fast",
                tune="zerolatency",
                keyframe_interval=2,
                buffer_size_ms=1000,
                lookahead=0,
                b_frames=0,
            )
        else:  # NORMAL
            return cls(
                mode=mode,
                preset="medium",
                tune="",
                keyframe_interval=2,
                buffer_size_ms=2000,
                lookahead=40,
                b_frames=3,
            )


def get_ffmpeg_args_for_latency(settings: LowLatencySettings) -> list[str]:
    """Get FFmpeg arguments for latency settings.
    
    Requirements: 10.4 - Optimize for low latency mode.
    
    Args:
        settings: Low latency settings
        
    Returns:
        List of FFmpeg arguments
    """
    args = [
        "-preset", settings.preset,
    ]
    
    if settings.tune:
        args.extend(["-tune", settings.tune])
    
    # Keyframe interval (in frames, assuming 30fps)
    gop_size = settings.keyframe_interval * 30
    args.extend(["-g", str(gop_size)])
    
    # B-frames
    args.extend(["-bf", str(settings.b_frames)])
    
    # Lookahead
    if settings.lookahead == 0:
        args.extend(["-rc-lookahead", "0"])
    
    return args


def get_ffmpeg_args_for_abr_variant(variant: ABRVariant) -> list[str]:
    """Get FFmpeg arguments for an ABR variant.
    
    Requirements: 10.3 - Support adaptive bitrate (ABR).
    
    Args:
        variant: ABR variant configuration
        
    Returns:
        List of FFmpeg arguments
    """
    width, height = RESOLUTION_DIMENSIONS[variant.resolution]
    
    return [
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-b:v", str(variant.bitrate),
        "-maxrate", str(variant.max_bitrate),
        "-bufsize", str(variant.buffer_size),
        "-profile:v", variant.profile,
        "-level", variant.level,
    ]


def calculate_optimal_bitrate(
    resolution: Resolution,
    frame_rate: float = 30.0,
    latency_mode: LatencyMode = LatencyMode.NORMAL,
) -> int:
    """Calculate optimal bitrate for given parameters.
    
    Args:
        resolution: Target resolution
        frame_rate: Target frame rate
        latency_mode: Latency mode
        
    Returns:
        Optimal bitrate in bps
    """
    # Base bitrates per resolution (at 30fps)
    base_bitrates = {
        Resolution.RES_720P: 3000000,
        Resolution.RES_1080P: 6000000,
        Resolution.RES_2K: 12000000,
        Resolution.RES_4K: 25000000,
    }
    
    base = base_bitrates.get(resolution, 6000000)
    
    # Adjust for frame rate
    if frame_rate > 30:
        base = int(base * (frame_rate / 30) * 0.8)  # Not linear scaling
    elif frame_rate < 30:
        base = int(base * (frame_rate / 30))
    
    # Adjust for latency mode
    latency_multipliers = {
        LatencyMode.NORMAL: 1.0,
        LatencyMode.LOW: 0.85,
        LatencyMode.ULTRA_LOW: 0.7,
    }
    
    multiplier = latency_multipliers.get(latency_mode, 1.0)
    
    return int(base * multiplier)


def validate_abr_config(ladder: ABRLadder) -> tuple[bool, list[str]]:
    """Validate ABR ladder configuration.
    
    Args:
        ladder: ABR ladder to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not ladder.variants:
        errors.append("ABR ladder must have at least one variant")
    
    if ladder.segment_duration < 1:
        errors.append("Segment duration must be at least 1 second")
    
    if ladder.keyframe_interval < 1:
        errors.append("Keyframe interval must be at least 1 second")
    
    # Check variants are ordered by bitrate
    prev_bitrate = 0
    for variant in ladder.variants:
        if variant.bitrate <= prev_bitrate:
            errors.append("Variants must be ordered by increasing bitrate")
            break
        prev_bitrate = variant.bitrate
        
        if variant.max_bitrate < variant.bitrate:
            errors.append(f"Max bitrate must be >= bitrate for {variant.resolution}")
    
    return len(errors) == 0, errors
