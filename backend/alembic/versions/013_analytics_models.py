"""Analytics models migration.

Revision ID: 013
Revises: 012
Create Date: 2024-01-01 00:00:00.000000

Creates AnalyticsSnapshot and AnalyticsReport tables.
Requirements: 17.1, 17.2, 17.3
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_snapshots table
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        # Channel metrics
        sa.Column("subscriber_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subscriber_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views_change", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_videos", sa.Integer(), nullable=False, server_default="0"),
        # Engagement metrics
        sa.Column("total_likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_view_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        # Watch time metrics
        sa.Column("watch_time_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_view_percentage", sa.Float(), nullable=False, server_default="0.0"),
        # Revenue metrics
        sa.Column("estimated_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("ad_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("membership_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("super_chat_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("merchandise_revenue", sa.Float(), nullable=False, server_default="0.0"),
        # JSON fields
        sa.Column("traffic_sources", postgresql.JSONB(), nullable=True),
        sa.Column("demographics", postgresql.JSONB(), nullable=True),
        sa.Column("top_videos", postgresql.JSONB(), nullable=True),
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
            ["account_id"],
            ["youtube_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analytics_snapshots_account_id"),
        "analytics_snapshots",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analytics_snapshots_snapshot_date"),
        "analytics_snapshots",
        ["snapshot_date"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_snapshots_account_date",
        "analytics_snapshots",
        ["account_id", "snapshot_date"],
        unique=True,
    )

    # Create analytics_reports table
    op.create_table(
        "analytics_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("account_ids", postgresql.JSONB(), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("ai_insights", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        op.f("ix_analytics_reports_user_id"),
        "analytics_reports",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analytics_reports_user_id"), table_name="analytics_reports")
    op.drop_table("analytics_reports")
    op.drop_index("ix_analytics_snapshots_account_date", table_name="analytics_snapshots")
    op.drop_index(op.f("ix_analytics_snapshots_snapshot_date"), table_name="analytics_snapshots")
    op.drop_index(op.f("ix_analytics_snapshots_account_id"), table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")
