"""Notification models migration.

Revision ID: 020
Revises: 019
Create Date: 2024-01-01 00:00:00.000000

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_preferences table (Requirements: 23.2)
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('slack_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('telegram_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_address', sa.String(255), nullable=True),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('slack_webhook_url', sa.String(500), nullable=True),
        sa.Column('telegram_chat_id', sa.String(100), nullable=True),
        sa.Column('batch_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('batch_interval_seconds', sa.Integer(), nullable=False, default=300),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiet_hours_start', sa.String(5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
    op.create_index('ix_notification_preferences_account_id', 'notification_preferences', ['account_id'])
    op.create_index('ix_notification_preferences_event_type', 'notification_preferences', ['event_type'])
    op.create_index('ix_notification_pref_user_event', 'notification_preferences', ['user_id', 'event_type'])
    op.create_index('ix_notification_pref_user_account', 'notification_preferences', ['user_id', 'account_id'])

    # Create notification_logs table (Requirements: 23.1, 23.5)
    op.create_table(
        'notification_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('recipient', sa.String(500), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, default='normal'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_time_seconds', sa.Float(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, default=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('response_time_seconds', sa.Float(), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_batched', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_escalated', sa.Boolean(), nullable=False, default=False),
        sa.Column('escalation_level', sa.Integer(), nullable=False, default=0),
        sa.Column('parent_notification_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_logs_user_id', 'notification_logs', ['user_id'])
    op.create_index('ix_notification_logs_account_id', 'notification_logs', ['account_id'])
    op.create_index('ix_notification_logs_event_type', 'notification_logs', ['event_type'])
    op.create_index('ix_notification_logs_channel', 'notification_logs', ['channel'])
    op.create_index('ix_notification_logs_status', 'notification_logs', ['status'])
    op.create_index('ix_notification_logs_batch_id', 'notification_logs', ['batch_id'])
    op.create_index('ix_notification_log_user_status', 'notification_logs', ['user_id', 'status'])
    op.create_index('ix_notification_log_created', 'notification_logs', ['created_at'])
    op.create_index('ix_notification_log_event', 'notification_logs', ['event_type', 'created_at'])

    # Create notification_batches table (Requirements: 23.3)
    op.create_table(
        'notification_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_count', sa.Integer(), nullable=False, default=0),
        sa.Column('priority', sa.String(20), nullable=False, default='normal'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_batches_user_id', 'notification_batches', ['user_id'])

    # Create escalation_rules table (Requirements: 23.4)
    op.create_table(
        'escalation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('event_types', postgresql.JSON(), nullable=False, default=[]),
        sa.Column('escalation_levels', postgresql.JSON(), nullable=False, default=[]),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_escalation_rules_user_id', 'escalation_rules', ['user_id'])


def downgrade() -> None:
    op.drop_table('escalation_rules')
    op.drop_table('notification_batches')
    op.drop_table('notification_logs')
    op.drop_table('notification_preferences')
