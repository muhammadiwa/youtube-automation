"""Competitor models for external channel tracking.

Implements Competitor and CompetitorMetric models for tracking external channels.
Requirements: 19.1
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Competitor(Base):
    """External YouTube channel being tracked as a competitor.

    Stores competitor channel data and tracking configuration.
    Requirements: 19.1
    """

    __tablename__ = "competitors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # YouTube channel info
    channel_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel_title: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    custom_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Current metrics (latest snapshot)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    # Tracking configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_new_content: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_milestone: Mapped[bool] = mapped_column(Boolean, default=False)

    # User notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Sync status
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_content_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    metrics: Mapped[list["CompetitorMetric"]] = relationship(
        "CompetitorMetric", back_populates="competitor", cascade="all, delete-orphan"
    )
    content_items: Mapped[list["CompetitorContent"]] = relationship(
        "CompetitorContent", back_populates="competitor", cascade="all, delete-orphan"
    )

    # Unique constraint: one competitor per user per channel
    __table_args__ = (
        Index(
            "ix_competitors_user_channel",
            "user_id",
            "channel_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, channel={self.channel_title})>"


class CompetitorMetric(Base):
    """Historical metrics snapshot for a competitor channel.

    Stores daily metrics for trend analysis.
    Requirements: 19.1, 19.2
    """

    __tablename__ = "competitor_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Snapshot date
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Channel metrics
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    subscriber_change: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    video_change: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    view_change: Mapped[int] = mapped_column(Integer, default=0)

    # Engagement estimates (from public data)
    avg_views_per_video: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Upload frequency
    videos_published_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    competitor: Mapped["Competitor"] = relationship(
        "Competitor", back_populates="metrics"
    )

    # Unique constraint: one metric per competitor per day
    __table_args__ = (
        Index(
            "ix_competitor_metrics_competitor_date",
            "competitor_id",
            "metric_date",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<CompetitorMetric(competitor_id={self.competitor_id}, date={self.metric_date})>"


class CompetitorContent(Base):
    """Tracked content from competitor channels.

    Stores recent videos/streams for content analysis.
    Requirements: 19.3
    """

    __tablename__ = "competitor_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # YouTube video info
    video_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Content type
    content_type: Mapped[str] = mapped_column(String(20), default="video")  # video, short, live

    # Metrics at discovery
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Publishing info
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Tags and category
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Notification status
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    competitor: Mapped["Competitor"] = relationship(
        "Competitor", back_populates="content_items"
    )

    # Unique constraint: one content item per competitor per video
    __table_args__ = (
        Index(
            "ix_competitor_content_competitor_video",
            "competitor_id",
            "video_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<CompetitorContent(video_id={self.video_id}, title={self.title})>"


class CompetitorAnalysis(Base):
    """AI-generated analysis and recommendations for competitors.

    Stores analysis results and actionable recommendations.
    Requirements: 19.4, 19.5
    """

    __tablename__ = "competitor_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Analysis scope
    competitor_ids: Mapped[list] = mapped_column(JSONB, nullable=False)  # List of competitor UUIDs
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)  # comparison, trend, content, strategy

    # Date range analyzed
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Analysis results
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    insights: Mapped[list] = mapped_column(JSONB, nullable=False)  # List of insight objects
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False)  # List of recommendation objects

    # Trend data
    trend_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Export info
    export_file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    export_format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # pdf, csv, json

    # Status
    status: Mapped[str] = mapped_column(String(20), default="completed")  # pending, generating, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<CompetitorAnalysis(id={self.id}, type={self.analysis_type})>"
