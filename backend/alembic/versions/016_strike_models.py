"""Strike models migration.

Revision ID: 016
Revises: 015
Create Date: 2024-01-01 00:00:00.000000

Creates Strike, StrikeAlert, and PausedStream tables.
Requirements: 20.1, 20.2, 20.3, 20.4, 20.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create strikes table for tracking YouTube strikes
    op.create_table(
        "strikes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Strike identification
        sa.Column("youtube_strike_id", sa.String(255), nullable=True),
        # Strike details
        sa.Column("strike_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="warning"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reason_details", sa.Text(), nullable=True),
        # Affected content
        sa.Column("affected_video_id", sa.String(50), nullable=True),
        sa.Column("affected_video_title", sa.String(255), nullable=True),
        sa.Column("affected_content_url", sa.String(512), nullable=True),
        # Status tracking
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        # Appeal tracking
        sa.Column("appeal_status", sa.String(50), nullable=False, server_default="not_appealed"),
        sa.Column("appeal_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("appeal_reason", sa.Text(), nullable=True),
        sa.Column("appeal_response", sa.Text(), nullable=True),
        sa.Column("appeal_resolved_at", sa.DateTime(timezone=True), nullable=True),
        # Strike timing
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        # Notification tracking
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        # Auto-pause tracking
        sa.Column("streams_paused", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("streams_paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("streams_resumed_at", sa.DateTime(timezone=True), nullable=True),
        # Additional data
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
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
        op.f("ix_strikes_account_id"),
        "strikes",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strikes_youtube_strike_id"),
        "strikes",
        ["youtube_strike_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_strikes_status"),
        "strikes",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_strikes_account_status",
        "strikes",
        ["account_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_strikes_issued_at",
        "strikes",
        ["issued_at"],
        unique=False,
    )

    # Create strike_alerts table for tracking notifications
    op.create_table(
        "strike_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strike_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Alert details
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="high"),
        # Delivery tracking
        sa.Column("channels_sent", postgresql.JSONB(), nullable=True),
        sa.Column("delivery_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        # User acknowledgment
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["strike_id"],
            ["strikes.id"],
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
        op.f("ix_strike_alerts_strike_id"),
        "strike_alerts",
        ["strike_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strike_alerts_account_id"),
        "strike_alerts",
        ["account_id"],
        unique=False,
    )

    # Create paused_streams table for tracking auto-paused streams
    op.create_table(
        "paused_streams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strike_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("live_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Original stream state
        sa.Column("original_status", sa.String(50), nullable=False),
        sa.Column("original_scheduled_start_at", sa.DateTime(timezone=True), nullable=True),
        # Pause details
        sa.Column(
            "paused_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("pause_reason", sa.Text(), nullable=False),
        # Resume tracking
        sa.Column("resumed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resume_confirmation", sa.Boolean(), nullable=False, server_default="false"),
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
            ["strike_id"],
            ["strikes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["live_event_id"],
            ["live_events.id"],
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
        op.f("ix_paused_streams_strike_id"),
        "paused_streams",
        ["strike_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_paused_streams_live_event_id"),
        "paused_streams",
        ["live_event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_paused_streams_account_id"),
        "paused_streams",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_paused_streams_account_resumed",
        "paused_streams",
        ["account_id", "resumed"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_paused_streams_account_resumed", table_name="paused_streams")
    op.drop_index(op.f("ix_paused_streams_account_id"), table_name="paused_streams")
    op.drop_index(op.f("ix_paused_streams_live_event_id"), table_name="paused_streams")
    op.drop_index(op.f("ix_paused_streams_strike_id"), table_name="paused_streams")
    op.drop_table("paused_streams")
    op.drop_index(op.f("ix_strike_alerts_account_id"), table_name="strike_alerts")
    op.drop_index(op.f("ix_strike_alerts_strike_id"), table_name="strike_alerts")
    op.drop_table("strike_alerts")
    op.drop_index("ix_strikes_issued_at", table_name="strikes")
    op.drop_index("ix_strikes_account_status", table_name="strikes")
    op.drop_index(op.f("ix_strikes_status"), table_name="strikes")
    op.drop_index(op.f("ix_strikes_youtube_strike_id"), table_name="strikes")
    op.drop_index(op.f("ix_strikes_account_id"), table_name="strikes")
    op.drop_table("strikes")
