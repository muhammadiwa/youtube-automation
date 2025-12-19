"""Add playlist tracking fields to stream_jobs

Revision ID: 046_playlist_tracking
Revises: 045_stream_jobs
Create Date: 2024-12-19

Requirements: 11.1, 11.5
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "046_playlist_tracking"
down_revision = "045_stream_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add playlist tracking columns to stream_jobs table."""
    # Add playlist tracking columns
    op.add_column(
        "stream_jobs",
        sa.Column("current_playlist_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "stream_jobs",
        sa.Column("total_playlist_items", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "stream_jobs",
        sa.Column("concat_file_path", sa.String(1024), nullable=True),
    )


def downgrade() -> None:
    """Remove playlist tracking columns from stream_jobs table."""
    op.drop_column("stream_jobs", "concat_file_path")
    op.drop_column("stream_jobs", "total_playlist_items")
    op.drop_column("stream_jobs", "current_playlist_index")
