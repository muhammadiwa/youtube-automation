"""Dashboard Export model for admin analytics export.

Revision ID: 034
Revises: 033
Create Date: 2024-12-12

Requirements: 2.5 - Generate CSV or PDF report with selected metrics
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create dashboard_exports table."""
    op.create_table(
        "dashboard_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", sa.String(10), nullable=False, server_default="csv"),
        sa.Column("metrics", postgresql.ARRAY(sa.String(100)), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("include_charts", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("download_url", sa.String(1000), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_dashboard_exports_admin_id"),
        "dashboard_exports",
        ["admin_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dashboard_exports_status"),
        "dashboard_exports",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Drop dashboard_exports table."""
    op.drop_index(op.f("ix_dashboard_exports_status"), table_name="dashboard_exports")
    op.drop_index(op.f("ix_dashboard_exports_admin_id"), table_name="dashboard_exports")
    op.drop_table("dashboard_exports")
