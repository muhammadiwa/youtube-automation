"""Agent models migration.

Revision ID: 018
Revises: 017
Create Date: 2025-12-08

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5 - Agent and Job management
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agents and agent_jobs tables."""
    # Create agents table
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_hash", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="offline"),
        sa.Column("current_load", sa.Integer(), nullable=False, default=0),
        sa.Column("max_capacity", sa.Integer(), nullable=False, default=5),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agent_metadata", postgresql.JSON(), nullable=True),
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

    # Create agent_jobs table
    op.create_table(
        "agent_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("job_type", sa.String(50), nullable=False, index=True),
        sa.Column("payload", postgresql.JSON(), nullable=False, default={}),
        sa.Column("priority", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(20), nullable=False, default="queued", index=True),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False, default=3),
        sa.Column("result", postgresql.JSON(), nullable=True),
        sa.Column("error", sa.String(1000), nullable=True),
        sa.Column("next_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_agent_jobs_status_priority",
        "agent_jobs",
        ["status", "priority"],
    )


def downgrade() -> None:
    """Drop agents and agent_jobs tables."""
    op.drop_index("ix_agent_jobs_status_priority", table_name="agent_jobs")
    op.drop_table("agent_jobs")
    op.drop_table("agents")
