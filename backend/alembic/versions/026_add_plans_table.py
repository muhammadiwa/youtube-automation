"""Add plans table for subscription plans.

Revision ID: 026
Revises: 025
Create Date: 2024-12-10

Requirements: 28.1 - Plan tiers with feature limits
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import json

# revision identifiers, used by Alembic.
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None

# Default plans data
DEFAULT_PLANS = [
    {
        "id": str(uuid.uuid4()),
        "slug": "free",
        "name": "Free",
        "description": "Perfect for getting started with YouTube automation",
        "price_monthly": 0,
        "price_yearly": 0,
        "currency": "USD",
        "max_accounts": 1,
        "max_videos_per_month": 5,
        "max_streams_per_month": 0,
        "max_storage_gb": 1,
        "max_bandwidth_gb": 5,
        "ai_generations_per_month": 0,
        "api_calls_per_month": 100,
        "encoding_minutes_per_month": 30,
        "concurrent_streams": 0,
        "features": json.dumps(["basic_upload", "basic_analytics"]),
        "display_features": json.dumps([
            {"name": "1 YouTube Account", "included": True},
            {"name": "5 Videos/month", "included": True},
            {"name": "Basic Analytics", "included": True},
            {"name": "AI Features", "included": False},
            {"name": "Live Streaming", "included": False},
        ]),
        "is_active": True,
        "is_popular": False,
        "sort_order": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "basic",
        "name": "Basic",
        "description": "Great for content creators who want more features",
        "price_monthly": 999,
        "price_yearly": 9999,
        "currency": "USD",
        "max_accounts": 3,
        "max_videos_per_month": 50,
        "max_streams_per_month": 5,
        "max_storage_gb": 10,
        "max_bandwidth_gb": 50,
        "ai_generations_per_month": 100,
        "api_calls_per_month": 1000,
        "encoding_minutes_per_month": 120,
        "concurrent_streams": 1,
        "features": json.dumps(["basic_upload", "advanced_analytics", "ai_titles", "ai_descriptions", "live_streaming"]),
        "display_features": json.dumps([
            {"name": "3 YouTube Accounts", "included": True},
            {"name": "50 Videos/month", "included": True},
            {"name": "Advanced Analytics", "included": True},
            {"name": "AI Features (100/month)", "included": True},
            {"name": "Live Streaming (5/month)", "included": True},
        ]),
        "is_active": True,
        "is_popular": False,
        "sort_order": 1,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "pro",
        "name": "Pro",
        "description": "For professional creators and small teams",
        "price_monthly": 2999,
        "price_yearly": 29999,
        "currency": "USD",
        "max_accounts": 10,
        "max_videos_per_month": -1,
        "max_streams_per_month": -1,
        "max_storage_gb": 100,
        "max_bandwidth_gb": 500,
        "ai_generations_per_month": 500,
        "api_calls_per_month": 10000,
        "encoding_minutes_per_month": 500,
        "concurrent_streams": 3,
        "features": json.dumps(["basic_upload", "advanced_analytics", "ai_titles", "ai_descriptions", "ai_thumbnails", "live_streaming", "simulcast", "api_access"]),
        "display_features": json.dumps([
            {"name": "10 YouTube Accounts", "included": True},
            {"name": "Unlimited Videos", "included": True},
            {"name": "Full Analytics Suite", "included": True},
            {"name": "AI Features (500/month)", "included": True},
            {"name": "Unlimited Streaming", "included": True},
        ]),
        "is_active": True,
        "is_popular": True,
        "sort_order": 2,
    },
    {
        "id": str(uuid.uuid4()),
        "slug": "enterprise",
        "name": "Enterprise",
        "description": "For large teams and agencies with custom needs",
        "price_monthly": 9999,
        "price_yearly": 99999,
        "currency": "USD",
        "max_accounts": -1,
        "max_videos_per_month": -1,
        "max_streams_per_month": -1,
        "max_storage_gb": -1,
        "max_bandwidth_gb": -1,
        "ai_generations_per_month": -1,
        "api_calls_per_month": -1,
        "encoding_minutes_per_month": -1,
        "concurrent_streams": -1,
        "features": json.dumps(["basic_upload", "advanced_analytics", "ai_titles", "ai_descriptions", "ai_thumbnails", "live_streaming", "simulcast", "api_access", "priority_support", "custom_integrations", "dedicated_manager"]),
        "display_features": json.dumps([
            {"name": "Unlimited Accounts", "included": True},
            {"name": "Unlimited Everything", "included": True},
            {"name": "Priority Support", "included": True},
            {"name": "Custom Integrations", "included": True},
            {"name": "Dedicated Account Manager", "included": True},
        ]),
        "is_active": True,
        "is_popular": False,
        "sort_order": 3,
    },
]


def upgrade() -> None:
    """Create plans table and insert default plans."""
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('price_yearly', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('max_accounts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_videos_per_month', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_streams_per_month', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_bandwidth_gb', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('ai_generations_per_month', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_calls_per_month', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('encoding_minutes_per_month', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('concurrent_streams', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('display_features', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('stripe_price_id_monthly', sa.String(255), nullable=True),
        sa.Column('stripe_price_id_yearly', sa.String(255), nullable=True),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_popular', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create index on slug for fast lookups
    op.create_index('ix_plans_slug', 'plans', ['slug'], unique=True)
    op.create_index('ix_plans_is_active', 'plans', ['is_active'])
    
    # Insert default plans
    plans_table = sa.table(
        'plans',
        sa.column('id', postgresql.UUID),
        sa.column('slug', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('price_monthly', sa.Integer),
        sa.column('price_yearly', sa.Integer),
        sa.column('currency', sa.String),
        sa.column('max_accounts', sa.Integer),
        sa.column('max_videos_per_month', sa.Integer),
        sa.column('max_streams_per_month', sa.Integer),
        sa.column('max_storage_gb', sa.Integer),
        sa.column('max_bandwidth_gb', sa.Integer),
        sa.column('ai_generations_per_month', sa.Integer),
        sa.column('api_calls_per_month', sa.Integer),
        sa.column('encoding_minutes_per_month', sa.Integer),
        sa.column('concurrent_streams', sa.Integer),
        sa.column('features', postgresql.JSON),
        sa.column('display_features', postgresql.JSON),
        sa.column('is_active', sa.Boolean),
        sa.column('is_popular', sa.Boolean),
        sa.column('sort_order', sa.Integer),
    )
    
    op.bulk_insert(plans_table, DEFAULT_PLANS)


def downgrade() -> None:
    """Drop plans table."""
    op.drop_index('ix_plans_is_active', table_name='plans')
    op.drop_index('ix_plans_slug', table_name='plans')
    op.drop_table('plans')
