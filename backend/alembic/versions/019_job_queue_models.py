"""Job Queue models migration.

Revision ID: 019
Revises: 018
Create Date: 2024-01-01 00:00:00.000000

Requirements: 22.1, 22.3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=False, default={}),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False, default='queued'),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('result', postgresql.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(), nullable=True),
        sa.Column('moved_to_dlq_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dlq_reason', sa.String(500), nullable=True),
        sa.Column('dlq_alert_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('dlq_alert_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for jobs table
    op.create_index('ix_jobs_job_type', 'jobs', ['job_type'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_priority', 'jobs', ['priority'])
    op.create_index('ix_jobs_workflow_id', 'jobs', ['workflow_id'])
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_account_id', 'jobs', ['account_id'])
    op.create_index('ix_jobs_status_priority', 'jobs', ['status', 'priority'])
    op.create_index('ix_jobs_status_created', 'jobs', ['status', 'created_at'])
    op.create_index('ix_jobs_dlq_alert', 'jobs', ['status', 'dlq_alert_sent'])
    
    # Create dlq_alerts table
    op.create_table(
        'dlq_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, default=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('notification_channels', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for dlq_alerts table
    op.create_index('ix_dlq_alerts_job_id', 'dlq_alerts', ['job_id'])
    op.create_index('ix_dlq_alerts_acknowledged', 'dlq_alerts', ['acknowledged'])


def downgrade() -> None:
    # Drop dlq_alerts table
    op.drop_index('ix_dlq_alerts_acknowledged', table_name='dlq_alerts')
    op.drop_index('ix_dlq_alerts_job_id', table_name='dlq_alerts')
    op.drop_table('dlq_alerts')
    
    # Drop jobs table
    op.drop_index('ix_jobs_dlq_alert', table_name='jobs')
    op.drop_index('ix_jobs_status_created', table_name='jobs')
    op.drop_index('ix_jobs_status_priority', table_name='jobs')
    op.drop_index('ix_jobs_account_id', table_name='jobs')
    op.drop_index('ix_jobs_user_id', table_name='jobs')
    op.drop_index('ix_jobs_workflow_id', table_name='jobs')
    op.drop_index('ix_jobs_priority', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_job_type', table_name='jobs')
    op.drop_table('jobs')
