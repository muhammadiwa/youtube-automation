"""Add country column to users table for geographic distribution.

Revision ID: 033
Revises: 032
Create Date: 2025-12-12 00:00:00.000000

Requirements: 17.3 - Display user map with country/region breakdown
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add country column to users table."""
    op.add_column(
        "users",
        sa.Column("country", sa.String(2), nullable=True, comment="ISO 3166-1 alpha-2 country code")
    )
    # Add index for efficient geographic queries
    op.create_index("ix_users_country", "users", ["country"])


def downgrade() -> None:
    """Remove country column from users table."""
    op.drop_index("ix_users_country", table_name="users")
    op.drop_column("users", "country")
