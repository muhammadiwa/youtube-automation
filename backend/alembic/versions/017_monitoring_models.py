"""Monitoring models migration.

Revision ID: 017
Revises: 016
Create Date: 2025-12-08

Requirements: 16.5 - Layout preferences
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create monitoring_layout_preferences table."""
    op.create_table(
        "monitoring_layout_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("grid_columns", sa.Integer(), nullable=False, default=4),
        sa.Column("grid_rows", sa.Integer(), nullable=False, default=3),
        sa.Column(
            "show_metrics",
            postgresql.JSON(),
            nullable=False,
            default=["subscribers", "views", "status", "quota"],
        ),
        sa.Column("sort_by", sa.String(50), nullable=False, default="status"),
        sa.Column("sort_order", sa.String(10), nullable=False, default="asc"),
        sa.Column("default_filter", sa.String(50), nullable=False, default="all"),
        sa.Column("compact_mode", sa.Boolean(), nullable=False, default=False),
        sa.Column("show_issues_only", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop monitoring_layout_preferences table."""
    op.drop_table("monitoring_layout_preferences")
