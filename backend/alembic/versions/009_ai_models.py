"""AI models migration.

Revision ID: 009
Revises: 008
Create Date: 2024-01-15

Creates tables for AI feedback, user preferences, and thumbnail library.
Requirements: 14.5, 15.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_feedback table
    op.create_table(
        'ai_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('suggestion_type', sa.String(50), nullable=False),
        sa.Column('suggestion_id', sa.String(100), nullable=False),
        sa.Column('was_selected', sa.Boolean(), nullable=False, default=False),
        sa.Column('user_modification', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_feedback_user_id', 'ai_feedback', ['user_id'])

    # Create ai_user_preferences table
    op.create_table(
        'ai_user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_title_style', sa.String(50), nullable=True),
        sa.Column('preferred_description_length', sa.Integer(), nullable=True),
        sa.Column('preferred_tag_count', sa.Integer(), nullable=True),
        sa.Column('preferred_thumbnail_style', sa.String(50), nullable=True),
        sa.Column('brand_colors', postgresql.JSON(), nullable=True),
        sa.Column('brand_keywords', postgresql.JSON(), nullable=True),
        sa.Column('avoid_keywords', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_ai_user_preferences_user_id', 'ai_user_preferences', ['user_id'])

    # Create thumbnail_library table
    op.create_table(
        'thumbnail_library',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('style', sa.String(50), nullable=True),
        sa.Column('width', sa.Integer(), nullable=False, default=1280),
        sa.Column('height', sa.Integer(), nullable=False, default=720),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('elements', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('is_generated', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_thumbnail_library_user_id', 'thumbnail_library', ['user_id'])
    op.create_index('ix_thumbnail_library_video_id', 'thumbnail_library', ['video_id'])


def downgrade() -> None:
    op.drop_index('ix_thumbnail_library_video_id', table_name='thumbnail_library')
    op.drop_index('ix_thumbnail_library_user_id', table_name='thumbnail_library')
    op.drop_table('thumbnail_library')

    op.drop_index('ix_ai_user_preferences_user_id', table_name='ai_user_preferences')
    op.drop_table('ai_user_preferences')

    op.drop_index('ix_ai_feedback_user_id', table_name='ai_feedback')
    op.drop_table('ai_feedback')
