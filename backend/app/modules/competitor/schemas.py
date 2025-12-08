"""Pydantic schemas for competitor module.

Defines request/response schemas for competitor tracking and analysis.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================
# Competitor Schemas
# ============================================

class CompetitorCreate(BaseModel):
    """Request schema for adding a competitor."""

    channel_id: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    notify_on_new_content: bool = True
    notify_on_milestone: bool = False


class CompetitorUpdate(BaseModel):
    """Request schema for updating a competitor."""

    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    notify_on_new_content: Optional[bool] = None
    notify_on_milestone: Optional[bool] = None
    is_active: Optional[bool] = None


class CompetitorResponse(BaseModel):
    """Response schema for competitor."""

    id: uuid.UUID
    user_id: uuid.UUID
    channel_id: str
    channel_title: str
    channel_description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    custom_url: Optional[str] = None
    country: Optional[str] = None

    # Current metrics
    subscriber_count: int
    video_count: int
    view_count: int

    # Configuration
    is_active: bool
    notify_on_new_content: bool
    notify_on_milestone: bool

    # User notes
    notes: Optional[str] = None
    tags: Optional[list[str]] = None

    # Sync status
    last_synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetitorListResponse(BaseModel):
    """Response schema for list of competitors."""

    competitors: list[CompetitorResponse]
    total: int


# ============================================
# Competitor Metrics Schemas
# ============================================

class CompetitorMetricResponse(BaseModel):
    """Response schema for competitor metric snapshot."""

    id: uuid.UUID
    competitor_id: uuid.UUID
    metric_date: date

    subscriber_count: int
    subscriber_change: int
    video_count: int
    video_change: int
    view_count: int
    view_change: int

    avg_views_per_video: float
    estimated_engagement_rate: float
    videos_published_count: int

    created_at: datetime

    class Config:
        from_attributes = True


class CompetitorMetricsRequest(BaseModel):
    """Request schema for fetching competitor metrics."""

    competitor_id: uuid.UUID
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class CompetitorTrendData(BaseModel):
    """Trend data for a competitor over time."""

    competitor_id: uuid.UUID
    channel_title: str
    dates: list[date]
    subscriber_counts: list[int]
    view_counts: list[int]
    video_counts: list[int]
    subscriber_changes: list[int]
    view_changes: list[int]


# ============================================
# Competitor Content Schemas
# ============================================

class CompetitorContentResponse(BaseModel):
    """Response schema for competitor content item."""

    id: uuid.UUID
    competitor_id: uuid.UUID
    video_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    content_type: str

    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int

    published_at: datetime
    tags: Optional[list[str]] = None
    category_id: Optional[str] = None

    notification_sent: bool
    discovered_at: datetime

    class Config:
        from_attributes = True


class CompetitorContentListResponse(BaseModel):
    """Response schema for list of competitor content."""

    content: list[CompetitorContentResponse]
    total: int


# ============================================
# Comparison Schemas
# ============================================

class ComparisonRequest(BaseModel):
    """Request schema for competitor comparison."""

    competitor_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=10)
    account_ids: Optional[list[uuid.UUID]] = None  # User's own accounts to compare
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class ComparisonChannelData(BaseModel):
    """Data for a single channel in comparison."""

    channel_id: str
    channel_title: str
    is_competitor: bool  # True if competitor, False if user's own account
    thumbnail_url: Optional[str] = None

    # Current metrics
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0

    # Period changes
    subscriber_change: int = 0
    view_change: int = 0
    videos_published: int = 0

    # Calculated metrics
    avg_views_per_video: float = 0.0
    growth_rate: float = 0.0  # Subscriber growth percentage

    # Variance from average
    subscriber_variance: float = 0.0
    view_variance: float = 0.0


class ComparisonResponse(BaseModel):
    """Response schema for competitor comparison."""

    channels: list[ComparisonChannelData]
    start_date: date
    end_date: date

    # Averages
    average_subscribers: float = 0.0
    average_views: float = 0.0
    average_growth_rate: float = 0.0


# ============================================
# AI Analysis Schemas
# ============================================

class AnalysisRequest(BaseModel):
    """Request schema for AI competitor analysis."""

    competitor_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=10)
    analysis_type: str = Field(..., pattern="^(comparison|trend|content|strategy)$")
    start_date: date
    end_date: date
    include_recommendations: bool = True

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class AnalysisInsight(BaseModel):
    """Single insight from AI analysis."""

    category: str  # growth, content, engagement, strategy
    title: str
    description: str
    importance: str = "medium"  # low, medium, high
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    metric_change: Optional[float] = None


class AnalysisRecommendation(BaseModel):
    """Single recommendation from AI analysis."""

    category: str  # content, timing, engagement, growth
    title: str
    description: str
    action_items: list[str]
    priority: str = "medium"  # low, medium, high
    estimated_impact: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0


class AnalysisResponse(BaseModel):
    """Response schema for AI competitor analysis."""

    id: uuid.UUID
    user_id: uuid.UUID
    competitor_ids: list[str]
    analysis_type: str
    start_date: date
    end_date: date

    summary: str
    insights: list[AnalysisInsight]
    recommendations: list[AnalysisRecommendation]
    trend_data: Optional[dict] = None

    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Export Schemas
# ============================================

class ExportRequest(BaseModel):
    """Request schema for exporting competitor analysis."""

    competitor_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=10)
    start_date: date
    end_date: date
    export_format: str = Field(..., pattern="^(pdf|csv|json)$")
    include_trend_data: bool = True
    include_insights: bool = True

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class ExportResponse(BaseModel):
    """Response schema for export request."""

    analysis_id: uuid.UUID
    export_format: str
    file_path: Optional[str] = None
    status: str  # pending, generating, completed, failed
    created_at: datetime


# ============================================
# Notification Schemas
# ============================================

class ContentNotification(BaseModel):
    """Notification for new competitor content."""

    competitor_id: uuid.UUID
    competitor_name: str
    content_id: uuid.UUID
    video_id: str
    title: str
    thumbnail_url: Optional[str] = None
    published_at: datetime
    content_type: str
