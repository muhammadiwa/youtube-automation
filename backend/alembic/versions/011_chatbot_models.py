"""Add chatbot models

Revision ID: 011
Revises: 010
Create Date: 2024-01-01 00:00:00.000000

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chatbot_configs table
    op.create_table(
        'chatbot_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_name', sa.String(100), nullable=False, server_default='StreamBot'),
        sa.Column('bot_prefix', sa.String(50), nullable=False, server_default='[BOT]'),
        sa.Column('personality', sa.String(50), nullable=False, server_default='friendly'),
        sa.Column('response_style', sa.String(50), nullable=False, server_default='concise'),
        sa.Column('custom_personality_prompt', sa.Text(), nullable=True),
        sa.Column('max_response_length', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('response_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('use_emojis', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('response_delay_ms', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('content_filter_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('blocked_topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('blocked_keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('takeover_command', sa.String(50), nullable=False, server_default='!botpause'),
        sa.Column('resume_command', sa.String(50), nullable=False, server_default='!botresume'),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_by', sa.String(255), nullable=True),
        sa.Column('total_responses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_declined', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id')
    )
    op.create_index('ix_chatbot_configs_account_id', 'chatbot_configs', ['account_id'])


    # Create chatbot_triggers table
    op.create_table(
        'chatbot_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False, server_default='keyword'),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('custom_response_prompt', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['config_id'], ['chatbot_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chatbot_triggers_config_id', 'chatbot_triggers', ['config_id'])

    # Create chatbot_interaction_logs table
    op.create_table(
        'chatbot_interaction_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_channel_id', sa.String(255), nullable=False),
        sa.Column('user_display_name', sa.String(255), nullable=False),
        sa.Column('input_message_id', sa.String(255), nullable=False),
        sa.Column('input_content', sa.Text(), nullable=False),
        sa.Column('was_responded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('response_content', sa.Text(), nullable=True),
        sa.Column('response_message_id', sa.String(255), nullable=True),
        sa.Column('was_declined', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('decline_reason', sa.String(255), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('matched_trigger_type', sa.String(50), nullable=True),
        sa.Column('matched_pattern', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['config_id'], ['chatbot_configs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['stream_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['trigger_id'], ['chatbot_triggers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chatbot_interaction_logs_config_id', 'chatbot_interaction_logs', ['config_id'])
    op.create_index('ix_chatbot_interaction_logs_session_id', 'chatbot_interaction_logs', ['session_id'])
    op.create_index('ix_chatbot_interaction_logs_user_channel_id', 'chatbot_interaction_logs', ['user_channel_id'])


def downgrade() -> None:
    op.drop_table('chatbot_interaction_logs')
    op.drop_table('chatbot_triggers')
    op.drop_table('chatbot_configs')
