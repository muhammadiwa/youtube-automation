"""Competitor models migration.

Revision ID: 015
Revises: 014
Create Date: 2024-01-01 00:00:00.000000

Creates Competitor, CompetitorMetric, CompetitorContent, and CompetitorAnalysis tables.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create competitors table for external channel tracking
    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # YouTube channel info
        sa.Column("channel_id", sa.String(50), nullable=False),
        sa.Column("channel_title", sa.String(255), nullable=False),
        sa.Column("channel_description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("custom_url", sa.String(255), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        # Current metrics
        sa.Column("subscriber_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        # Tracking configuration
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_new_content", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_milestone", sa.Boolean(), nullable=False, server_default="false"),
        # User notes
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        # Sync status
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_content_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_competitors_user_id"),
        "competitors",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitors_channel_id"),
        "competitors",
        ["channel_id"],
        unique=False,
    )
    op.create_index(
        "ix_competitors_user_channel",
        "competitors",
        ["user_id", "channel_id"],
        unique=True,
    )

    # Create competitor_metrics table for historical tracking
    op.create_table(
        "competitor_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        # Channel metrics
        sa.Column("subscriber_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subscriber_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_change", sa.Integer(), nullable=False, server_default="0"),
        # Engagement estimates
        sa.Column("avg_views_per_video", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("estimated_engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        # Upload frequency
        sa.Column("videos_published_count", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["competitor_id"],
            ["competitors.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_competitor_metrics_competitor_id"),
        "competitor_metrics",
        ["competitor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_metrics_metric_date"),
        "competitor_metrics",
        ["metric_date"],
        unique=False,
    )
    op.create_index(
        "ix_competitor_metrics_competitor_date",
        "competitor_metrics",
        ["competitor_id", "metric_date"],
        unique=True,
    )

    # Create competitor_content table for tracking new content
    op.create_table(
        "competitor_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        # YouTube video info
        sa.Column("video_id", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        # Content type
        sa.Column("content_type", sa.String(20), nullable=False, server_default="video"),
        # Metrics at discovery
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        # Publishing info
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        # Tags and category
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("category_id", sa.String(10), nullable=True),
        # Notification status
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["competitor_id"],
            ["competitors.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_competitor_content_competitor_id"),
        "competitor_content",
        ["competitor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_content_video_id"),
        "competitor_content",
        ["video_id"],
        unique=False,
    )
    op.create_index(
        "ix_competitor_content_competitor_video",
        "competitor_content",
        ["competitor_id", "video_id"],
        unique=True,
    )

    # Create competitor_analyses table for AI analysis
    op.create_table(
        "competitor_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Analysis scope
        sa.Column("competitor_ids", postgresql.JSONB(), nullable=False),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        # Date range
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        # Analysis results
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("insights", postgresql.JSONB(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        # Trend data
        sa.Column("trend_data", postgresql.JSONB(), nullable=True),
        # Export info
        sa.Column("export_file_path", sa.String(512), nullable=True),
        sa.Column("export_format", sa.String(10), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_competitor_analyses_user_id"),
        "competitor_analyses",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_competitor_analyses_user_id"), table_name="competitor_analyses")
    op.drop_table("competitor_analyses")
    op.drop_index("ix_competitor_content_competitor_video", table_name="competitor_content")
    op.drop_index(op.f("ix_competitor_content_video_id"), table_name="competitor_content")
    op.drop_index(op.f("ix_competitor_content_competitor_id"), table_name="competitor_content")
    op.drop_table("competitor_content")
    op.drop_index("ix_competitor_metrics_competitor_date", table_name="competitor_metrics")
    op.drop_index(op.f("ix_competitor_metrics_metric_date"), table_name="competitor_metrics")
    op.drop_index(op.f("ix_competitor_metrics_competitor_id"), table_name="competitor_metrics")
    op.drop_table("competitor_metrics")
    op.drop_index("ix_competitors_user_channel", table_name="competitors")
    op.drop_index(op.f("ix_competitors_channel_id"), table_name="competitors")
    op.drop_index(op.f("ix_competitors_user_id"), table_name="competitors")
    op.drop_table("competitors")
