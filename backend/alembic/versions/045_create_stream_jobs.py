"""Create stream_jobs and stream_job_health tables.

Revision ID: 045
Revises: 044
Create Date: 2025-12-19

Requirements: 1.1, 4.2
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "045_stream_jobs"
down_revision = "044_local_thumbnail"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stream_jobs table
    op.create_table(
        "stream_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Video source
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("video_path", sa.String(1024), nullable=False),
        sa.Column(
            "playlist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stream_playlists.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Stream target (RTMP)
        sa.Column(
            "rtmp_url",
            sa.String(512),
            nullable=False,
            server_default="rtmp://a.rtmp.youtube.com/live2",
        ),
        sa.Column("stream_key", sa.Text, nullable=True),  # Encrypted
        sa.Column("is_stream_key_locked", sa.Boolean, default=False, nullable=False),
        # Job metadata
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Loop configuration
        sa.Column("loop_mode", sa.String(50), nullable=False, server_default="none"),
        sa.Column("loop_count", sa.Integer, nullable=True),
        sa.Column("current_loop", sa.Integer, nullable=False, server_default="0"),
        # Output settings
        sa.Column("resolution", sa.String(20), nullable=False, server_default="1080p"),
        sa.Column("target_bitrate", sa.Integer, nullable=False, server_default="6000"),
        sa.Column("encoding_mode", sa.String(10), nullable=False, server_default="cbr"),
        sa.Column("target_fps", sa.Integer, nullable=False, server_default="30"),
        # Scheduling
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=True),
        # Process tracking
        sa.Column("pid", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        # Timing
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer, nullable=False, server_default="0"),
        # Error handling
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("restart_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_restarts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("enable_auto_restart", sa.Boolean, nullable=False, server_default="true"),
        # Current metrics
        sa.Column("current_bitrate", sa.Integer, nullable=True),
        sa.Column("current_fps", sa.Float, nullable=True),
        sa.Column("current_speed", sa.String(20), nullable=True),
        sa.Column("dropped_frames", sa.Integer, nullable=False, server_default="0"),
        sa.Column("frame_count", sa.Integer, nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for stream_jobs
    op.create_index("idx_stream_jobs_user_id", "stream_jobs", ["user_id"])
    op.create_index("idx_stream_jobs_account_id", "stream_jobs", ["account_id"])
    op.create_index("idx_stream_jobs_status", "stream_jobs", ["status"])
    op.create_index("idx_stream_jobs_scheduled_start", "stream_jobs", ["scheduled_start_at"])

    # Create stream_job_health table
    op.create_table(
        "stream_job_health",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "stream_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stream_jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # FFmpeg metrics
        sa.Column("bitrate", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fps", sa.Float, nullable=True),
        sa.Column("speed", sa.String(20), nullable=True),
        sa.Column("dropped_frames", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dropped_frames_delta", sa.Integer, nullable=False, server_default="0"),
        sa.Column("frame_count", sa.Integer, nullable=False, server_default="0"),
        # System resources
        sa.Column("cpu_percent", sa.Float, nullable=True),
        sa.Column("memory_mb", sa.Float, nullable=True),
        # Alert info
        sa.Column("alert_type", sa.String(50), nullable=True),
        sa.Column("alert_message", sa.Text, nullable=True),
        sa.Column("is_alert_acknowledged", sa.Boolean, nullable=False, server_default="false"),
        # Timestamp for this metric collection
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for stream_job_health
    op.create_index("idx_stream_job_health_job_id", "stream_job_health", ["stream_job_id"])
    op.create_index("idx_stream_job_health_collected_at", "stream_job_health", ["collected_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_stream_job_health_collected_at", table_name="stream_job_health")
    op.drop_index("idx_stream_job_health_job_id", table_name="stream_job_health")
    op.drop_index("idx_stream_jobs_scheduled_start", table_name="stream_jobs")
    op.drop_index("idx_stream_jobs_status", table_name="stream_jobs")
    op.drop_index("idx_stream_jobs_account_id", table_name="stream_jobs")
    op.drop_index("idx_stream_jobs_user_id", table_name="stream_jobs")
    
    # Drop tables
    op.drop_table("stream_job_health")
    op.drop_table("stream_jobs")
