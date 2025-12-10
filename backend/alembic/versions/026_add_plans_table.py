"""Add plans table for subscription plans.

Revision ID: 026
Revises: 025
Create Date: 2024-12-10

Requirements: 28.1 - Plan tiers with feature limits
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create plans table."""
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


def downgrade() -> None:
    """Drop plans table."""
    op.drop_index('ix_plans_is_active', table_name='plans')
    op.drop_index('ix_plans_slug', table_name='plans')
    op.drop_table('plans')
