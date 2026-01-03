"""Add youtube_broadcast_id and enable_chat_moderation to stream_jobs.

Revision ID: 048_add_broadcast_id
Revises: 047_add_stream_key
Create Date: 2025-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '048_add_broadcast_id'
down_revision = '047_add_stream_key'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add youtube_broadcast_id and enable_chat_moderation columns to stream_jobs."""
    # Add youtube_broadcast_id column (YouTube Live Event ID for chat moderation)
    op.add_column(
        'stream_jobs',
        sa.Column('youtube_broadcast_id', sa.String(255), nullable=True)
    )
    
    # Add index for broadcast_id lookups
    op.create_index(
        'ix_stream_jobs_youtube_broadcast_id',
        'stream_jobs',
        ['youtube_broadcast_id']
    )
    
    # Add enable_chat_moderation column with default True
    op.add_column(
        'stream_jobs',
        sa.Column(
            'enable_chat_moderation',
            sa.Boolean(),
            nullable=False,
            server_default='true'
        )
    )


def downgrade() -> None:
    """Remove youtube_broadcast_id and enable_chat_moderation columns."""
    op.drop_column('stream_jobs', 'enable_chat_moderation')
    op.drop_index('ix_stream_jobs_youtube_broadcast_id', table_name='stream_jobs')
    op.drop_column('stream_jobs', 'youtube_broadcast_id')
