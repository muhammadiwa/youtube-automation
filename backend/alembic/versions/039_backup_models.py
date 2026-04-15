"""Add Backup, BackupSchedule, and BackupRestore models.

Requirements: 18.1 - Backup status with type, size, location
Requirements: 18.2 - Configure frequency, retention period, and storage location
Requirements: 18.3 - Create full backup with progress indicator
Requirements: 18.4 - Restore with super_admin approval and pre-restore snapshot
Requirements: 18.5 - Alert admin on failure and retry with exponential backoff

Revision ID: 039_backup_models
Revises: 038_compliance_extended
Create Date: 2024-12-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "039_backup_models"
down_revision = "038_compliance_extended"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admin_backups table
    op.create_table(
        "admin_backups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("backup_type", sa.String(20), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("progress", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("storage_provider", sa.String(50), nullable=False, default="local"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("max_retries", sa.Integer(), nullable=False, default=3),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create admin_backup_schedules table
    op.create_table(
        "admin_backup_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("backup_type", sa.String(20), nullable=False, default="full"),
        sa.Column("frequency", sa.String(50), nullable=False, default="daily"),
        sa.Column("cron_expression", sa.String(100), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, default=30),
        sa.Column("max_backups", sa.Integer(), nullable=True),
        sa.Column("storage_provider", sa.String(50), nullable=False, default="local"),
        sa.Column("storage_location", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_backup_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_backups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("configured_by", postgresql.UUID(as_uuid=True), nullable=False),
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

    # Create backup_restores table
    op.create_table(
        "backup_restores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "backup_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_backups.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "pre_restore_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_backups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, default="pending_approval", index=True),
        sa.Column("progress", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("backup_restores")
    op.drop_table("admin_backup_schedules")
    op.drop_table("admin_backups")
