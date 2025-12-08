"""Analytics models for metrics tracking and reporting.

Implements AnalyticsSnapshot model for storing daily metrics per account.
Requirements: 17.1, 17.2
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AnalyticsSnapshot(Base):
    """Daily analytics snapshot for a YouTube account.

    Stores aggregated metrics for a specific date, enabling
    historical analysis and period comparisons.
    Requirements: 17.1, 17.2
    """

    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date for this snapshot (one snapshot per account per day)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Channel metrics
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    subscriber_change: Mapped[int] = mapped_column(Integer, default=0)  # Change from previous day
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    views_change: Mapped[int] = mapped_column(Integer, default=0)
    total_videos: Mapped[int] = mapped_column(Integer, default=0)

    # Engagement metrics
    total_likes: Mapped[int] = mapped_column(Integer, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    total_shares: Mapped[int] = mapped_column(Integer, default=0)
    average_view_duration: Mapped[float] = mapped_column(Float, default=0.0)  # In seconds
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage

    # Watch time metrics
    watch_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_view_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Revenue metrics (for monetized channels)
    estimated_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    ad_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    membership_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    super_chat_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    merchandise_revenue: Mapped[float] = mapped_column(Float, default=0.0)

    # Traffic sources (stored as JSON for flexibility)
    traffic_sources: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Demographics (stored as JSON)
    demographics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Top performing content (stored as JSON)
    top_videos: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Composite unique constraint: one snapshot per account per day
    __table_args__ = (
        Index(
            "ix_analytics_snapshots_account_date",
            "account_id",
            "snapshot_date",
            unique=True,
        ),
    )

    def get_total_revenue(self) -> float:
        """Calculate total revenue from all sources.

        Returns:
            float: Sum of all revenue sources
        """
        return (
            self.ad_revenue
            + self.membership_revenue
            + self.super_chat_revenue
            + self.merchandise_revenue
        )

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot(account_id={self.account_id}, date={self.snapshot_date})>"


class AnalyticsReport(Base):
    """Generated analytics report.

    Stores generated reports in PDF/CSV format.
    Requirements: 17.3
    """

    __tablename__ = "analytics_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'pdf', 'csv'
    
    # Date range for the report
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Accounts included in the report (stored as JSON array of UUIDs)
    account_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # File storage
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # AI insights (stored as JSON)
    ai_insights: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, generating, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AnalyticsReport(id={self.id}, title={self.title}, status={self.status})>"
