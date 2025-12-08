"""Backup models migration.

Revision ID: 021
Revises: 020
Create Date: 2024-01-01 00:00:00.000000

Creates Backup, BackupSchedule, DataExport, DataImport, and StorageUsage tables.
Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create backups table
    op.create_table(
        "backups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("backup_type", sa.String(50), nullable=False, server_default="manual"),
        # Storage information
        sa.Column("storage_key", sa.String(512), nullable=True),
        sa.Column("storage_url", sa.String(1024), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(64), nullable=True),
        # Backup content configuration
        sa.Column("include_accounts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_videos", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_streams", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_analytics", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_settings", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("account_ids", postgresql.JSONB(), nullable=True),
        # Status tracking
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        # Backup statistics
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accounts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("videos_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streams_count", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backups_user_id"), "backups", ["user_id"], unique=False)
    op.create_index("ix_backups_user_status", "backups", ["user_id", "status"], unique=False)
    op.create_index("ix_backups_created_at", "backups", ["created_at"], unique=False)

    # Create backup_schedules table
    op.create_table(
        "backup_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Interval settings
        sa.Column("interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("cron_expression", sa.String(100), nullable=True),
        # Retention policy
        sa.Column("retention_count", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        # Backup content configuration
        sa.Column("include_accounts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_videos", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_streams", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_analytics", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("include_settings", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("account_ids", postgresql.JSONB(), nullable=True),
        # Execution tracking
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_backup_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_backup_schedules_user_id"), "backup_schedules", ["user_id"], unique=False
    )

    # Create data_exports table
    op.create_table(
        "data_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("export_format", sa.String(20), nullable=False),
        sa.Column("data_types", postgresql.JSONB(), nullable=False),
        # Storage information
        sa.Column("storage_key", sa.String(512), nullable=True),
        sa.Column("storage_url", sa.String(1024), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        # Status tracking
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_data_exports_user_id"), "data_exports", ["user_id"], unique=False
    )

    # Create data_imports table
    op.create_table(
        "data_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_backup_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_file_key", sa.String(512), nullable=True),
        sa.Column("import_format", sa.String(20), nullable=False),
        sa.Column("conflict_resolution", sa.String(50), nullable=False, server_default="skip"),
        # Status tracking
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        # Import statistics
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflict_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("import_results", postgresql.JSONB(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_data_imports_user_id"), "data_imports", ["user_id"], unique=False
    )

    # Create storage_usage table
    op.create_table(
        "storage_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Storage limits (in bytes)
        sa.Column(
            "storage_limit", sa.BigInteger(), nullable=False, server_default="10737418240"
        ),  # 10GB
        sa.Column("storage_used", sa.BigInteger(), nullable=False, server_default="0"),
        # Breakdown by type
        sa.Column("backups_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("exports_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("other_size", sa.BigInteger(), nullable=False, server_default="0"),
        # Alert tracking
        sa.Column("last_alert_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_alert_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("storage_usage")
    op.drop_index(op.f("ix_data_imports_user_id"), table_name="data_imports")
    op.drop_table("data_imports")
    op.drop_index(op.f("ix_data_exports_user_id"), table_name="data_exports")
    op.drop_table("data_exports")
    op.drop_index(op.f("ix_backup_schedules_user_id"), table_name="backup_schedules")
    op.drop_table("backup_schedules")
    op.drop_index("ix_backups_created_at", table_name="backups")
    op.drop_index("ix_backups_user_status", table_name="backups")
    op.drop_index(op.f("ix_backups_user_id"), table_name="backups")
    op.drop_table("backups")
