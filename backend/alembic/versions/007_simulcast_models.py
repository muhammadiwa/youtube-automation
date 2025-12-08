"""Add simulcast models for multi-platform streaming.

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 00:00:00.000000

Requirements: 9.1, 9.4, 9.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create simulcast_targets and simulcast_health_logs tables."""
    
    # Create simulcast_targets table (Requirements: 9.1, 9.4)
    op.create_table(
        'simulcast_targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('live_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Platform configuration
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_name', sa.String(255), nullable=False),
        
        # RTMP endpoint configuration
        sa.Column('rtmp_url', sa.String(1024), nullable=False),
        sa.Column('stream_key', sa.Text(), nullable=True),
        
        # Connection settings
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        
        # Instagram proxy settings (Requirements: 9.5)
        sa.Column('use_proxy', sa.Boolean(), nullable=False, default=False),
        sa.Column('proxy_url', sa.String(512), nullable=True),
        
        # Status tracking
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        
        # Health metrics
        sa.Column('current_bitrate', sa.Integer(), nullable=True),
        sa.Column('dropped_frames', sa.Integer(), nullable=False, default=0),
        sa.Column('connection_quality', sa.String(50), nullable=True),
        sa.Column('last_health_check_at', sa.DateTime(timezone=True), nullable=True),
        
        # Session tracking
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_streaming_seconds', sa.Integer(), nullable=False, default=0),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['live_event_id'], ['live_events.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for simulcast_targets
    op.create_index('ix_simulcast_targets_live_event_id', 'simulcast_targets', ['live_event_id'])
    op.create_index('ix_simulcast_targets_platform', 'simulcast_targets', ['platform'])
    op.create_index('ix_simulcast_targets_status', 'simulcast_targets', ['status'])
    
    # Create simulcast_health_logs table (Requirements: 9.4)
    op.create_table(
        'simulcast_health_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Health metrics
        sa.Column('bitrate', sa.Integer(), nullable=False, default=0),
        sa.Column('frame_rate', sa.Float(), nullable=True),
        sa.Column('dropped_frames', sa.Integer(), nullable=False, default=0),
        sa.Column('dropped_frames_delta', sa.Integer(), nullable=False, default=0),
        
        # Connection status
        sa.Column('connection_status', sa.String(50), nullable=False, default='good'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        
        # Alert flags
        sa.Column('is_alert_triggered', sa.Boolean(), nullable=False, default=False),
        sa.Column('alert_type', sa.String(100), nullable=True),
        sa.Column('alert_message', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['target_id'], ['simulcast_targets.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for simulcast_health_logs
    op.create_index('ix_simulcast_health_logs_target_id', 'simulcast_health_logs', ['target_id'])
    op.create_index('ix_simulcast_health_logs_collected_at', 'simulcast_health_logs', ['collected_at'])


def downgrade() -> None:
    """Drop simulcast tables."""
    op.drop_index('ix_simulcast_health_logs_collected_at', table_name='simulcast_health_logs')
    op.drop_index('ix_simulcast_health_logs_target_id', table_name='simulcast_health_logs')
    op.drop_table('simulcast_health_logs')
    
    op.drop_index('ix_simulcast_targets_status', table_name='simulcast_targets')
    op.drop_index('ix_simulcast_targets_platform', table_name='simulcast_targets')
    op.drop_index('ix_simulcast_targets_live_event_id', table_name='simulcast_targets')
    op.drop_table('simulcast_targets')
