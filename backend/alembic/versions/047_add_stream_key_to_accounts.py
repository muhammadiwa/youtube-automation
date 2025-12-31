"""Add stream key fields to youtube_accounts table.

Revision ID: 047_add_stream_key
Revises: 4e81339d4822
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '047_add_stream_key'
down_revision = '4e81339d4822'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add stream_key, rtmp_url, and default_stream_id columns to youtube_accounts."""
    # Add stream_key column (encrypted, nullable)
    op.add_column(
        'youtube_accounts',
        sa.Column('stream_key', sa.Text(), nullable=True)
    )
    
    # Add rtmp_url column with default value
    op.add_column(
        'youtube_accounts',
        sa.Column(
            'rtmp_url',
            sa.String(512),
            nullable=True,
            server_default='rtmp://a.rtmp.youtube.com/live2'
        )
    )
    
    # Add default_stream_id column (YouTube liveStream ID)
    op.add_column(
        'youtube_accounts',
        sa.Column('default_stream_id', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    """Remove stream_key, rtmp_url, and default_stream_id columns."""
    op.drop_column('youtube_accounts', 'default_stream_id')
    op.drop_column('youtube_accounts', 'rtmp_url')
    op.drop_column('youtube_accounts', 'stream_key')
