"""Revenue models migration.

Revision ID: 014
Revises: 013
Create Date: 2024-01-01 00:00:00.000000

Creates RevenueRecord and RevenueGoal tables for revenue tracking.
Requirements: 18.1, 18.4
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create revenue_records table for daily earnings
    op.create_table(
        "revenue_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        # Revenue by source
        sa.Column("ad_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("membership_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("super_chat_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("super_sticker_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("merchandise_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("youtube_premium_revenue", sa.Float(), nullable=False, server_default="0.0"),
        # Total (computed but stored for query efficiency)
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0.0"),
        # Currency
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        # Additional metadata
        sa.Column("estimated_cpm", sa.Float(), nullable=True),
        sa.Column("monetized_playbacks", sa.Integer(), nullable=True),
        sa.Column("playback_based_cpm", sa.Float(), nullable=True),
        # Sync status
        sa.Column("synced_from_youtube", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
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
        op.f("ix_revenue_records_account_id"),
        "revenue_records",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_records_record_date"),
        "revenue_records",
        ["record_date"],
        unique=False,
    )
    op.create_index(
        "ix_revenue_records_account_date",
        "revenue_records",
        ["account_id", "record_date"],
        unique=True,
    )

    # Create revenue_goals table for targets
    op.create_table(
        "revenue_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),  # Null = all accounts
        # Goal details
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        # Period
        sa.Column("period_type", sa.String(20), nullable=False),  # daily, weekly, monthly, yearly, custom
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        # Progress tracking
        sa.Column("current_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("forecast_amount", sa.Float(), nullable=True),
        sa.Column("forecast_probability", sa.Float(), nullable=True),  # 0.0 to 1.0
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active, achieved, missed, cancelled
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=True),
        # Notification settings
        sa.Column("notify_at_percentage", postgresql.ARRAY(sa.Integer()), nullable=True),  # e.g., [50, 75, 90, 100]
        sa.Column("last_notification_percentage", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["youtube_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_revenue_goals_user_id"),
        "revenue_goals",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_goals_account_id"),
        "revenue_goals",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_goals_status"),
        "revenue_goals",
        ["status"],
        unique=False,
    )

    # Create revenue_alerts table for trend change notifications
    op.create_table(
        "revenue_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Alert details
        sa.Column("alert_type", sa.String(50), nullable=False),  # trend_change, goal_progress, anomaly
        sa.Column("severity", sa.String(20), nullable=False),  # info, warning, critical
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        # Metrics
        sa.Column("metric_name", sa.String(100), nullable=True),
        sa.Column("previous_value", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("change_percentage", sa.Float(), nullable=True),
        # AI analysis
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column("ai_recommendations", postgresql.JSONB(), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="unread"),  # unread, read, dismissed
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["youtube_accounts.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_revenue_alerts_user_id"),
        "revenue_alerts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_alerts_status"),
        "revenue_alerts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_revenue_alerts_status"), table_name="revenue_alerts")
    op.drop_index(op.f("ix_revenue_alerts_user_id"), table_name="revenue_alerts")
    op.drop_table("revenue_alerts")
    op.drop_index(op.f("ix_revenue_goals_status"), table_name="revenue_goals")
    op.drop_index(op.f("ix_revenue_goals_account_id"), table_name="revenue_goals")
    op.drop_index(op.f("ix_revenue_goals_user_id"), table_name="revenue_goals")
    op.drop_table("revenue_goals")
    op.drop_index("ix_revenue_records_account_date", table_name="revenue_records")
    op.drop_index(op.f("ix_revenue_records_record_date"), table_name="revenue_records")
    op.drop_index(op.f("ix_revenue_records_account_id"), table_name="revenue_records")
    op.drop_table("revenue_records")
