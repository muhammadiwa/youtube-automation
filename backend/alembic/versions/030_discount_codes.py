"""Create discount_codes table for promotional tools.

Revision ID: 030
Revises: 029
Create Date: 2024-12-12

Requirements: 14.1 - Promotional Tools (Discount Codes)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create discount_codes table."""
    op.create_table(
        'discount_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('discount_type', sa.String(20), nullable=False, default='percentage'),
        sa.Column('discount_value', sa.Float(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('applicable_plans', postgresql.ARRAY(sa.String(50)), nullable=False, default=[]),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create index on code for fast lookups
    op.create_index('ix_discount_codes_code', 'discount_codes', ['code'], unique=True)
    
    # Create index on is_active for filtering active codes
    op.create_index('ix_discount_codes_is_active', 'discount_codes', ['is_active'])
    
    # Create index on valid_from and valid_until for date range queries
    op.create_index('ix_discount_codes_validity', 'discount_codes', ['valid_from', 'valid_until'])
    
    # Create index on created_by for admin filtering
    op.create_index('ix_discount_codes_created_by', 'discount_codes', ['created_by'])


def downgrade() -> None:
    """Drop discount_codes table."""
    op.drop_index('ix_discount_codes_created_by', table_name='discount_codes')
    op.drop_index('ix_discount_codes_validity', table_name='discount_codes')
    op.drop_index('ix_discount_codes_is_active', table_name='discount_codes')
    op.drop_index('ix_discount_codes_code', table_name='discount_codes')
    op.drop_table('discount_codes')
