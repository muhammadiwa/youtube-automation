"""add soft delete to videos

Revision ID: 050_soft_delete
Revises: 4e81339d4822
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '050_soft_delete'
down_revision = '4e81339d4822'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add deleted_at column to videos table for soft delete functionality.
    
    This enables:
    - Preserving video records for billing/audit purposes
    - Keeping VideoUsageLog data intact for accurate quota tracking
    - Hard deleting files from storage while soft deleting database records
    """
    # Add deleted_at column
    op.add_column('videos', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add index for better query performance
    op.create_index(
        'ix_videos_deleted_at',
        'videos',
        ['deleted_at'],
        unique=False
    )
    
    # Add comment to column
    op.execute("""
        COMMENT ON COLUMN videos.deleted_at IS 
        'Timestamp when video was soft deleted. NULL means video is active. 
        Files are hard deleted from storage but record preserved for billing.'
    """)


def downgrade() -> None:
    """Remove soft delete functionality."""
    # Drop index
    op.drop_index('ix_videos_deleted_at', table_name='videos')
    
    # Drop column
    op.drop_column('videos', 'deleted_at')
