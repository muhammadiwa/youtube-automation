"""Stream health log migration.

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

Creates StreamHealthLog table for health metrics storage.
Requirements: 8.1, 8.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stream_health_logs table
    op.create_table(
        "stream_health_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Health metrics
        sa.Column("bitrate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frame_rate", sa.Float(), nullable=True),
        sa.Column("dropped_frames", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dropped_frames_delta", sa.Integer(), nullable=False, server_default="0"),
        # Connection status
        sa.Column("connection_status", sa.String(50), nullable=False, server_default="good"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        # Viewer metrics
        sa.Column("viewer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chat_rate", sa.Float(), nullable=False, server_default="0.0"),
        # Stream quality indicators
        sa.Column("audio_level_db", sa.Float(), nullable=True),
        sa.Column("video_quality_score", sa.Float(), nullable=True),
        # Alert flags
        sa.Column("is_alert_triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alert_type", sa.String(100), nullable=True),
        sa.Column("alert_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "collected_at",
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
            ["session_id"],
            ["stream_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for efficient querying by session
    op.create_index(
        op.f("ix_stream_health_logs_session_id"),
        "stream_health_logs",
        ["session_id"],
        unique=False,
    )
    # Index for time-based queries (historical data retention)
    op.create_index(
        op.f("ix_stream_health_logs_collected_at"),
        "stream_health_logs",
        ["collected_at"],
        unique=False,
    )
    # Composite index for efficient session + time queries
    op.create_index(
        "ix_stream_health_logs_session_time",
        "stream_health_logs",
        ["session_id", "collected_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stream_health_logs_session_time", table_name="stream_health_logs")
    op.drop_index(op.f("ix_stream_health_logs_collected_at"), table_name="stream_health_logs")
    op.drop_index(op.f("ix_stream_health_logs_session_id"), table_name="stream_health_logs")
    op.drop_table("stream_health_logs")
