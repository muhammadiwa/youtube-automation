"""refactor_video_library_first_approach

Revision ID: 4e81339d4822
Revises: 046_playlist_tracking
Create Date: 2025-12-29 12:13:25.071334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e81339d4822'
down_revision: Union[str, None] = '046_playlist_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Refactor Video model for library-first approach."""
    
    # ===== Step 1: Add new columns to videos table =====
    
    # Add user_id (nullable first for migration)
    op.add_column('videos', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_videos_user_id', 'videos', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_videos_user_id', 'videos', ['user_id'])
    
    # Add file metadata fields
    op.add_column('videos', sa.Column('format', sa.String(50), nullable=True))
    op.add_column('videos', sa.Column('resolution', sa.String(50), nullable=True))
    op.add_column('videos', sa.Column('frame_rate', sa.Float(), nullable=True))
    op.add_column('videos', sa.Column('bitrate', sa.Integer(), nullable=True))
    op.add_column('videos', sa.Column('codec', sa.String(50), nullable=True))
    
    # Add library organization fields
    op.add_column('videos', sa.Column('folder_id', sa.UUID(), nullable=True))
    op.add_column('videos', sa.Column('is_favorite', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('videos', sa.Column('custom_tags', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('videos', sa.Column('notes', sa.Text(), nullable=True))
    
    # Add YouTube upload status fields
    op.add_column('videos', sa.Column('youtube_status', sa.String(50), nullable=True))
    op.add_column('videos', sa.Column('youtube_uploaded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('videos', sa.Column('youtube_url', sa.String(512), nullable=True))
    
    # Add YouTube stats fields
    op.add_column('videos', sa.Column('watch_time_minutes', sa.Integer(), server_default='0', nullable=False))
    
    # Add streaming usage fields
    op.add_column('videos', sa.Column('is_used_for_streaming', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('videos', sa.Column('streaming_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('videos', sa.Column('last_streamed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('videos', sa.Column('total_streaming_duration', sa.Integer(), server_default='0', nullable=False))
    
    # Add last_accessed_at for analytics
    op.add_column('videos', sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True))
    
    # ===== Step 2: Create video_folders table =====
    
    op.create_table(
        'video_folders',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['video_folders.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'parent_id', 'name', name='uq_video_folders_user_parent_name')
    )
    
    op.create_index('ix_video_folders_user_id', 'video_folders', ['user_id'])
    op.create_index('ix_video_folders_parent_id', 'video_folders', ['parent_id'])
    
    # Add foreign key for folder_id in videos table
    op.create_foreign_key('fk_videos_folder_id', 'videos', 'video_folders', ['folder_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_videos_folder_id', 'videos', ['folder_id'])
    
    # ===== Step 3: Create video_usage_logs table =====
    
    op.create_table(
        'video_usage_logs',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('video_id', sa.UUID(), nullable=False),
        sa.Column('usage_type', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_video_usage_logs_video_id', 'video_usage_logs', ['video_id'])
    op.create_index('ix_video_usage_logs_usage_type', 'video_usage_logs', ['usage_type'])
    
    # ===== Step 4: Add additional indexes for performance =====
    
    op.create_index('ix_videos_status', 'videos', ['status'])
    op.create_index('ix_videos_is_favorite', 'videos', ['is_favorite'])
    op.create_index('ix_videos_created_at', 'videos', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('ix_videos_user_status', 'videos', ['user_id', 'status'])
    op.create_index('ix_videos_user_folder', 'videos', ['user_id', 'folder_id'])
    
    # Full-text search indexes
    op.execute("""
        CREATE INDEX ix_videos_title_search ON videos 
        USING gin(to_tsvector('english', title))
    """)
    op.execute("""
        CREATE INDEX ix_videos_description_search ON videos 
        USING gin(to_tsvector('english', COALESCE(description, '')))
    """)
    
    # ===== Step 5: Migrate existing data =====
    
    # Set user_id from account relationship
    op.execute("""
        UPDATE videos v
        SET user_id = ya.user_id
        FROM youtube_accounts ya
        WHERE v.account_id = ya.id
    """)
    
    # Set youtube_status based on youtube_id
    op.execute("""
        UPDATE videos
        SET youtube_status = CASE
            WHEN youtube_id IS NOT NULL THEN 'published'
            ELSE NULL
        END
    """)
    
    # Set youtube_url based on youtube_id
    op.execute("""
        UPDATE videos
        SET youtube_url = 'https://www.youtube.com/watch?v=' || youtube_id
        WHERE youtube_id IS NOT NULL
    """)
    
    # Set last_accessed_at to created_at for existing videos
    op.execute("""
        UPDATE videos
        SET last_accessed_at = created_at
        WHERE last_accessed_at IS NULL
    """)
    
    # ===== Step 6: Make account_id nullable =====
    
    op.alter_column('videos', 'account_id', nullable=True)
    
    # ===== Step 7: Make user_id required =====
    
    op.alter_column('videos', 'user_id', nullable=False)


def downgrade() -> None:
    """Rollback library-first refactor."""
    
    # Drop indexes
    op.drop_index('ix_videos_user_folder', 'videos')
    op.drop_index('ix_videos_user_status', 'videos')
    op.drop_index('ix_videos_created_at', 'videos')
    op.drop_index('ix_videos_is_favorite', 'videos')
    op.drop_index('ix_videos_status', 'videos')
    op.execute('DROP INDEX IF EXISTS ix_videos_description_search')
    op.execute('DROP INDEX IF EXISTS ix_videos_title_search')
    
    # Drop video_usage_logs table
    op.drop_index('ix_video_usage_logs_usage_type', 'video_usage_logs')
    op.drop_index('ix_video_usage_logs_video_id', 'video_usage_logs')
    op.drop_table('video_usage_logs')
    
    # Drop video_folders table
    op.drop_constraint('fk_videos_folder_id', 'videos', type_='foreignkey')
    op.drop_index('ix_videos_folder_id', 'videos')
    op.drop_index('ix_video_folders_parent_id', 'video_folders')
    op.drop_index('ix_video_folders_user_id', 'video_folders')
    op.drop_table('video_folders')
    
    # Drop new columns from videos table
    op.drop_column('videos', 'last_accessed_at')
    op.drop_column('videos', 'total_streaming_duration')
    op.drop_column('videos', 'last_streamed_at')
    op.drop_column('videos', 'streaming_count')
    op.drop_column('videos', 'is_used_for_streaming')
    op.drop_column('videos', 'watch_time_minutes')
    op.drop_column('videos', 'youtube_url')
    op.drop_column('videos', 'youtube_uploaded_at')
    op.drop_column('videos', 'youtube_status')
    op.drop_column('videos', 'notes')
    op.drop_column('videos', 'custom_tags')
    op.drop_column('videos', 'is_favorite')
    op.drop_column('videos', 'folder_id')
    op.drop_column('videos', 'codec')
    op.drop_column('videos', 'bitrate')
    op.drop_column('videos', 'frame_rate')
    op.drop_column('videos', 'resolution')
    op.drop_column('videos', 'format')
    
    # Make account_id required again
    op.alter_column('videos', 'account_id', nullable=False)
    
    # Drop user_id
    op.drop_constraint('fk_videos_user_id', 'videos', type_='foreignkey')
    op.drop_index('ix_videos_user_id', 'videos')
    op.drop_column('videos', 'user_id')
