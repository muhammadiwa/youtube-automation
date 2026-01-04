"""Pydantic schemas for StreamJob API.

Requirements: 1.1, 1.5, 1.6, 1.7
"""

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.core.datetime_utils import ensure_utc
from app.modules.stream.stream_job_models import (
    StreamJobStatus,
    LoopMode,
    EncodingMode,
    Resolution,
)


# ============================================
# Base Schemas
# ============================================


class StreamJobBase(BaseModel):
    """Base schema for StreamJob."""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Loop configuration
    loop_mode: str = Field(default=LoopMode.NONE.value)
    loop_count: Optional[int] = Field(default=None, ge=1)
    
    # Output settings
    resolution: str = Field(default=Resolution.RES_1080P.value)
    target_bitrate: int = Field(default=6000, ge=1000, le=10000)
    encoding_mode: str = Field(default=EncodingMode.CBR.value)
    target_fps: int = Field(default=30)
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    
    # Auto-restart
    enable_auto_restart: bool = True
    max_restarts: int = Field(default=5, ge=0, le=10)

    @field_validator("loop_mode")
    @classmethod
    def validate_loop_mode(cls, v: str) -> str:
        valid_modes = [m.value for m in LoopMode]
        if v not in valid_modes:
            raise ValueError(f"loop_mode must be one of: {valid_modes}")
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        valid_resolutions = [r.value for r in Resolution]
        if v not in valid_resolutions:
            raise ValueError(f"resolution must be one of: {valid_resolutions}")
        return v

    @field_validator("encoding_mode")
    @classmethod
    def validate_encoding_mode(cls, v: str) -> str:
        valid_modes = [m.value for m in EncodingMode]
        if v not in valid_modes:
            raise ValueError(f"encoding_mode must be one of: {valid_modes}")
        return v

    @field_validator("target_fps")
    @classmethod
    def validate_target_fps(cls, v: int) -> int:
        valid_fps = [24, 30, 60]
        if v not in valid_fps:
            raise ValueError(f"target_fps must be one of: {valid_fps}")
        return v

    @field_validator("loop_count")
    @classmethod
    def validate_loop_count(cls, v: Optional[int], info) -> Optional[int]:
        # loop_count is required when loop_mode is "count"
        loop_mode = info.data.get("loop_mode")
        if loop_mode == LoopMode.COUNT.value and v is None:
            raise ValueError("loop_count is required when loop_mode is 'count'")
        return v


# ============================================
# Create/Update Schemas
# ============================================


class CreateStreamJobRequest(StreamJobBase):
    """Schema for creating a stream job."""
    
    account_id: uuid.UUID
    video_id: Optional[uuid.UUID] = None
    video_path: str = Field(..., min_length=1, max_length=1024)
    playlist_id: Optional[uuid.UUID] = None
    
    # RTMP settings
    rtmp_url: str = Field(default="rtmp://a.rtmp.youtube.com/live2", max_length=512)
    stream_key: str = Field(..., min_length=1)
    
    # YouTube Live Event settings (for chat moderation)
    youtube_broadcast_id: Optional[str] = Field(default=None, max_length=255)
    enable_chat_moderation: bool = Field(default=True)


class ScheduleItem(BaseModel):
    """Single schedule item for bulk create."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format (local time)")
    end_time: Optional[str] = Field(None, description="End time in HH:MM format (local time, optional)")


class BulkCreateStreamJobRequest(BaseModel):
    """Schema for bulk creating stream jobs with multiple schedules."""
    
    account_id: uuid.UUID
    video_id: Optional[uuid.UUID] = None
    video_path: str = Field(..., min_length=1, max_length=1024)
    
    # Stream settings
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # RTMP settings
    rtmp_url: str = Field(default="rtmp://a.rtmp.youtube.com/live2", max_length=512)
    stream_key: str = Field(..., min_length=1)
    
    # Loop configuration
    loop_mode: str = Field(default="infinite")
    loop_count: Optional[int] = Field(default=None, ge=1)
    
    # Output settings
    resolution: str = Field(default="1080p")
    target_bitrate: int = Field(default=6000, ge=1000, le=10000)
    encoding_mode: str = Field(default="cbr")
    target_fps: int = Field(default=30)
    
    # Auto-restart
    enable_auto_restart: bool = True
    max_restarts: int = Field(default=5, ge=0, le=10)
    
    # Chat moderation
    enable_chat_moderation: bool = Field(default=True)
    
    # Timezone offset in minutes from UTC (e.g., +420 for UTC+7/WIB)
    # Positive = ahead of UTC, Negative = behind UTC
    timezone_offset: int = Field(default=0, description="Timezone offset in minutes from UTC")
    
    # Schedules - list of date/time combinations
    schedules: List[ScheduleItem] = Field(..., min_length=1, max_length=30)


class BulkCreateStreamJobResponse(BaseModel):
    """Response for bulk create stream jobs."""
    total_requested: int
    total_created: int
    created_jobs: List[dict]
    errors: List[str]


class UpdateStreamJobRequest(BaseModel):
    """Schema for updating a stream job."""
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Loop configuration
    loop_mode: Optional[str] = None
    loop_count: Optional[int] = Field(default=None, ge=1)
    
    # Output settings (only updatable when not running)
    resolution: Optional[str] = None
    target_bitrate: Optional[int] = Field(default=None, ge=1000, le=10000)
    encoding_mode: Optional[str] = None
    target_fps: Optional[int] = None
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    
    # Auto-restart
    enable_auto_restart: Optional[bool] = None
    max_restarts: Optional[int] = Field(default=None, ge=0, le=10)

    @field_validator("loop_mode")
    @classmethod
    def validate_loop_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_modes = [m.value for m in LoopMode]
        if v not in valid_modes:
            raise ValueError(f"loop_mode must be one of: {valid_modes}")
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_resolutions = [r.value for r in Resolution]
        if v not in valid_resolutions:
            raise ValueError(f"resolution must be one of: {valid_resolutions}")
        return v

    @field_validator("encoding_mode")
    @classmethod
    def validate_encoding_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_modes = [m.value for m in EncodingMode]
        if v not in valid_modes:
            raise ValueError(f"encoding_mode must be one of: {valid_modes}")
        return v

    @field_validator("target_fps")
    @classmethod
    def validate_target_fps(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        valid_fps = [24, 30, 60]
        if v not in valid_fps:
            raise ValueError(f"target_fps must be one of: {valid_fps}")
        return v


# ============================================
# Response Schemas
# ============================================


class StreamJobResponse(BaseModel):
    """Schema for stream job response."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    video_id: Optional[uuid.UUID] = None
    video_path: str
    playlist_id: Optional[uuid.UUID] = None
    
    # RTMP settings (masked key)
    rtmp_url: str
    stream_key_masked: Optional[str] = None
    is_stream_key_locked: bool
    
    # YouTube Live Event settings
    youtube_broadcast_id: Optional[str] = None
    enable_chat_moderation: bool = True
    
    # Metadata
    title: str
    description: Optional[str] = None
    
    # Loop configuration
    loop_mode: str
    loop_count: Optional[int] = None
    current_loop: int
    
    # Output settings
    resolution: str
    target_bitrate: int
    encoding_mode: str
    target_fps: int
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    time_until_start: Optional[int] = None  # seconds
    
    # Process tracking
    pid: Optional[int] = None
    status: str
    
    # Timing
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    total_duration_seconds: int
    current_duration_seconds: int = 0
    
    # Error handling
    last_error: Optional[str] = None
    restart_count: int
    max_restarts: int
    enable_auto_restart: bool
    
    # Current metrics
    current_bitrate: Optional[int] = None
    current_bitrate_kbps: Optional[float] = None
    current_fps: Optional[float] = None
    current_speed: Optional[str] = None
    dropped_frames: int
    frame_count: int
    
    # Playlist tracking (Requirements: 11.5)
    current_playlist_index: int = 0
    total_playlist_items: int = 0
    playlist_progress: float = 0.0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, job) -> "StreamJobResponse":
        """Create response from StreamJob model.
        
        All datetime fields are converted to UTC-aware for proper frontend handling.
        """
        return cls(
            id=job.id,
            user_id=job.user_id,
            account_id=job.account_id,
            video_id=job.video_id,
            video_path=job.video_path,
            playlist_id=job.playlist_id,
            rtmp_url=job.rtmp_url,
            stream_key_masked=job.get_masked_stream_key(),
            is_stream_key_locked=job.is_stream_key_locked,
            youtube_broadcast_id=job.youtube_broadcast_id,
            enable_chat_moderation=job.enable_chat_moderation,
            title=job.title,
            description=job.description,
            loop_mode=job.loop_mode,
            loop_count=job.loop_count,
            current_loop=job.current_loop,
            resolution=job.resolution,
            target_bitrate=job.target_bitrate,
            encoding_mode=job.encoding_mode,
            target_fps=job.target_fps,
            # Use ensure_utc() for timezone-aware datetime (frontend interprets correctly)
            scheduled_start_at=ensure_utc(job.scheduled_start_at),
            scheduled_end_at=ensure_utc(job.scheduled_end_at),
            time_until_start=job.get_time_until_start(),
            pid=job.pid,
            status=job.status,
            actual_start_at=ensure_utc(job.actual_start_at),
            actual_end_at=ensure_utc(job.actual_end_at),
            total_duration_seconds=job.total_duration_seconds,
            current_duration_seconds=job.get_duration_seconds(),
            last_error=job.last_error,
            restart_count=job.restart_count,
            max_restarts=job.max_restarts,
            enable_auto_restart=job.enable_auto_restart,
            current_bitrate=job.current_bitrate,
            current_bitrate_kbps=job.current_bitrate / 1000 if job.current_bitrate else None,
            current_fps=job.current_fps,
            current_speed=job.current_speed,
            dropped_frames=job.dropped_frames,
            frame_count=job.frame_count,
            current_playlist_index=job.current_playlist_index,
            total_playlist_items=job.total_playlist_items,
            playlist_progress=job.get_playlist_progress(),
            created_at=ensure_utc(job.created_at),
            updated_at=ensure_utc(job.updated_at),
        )


class StreamJobListResponse(BaseModel):
    """Schema for paginated stream job list."""
    
    jobs: List[StreamJobResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Health Schemas
# ============================================


class StreamJobHealthResponse(BaseModel):
    """Schema for stream job health response."""
    
    id: uuid.UUID
    stream_job_id: uuid.UUID
    
    # FFmpeg metrics
    bitrate: int
    bitrate_kbps: float
    fps: Optional[float] = None
    speed: Optional[str] = None
    dropped_frames: int
    dropped_frames_delta: int
    frame_count: int
    
    # System resources
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    
    # Alert info
    alert_type: Optional[str] = None
    alert_message: Optional[str] = None
    is_alert_acknowledged: bool
    is_healthy: bool
    
    # Timestamp
    collected_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, health) -> "StreamJobHealthResponse":
        """Create response from StreamJobHealth model."""
        return cls(
            id=health.id,
            stream_job_id=health.stream_job_id,
            bitrate=health.bitrate,
            bitrate_kbps=health.get_bitrate_kbps(),
            fps=health.fps,
            speed=health.speed,
            dropped_frames=health.dropped_frames,
            dropped_frames_delta=health.dropped_frames_delta,
            frame_count=health.frame_count,
            cpu_percent=health.cpu_percent,
            memory_mb=health.memory_mb,
            alert_type=health.alert_type,
            alert_message=health.alert_message,
            is_alert_acknowledged=health.is_alert_acknowledged,
            is_healthy=health.is_healthy(),
            collected_at=health.collected_at,
        )


class StreamJobHealthListResponse(BaseModel):
    """Schema for paginated health history."""
    
    records: List[StreamJobHealthResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Slot/Resource Schemas
# ============================================


class SlotStatusResponse(BaseModel):
    """Schema for stream slot status."""
    
    used_slots: int
    total_slots: int
    available_slots: int
    plan: str


# ============================================
# Analytics & History Schemas (Requirements: 12.1, 12.2, 12.5)
# ============================================


class StreamJobStatistics(BaseModel):
    """Schema for stream job statistics on completion."""
    
    total_duration_seconds: int
    total_loops: int
    avg_bitrate_kbps: float
    avg_fps: float
    total_dropped_frames: int
    peak_cpu_percent: float
    peak_memory_mb: float


class StreamJobHistoryItem(BaseModel):
    """Schema for stream job history item."""
    
    id: uuid.UUID
    title: str
    status: str
    loop_mode: str
    resolution: str
    target_bitrate: int
    
    # Timing
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    total_duration_seconds: int
    
    # Statistics
    total_loops: int
    avg_bitrate_kbps: Optional[float] = None
    total_dropped_frames: int
    
    created_at: datetime


class StreamJobHistoryResponse(BaseModel):
    """Schema for paginated stream job history."""
    
    items: List[StreamJobHistoryItem]
    total: int
    page: int
    page_size: int


class StreamAnalyticsSummary(BaseModel):
    """Schema for stream analytics summary."""
    
    total_streams: int
    total_duration_hours: float
    total_loops_completed: int
    avg_stream_duration_minutes: float
    avg_bitrate_kbps: float
    total_data_transferred_gb: float
    
    # Trends (last 7 days)
    streams_by_day: List[dict]  # [{date, count}]
    duration_by_day: List[dict]  # [{date, hours}]


class ResourceUsageResponse(BaseModel):
    """Schema for resource usage."""
    
    total_cpu_percent: float
    total_memory_mb: float
    total_bandwidth_kbps: float
    active_streams: int
    estimated_remaining_slots: int
    is_warning: bool  # True if usage > 80%


class StreamResourceResponse(BaseModel):
    """Schema for per-stream resource usage."""
    
    stream_job_id: uuid.UUID
    title: str
    status: str
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    bitrate_kbps: Optional[float] = None


class ResourceDashboardResponse(BaseModel):
    """Schema for resource dashboard."""
    
    aggregate: ResourceUsageResponse
    streams: List[StreamResourceResponse]
