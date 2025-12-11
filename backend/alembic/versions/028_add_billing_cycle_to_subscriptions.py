"""Add billing_cycle column to subscriptions table.

Revision ID: 028
Revises: 027
Create Date: 2025-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '028'
down_revision: Union[str, None] = '027'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add billing_cycle column to subscriptions table."""
    # Add billing_cycle column with default value 'monthly'
    op.add_column(
        'subscriptions',
        sa.Column('billing_cycle', sa.String(20), nullable=False, server_default='monthly')
    )
    
    # Update existing subscriptions to detect billing_cycle from period length
    # If period is > 60 days, assume yearly
    op.execute("""
        UPDATE subscriptions 
        SET billing_cycle = 'yearly' 
        WHERE EXTRACT(DAY FROM (current_period_end - current_period_start)) > 60
    """)


def downgrade() -> None:
    """Remove billing_cycle column from subscriptions table."""
    op.drop_column('subscriptions', 'billing_cycle')
