"""Add backup_codes column to users table.

Revision ID: 025
Revises: 024
Create Date: 2025-12-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add backup_codes column to users table."""
    op.add_column(
        "users",
        sa.Column("backup_codes", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove backup_codes column from users table."""
    op.drop_column("users", "backup_codes")
