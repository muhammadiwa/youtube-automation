"""Admin Analytics Schemas.

Pydantic models for admin analytics API responses.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 17.1, 17.2, 17.3, 17.4, 17.5
"""

import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ==================== Platform Metrics (2.1) ====================

class PeriodComparison(BaseModel):
    """Comparison with previous period."""
    previous_value: float = Field(..., description="Value from previous period")
    change_percent: float = Field(..., description="Percentage change")
    trend: Literal["up", "down", "stable"] = Field(..., description="Trend direction")


class PlatformMetricsResponse(BaseModel):
    """Platform-wide metrics response.
    
    Requirements: 2.1 - Display key metrics (total users, active users, MRR, ARR, 
    total streams, total videos)
    """
    total_users: int = Field(..., description="Total registered users")
    active_users: int = Field(..., description="Active users in period")
    new_users: int = Field(..., description="New users in period")
    mrr: float = Field(..., description="Monthly Recurring Revenue")
    arr: float = Field(..., description="Annual Recurring Revenue")
    total_streams: int = Field(..., description="Total streams created")
    total_videos: int = Field(..., description="Total videos uploaded")
    active_streams: int = Field(..., description="Currently active streams")
    active_subscriptions: int = Field(..., description="Active paid subscriptions")
    
    # Period info
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    
    # Comparisons with previous period
    users_comparison: Optional[PeriodComparison] = Field(None, description="User count comparison")
    mrr_comparison: Optional[PeriodComparison] = Field(None, description="MRR comparison")
    streams_comparison: Optional[PeriodComparison] = Field(None, description="Streams comparison")


# ==================== Growth Metrics (2.2) ====================

class GrowthDataPoint(BaseModel):
    """Single data point for growth charts."""
    date: datetime = Field(..., description="Data point date")
    value: float = Field(..., description="Metric value")


class GrowthMetricsResponse(BaseModel):
    """Growth metrics response.
    
    Requirements: 2.2 - Show user growth chart, revenue growth chart, and churn rate over time
    """
    # User growth
    user_growth: list[GrowthDataPoint] = Field(..., description="User growth over time")
    user_growth_rate: float = Field(..., description="User growth rate percentage")
    
    # Revenue growth
    revenue_growth: list[GrowthDataPoint] = Field(..., description="Revenue growth over time")
    revenue_growth_rate: float = Field(..., description="Revenue growth rate percentage")
    
    # Churn
    churn_data: list[GrowthDataPoint] = Field(..., description="Churn rate over time")
    current_churn_rate: float = Field(..., description="Current churn rate percentage")
    
    # Period info
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    granularity: Literal["daily", "weekly", "monthly"] = Field(..., description="Data granularity")


# ==================== Real-time Metrics (2.3) ====================

class RealtimeMetricsResponse(BaseModel):
    """Real-time metrics response.
    
    Requirements: 2.3 - Display active streams count, concurrent users, API requests per minute
    """
    active_streams: int = Field(..., description="Currently active streams")
    concurrent_users: int = Field(..., description="Currently online users")
    api_requests_per_minute: int = Field(..., description="API requests in last minute")
    
    # Additional real-time stats
    active_jobs: int = Field(..., description="Currently processing jobs")
    queue_depth: int = Field(..., description="Jobs waiting in queue")
    avg_response_time_ms: float = Field(..., description="Average API response time")
    
    timestamp: datetime = Field(..., description="Metrics timestamp")


# ==================== Cohort Analysis (17.1) ====================

class CohortRow(BaseModel):
    """Single cohort row data."""
    cohort_date: str = Field(..., description="Cohort identifier (e.g., '2024-01')")
    cohort_size: int = Field(..., description="Number of users in cohort")
    retention: list[float] = Field(..., description="Retention percentages by period")


class CohortAnalysisResponse(BaseModel):
    """Cohort analysis response.
    
    Requirements: 17.1 - Display user retention by signup month with weekly/monthly breakdown
    """
    cohorts: list[CohortRow] = Field(..., description="Cohort data rows")
    periods: list[str] = Field(..., description="Period labels (Week 1, Week 2, etc.)")
    granularity: Literal["weekly", "monthly"] = Field(..., description="Retention granularity")
    period_start: datetime = Field(..., description="Analysis start date")
    period_end: datetime = Field(..., description="Analysis end date")


# ==================== Funnel Analysis (17.2) ====================

class FunnelStage(BaseModel):
    """Single funnel stage data."""
    stage: str = Field(..., description="Stage name")
    count: int = Field(..., description="Users at this stage")
    conversion_rate: float = Field(..., description="Conversion rate from previous stage")
    drop_off_rate: float = Field(..., description="Drop-off rate from previous stage")


class FunnelAnalysisResponse(BaseModel):
    """Funnel analysis response.
    
    Requirements: 17.2 - Show conversion rates (signup → verify → connect account → first stream → paid)
    """
    stages: list[FunnelStage] = Field(..., description="Funnel stages")
    overall_conversion: float = Field(..., description="Overall conversion rate")
    period_start: datetime = Field(..., description="Analysis start date")
    period_end: datetime = Field(..., description="Analysis end date")


# ==================== Geographic Distribution (17.3) ====================

class CountryData(BaseModel):
    """User data for a single country."""
    country_code: str = Field(..., description="ISO country code")
    country_name: str = Field(..., description="Country name")
    user_count: int = Field(..., description="Number of users")
    percentage: float = Field(..., description="Percentage of total users")


class RegionData(BaseModel):
    """User data for a region."""
    region: str = Field(..., description="Region name")
    user_count: int = Field(..., description="Number of users")
    percentage: float = Field(..., description="Percentage of total users")
    countries: list[CountryData] = Field(..., description="Countries in region")


class GeographicDistributionResponse(BaseModel):
    """Geographic distribution response.
    
    Requirements: 17.3 - Display user map with country/region breakdown
    """
    total_users: int = Field(..., description="Total users with location data")
    by_country: list[CountryData] = Field(..., description="Users by country")
    by_region: list[RegionData] = Field(..., description="Users by region")
    unknown_location: int = Field(..., description="Users without location data")


# ==================== Usage Heatmap (17.4) ====================

class HeatmapCell(BaseModel):
    """Single heatmap cell data."""
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    value: int = Field(..., description="Activity count")
    intensity: float = Field(..., ge=0, le=1, description="Normalized intensity (0-1)")


class UsageHeatmapResponse(BaseModel):
    """Usage heatmap response.
    
    Requirements: 17.4 - Show peak usage times by hour and day of week
    """
    data: list[HeatmapCell] = Field(..., description="Heatmap data")
    peak_hour: int = Field(..., description="Hour with highest activity")
    peak_day: int = Field(..., description="Day with highest activity")
    peak_value: int = Field(..., description="Highest activity value")
    total_activity: int = Field(..., description="Total activity count")
    period_start: datetime = Field(..., description="Analysis start date")
    period_end: datetime = Field(..., description="Analysis end date")


# ==================== Feature Adoption (17.5) ====================

class FeatureUsage(BaseModel):
    """Usage data for a single feature."""
    feature_name: str = Field(..., description="Feature name")
    feature_key: str = Field(..., description="Feature identifier")
    total_users: int = Field(..., description="Total users who used feature")
    active_users: int = Field(..., description="Active users in period")
    usage_count: int = Field(..., description="Total usage count")
    adoption_rate: float = Field(..., description="Adoption rate percentage")
    trend: Literal["up", "down", "stable"] = Field(..., description="Usage trend")
    trend_percent: float = Field(..., description="Trend percentage change")


class FeatureAdoptionResponse(BaseModel):
    """Feature adoption response.
    
    Requirements: 17.5 - Display usage statistics per feature with trend indicators
    """
    features: list[FeatureUsage] = Field(..., description="Feature usage data")
    total_users: int = Field(..., description="Total platform users")
    period_start: datetime = Field(..., description="Analysis start date")
    period_end: datetime = Field(..., description="Analysis end date")


# ==================== Dashboard Export (2.5) ====================

class ExportRequest(BaseModel):
    """Dashboard export request.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    """
    format: Literal["csv", "pdf"] = Field(..., description="Export format")
    metrics: list[str] = Field(..., description="Metrics to include")
    start_date: Optional[datetime] = Field(None, description="Start date for data")
    end_date: Optional[datetime] = Field(None, description="End date for data")
    include_charts: bool = Field(default=False, description="Include charts in PDF")


class ExportResponse(BaseModel):
    """Dashboard export response.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    """
    export_id: str = Field(..., description="Export job ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    format: str = Field(..., description="Export format")
    created_at: datetime = Field(..., description="Export request time")
    completed_at: Optional[datetime] = Field(None, description="Export completion time")
    file_size: Optional[int] = Field(None, description="File size in bytes")
