"""Moderation models migration.

Revision ID: 010
Revises: 009
Create Date: 2024-01-16

Creates tables for chat moderation: rules, action logs, messages, slow mode, and commands.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create moderation_rules table (Requirements: 12.1, 12.2)
    op.create_table(
        'moderation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('settings', postgresql.JSON(), nullable=True),
        sa.Column('caps_threshold_percent', sa.Integer(), nullable=True, default=70),
        sa.Column('min_message_length', sa.Integer(), nullable=True, default=5),
        sa.Column('action_type', sa.String(50), nullable=False, default='hide'),
        sa.Column('severity', sa.String(50), nullable=False, default='medium'),
        sa.Column('timeout_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('trigger_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_moderation_rules_account_id', 'moderation_rules', ['account_id'])
    op.create_index('ix_moderation_rules_rule_type', 'moderation_rules', ['rule_type'])

    # Create moderation_action_logs table (Requirements: 12.2, 12.5)
    op.create_table(
        'moderation_action_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, default='medium'),
        sa.Column('user_channel_id', sa.String(255), nullable=False),
        sa.Column('user_display_name', sa.String(255), nullable=True),
        sa.Column('message_id', sa.String(255), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('was_successful', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timeout_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('timeout_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['rule_id'], ['moderation_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['stream_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_moderation_action_logs_rule_id', 'moderation_action_logs', ['rule_id'])
    op.create_index('ix_moderation_action_logs_account_id', 'moderation_action_logs', ['account_id'])
    op.create_index('ix_moderation_action_logs_session_id', 'moderation_action_logs', ['session_id'])
    op.create_index('ix_moderation_action_logs_user_channel_id', 'moderation_action_logs', ['user_channel_id'])


    # Create chat_messages table (Requirements: 12.1)
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('youtube_message_id', sa.String(255), nullable=False, unique=True),
        sa.Column('youtube_live_chat_id', sa.String(255), nullable=False),
        sa.Column('author_channel_id', sa.String(255), nullable=False),
        sa.Column('author_display_name', sa.String(255), nullable=False),
        sa.Column('author_profile_image_url', sa.String(512), nullable=True),
        sa.Column('is_moderator', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_owner', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_member', sa.Boolean(), nullable=False, default=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False, default='text'),
        sa.Column('super_chat_amount', sa.Float(), nullable=True),
        sa.Column('super_chat_currency', sa.String(10), nullable=True),
        sa.Column('is_moderated', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('moderation_reason', sa.Text(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysis_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('violated_rules', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['stream_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_messages_account_id', 'chat_messages', ['account_id'])
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_youtube_message_id', 'chat_messages', ['youtube_message_id'])
    op.create_index('ix_chat_messages_author_channel_id', 'chat_messages', ['author_channel_id'])

    # Create slow_mode_configs table (Requirements: 12.3)
    op.create_table(
        'slow_mode_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('delay_seconds', sa.Integer(), nullable=False, default=30),
        sa.Column('auto_enable', sa.Boolean(), nullable=False, default=True),
        sa.Column('spam_threshold_per_minute', sa.Integer(), nullable=False, default=10),
        sa.Column('auto_disable_after_minutes', sa.Integer(), nullable=True, default=5),
        sa.Column('is_currently_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_disable_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_slow_mode_configs_account_id', 'slow_mode_configs', ['account_id'])

    # Create custom_commands table (Requirements: 12.4)
    op.create_table(
        'custom_commands',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('response_type', sa.String(50), nullable=False, default='text'),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('webhook_url', sa.String(512), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('moderator_only', sa.Boolean(), nullable=False, default=False),
        sa.Column('member_only', sa.Boolean(), nullable=False, default=False),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=False, default=5),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_custom_commands_account_id', 'custom_commands', ['account_id'])


def downgrade() -> None:
    op.drop_index('ix_custom_commands_account_id', table_name='custom_commands')
    op.drop_table('custom_commands')

    op.drop_index('ix_slow_mode_configs_account_id', table_name='slow_mode_configs')
    op.drop_table('slow_mode_configs')

    op.drop_index('ix_chat_messages_author_channel_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_youtube_message_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_account_id', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('ix_moderation_action_logs_user_channel_id', table_name='moderation_action_logs')
    op.drop_index('ix_moderation_action_logs_session_id', table_name='moderation_action_logs')
    op.drop_index('ix_moderation_action_logs_account_id', table_name='moderation_action_logs')
    op.drop_index('ix_moderation_action_logs_rule_id', table_name='moderation_action_logs')
    op.drop_table('moderation_action_logs')

    op.drop_index('ix_moderation_rules_rule_type', table_name='moderation_rules')
    op.drop_index('ix_moderation_rules_account_id', table_name='moderation_rules')
    op.drop_table('moderation_rules')
