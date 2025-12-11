"""Seed default payment gateways and admin user.

Revision ID: 027
Revises: 026
Create Date: 2024-12-11

Requirements: 30.1 - Payment gateway configuration, 1.1 - Admin access
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import json

# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None

# Default payment gateways (matching payment_gateway_configs table structure)
# Note: JSON columns should receive Python objects, not json.dumps() strings
# Note: Gateways are disabled by default - enable after configuring credentials
DEFAULT_GATEWAYS = [
    {
        "id": str(uuid.uuid4()),
        "provider": "stripe",
        "display_name": "Stripe",
        "is_enabled": False,  # Disabled until credentials are configured
        "is_default": False,
        "api_key_encrypted": None,
        "api_secret_encrypted": None,
        "webhook_secret_encrypted": None,
        "sandbox_mode": True,
        "supported_currencies": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD", "IDR"],
        "supported_payment_methods": ["card", "bank_transfer", "wallet"],
        "transaction_fee_percent": 2.9,
        "fixed_fee": 0.30,
        "min_amount": 0.50,
        "max_amount": 999999.99,
        "config_metadata": {"api_version": "2023-10-16"},
    },
    {
        "id": str(uuid.uuid4()),
        "provider": "paypal",
        "display_name": "PayPal",
        "is_enabled": False,
        "is_default": False,
        "api_key_encrypted": None,
        "api_secret_encrypted": None,
        "webhook_secret_encrypted": None,
        "sandbox_mode": True,
        "supported_currencies": ["USD", "EUR", "GBP", "AUD", "CAD"],
        "supported_payment_methods": ["paypal", "card"],
        "transaction_fee_percent": 3.49,
        "fixed_fee": 0.49,
        "min_amount": 1.00,
        "max_amount": 999999.99,
        "config_metadata": {"environment": "sandbox"},
    },
    {
        "id": str(uuid.uuid4()),
        "provider": "midtrans",
        "display_name": "Midtrans",
        "is_enabled": False,
        "is_default": False,
        "api_key_encrypted": None,
        "api_secret_encrypted": None,
        "webhook_secret_encrypted": None,
        "sandbox_mode": True,
        "supported_currencies": ["IDR"],
        "supported_payment_methods": ["bank_transfer", "e_wallet", "card", "qris"],
        "transaction_fee_percent": 2.9,
        "fixed_fee": 0,
        "min_amount": 10000,
        "max_amount": 999999999,
        "config_metadata": {"enable_3ds": True},
    },
    {
        "id": str(uuid.uuid4()),
        "provider": "xendit",
        "display_name": "Xendit",
        "is_enabled": False,
        "is_default": False,
        "api_key_encrypted": None,
        "api_secret_encrypted": None,
        "webhook_secret_encrypted": None,
        "sandbox_mode": True,
        "supported_currencies": ["IDR", "PHP", "VND", "THB", "MYR"],
        "supported_payment_methods": ["bank_transfer", "e_wallet", "card", "retail"],
        "transaction_fee_percent": 2.5,
        "fixed_fee": 0,
        "min_amount": 10000,
        "max_amount": 999999999,
        "config_metadata": {},
    },
]

# Default admin user (password: Admin@123456)
# Password hash generated with bcrypt
# Note: Using actual users table structure from migration 001
DEFAULT_ADMIN = {
    "id": str(uuid.uuid4()),
    "email": "admin@youtubeautomation.com",
    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWWQIqjSXHy",  # Admin@123456
    "name": "System Administrator",
    "is_active": True,
    "is_2fa_enabled": False,
}


def upgrade() -> None:
    """Insert default payment gateways and admin user."""
    
    # Insert default payment gateways into payment_gateway_configs table
    gateways_table = sa.table(
        'payment_gateway_configs',
        sa.column('id', postgresql.UUID),
        sa.column('provider', sa.String),
        sa.column('display_name', sa.String),
        sa.column('is_enabled', sa.Boolean),
        sa.column('is_default', sa.Boolean),
        sa.column('api_key_encrypted', sa.Text),
        sa.column('api_secret_encrypted', sa.Text),
        sa.column('webhook_secret_encrypted', sa.Text),
        sa.column('sandbox_mode', sa.Boolean),
        sa.column('supported_currencies', postgresql.JSON),
        sa.column('supported_payment_methods', postgresql.JSON),
        sa.column('transaction_fee_percent', sa.Float),
        sa.column('fixed_fee', sa.Float),
        sa.column('min_amount', sa.Float),
        sa.column('max_amount', sa.Float),
        sa.column('config_metadata', postgresql.JSON),
    )
    
    op.bulk_insert(gateways_table, DEFAULT_GATEWAYS)
    
    # Insert default admin user (matching users table structure from migration 001)
    users_table = sa.table(
        'users',
        sa.column('id', postgresql.UUID),
        sa.column('email', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('name', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_2fa_enabled', sa.Boolean),
    )
    
    op.bulk_insert(users_table, [DEFAULT_ADMIN])


def downgrade() -> None:
    """Remove default payment gateways and admin user."""
    # Remove default gateways
    op.execute("DELETE FROM payment_gateway_configs WHERE provider IN ('stripe', 'paypal', 'midtrans', 'xendit')")
    
    # Remove default admin
    op.execute("DELETE FROM users WHERE email = 'admin@youtubeautomation.com'")
