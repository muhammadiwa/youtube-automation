"""Drop comment tables.

Revision ID: 049_drop_comment_tables
Revises: 048_add_broadcast_id
Create Date: 2026-01-04

This migration removes the comment-related tables as the feature has been removed.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '049_drop_comment_tables'
down_revision = '048_add_broadcast_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop comment-related tables."""
    # Drop comment_replies table first (has foreign key to comments)
    op.drop_index('ix_comment_replies_youtube_reply_id', table_name='comment_replies', if_exists=True)
    op.drop_index('ix_comment_replies_account_id', table_name='comment_replies', if_exists=True)
    op.drop_index('ix_comment_replies_comment_id', table_name='comment_replies', if_exists=True)
    op.drop_table('comment_replies', if_exists=True)
    
    # Drop comments table
    op.drop_index('ix_comments_requires_attention', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_sentiment', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_status', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_author_channel_id', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_youtube_parent_id', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_youtube_video_id', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_youtube_comment_id', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_video_id', table_name='comments', if_exists=True)
    op.drop_index('ix_comments_account_id', table_name='comments', if_exists=True)
    op.drop_table('comments', if_exists=True)
    
    # Drop auto_reply_rules table
    op.drop_index('ix_auto_reply_rules_account_id', table_name='auto_reply_rules', if_exists=True)
    op.drop_table('auto_reply_rules', if_exists=True)


def downgrade() -> None:
    """Recreate comment-related tables (not recommended)."""
    # Note: This downgrade is provided for completeness but the feature has been removed
    # If you need to restore this feature, consider creating a new migration instead
    pass
