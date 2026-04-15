"""Add icon and color columns to plans table.

Revision ID: 042_plan_icon_color
Revises: 041_data_requests
Create Date: 2025-12-13
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "042_plan_icon_color"
down_revision = "041_data_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add icon and color columns to plans table."""
    # Add icon column with default value
    op.add_column(
        "plans",
        sa.Column("icon", sa.String(50), nullable=False, server_default="Sparkles")
    )
    
    # Add color column with default value
    op.add_column(
        "plans",
        sa.Column("color", sa.String(20), nullable=False, server_default="slate")
    )


def downgrade() -> None:
    """Remove icon and color columns from plans table."""
    op.drop_column("plans", "color")
    op.drop_column("plans", "icon")
