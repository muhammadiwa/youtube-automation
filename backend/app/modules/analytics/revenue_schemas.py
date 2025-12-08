"""Pydantic schemas for revenue tracking module.

Defines request/response schemas for revenue records, goals, and alerts.
Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import uuid
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class RevenueSourceType(str, Enum):
    """Types of revenue sources."""
    AD = "ad"
    MEMBERSHIP = "membership"
    SUPER_CHAT = "super_chat"
    SUPER_STICKER = "super_sticker"
    MERCHANDISE = "merchandise"
    YOUTUBE_PREMIUM = "youtube_premium"


class GoalPeriodType(str, Enum):
    """Types of goal periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class GoalStatus(str, Enum):
    """Status of a revenue goal."""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    MISSED = "missed"
    CANCELLED = "cancelled"


class AlertType(str, Enum):
    """Types of revenue alerts."""
    TREND_CHANGE = "trend_change"
    GOAL_PROGRESS = "goal_progress"
    ANOMALY = "anomaly"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status of an alert."""
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


# ============== Revenue Record Schemas ==============

class RevenueRecordCreate(BaseModel):
    """Request schema for creating a revenue record."""
    account_id: uuid.UUID
    record_date: date
    ad_revenue: float = 0.0
    membership_revenue: float = 0.0
    super_chat_revenue: float = 0.0
    super_sticker_revenue: float = 0.0
    merchandise_revenue: float = 0.0
    youtube_premium_revenue: float = 0.0
    currency: str = "USD"
    estimated_cpm: Optional[float] = None
    monetized_playbacks: Optional[int] = None
    playback_based_cpm: Optional[float] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()


class RevenueRecordUpdate(BaseModel):
    """Request schema for updating a revenue record."""
    ad_revenue: Optional[float] = None
    membership_revenue: Optional[float] = None
    super_chat_revenue: Optional[float] = None
    super_sticker_revenue: Optional[float] = None
    merchandise_revenue: Optional[float] = None
    youtube_premium_revenue: Optional[float] = None
    estimated_cpm: Optional[float] = None
    monetized_playbacks: Optional[int] = None
    playback_based_cpm: Optional[float] = None


class RevenueRecordResponse(BaseModel):
    """Response schema for a revenue record."""
    id: uuid.UUID
    account_id: uuid.UUID
    record_date: date
    ad_revenue: float
    membership_revenue: float
    super_chat_revenue: float
    super_sticker_revenue: float
    merchandise_revenue: float
    youtube_premium_revenue: float
    total_revenue: float
    currency: str
    estimated_cpm: Optional[float] = None
    monetized_playbacks: Optional[int] = None
    playback_based_cpm: Optional[float] = None
    synced_from_youtube: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RevenueBreakdown(BaseModel):
    """Revenue breakdown by source."""
    ad: float = Field(default=0.0, alias="ad_revenue")
    membership: float = Field(default=0.0, alias="membership_revenue")
    super_chat: float = Field(default=0.0, alias="super_chat_revenue")
    super_sticker: float = Field(default=0.0, alias="super_sticker_revenue")
    merchandise: float = Field(default=0.0, alias="merchandise_revenue")
    youtube_premium: float = Field(default=0.0, alias="youtube_premium_revenue")
    total: float = Field(default=0.0, alias="total_revenue")

    @model_validator(mode="after")
    def validate_total_equals_sum(self) -> "RevenueBreakdown":
        """Validate that total equals sum of all sources."""
        calculated_total = (
            self.ad + self.membership + self.super_chat +
            self.super_sticker + self.merchandise + self.youtube_premium
        )
        # Allow small floating point differences
        if abs(self.total - calculated_total) > 0.01:
            # Auto-correct the total
            self.total = calculated_total
        return self


# ============== Revenue Dashboard Schemas ==============

class RevenueDashboardRequest(BaseModel):
    """Request schema for revenue dashboard."""
    start_date: date
    end_date: date
    account_ids: Optional[List[uuid.UUID]] = None  # None = all accounts

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class AccountRevenue(BaseModel):
    """Revenue for a single account."""
    account_id: uuid.UUID
    channel_title: Optional[str] = None
    total_revenue: float = 0.0
    ad_revenue: float = 0.0
    membership_revenue: float = 0.0
    super_chat_revenue: float = 0.0
    super_sticker_revenue: float = 0.0
    merchandise_revenue: float = 0.0
    youtube_premium_revenue: float = 0.0
    revenue_change: float = 0.0
    revenue_change_percent: float = 0.0


class RevenueDashboardResponse(BaseModel):
    """Response schema for revenue dashboard."""
    # Totals across all accounts
    total_revenue: float = 0.0
    ad_revenue: float = 0.0
    membership_revenue: float = 0.0
    super_chat_revenue: float = 0.0
    super_sticker_revenue: float = 0.0
    merchandise_revenue: float = 0.0
    youtube_premium_revenue: float = 0.0

    # Changes from previous period
    revenue_change: float = 0.0
    revenue_change_percent: float = 0.0

    # Breakdown by source (for pie chart)
    breakdown: RevenueBreakdown

    # Per-account breakdown
    accounts: List[AccountRevenue] = []

    # Period info
    start_date: date
    end_date: date
    comparison_start_date: Optional[date] = None
    comparison_end_date: Optional[date] = None
    currency: str = "USD"


# ============== Revenue Goal Schemas ==============

class RevenueGoalCreate(BaseModel):
    """Request schema for creating a revenue goal."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: float = Field(..., gt=0)
    currency: str = "USD"
    period_type: GoalPeriodType
    start_date: date
    end_date: date
    account_id: Optional[uuid.UUID] = None  # None = all accounts
    notify_at_percentage: Optional[List[int]] = Field(default=[50, 75, 90, 100])

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v

    @field_validator("notify_at_percentage")
    @classmethod
    def validate_percentages(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v:
            for p in v:
                if p < 0 or p > 100:
                    raise ValueError("Percentages must be between 0 and 100")
        return v


class RevenueGoalUpdate(BaseModel):
    """Request schema for updating a revenue goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    end_date: Optional[date] = None
    status: Optional[GoalStatus] = None
    notify_at_percentage: Optional[List[int]] = None


class RevenueGoalResponse(BaseModel):
    """Response schema for a revenue goal."""
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    target_amount: float
    currency: str
    period_type: str
    start_date: date
    end_date: date
    current_amount: float
    progress_percentage: float
    forecast_amount: Optional[float] = None
    forecast_probability: Optional[float] = None
    status: str
    achieved_at: Optional[datetime] = None
    notify_at_percentage: Optional[List[int]] = None
    last_notification_percentage: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalProgressUpdate(BaseModel):
    """Schema for updating goal progress."""
    current_amount: float


# ============== Revenue Alert Schemas ==============

class RevenueAlertCreate(BaseModel):
    """Request schema for creating a revenue alert."""
    user_id: uuid.UUID
    account_id: Optional[uuid.UUID] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    metric_name: Optional[str] = None
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    change_percentage: Optional[float] = None
    ai_analysis: Optional[str] = None
    ai_recommendations: Optional[dict] = None


class RevenueAlertResponse(BaseModel):
    """Response schema for a revenue alert."""
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: Optional[uuid.UUID] = None
    alert_type: str
    severity: str
    title: str
    message: str
    metric_name: Optional[str] = None
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    change_percentage: Optional[float] = None
    ai_analysis: Optional[str] = None
    ai_recommendations: Optional[dict] = None
    status: str
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Tax Report Schemas ==============

class TaxReportRequest(BaseModel):
    """Request schema for generating tax report."""
    year: int = Field(..., ge=2000, le=2100)
    account_ids: Optional[List[uuid.UUID]] = None  # None = all accounts
    format: str = Field(default="csv", pattern="^(csv|pdf)$")


class TaxReportSummary(BaseModel):
    """Tax report summary for a single account."""
    account_id: uuid.UUID
    channel_title: Optional[str] = None
    total_revenue: float = 0.0
    ad_revenue: float = 0.0
    membership_revenue: float = 0.0
    super_chat_revenue: float = 0.0
    super_sticker_revenue: float = 0.0
    merchandise_revenue: float = 0.0
    youtube_premium_revenue: float = 0.0
    currency: str = "USD"


class TaxReportResponse(BaseModel):
    """Response schema for tax report."""
    year: int
    total_revenue: float
    accounts: List[TaxReportSummary]
    generated_at: datetime
    file_path: Optional[str] = None
    currency: str = "USD"


class MonthlyRevenueSummary(BaseModel):
    """Monthly revenue summary for tax purposes."""
    month: int
    year: int
    total_revenue: float
    ad_revenue: float
    membership_revenue: float
    super_chat_revenue: float
    super_sticker_revenue: float
    merchandise_revenue: float
    youtube_premium_revenue: float
