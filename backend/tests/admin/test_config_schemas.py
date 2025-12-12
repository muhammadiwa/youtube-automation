"""Unit tests for Global Configuration schemas.

Requirements: 19-29 - Global Configuration Management
"""

import pytest
from pydantic import ValidationError

from app.modules.admin.config_schemas import (
    AuthConfig, AuthConfigUpdate,
    UploadConfig, UploadConfigUpdate,
    StreamingConfig, StreamingConfigUpdate,
    AIConfig, AIConfigUpdate,
    ModerationConfig, ModerationConfigUpdate,
    NotificationConfig, NotificationConfigUpdate,
    JobQueueConfig, JobQueueConfigUpdate,
)


class TestAuthConfig:
    """Tests for AuthConfig schema."""

    def test_default_values(self):
        """Test AuthConfig has correct default values."""
        config = AuthConfig()
        assert config.jwt_access_token_expire_minutes == 15
        assert config.jwt_refresh_token_expire_days == 7
        assert config.password_min_length == 8
        assert config.password_require_uppercase is True
        assert config.password_require_lowercase is True
        assert config.password_require_digit is True
        assert config.password_require_special is True
        assert config.max_login_attempts == 5
        assert config.lockout_duration_minutes == 30
        assert config.require_email_verification is True
        assert config.allow_social_login is True
        assert config.admin_require_2fa is True
        assert config.session_timeout_minutes == 60

    def test_custom_values(self):
        """Test AuthConfig accepts custom values."""
        config = AuthConfig(
            jwt_access_token_expire_minutes=30,
            password_min_length=12,
            max_login_attempts=3,
        )
        assert config.jwt_access_token_expire_minutes == 30
        assert config.password_min_length == 12
        assert config.max_login_attempts == 3

    def test_validation_min_values(self):
        """Test AuthConfig validates minimum values."""
        with pytest.raises(ValidationError):
            AuthConfig(jwt_access_token_expire_minutes=0)
        with pytest.raises(ValidationError):
            AuthConfig(password_min_length=5)

    def test_validation_max_values(self):
        """Test AuthConfig validates maximum values."""
        with pytest.raises(ValidationError):
            AuthConfig(jwt_access_token_expire_minutes=61)
        with pytest.raises(ValidationError):
            AuthConfig(jwt_refresh_token_expire_days=31)


class TestUploadConfig:
    """Tests for UploadConfig schema."""

    def test_default_values(self):
        """Test UploadConfig has correct default values."""
        config = UploadConfig()
        assert config.max_file_size_gb == 5.0
        assert config.allowed_formats == ["mp4", "mov", "avi", "wmv", "webm", "mpeg"]
        assert config.max_concurrent_uploads == 3
        assert config.upload_chunk_size_mb == 10
        assert config.auto_generate_thumbnail is True
        assert config.default_visibility == "private"

    def test_custom_values(self):
        """Test UploadConfig accepts custom values."""
        config = UploadConfig(
            max_file_size_gb=10.0,
            allowed_formats=["mp4", "webm"],
            max_concurrent_uploads=5,
        )
        assert config.max_file_size_gb == 10.0
        assert config.allowed_formats == ["mp4", "webm"]
        assert config.max_concurrent_uploads == 5


class TestStreamingConfig:
    """Tests for StreamingConfig schema."""

    def test_default_values(self):
        """Test StreamingConfig has correct default values."""
        config = StreamingConfig()
        assert config.max_concurrent_streams_per_account == 1
        assert config.max_stream_duration_hours == 12
        assert config.health_check_interval_seconds == 10
        assert config.reconnect_max_attempts == 5
        assert config.default_latency_mode == "normal"
        assert config.enable_dvr_by_default is True
        assert config.simulcast_max_platforms == 5


class TestAIConfig:
    """Tests for AIConfig schema."""

    def test_default_values(self):
        """Test AIConfig has correct default values."""
        config = AIConfig()
        assert config.openai_model == "gpt-4"
        assert config.openai_max_tokens == 1000
        assert config.title_suggestions_count == 5
        assert config.thumbnail_variations_count == 3
        assert config.ai_monthly_budget_usd == 1000.0
        assert config.enable_content_moderation_ai is True


class TestModerationConfig:
    """Tests for ModerationConfig schema."""

    def test_default_values(self):
        """Test ModerationConfig has correct default values."""
        config = ModerationConfig()
        assert config.moderation_analysis_timeout_seconds == 2
        assert config.auto_slow_mode_threshold == 50
        assert config.slow_mode_duration_seconds == 30
        assert config.max_warnings_before_ban == 3
        assert config.spam_detection_enabled is True
        assert config.profanity_filter_enabled is True


class TestNotificationConfig:
    """Tests for NotificationConfig schema."""

    def test_default_values(self):
        """Test NotificationConfig has correct default values."""
        config = NotificationConfig()
        assert config.email_enabled is True
        assert config.sms_enabled is False
        assert config.slack_enabled is True
        assert config.telegram_enabled is True
        assert config.whatsapp_enabled is False
        assert config.critical_alert_channels == ["email", "slack"]
        assert config.notification_retention_days == 90


class TestJobQueueConfig:
    """Tests for JobQueueConfig schema."""

    def test_default_values(self):
        """Test JobQueueConfig has correct default values."""
        config = JobQueueConfig()
        assert config.max_job_retries == 3
        assert config.retry_backoff_multiplier == 2.0
        assert config.retry_initial_delay_seconds == 5
        assert config.job_timeout_minutes == 60
        assert config.dlq_alert_threshold == 10
        assert config.max_jobs_per_worker == 5


class TestConfigUpdateSchemas:
    """Tests for config update schemas."""

    def test_auth_config_update_partial(self):
        """Test AuthConfigUpdate allows partial updates."""
        update = AuthConfigUpdate(jwt_access_token_expire_minutes=30)
        assert update.jwt_access_token_expire_minutes == 30
        assert update.password_min_length is None

    def test_upload_config_update_partial(self):
        """Test UploadConfigUpdate allows partial updates."""
        update = UploadConfigUpdate(max_file_size_gb=10.0)
        assert update.max_file_size_gb == 10.0
        assert update.allowed_formats is None

    def test_streaming_config_update_partial(self):
        """Test StreamingConfigUpdate allows partial updates."""
        update = StreamingConfigUpdate(max_stream_duration_hours=24)
        assert update.max_stream_duration_hours == 24
        assert update.health_check_interval_seconds is None

    def test_ai_config_update_partial(self):
        """Test AIConfigUpdate allows partial updates."""
        update = AIConfigUpdate(openai_model="gpt-3.5-turbo")
        assert update.openai_model == "gpt-3.5-turbo"
        assert update.openai_max_tokens is None

    def test_moderation_config_update_partial(self):
        """Test ModerationConfigUpdate allows partial updates."""
        update = ModerationConfigUpdate(max_warnings_before_ban=5)
        assert update.max_warnings_before_ban == 5
        assert update.spam_detection_enabled is None

    def test_notification_config_update_partial(self):
        """Test NotificationConfigUpdate allows partial updates."""
        update = NotificationConfigUpdate(email_enabled=False)
        assert update.email_enabled is False
        assert update.sms_enabled is None

    def test_job_queue_config_update_partial(self):
        """Test JobQueueConfigUpdate allows partial updates."""
        update = JobQueueConfigUpdate(max_job_retries=5)
        assert update.max_job_retries == 5
        assert update.retry_backoff_multiplier is None
