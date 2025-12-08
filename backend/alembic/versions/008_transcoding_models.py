"""Transcoding models migration.

Revision ID: 008
Revises: 007
Create Date: 2024-01-01 00:00:00.000000

Requirements: 10.1, 10.2, 10.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transcode_workers table
    op.create_table(
        'transcode_workers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hostname', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('max_concurrent_jobs', sa.Integer(), nullable=False, default=2),
        sa.Column('current_jobs', sa.Integer(), nullable=False, default=0),
        sa.Column('current_load', sa.Float(), nullable=False, default=0.0),
        sa.Column('is_healthy', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=False),
        sa.Column('supports_4k', sa.Boolean(), nullable=False, default=True),
        sa.Column('supports_hardware_encoding', sa.Boolean(), nullable=False, default=False),
        sa.Column('gpu_type', sa.String(100), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hostname'),
    )
    
    # Create transcode_jobs table
    op.create_table(
        'transcode_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_file_path', sa.String(1024), nullable=False),
        sa.Column('source_file_size', sa.Integer(), nullable=True),
        sa.Column('source_duration', sa.Float(), nullable=True),
        sa.Column('target_resolution', sa.Enum('720p', '1080p', '2k', '4k', name='resolution'), nullable=False),
        sa.Column('target_bitrate', sa.Integer(), nullable=True),
        sa.Column('latency_mode', sa.Enum('normal', 'low', 'ultra_low', name='latencymode'), nullable=False, default='normal'),
        sa.Column('enable_abr', sa.Boolean(), nullable=False, default=False),
        sa.Column('output_file_path', sa.String(1024), nullable=True),
        sa.Column('output_file_size', sa.Integer(), nullable=True),
        sa.Column('output_width', sa.Integer(), nullable=True),
        sa.Column('output_height', sa.Integer(), nullable=True),
        sa.Column('cdn_url', sa.String(1024), nullable=True),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', name='transcodestatus'), nullable=False, default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, default=0.0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('assigned_worker_id', sa.String(255), nullable=True),
        sa.Column('worker_load_at_assignment', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('live_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['youtube_accounts.id']),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id']),
        sa.ForeignKeyConstraint(['live_event_id'], ['live_events.id']),
    )
    
    # Create transcoded_outputs table
    op.create_table(
        'transcoded_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcode_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resolution', sa.Enum('720p', '1080p', '2k', '4k', name='resolution', create_type=False), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('bitrate', sa.Integer(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('storage_bucket', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(1024), nullable=False),
        sa.Column('cdn_url', sa.String(1024), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transcode_job_id'], ['transcode_jobs.id']),
    )
    
    # Create indexes
    op.create_index('ix_transcode_jobs_status', 'transcode_jobs', ['status'])
    op.create_index('ix_transcode_jobs_created_at', 'transcode_jobs', ['created_at'])
    op.create_index('ix_transcode_workers_is_healthy', 'transcode_workers', ['is_healthy'])


def downgrade() -> None:
    op.drop_index('ix_transcode_workers_is_healthy')
    op.drop_index('ix_transcode_jobs_created_at')
    op.drop_index('ix_transcode_jobs_status')
    op.drop_table('transcoded_outputs')
    op.drop_table('transcode_jobs')
    op.drop_table('transcode_workers')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS transcodestatus')
    op.execute('DROP TYPE IF EXISTS latencymode')
    op.execute('DROP TYPE IF EXISTS resolution')
