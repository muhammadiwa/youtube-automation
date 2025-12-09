"""Integration models migration.

Revision ID: 024
Revises: 023
Create Date: 2024-01-01 00:00:00.000000

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('allowed_ips', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('ix_api_key_user_active', 'api_keys', ['user_id', 'is_active'])

    # Create api_key_usage table for rate limiting
    op.create_table(
        'api_key_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_type', sa.String(20), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_key_usage_api_key_id', 'api_key_usage', ['api_key_id'])
    op.create_index('ix_api_key_usage_window_start', 'api_key_usage', ['window_start'])
    op.create_index('ix_api_key_usage_key_window', 'api_key_usage', ['api_key_id', 'window_start', 'window_type'])

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('secret', sa.String(64), nullable=False),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('custom_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_delivery_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhooks_user_id', 'webhooks', ['user_id'])
    op.create_index('ix_webhook_user_active', 'webhooks', ['user_id', 'is_active'])

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_index('ix_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'])
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('ix_webhook_delivery_status_retry', 'webhook_deliveries', ['status', 'next_retry_at'])
    op.create_index('ix_webhook_delivery_webhook_created', 'webhook_deliveries', ['webhook_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
    op.drop_table('api_key_usage')
    op.drop_table('api_keys')
