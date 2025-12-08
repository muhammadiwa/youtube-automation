"""Pydantic schemas for stream module.

Defines request/response schemas for live event management.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.stream.models import (
    LiveEventStatus,
    LatencyMode,
    ConnectionStatus,
    RecurrenceFrequency,
    TransitionType,
    PlaylistLoopMode,
    PlaylistItemStatus,
)


# Validation constants
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000
MAX_TAGS = 500


class CreateLiveEventRequest(BaseModel):
    """Request schema for creating a live event."""

    account_id: uuid.UUID = Field(..., description="YouTube account ID")
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    thumbnail_url: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    latency_mode: LatencyMode = LatencyMode.NORMAL
    enable_dvr: bool = True
    enable_auto_start: bool = False
    enable_auto_stop: bool = False
    privacy_status: str = Field("private", pattern="^(public|unlisted|private)$")
    made_for_kids: bool = False
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        cleaned = list(dict.fromkeys(tag.strip() for tag in v if tag.strip()))
        if len(cleaned) > MAX_TAGS:
            raise ValueError(f"Maximum {MAX_TAGS} tags allowed")
        return cleaned

    @field_validator("scheduled_end_at")
    @classmethod
    def validate_end_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v is None:
            return v
        start = info.data.get("scheduled_start_at")
        if start and v <= start:
            raise ValueError("End time must be after start time")
        return v


class ScheduleLiveEventRequest(BaseModel):
    """Request schema for scheduling a live event."""

    account_id: uuid.UUID = Field(..., description="YouTube account ID")
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    thumbnail_url: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    latency_mode: LatencyMode = LatencyMode.NORMAL
    enable_dvr: bool = True
    privacy_status: str = Field("private", pattern="^(public|unlisted|private)$")
    scheduled_start_at: datetime = Field(..., description="Scheduled start time")
    scheduled_end_at: Optional[datetime] = None

    @field_validator("scheduled_start_at")
    @classmethod
    def validate_future_start(cls, v: datetime) -> datetime:
        if v.replace(tzinfo=None) < datetime.utcnow():
            raise ValueError("Scheduled start time must be in the future")
        return v


class UpdateLiveEventRequest(BaseModel):
    """Request schema for updating a live event."""

    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    thumbnail_url: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    latency_mode: Optional[LatencyMode] = None
    enable_dvr: Optional[bool] = None
    privacy_status: Optional[str] = Field(None, pattern="^(public|unlisted|private)$")
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None


class RecurrencePatternRequest(BaseModel):
    """Request schema for recurrence pattern."""

    frequency: RecurrenceFrequency = RecurrenceFrequency.WEEKLY
    interval: int = Field(1, ge=1, le=52, description="Interval between occurrences")
    days_of_week: Optional[list[int]] = Field(
        None, description="Days of week (0=Monday, 6=Sunday)"
    )
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    duration_minutes: int = Field(60, ge=1, le=720, description="Duration in minutes")
    end_date: Optional[datetime] = None
    occurrence_count: Optional[int] = Field(None, ge=1, le=365)

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is None:
            return v
        for day in v:
            if day < 0 or day > 6:
                raise ValueError("Days of week must be between 0 (Monday) and 6 (Sunday)")
        return sorted(set(v))


class CreateRecurringEventRequest(BaseModel):
    """Request schema for creating a recurring live event."""

    account_id: uuid.UUID = Field(..., description="YouTube account ID")
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    thumbnail_url: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[list[str]] = Field(None, max_length=MAX_TAGS)
    latency_mode: LatencyMode = LatencyMode.NORMAL
    enable_dvr: bool = True
    privacy_status: str = Field("private", pattern="^(public|unlisted|private)$")
    first_occurrence_at: datetime = Field(..., description="First occurrence start time")
    recurrence: RecurrencePatternRequest


class LiveEventResponse(BaseModel):
    """Response schema for live event."""

    id: uuid.UUID
    account_id: uuid.UUID
    youtube_broadcast_id: Optional[str]
    youtube_stream_id: Optional[str]
    rtmp_url: Optional[str]
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    category_id: Optional[str]
    tags: Optional[list[str]]
    latency_mode: str
    enable_dvr: bool
    enable_auto_start: bool
    enable_auto_stop: bool
    privacy_status: str
    made_for_kids: bool
    scheduled_start_at: Optional[datetime]
    scheduled_end_at: Optional[datetime]
    actual_start_at: Optional[datetime]
    actual_end_at: Optional[datetime]
    is_recurring: bool
    parent_event_id: Optional[uuid.UUID]
    status: str
    last_error: Optional[str]
    peak_viewers: int
    total_chat_messages: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LiveEventWithRtmpResponse(LiveEventResponse):
    """Response schema for live event with RTMP key (for authorized users)."""

    rtmp_key: Optional[str] = None


class StreamSessionResponse(BaseModel):
    """Response schema for stream session."""

    id: uuid.UUID
    live_event_id: uuid.UUID
    agent_id: Optional[uuid.UUID]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    peak_viewers: int
    total_chat_messages: int
    average_bitrate: Optional[int]
    dropped_frames: int
    connection_status: str
    reconnection_attempts: int
    end_reason: Optional[str]
    last_error: Optional[str]
    duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecurrencePatternResponse(BaseModel):
    """Response schema for recurrence pattern."""

    id: uuid.UUID
    live_event_id: uuid.UUID
    frequency: str
    interval: int
    days_of_week: Optional[list[int]]
    day_of_month: Optional[int]
    duration_minutes: int
    end_date: Optional[datetime]
    occurrence_count: Optional[int]
    generated_count: int
    last_generated_at: Optional[datetime]
    next_occurrence_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StreamHealthResponse(BaseModel):
    """Response schema for stream health metrics."""

    session_id: uuid.UUID
    live_event_id: uuid.UUID
    bitrate: Optional[int]
    frame_rate: Optional[float]
    dropped_frames: int
    connection_status: str
    viewer_count: int
    chat_rate: float
    uptime_seconds: Optional[int]
    last_updated_at: datetime


class ScheduleConflictError(BaseModel):
    """Error response for schedule conflict."""

    message: str
    conflicting_event_id: uuid.UUID
    conflicting_event_title: str
    conflicting_start_at: Optional[datetime]
    conflicting_end_at: Optional[datetime]


class LiveEventListResponse(BaseModel):
    """Response schema for list of live events."""

    events: list[LiveEventResponse]
    total: int


class YouTubeBroadcastInfo(BaseModel):
    """YouTube broadcast information from API."""

    broadcast_id: str
    stream_id: str
    rtmp_key: str
    rtmp_url: str
    status: str


# ============================================
# Playlist Schemas (Requirements: 7.1, 7.2, 7.3, 7.4, 7.5)
# ============================================


class PlaylistItemCreate(BaseModel):
    """Request schema for creating a playlist item."""

    video_id: Optional[uuid.UUID] = None
    video_url: Optional[str] = None
    video_title: str = Field(..., min_length=1, max_length=255)
    video_duration_seconds: Optional[int] = Field(None, ge=0)
    position: int = Field(..., ge=0, description="Position in playlist (0-indexed)")
    transition_type: TransitionType = TransitionType.CUT
    transition_duration_ms: int = Field(500, ge=0, le=5000)
    start_offset_seconds: int = Field(0, ge=0)
    end_offset_seconds: Optional[int] = Field(None, ge=0)

    @field_validator("video_url")
    @classmethod
    def validate_video_source(cls, v: Optional[str], info) -> Optional[str]:
        video_id = info.data.get("video_id")
        if v is None and video_id is None:
            raise ValueError("Either video_id or video_url must be provided")
        return v


class PlaylistItemUpdate(BaseModel):
    """Request schema for updating a playlist item."""

    video_title: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[int] = Field(None, ge=0)
    transition_type: Optional[TransitionType] = None
    transition_duration_ms: Optional[int] = Field(None, ge=0, le=5000)
    start_offset_seconds: Optional[int] = Field(None, ge=0)
    end_offset_seconds: Optional[int] = Field(None, ge=0)


class PlaylistItemResponse(BaseModel):
    """Response schema for playlist item."""

    id: uuid.UUID
    playlist_id: uuid.UUID
    video_id: Optional[uuid.UUID]
    video_url: Optional[str]
    video_title: str
    video_duration_seconds: Optional[int]
    position: int
    transition_type: str
    transition_duration_ms: int
    start_offset_seconds: int
    end_offset_seconds: Optional[int]
    status: str
    play_count: int
    last_played_at: Optional[datetime]
    last_error: Optional[str]
    effective_duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreatePlaylistRequest(BaseModel):
    """Request schema for creating a stream playlist."""

    live_event_id: uuid.UUID = Field(..., description="Live event to attach playlist to")
    name: str = Field("Default Playlist", min_length=1, max_length=255)
    loop_mode: PlaylistLoopMode = PlaylistLoopMode.NONE
    loop_count: Optional[int] = Field(None, ge=1, le=1000, description="Number of loops (for COUNT mode)")
    default_transition: TransitionType = TransitionType.CUT
    default_transition_duration_ms: int = Field(500, ge=0, le=5000)
    items: list[PlaylistItemCreate] = Field(default_factory=list, description="Initial playlist items")

    @field_validator("loop_count")
    @classmethod
    def validate_loop_count(cls, v: Optional[int], info) -> Optional[int]:
        loop_mode = info.data.get("loop_mode")
        if loop_mode == PlaylistLoopMode.COUNT and v is None:
            raise ValueError("loop_count is required when loop_mode is COUNT")
        return v


class UpdatePlaylistRequest(BaseModel):
    """Request schema for updating a stream playlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    loop_mode: Optional[PlaylistLoopMode] = None
    loop_count: Optional[int] = Field(None, ge=1, le=1000)
    default_transition: Optional[TransitionType] = None
    default_transition_duration_ms: Optional[int] = Field(None, ge=0, le=5000)


class PlaylistResponse(BaseModel):
    """Response schema for stream playlist."""

    id: uuid.UUID
    live_event_id: uuid.UUID
    name: str
    loop_mode: str
    loop_count: Optional[int]
    current_loop: int
    default_transition: str
    default_transition_duration_ms: int
    current_item_index: int
    is_active: bool
    total_plays: int
    total_skips: int
    total_failures: int
    total_items: int = 0
    items: list[PlaylistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistWithItemsResponse(PlaylistResponse):
    """Response schema for playlist with all items."""

    items: list[PlaylistItemResponse] = []


class ReorderPlaylistRequest(BaseModel):
    """Request schema for reordering playlist items."""

    item_ids: list[uuid.UUID] = Field(..., description="Item IDs in new order")


class PlaylistStreamStatus(BaseModel):
    """Status of playlist streaming."""

    playlist_id: uuid.UUID
    is_active: bool
    current_item_index: int
    current_item: Optional[PlaylistItemResponse]
    next_item: Optional[PlaylistItemResponse]
    current_loop: int
    total_loops: Optional[int]
    loop_mode: str
    total_items: int
    completed_items: int
    skipped_items: int
    failed_items: int


class PlaylistLoopResult(BaseModel):
    """Result of playlist loop behavior calculation.
    
    Used for property testing of loop behavior (Property 12).
    """

    should_loop: bool
    current_loop: int
    loop_count: Optional[int]
    loop_mode: str
    total_plays_expected: int  # Expected total plays based on loop config
