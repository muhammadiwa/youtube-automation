"""Stream models migration.

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

Creates LiveEvent, StreamSession, and RecurrencePattern tables.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create live_events table
    op.create_table(
        "live_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("youtube_broadcast_id", sa.String(255), nullable=True),
        sa.Column("youtube_stream_id", sa.String(255), nullable=True),
        sa.Column("rtmp_key", sa.Text(), nullable=True),
        sa.Column("rtmp_url", sa.String(512), nullable=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("latency_mode", sa.String(50), nullable=False, server_default="normal"),
        sa.Column("enable_dvr", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enable_content_encryption", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enable_auto_start", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enable_auto_stop", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enable_embed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("record_from_start", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("privacy_status", sa.String(50), nullable=False, server_default="private"),
        sa.Column("made_for_kids", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recurrence_frequency", sa.String(50), nullable=True),
        sa.Column("recurrence_interval", sa.Integer(), nullable=True),
        sa.Column("recurrence_days_of_week", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("recurrence_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_count", sa.Integer(), nullable=True),
        sa.Column("parent_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="created"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("peak_viewers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chat_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_watch_time", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["parent_event_id"],
            ["live_events.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_live_events_account_id"),
        "live_events",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_live_events_youtube_broadcast_id"),
        "live_events",
        ["youtube_broadcast_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_live_events_scheduled_start_at"),
        "live_events",
        ["scheduled_start_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_live_events_status"),
        "live_events",
        ["status"],
        unique=False,
    )

    # Create stream_sessions table
    op.create_table(
        "stream_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("live_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("peak_viewers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chat_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_bitrate", sa.Integer(), nullable=True),
        sa.Column("dropped_frames", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("connection_status", sa.String(50), nullable=False, server_default="disconnected"),
        sa.Column("reconnection_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_reason", sa.String(255), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
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
            ["live_event_id"],
            ["live_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_stream_sessions_live_event_id"),
        "stream_sessions",
        ["live_event_id"],
        unique=False,
    )

    # Create recurrence_patterns table
    op.create_table(
        "recurrence_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("live_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False, server_default="weekly"),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("days_of_week", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("occurrence_count", sa.Integer(), nullable=True),
        sa.Column("generated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_occurrence_at", sa.DateTime(timezone=True), nullable=True),
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
            ["live_event_id"],
            ["live_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("live_event_id"),
    )
    op.create_index(
        op.f("ix_recurrence_patterns_live_event_id"),
        "recurrence_patterns",
        ["live_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recurrence_patterns_live_event_id"), table_name="recurrence_patterns")
    op.drop_table("recurrence_patterns")
    op.drop_index(op.f("ix_stream_sessions_live_event_id"), table_name="stream_sessions")
    op.drop_table("stream_sessions")
    op.drop_index(op.f("ix_live_events_status"), table_name="live_events")
    op.drop_index(op.f("ix_live_events_scheduled_start_at"), table_name="live_events")
    op.drop_index(op.f("ix_live_events_youtube_broadcast_id"), table_name="live_events")
    op.drop_index(op.f("ix_live_events_account_id"), table_name="live_events")
    op.drop_table("live_events")
