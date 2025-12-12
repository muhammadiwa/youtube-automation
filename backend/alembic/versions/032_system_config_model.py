"""Create system_config table for global configuration.

Revision ID: 032
Revises: 031
Create Date: 2024-12-12

Requirements: 19-29 - Global Configuration Management
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import json

# revision identifiers, used by Alembic.
revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


# Default configurations for seeding
DEFAULT_CONFIGS = {
    "auth": {
        "jwt_access_token_expire_minutes": 15,
        "jwt_refresh_token_expire_days": 7,
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_digit": True,
        "password_require_special": True,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30,
        "require_email_verification": True,
        "allow_social_login": True,
        "admin_require_2fa": True,
        "session_timeout_minutes": 60
    },
    "upload": {
        "max_file_size_gb": 5.0,
        "allowed_formats": ["mp4", "mov", "avi", "wmv", "webm", "mpeg"],
        "max_concurrent_uploads": 3,
        "upload_chunk_size_mb": 10,
        "max_retry_attempts": 3,
        "retry_delay_seconds": 5,
        "auto_generate_thumbnail": True,
        "default_visibility": "private",
        "max_title_length": 100,
        "max_description_length": 5000,
        "max_tags_count": 500
    },
    "streaming": {
        "max_concurrent_streams_per_account": 1,
        "max_stream_duration_hours": 12,
        "health_check_interval_seconds": 10,
        "reconnect_max_attempts": 5,
        "reconnect_initial_delay_seconds": 2,
        "reconnect_max_delay_seconds": 30,
        "default_latency_mode": "normal",
        "enable_dvr_by_default": True,
        "simulcast_max_platforms": 5,
        "playlist_max_videos": 100,
        "stream_start_tolerance_seconds": 30
    },
    "ai": {
        "openai_model": "gpt-4",
        "openai_max_tokens": 1000,
        "title_suggestions_count": 5,
        "thumbnail_variations_count": 3,
        "thumbnail_width": 1280,
        "thumbnail_height": 720,
        "chatbot_response_timeout_seconds": 3,
        "chatbot_max_response_length": 500,
        "sentiment_analysis_enabled": True,
        "ai_monthly_budget_usd": 1000.0,
        "enable_content_moderation_ai": True
    },
    "moderation": {
        "moderation_analysis_timeout_seconds": 2,
        "auto_slow_mode_threshold": 50,
        "slow_mode_duration_seconds": 30,
        "default_timeout_duration_seconds": 300,
        "max_warnings_before_ban": 3,
        "spam_detection_enabled": True,
        "profanity_filter_enabled": True,
        "link_filter_enabled": True,
        "caps_filter_threshold_percent": 70
    },
    "notification": {
        "email_enabled": True,
        "sms_enabled": False,
        "slack_enabled": True,
        "telegram_enabled": True,
        "whatsapp_enabled": False,
        "notification_batch_interval_seconds": 60,
        "max_notifications_per_batch": 10,
        "critical_alert_channels": ["email", "slack"],
        "notification_retention_days": 90
    },
    "jobs": {
        "max_job_retries": 3,
        "retry_backoff_multiplier": 2.0,
        "retry_initial_delay_seconds": 5,
        "retry_max_delay_seconds": 300,
        "job_timeout_minutes": 60,
        "dlq_alert_threshold": 10,
        "worker_heartbeat_interval_seconds": 30,
        "worker_unhealthy_threshold_seconds": 60,
        "max_jobs_per_worker": 5,
        "queue_priority_levels": 3
    }
}


def upgrade() -> None:
    """Create system_config table and seed default configurations."""
    op.create_table(
        'system_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', postgresql.JSON, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_system_configs_key', 'system_configs', ['key'])
    op.create_index('ix_system_configs_category', 'system_configs', ['category'])
    
    # Seed default configurations
    for category, config_value in DEFAULT_CONFIGS.items():
        op.execute(f"""
            INSERT INTO system_configs (id, key, value, category, description)
            VALUES (
                gen_random_uuid(),
                '{category}',
                '{json.dumps(config_value)}'::jsonb,
                '{category}',
                'Default {category} configuration'
            )
            ON CONFLICT (key) DO NOTHING
        """)


def downgrade() -> None:
    """Drop system_config table."""
    op.drop_index('ix_system_configs_category', table_name='system_configs')
    op.drop_index('ix_system_configs_key', table_name='system_configs')
    op.drop_table('system_configs')
