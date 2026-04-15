"""Trial codes model for extended trial promotions.

Requirements: 14.4 - Create extended trial codes

Revision ID: 037_trial_codes
Revises: 036_ai_logs_model
Create Date: 2024-12-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '037_trial_codes'
down_revision = '036_ai_logs_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trial_codes table
    op.create_table(
        'trial_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('trial_days', sa.Integer(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('applicable_plans', postgresql.ARRAY(sa.String(50)), nullable=False, server_default='{}'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_trial_codes_code', 'trial_codes', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_trial_codes_code', table_name='trial_codes')
    op.drop_table('trial_codes')
