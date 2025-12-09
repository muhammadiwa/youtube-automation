"""Payment gateway models migration.

Revision ID: 023
Revises: 022
Create Date: 2024-01-01 00:00:00.000000

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_gateway_configs table
    op.create_table(
        'payment_gateway_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('webhook_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('sandbox_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supported_currencies', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('supported_payment_methods', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('transaction_fee_percent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('fixed_fee', sa.Float(), nullable=False, server_default='0'),
        sa.Column('min_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('max_amount', sa.Float(), nullable=True),
        sa.Column('config_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider'),
    )
    op.create_index('ix_payment_gateway_configs_provider', 'payment_gateway_configs', ['provider'])
    op.create_index('ix_payment_gateway_configs_is_enabled', 'payment_gateway_configs', ['is_enabled'])

    # Create payment_transactions table
    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gateway_provider', sa.String(50), nullable=False),
        sa.Column('gateway_payment_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(100), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('gateway_response', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('previous_gateway', sa.String(50), nullable=True),
        sa.Column('checkout_url', sa.String(1000), nullable=True),
        sa.Column('success_url', sa.String(500), nullable=True),
        sa.Column('cancel_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payment_transactions_user_id', 'payment_transactions', ['user_id'])
    op.create_index('ix_payment_transactions_subscription_id', 'payment_transactions', ['subscription_id'])
    op.create_index('ix_payment_transactions_gateway_provider', 'payment_transactions', ['gateway_provider'])
    op.create_index('ix_payment_transactions_gateway_payment_id', 'payment_transactions', ['gateway_payment_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'])
    op.create_index('ix_payment_tx_user_status', 'payment_transactions', ['user_id', 'status'])
    op.create_index('ix_payment_tx_gateway_created', 'payment_transactions', ['gateway_provider', 'created_at'])

    # Create gateway_statistics table
    op.create_table(
        'gateway_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_volume', sa.Float(), nullable=False, server_default='0'),
        sa.Column('average_transaction', sa.Float(), nullable=False, server_default='0'),
        sa.Column('health_status', sa.String(50), nullable=False, server_default='healthy'),
        sa.Column('last_transaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transactions_24h', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate_24h', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider'),
    )
    op.create_index('ix_gateway_statistics_provider', 'gateway_statistics', ['provider'])


def downgrade() -> None:
    op.drop_table('gateway_statistics')
    op.drop_table('payment_transactions')
    op.drop_table('payment_gateway_configs')
