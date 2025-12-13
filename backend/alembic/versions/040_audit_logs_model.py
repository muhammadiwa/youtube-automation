"""Create audit_logs table.

Revision ID: 040_audit_logs
Revises: 039_backup_models
Create Date: 2025-12-13

Requirements: 8.1, 8.2, 8.3 - Audit Logs & Security
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "040_audit_logs"
down_revision = "039_backup_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        ),
    )
    
    # Create index on details->>'event' for filtering by event type
    op.create_index(
        "ix_audit_logs_event",
        "audit_logs",
        [sa.text("(details->>'event')")],
        postgresql_using="btree",
    )
    
    # Create index on details->>'resource_type' for filtering by resource type
    op.create_index(
        "ix_audit_logs_resource_type",
        "audit_logs",
        [sa.text("(details->>'resource_type')")],
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event", table_name="audit_logs")
    op.drop_table("audit_logs")
