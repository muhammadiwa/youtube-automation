"""Revenue models for earnings tracking and goal management.

Implements RevenueRecord and RevenueGoal models for revenue tracking.
Requirements: 18.1, 18.2, 18.4
"""

import uuid
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


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


class RevenueRecord(Base):
    """Daily revenue record for a YouTube account.

    Stores earnings breakdown by source for a specific date.
    Requirements: 18.1, 18.2
    """

    __tablename__ = "revenue_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date for this record (one record per account per day)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Revenue by source
    ad_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    membership_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    super_chat_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    super_sticker_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    merchandise_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    youtube_premium_revenue: Mapped[float] = mapped_column(Float, default=0.0)

    # Total (computed but stored for query efficiency)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)

    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Additional metadata
    estimated_cpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    monetized_playbacks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    playback_based_cpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Sync status
    synced_from_youtube: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Composite unique constraint: one record per account per day
    __table_args__ = (
        Index(
            "ix_revenue_records_account_date",
            "account_id",
            "record_date",
            unique=True,
        ),
    )

    def calculate_total(self) -> float:
        """Calculate total revenue from all sources.

        Returns:
            float: Sum of all revenue sources
        """
        return (
            self.ad_revenue
            + self.membership_revenue
            + self.super_chat_revenue
            + self.super_sticker_revenue
            + self.merchandise_revenue
            + self.youtube_premium_revenue
        )

    def get_breakdown(self) -> dict[str, float]:
        """Get revenue breakdown by source.

        Returns:
            dict: Revenue amounts by source type
        """
        return {
            RevenueSourceType.AD.value: self.ad_revenue,
            RevenueSourceType.MEMBERSHIP.value: self.membership_revenue,
            RevenueSourceType.SUPER_CHAT.value: self.super_chat_revenue,
            RevenueSourceType.SUPER_STICKER.value: self.super_sticker_revenue,
            RevenueSourceType.MERCHANDISE.value: self.merchandise_revenue,
            RevenueSourceType.YOUTUBE_PREMIUM.value: self.youtube_premium_revenue,
        }

    def __repr__(self) -> str:
        return f"<RevenueRecord(account_id={self.account_id}, date={self.record_date}, total={self.total_revenue})>"


class RevenueGoal(Base):
    """Revenue goal for tracking targets.

    Allows users to set revenue targets and track progress.
    Requirements: 18.4
    """

    __tablename__ = "revenue_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=True,  # Null means goal applies to all accounts
        index=True,
    )

    # Goal details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Period
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Progress tracking
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    forecast_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forecast_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=GoalStatus.ACTIVE.value)
    achieved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notification settings
    notify_at_percentage: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )
    last_notification_percentage: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def update_progress(self, current_amount: float) -> None:
        """Update goal progress.

        Args:
            current_amount: Current revenue amount
        """
        self.current_amount = current_amount
        if self.target_amount > 0:
            self.progress_percentage = (current_amount / self.target_amount) * 100
        else:
            self.progress_percentage = 0.0

        # Check if goal is achieved
        if self.progress_percentage >= 100 and self.status == GoalStatus.ACTIVE.value:
            self.status = GoalStatus.ACHIEVED.value
            self.achieved_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if goal is currently active."""
        return self.status == GoalStatus.ACTIVE.value

    def __repr__(self) -> str:
        return f"<RevenueGoal(id={self.id}, name={self.name}, progress={self.progress_percentage:.1f}%)>"


class RevenueAlert(Base):
    """Revenue alert for trend changes and anomalies.

    Stores alerts generated when significant revenue changes are detected.
    Requirements: 18.3
    """

    __tablename__ = "revenue_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Alert details
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Metrics
    metric_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    previous_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    change_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # AI analysis
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommendations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=AlertStatus.UNREAD.value)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def mark_as_read(self) -> None:
        """Mark alert as read."""
        self.status = AlertStatus.READ.value
        self.read_at = datetime.utcnow()

    def dismiss(self) -> None:
        """Dismiss the alert."""
        self.status = AlertStatus.DISMISSED.value

    def __repr__(self) -> str:
        return f"<RevenueAlert(id={self.id}, type={self.alert_type}, severity={self.severity})>"
