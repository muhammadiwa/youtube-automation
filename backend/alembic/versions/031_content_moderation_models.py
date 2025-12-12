"""Create content_reports and user_warnings tables for admin moderation.

Revision ID: 031
Revises: 030
Create Date: 2024-12-12

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5 - Content Moderation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create content_reports and user_warnings tables."""
    
    # Create content_reports table
    op.create_table(
        'content_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        # Content identification
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_preview', sa.Text(), nullable=True),
        sa.Column('content_owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Reporter information
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Report details
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reason_category', sa.String(100), nullable=True),
        sa.Column('additional_info', postgresql.JSON(), nullable=True),
        # Severity and aggregation
        sa.Column('severity', sa.String(20), nullable=False, default='medium'),
        sa.Column('report_count', sa.Integer(), nullable=False, default=1),
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        # Review information
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(['content_owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['admins.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for content_reports
    op.create_index('ix_content_reports_content_type', 'content_reports', ['content_type'])
    op.create_index('ix_content_reports_content_id', 'content_reports', ['content_id'])
    op.create_index('ix_content_reports_content_owner_id', 'content_reports', ['content_owner_id'])
    op.create_index('ix_content_reports_reporter_id', 'content_reports', ['reporter_id'])
    op.create_index('ix_content_reports_severity', 'content_reports', ['severity'])
    op.create_index('ix_content_reports_status', 'content_reports', ['status'])
    # Composite index for queue sorting (severity desc, report_count desc)
    op.create_index('ix_content_reports_queue_sort', 'content_reports', ['severity', 'report_count'])
    
    # Create user_warnings table
    op.create_table(
        'user_warnings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Warning details
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('warning_number', sa.Integer(), nullable=False),
        # Related report
        sa.Column('related_report_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_report_id'], ['content_reports.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for user_warnings
    op.create_index('ix_user_warnings_user_id', 'user_warnings', ['user_id'])
    op.create_index('ix_user_warnings_admin_id', 'user_warnings', ['admin_id'])
    op.create_index('ix_user_warnings_related_report_id', 'user_warnings', ['related_report_id'])


def downgrade() -> None:
    """Drop content_reports and user_warnings tables."""
    # Drop user_warnings indexes and table
    op.drop_index('ix_user_warnings_related_report_id', table_name='user_warnings')
    op.drop_index('ix_user_warnings_admin_id', table_name='user_warnings')
    op.drop_index('ix_user_warnings_user_id', table_name='user_warnings')
    op.drop_table('user_warnings')
    
    # Drop content_reports indexes and table
    op.drop_index('ix_content_reports_queue_sort', table_name='content_reports')
    op.drop_index('ix_content_reports_status', table_name='content_reports')
    op.drop_index('ix_content_reports_severity', table_name='content_reports')
    op.drop_index('ix_content_reports_reporter_id', table_name='content_reports')
    op.drop_index('ix_content_reports_content_owner_id', table_name='content_reports')
    op.drop_index('ix_content_reports_content_id', table_name='content_reports')
    op.drop_index('ix_content_reports_content_type', table_name='content_reports')
    op.drop_table('content_reports')
