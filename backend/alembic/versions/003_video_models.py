"""Video models migration.

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

Creates Video, MetadataVersion, and VideoTemplate tables.
Requirements: 3.4, 4.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video_templates table
    op.create_table(
        "video_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description_template", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("visibility", sa.String(50), nullable=False, server_default="private"),
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
        op.f("ix_video_templates_user_id"),
        "video_templates",
        ["user_id"],
        unique=False,
    )

    # Create videos table
    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("youtube_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("visibility", sa.String(50), nullable=False, server_default="private"),
        sa.Column("scheduled_publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dislike_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("upload_job_id", sa.String(255), nullable=True),
        sa.Column("upload_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("upload_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_upload_error", sa.Text(), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        op.f("ix_videos_account_id"),
        "videos",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_videos_youtube_id"),
        "videos",
        ["youtube_id"],
        unique=True,
    )

    # Create metadata_versions table
    op.create_table(
        "metadata_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("visibility", sa.String(50), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_metadata_versions_video_id"),
        "metadata_versions",
        ["video_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_metadata_versions_video_id"), table_name="metadata_versions")
    op.drop_table("metadata_versions")
    op.drop_index(op.f("ix_videos_youtube_id"), table_name="videos")
    op.drop_index(op.f("ix_videos_account_id"), table_name="videos")
    op.drop_table("videos")
    op.drop_index(op.f("ix_video_templates_user_id"), table_name="video_templates")
    op.drop_table("video_templates")
