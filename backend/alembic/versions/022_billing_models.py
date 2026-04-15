"""Billing models migration.

Revision ID: 022
Revises: 020
Create Date: 2024-01-01 00:00:00.000000

Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('custom_limits', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('stripe_subscription_id'),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_plan_tier', 'subscriptions', ['plan_tier'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])

    # Create usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_usage_records_user_id', 'usage_records', ['user_id'])
    op.create_index('ix_usage_records_subscription_id', 'usage_records', ['subscription_id'])
    op.create_index('ix_usage_records_resource_type', 'usage_records', ['resource_type'])
    op.create_index('ix_usage_records_billing_period_start', 'usage_records', ['billing_period_start'])
    op.create_index('ix_usage_user_resource_period', 'usage_records', ['user_id', 'resource_type', 'billing_period_start'])

    # Create usage_aggregates table
    op.create_table(
        'usage_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('total_used', sa.Float(), nullable=False, server_default='0'),
        sa.Column('limit_value', sa.Float(), nullable=False),
        sa.Column('warning_50_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warning_75_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warning_90_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_usage_aggregates_user_id', 'usage_aggregates', ['user_id'])
    op.create_index('ix_usage_aggregates_subscription_id', 'usage_aggregates', ['subscription_id'])
    op.create_index('ix_usage_aggregates_resource_type', 'usage_aggregates', ['resource_type'])
    op.create_index('ix_usage_aggregates_billing_period_start', 'usage_aggregates', ['billing_period_start'])
    op.create_index('ix_usage_agg_user_resource_period', 'usage_aggregates', ['user_id', 'resource_type', 'billing_period_start'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('amount_paid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('amount_due', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('line_items', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('payment_intent_id', sa.String(255), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_pdf_url', sa.String(500), nullable=True),
        sa.Column('hosted_invoice_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_invoice_id'),
        sa.UniqueConstraint('invoice_number'),
    )
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_subscription_id', 'invoices', ['subscription_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])
    op.create_index('ix_invoice_user_period', 'invoices', ['user_id', 'period_start'])

    # Create payment_methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(255), nullable=False),
        sa.Column('card_brand', sa.String(50), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_exp_month', sa.Integer(), nullable=True),
        sa.Column('card_exp_year', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_method_id'),
    )
    op.create_index('ix_payment_methods_user_id', 'payment_methods', ['user_id'])


def downgrade() -> None:
    op.drop_table('payment_methods')
    op.drop_table('invoices')
    op.drop_table('usage_aggregates')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
