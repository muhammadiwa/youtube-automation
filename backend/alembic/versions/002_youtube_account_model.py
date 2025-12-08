"""Add YouTube Account model.

Revision ID: 002
Revises: 001_initial_user_model
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001_initial_user_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'youtube_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_id', sa.String(255), nullable=False),
        sa.Column('channel_title', sa.String(255), nullable=False),
        sa.Column('thumbnail_url', sa.String(512), nullable=True),
        sa.Column('subscriber_count', sa.Integer(), nullable=False, default=0),
        sa.Column('video_count', sa.Integer(), nullable=False, default=0),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_monetized', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_live_streaming_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('strike_count', sa.Integer(), nullable=False, default=0),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('daily_quota_used', sa.Integer(), nullable=False, default=0),
        sa.Column('quota_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_youtube_accounts_user_id', 'youtube_accounts', ['user_id'])
    op.create_index('ix_youtube_accounts_channel_id', 'youtube_accounts', ['channel_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_youtube_accounts_channel_id', table_name='youtube_accounts')
    op.drop_index('ix_youtube_accounts_user_id', table_name='youtube_accounts')
    op.drop_table('youtube_accounts')
