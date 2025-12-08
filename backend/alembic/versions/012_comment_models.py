"""Comment models migration.

Revision ID: 012
Revises: 011
Create Date: 2024-01-17

Creates tables for comment management: comments, auto_reply_rules, comment_replies.
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create auto_reply_rules table first (Requirements: 13.4)
    # This needs to be created before comments due to foreign key
    op.create_table(
        'auto_reply_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(50), nullable=False, default='keyword'),
        sa.Column('trigger_keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('trigger_pattern', sa.Text(), nullable=True),
        sa.Column('trigger_sentiment', sa.String(50), nullable=True),
        sa.Column('case_sensitive', sa.Boolean(), nullable=False, default=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('response_delay_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('max_replies_per_video', sa.Integer(), nullable=True),
        sa.Column('max_replies_per_day', sa.Integer(), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replies_today', sa.Integer(), nullable=False, default=0),
        sa.Column('replies_today_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auto_reply_rules_account_id', 'auto_reply_rules', ['account_id'])

    # Create comments table (Requirements: 13.1, 13.3)
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('youtube_comment_id', sa.String(255), nullable=False, unique=True),
        sa.Column('youtube_video_id', sa.String(255), nullable=False),
        sa.Column('youtube_parent_id', sa.String(255), nullable=True),
        sa.Column('author_channel_id', sa.String(255), nullable=False),
        sa.Column('author_display_name', sa.String(255), nullable=False),
        sa.Column('author_profile_image_url', sa.String(512), nullable=True),
        sa.Column('text_original', sa.Text(), nullable=False),
        sa.Column('text_display', sa.Text(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, default=0),
        sa.Column('reply_count', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True),
        sa.Column('can_reply', sa.Boolean(), nullable=False, default=True),
        # Sentiment analysis fields (Requirements: 13.3)
        sa.Column('sentiment', sa.String(50), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('requires_attention', sa.Boolean(), nullable=False, default=False),
        sa.Column('sentiment_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        # Auto-reply tracking (Requirements: 13.4)
        sa.Column('auto_replied', sa.Boolean(), nullable=False, default=False),
        sa.Column('auto_reply_rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at_youtube', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['auto_reply_rule_id'], ['auto_reply_rules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comments_account_id', 'comments', ['account_id'])
    op.create_index('ix_comments_video_id', 'comments', ['video_id'])
    op.create_index('ix_comments_youtube_comment_id', 'comments', ['youtube_comment_id'])
    op.create_index('ix_comments_youtube_video_id', 'comments', ['youtube_video_id'])
    op.create_index('ix_comments_youtube_parent_id', 'comments', ['youtube_parent_id'])
    op.create_index('ix_comments_author_channel_id', 'comments', ['author_channel_id'])
    op.create_index('ix_comments_status', 'comments', ['status'])
    op.create_index('ix_comments_sentiment', 'comments', ['sentiment'])
    op.create_index('ix_comments_requires_attention', 'comments', ['requires_attention'])

    # Create comment_replies table (Requirements: 13.2)
    op.create_table(
        'comment_replies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('youtube_reply_id', sa.String(255), nullable=True, unique=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_auto_reply', sa.Boolean(), nullable=False, default=False),
        sa.Column('auto_reply_rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['auto_reply_rule_id'], ['auto_reply_rules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comment_replies_comment_id', 'comment_replies', ['comment_id'])
    op.create_index('ix_comment_replies_account_id', 'comment_replies', ['account_id'])
    op.create_index('ix_comment_replies_youtube_reply_id', 'comment_replies', ['youtube_reply_id'])


def downgrade() -> None:
    op.drop_index('ix_comment_replies_youtube_reply_id', table_name='comment_replies')
    op.drop_index('ix_comment_replies_account_id', table_name='comment_replies')
    op.drop_index('ix_comment_replies_comment_id', table_name='comment_replies')
    op.drop_table('comment_replies')

    op.drop_index('ix_comments_requires_attention', table_name='comments')
    op.drop_index('ix_comments_sentiment', table_name='comments')
    op.drop_index('ix_comments_status', table_name='comments')
    op.drop_index('ix_comments_author_channel_id', table_name='comments')
    op.drop_index('ix_comments_youtube_parent_id', table_name='comments')
    op.drop_index('ix_comments_youtube_video_id', table_name='comments')
    op.drop_index('ix_comments_youtube_comment_id', table_name='comments')
    op.drop_index('ix_comments_video_id', table_name='comments')
    op.drop_index('ix_comments_account_id', table_name='comments')
    op.drop_table('comments')

    op.drop_index('ix_auto_reply_rules_account_id', table_name='auto_reply_rules')
    op.drop_table('auto_reply_rules')
