"""Add playlist models for stream looping

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stream_playlists table
    op.create_table(
        'stream_playlists',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('live_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, server_default='Default Playlist'),
        sa.Column('loop_mode', sa.String(50), nullable=False, server_default='none'),
        sa.Column('loop_count', sa.Integer(), nullable=True),
        sa.Column('current_loop', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('default_transition', sa.String(50), nullable=False, server_default='cut'),
        sa.Column('default_transition_duration_ms', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('current_item_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('total_plays', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_skips', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['live_event_id'], ['live_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('live_event_id')
    )
    op.create_index('ix_stream_playlists_live_event_id', 'stream_playlists', ['live_event_id'])

    # Create playlist_items table
    op.create_table(
        'playlist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('playlist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('video_url', sa.String(1024), nullable=True),
        sa.Column('video_title', sa.String(255), nullable=False),
        sa.Column('video_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('transition_type', sa.String(50), nullable=False, server_default='cut'),
        sa.Column('transition_duration_ms', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('start_offset_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('end_offset_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('play_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_played_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['playlist_id'], ['stream_playlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_playlist_items_playlist_id', 'playlist_items', ['playlist_id'])
    op.create_index('ix_playlist_items_position', 'playlist_items', ['position'])


def downgrade() -> None:
    op.drop_index('ix_playlist_items_position', table_name='playlist_items')
    op.drop_index('ix_playlist_items_playlist_id', table_name='playlist_items')
    op.drop_table('playlist_items')
    op.drop_index('ix_stream_playlists_live_event_id', table_name='stream_playlists')
    op.drop_table('stream_playlists')
