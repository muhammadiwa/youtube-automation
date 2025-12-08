"""Pydantic schemas for transcoding service.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.transcoding.models import (
    Resolution,
    TranscodeStatus,
    LatencyMode,
    RESOLUTION_DIMENSIONS,
)


class TranscodeJobCreate(BaseModel):
    """Schema for creating a transcoding job."""
    source_file_path: str = Field(..., description="Path to source video file")
    target_resolution: Resolution = Field(..., description="Target output resolution")
    target_bitrate: Optional[int] = Field(None, description="Target bitrate in bps")
    latency_mode: LatencyMode = Field(default=LatencyMode.NORMAL, description="Latency optimization mode")
    enable_abr: bool = Field(default=False, description="Enable adaptive bitrate")
    account_id: Optional[UUID] = None
    video_id: Optional[UUID] = None
    live_event_id: Optional[UUID] = None


class TranscodeJobResponse(BaseModel):
    """Schema for transcoding job response."""
    id: UUID
    source_file_path: str
    target_resolution: Resolution
    target_bitrate: Optional[int]
    latency_mode: LatencyMode
    enable_abr: bool
    status: TranscodeStatus
    progress: float
    output_file_path: Optional[str]
    output_width: Optional[int]
    output_height: Optional[int]
    cdn_url: Optional[str]
    error_message: Optional[str]
    assigned_worker_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TranscodeProgress(BaseModel):
    """Schema for transcoding progress update."""
    job_id: UUID
    progress: float = Field(..., ge=0, le=100)
    status: TranscodeStatus
    current_frame: Optional[int] = None
    total_frames: Optional[int] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None


class TranscodeResult(BaseModel):
    """Schema for transcoding result."""
    job_id: UUID
    success: bool
    output_file_path: Optional[str] = None
    output_width: Optional[int] = None
    output_height: Optional[int] = None
    output_file_size: Optional[int] = None
    cdn_url: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


class WorkerRegistration(BaseModel):
    """Schema for worker registration."""
    hostname: str
    ip_address: Optional[str] = None
    max_concurrent_jobs: int = Field(default=2, ge=1, le=10)
    supports_4k: bool = True
    supports_hardware_encoding: bool = False
    gpu_type: Optional[str] = None


class WorkerHeartbeat(BaseModel):
    """Schema for worker heartbeat."""
    hostname: str
    current_jobs: int
    current_load: float = Field(..., ge=0, le=100)


class WorkerStatus(BaseModel):
    """Schema for worker status response."""
    id: UUID
    hostname: str
    ip_address: Optional[str]
    max_concurrent_jobs: int
    current_jobs: int
    current_load: float
    is_healthy: bool
    last_heartbeat: datetime
    supports_4k: bool
    supports_hardware_encoding: bool

    class Config:
        from_attributes = True


class WorkerSelection(BaseModel):
    """Schema for worker selection result."""
    worker_id: UUID
    hostname: str
    current_load: float
    reason: str


class ABRConfig(BaseModel):
    """Configuration for Adaptive Bitrate streaming.
    
    Requirements: 10.3 - Support adaptive bitrate (ABR).
    """
    resolutions: list[Resolution] = Field(
        default=[Resolution.RES_720P, Resolution.RES_1080P],
        description="Resolutions to generate for ABR"
    )
    bitrates: list[int] = Field(
        default=[2000000, 4000000],  # 2 Mbps, 4 Mbps
        description="Bitrates for each resolution"
    )
    segment_duration: int = Field(default=4, description="HLS segment duration in seconds")
    playlist_type: str = Field(default="vod", description="HLS playlist type (vod or event)")


class LowLatencyConfig(BaseModel):
    """Configuration for low latency streaming.
    
    Requirements: 10.4 - Optimize for low latency mode.
    """
    mode: LatencyMode
    keyframe_interval: int = Field(default=2, description="Keyframe interval in seconds")
    buffer_size: int = Field(default=1000, description="Buffer size in ms")
    preset: str = Field(default="ultrafast", description="FFmpeg encoding preset")
    tune: str = Field(default="zerolatency", description="FFmpeg tune option")


class CDNUploadResult(BaseModel):
    """Result of CDN upload operation.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    """
    success: bool
    bucket: str
    key: str
    cdn_url: str
    file_size: int
    etag: Optional[str] = None
    error_message: Optional[str] = None


def get_resolution_dimensions(resolution: Resolution) -> tuple[int, int]:
    """Get width and height for a resolution.
    
    Args:
        resolution: Target resolution
        
    Returns:
        Tuple of (width, height)
    """
    return RESOLUTION_DIMENSIONS[resolution]


def get_recommended_bitrate(resolution: Resolution, latency_mode: LatencyMode = LatencyMode.NORMAL) -> int:
    """Get recommended bitrate for a resolution.
    
    Args:
        resolution: Target resolution
        latency_mode: Latency mode
        
    Returns:
        Recommended bitrate in bps
    """
    base_bitrates = {
        Resolution.RES_720P: 3000000,   # 3 Mbps
        Resolution.RES_1080P: 6000000,  # 6 Mbps
        Resolution.RES_2K: 12000000,    # 12 Mbps
        Resolution.RES_4K: 25000000,    # 25 Mbps
    }
    
    bitrate = base_bitrates.get(resolution, 6000000)
    
    # Reduce bitrate for low latency modes
    if latency_mode == LatencyMode.LOW:
        bitrate = int(bitrate * 0.8)
    elif latency_mode == LatencyMode.ULTRA_LOW:
        bitrate = int(bitrate * 0.6)
    
    return bitrate
