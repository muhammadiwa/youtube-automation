"""Pydantic schemas for analytics module.

Defines request/response schemas for analytics and reporting.
Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DateRangeRequest(BaseModel):
    """Request schema for date range queries."""

    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class AnalyticsSnapshotResponse(BaseModel):
    """Response schema for analytics snapshot."""

    id: uuid.UUID
    account_id: uuid.UUID
    snapshot_date: date

    # Channel metrics
    subscriber_count: int
    subscriber_change: int
    total_views: int
    views_change: int
    total_videos: int

    # Engagement metrics
    total_likes: int
    total_comments: int
    total_shares: int
    average_view_duration: float
    engagement_rate: float

    # Watch time metrics
    watch_time_minutes: int
    average_view_percentage: float

    # Revenue metrics
    estimated_revenue: float
    ad_revenue: float
    membership_revenue: float
    super_chat_revenue: float
    merchandise_revenue: float

    # JSON fields
    traffic_sources: Optional[dict] = None
    demographics: Optional[dict] = None
    top_videos: Optional[dict] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSnapshotCreate(BaseModel):
    """Request schema for creating analytics snapshot."""

    account_id: uuid.UUID
    snapshot_date: date

    # Channel metrics
    subscriber_count: int = 0
    subscriber_change: int = 0
    total_views: int = 0
    views_change: int = 0
    total_videos: int = 0

    # Engagement metrics
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    average_view_duration: float = 0.0
    engagement_rate: float = 0.0

    # Watch time metrics
    watch_time_minutes: int = 0
    average_view_percentage: float = 0.0

    # Revenue metrics
    estimated_revenue: float = 0.0
    ad_revenue: float = 0.0
    membership_revenue: float = 0.0
    super_chat_revenue: float = 0.0
    merchandise_revenue: float = 0.0

    # JSON fields
    traffic_sources: Optional[dict] = None
    demographics: Optional[dict] = None
    top_videos: Optional[dict] = None


class DashboardMetrics(BaseModel):
    """Aggregated dashboard metrics across all accounts."""

    # Totals
    total_subscribers: int = 0
    total_views: int = 0
    total_videos: int = 0
    total_revenue: float = 0.0

    # Changes from previous period
    subscriber_change: int = 0
    subscriber_change_percent: float = 0.0
    views_change: int = 0
    views_change_percent: float = 0.0
    revenue_change: float = 0.0
    revenue_change_percent: float = 0.0

    # Engagement
    total_likes: int = 0
    total_comments: int = 0
    average_engagement_rate: float = 0.0

    # Watch time
    total_watch_time_minutes: int = 0

    # Period info
    start_date: date
    end_date: date
    comparison_start_date: Optional[date] = None
    comparison_end_date: Optional[date] = None


class AccountMetrics(BaseModel):
    """Metrics for a single account."""

    account_id: uuid.UUID
    channel_title: Optional[str] = None

    # Current metrics
    subscriber_count: int = 0
    total_views: int = 0
    total_videos: int = 0
    estimated_revenue: float = 0.0

    # Changes
    subscriber_change: int = 0
    views_change: int = 0
    revenue_change: float = 0.0

    # Engagement
    engagement_rate: float = 0.0
    watch_time_minutes: int = 0


class ChannelComparisonRequest(BaseModel):
    """Request schema for channel comparison."""

    account_ids: list[uuid.UUID] = Field(..., min_length=2, max_length=10)
    start_date: date
    end_date: date


class ChannelComparisonItem(BaseModel):
    """Single channel in comparison."""

    account_id: uuid.UUID
    channel_title: Optional[str] = None

    # Metrics
    subscriber_count: int = 0
    subscriber_change: int = 0
    total_views: int = 0
    views_change: int = 0
    estimated_revenue: float = 0.0
    engagement_rate: float = 0.0
    watch_time_minutes: int = 0

    # Variance from average (percentage)
    subscriber_variance: float = 0.0
    views_variance: float = 0.0
    revenue_variance: float = 0.0
    engagement_variance: float = 0.0


class ChannelComparisonResponse(BaseModel):
    """Response schema for channel comparison."""

    channels: list[ChannelComparisonItem]
    start_date: date
    end_date: date

    # Averages for variance calculation
    average_subscribers: float = 0.0
    average_views: float = 0.0
    average_revenue: float = 0.0
    average_engagement: float = 0.0


class ReportGenerationRequest(BaseModel):
    """Request schema for generating analytics report."""

    title: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., pattern="^(pdf|csv)$")
    start_date: date
    end_date: date
    account_ids: Optional[list[uuid.UUID]] = None  # None means all accounts
    include_ai_insights: bool = True

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class AnalyticsReportResponse(BaseModel):
    """Response schema for analytics report."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    report_type: str
    start_date: date
    end_date: date
    account_ids: Optional[list] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    ai_insights: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIInsight(BaseModel):
    """AI-generated insight for analytics."""

    category: str  # 'growth', 'engagement', 'revenue', 'content', 'audience'
    title: str
    description: str
    recommendation: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    metric_change: Optional[float] = None
    metric_name: Optional[str] = None


class AIInsightsResponse(BaseModel):
    """Response schema for AI insights."""

    insights: list[AIInsight]
    generated_at: datetime
    period_start: date
    period_end: date
