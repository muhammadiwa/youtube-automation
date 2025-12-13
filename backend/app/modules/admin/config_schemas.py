"""Pydantic schemas for Global Configuration module.

Requirements: 19-29 - Global Configuration Management
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ==================== Auth Config Schemas (Requirements 19.1-19.5) ====================


class AuthConfig(BaseModel):
    """Authentication & Security configuration.
    
    Requirements: 19.1-19.5 - Global Authentication Configuration
    """
    jwt_access_token_expire_minutes: int = Field(
        default=15, ge=1, le=60, description="Access token expiry in minutes (1-60)"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, le=30, description="Refresh token expiry in days (1-30)"
    )
    password_min_length: int = Field(
        default=8, ge=6, le=32, description="Minimum password length"
    )
    password_require_uppercase: bool = Field(
        default=True, description="Require uppercase characters"
    )
    password_require_lowercase: bool = Field(
        default=True, description="Require lowercase characters"
    )
    password_require_digit: bool = Field(
        default=True, description="Require digit characters"
    )
    password_require_special: bool = Field(
        default=True, description="Require special characters"
    )
    max_login_attempts: int = Field(
        default=5, ge=1, le=20, description="Max login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=30, ge=1, le=1440, description="Lockout duration in minutes"
    )
    require_email_verification: bool = Field(
        default=True, description="Require email verification for new users"
    )
    allow_social_login: bool = Field(
        default=True, description="Allow social login (Google, etc.)"
    )
    admin_require_2fa: bool = Field(
        default=True, description="Require 2FA for admin users"
    )
    session_timeout_minutes: int = Field(
        default=60, ge=5, le=1440, description="Session timeout in minutes"
    )


class AuthConfigUpdate(BaseModel):
    """Update schema for auth configuration."""
    jwt_access_token_expire_minutes: Optional[int] = Field(None, ge=1, le=60)
    jwt_refresh_token_expire_days: Optional[int] = Field(None, ge=1, le=30)
    password_min_length: Optional[int] = Field(None, ge=6, le=32)
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_digit: Optional[bool] = None
    password_require_special: Optional[bool] = None
    max_login_attempts: Optional[int] = Field(None, ge=1, le=20)
    lockout_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    require_email_verification: Optional[bool] = None
    allow_social_login: Optional[bool] = None
    admin_require_2fa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)


# ==================== Upload Config Schemas (Requirements 20.1-20.5) ====================


class UploadConfig(BaseModel):
    """Video Upload configuration.
    
    Requirements: 20.1-20.5 - Global Upload & Video Configuration
    """
    max_file_size_gb: float = Field(
        default=5.0, ge=0.1, le=50.0, description="Max file size in GB (1-50)"
    )
    allowed_formats: list[str] = Field(
        default=["mp4", "mov", "avi", "wmv", "webm", "mpeg"],
        description="Allowed video formats"
    )
    max_concurrent_uploads: int = Field(
        default=3, ge=1, le=10, description="Max concurrent uploads per user"
    )
    upload_chunk_size_mb: int = Field(
        default=10, ge=1, le=100, description="Upload chunk size in MB"
    )
    max_retry_attempts: int = Field(
        default=3, ge=1, le=10, description="Max retry attempts for failed uploads"
    )
    retry_delay_seconds: int = Field(
        default=5, ge=1, le=60, description="Delay between retries in seconds"
    )
    auto_generate_thumbnail: bool = Field(
        default=True, description="Auto-generate thumbnail from video"
    )
    default_visibility: str = Field(
        default="private", description="Default video visibility"
    )
    max_title_length: int = Field(
        default=100, ge=10, le=200, description="Max video title length"
    )
    max_description_length: int = Field(
        default=5000, ge=100, le=10000, description="Max video description length"
    )
    max_tags_count: int = Field(
        default=500, ge=10, le=1000, description="Max number of tags per video"
    )


class UploadConfigUpdate(BaseModel):
    """Update schema for upload configuration."""
    max_file_size_gb: Optional[float] = Field(None, ge=0.1, le=50.0)
    allowed_formats: Optional[list[str]] = None
    max_concurrent_uploads: Optional[int] = Field(None, ge=1, le=10)
    upload_chunk_size_mb: Optional[int] = Field(None, ge=1, le=100)
    max_retry_attempts: Optional[int] = Field(None, ge=1, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=1, le=60)
    auto_generate_thumbnail: Optional[bool] = None
    default_visibility: Optional[str] = None
    max_title_length: Optional[int] = Field(None, ge=10, le=200)
    max_description_length: Optional[int] = Field(None, ge=100, le=10000)
    max_tags_count: Optional[int] = Field(None, ge=10, le=1000)


# ==================== Streaming Config Schemas (Requirements 21.1-21.5) ====================


class StreamingConfig(BaseModel):
    """Live Streaming configuration.
    
    Requirements: 21.1-21.5 - Global Streaming Configuration
    """
    max_concurrent_streams_per_account: int = Field(
        default=1, ge=1, le=10, description="Max concurrent streams per account"
    )
    max_stream_duration_hours: int = Field(
        default=12, ge=1, le=48, description="Max stream duration in hours"
    )
    health_check_interval_seconds: int = Field(
        default=10, ge=5, le=60, description="Health check interval in seconds"
    )
    reconnect_max_attempts: int = Field(
        default=5, ge=1, le=20, description="Max reconnection attempts"
    )
    reconnect_initial_delay_seconds: int = Field(
        default=2, ge=1, le=30, description="Initial reconnection delay"
    )
    reconnect_max_delay_seconds: int = Field(
        default=30, ge=5, le=300, description="Max reconnection delay"
    )
    default_latency_mode: str = Field(
        default="normal", description="Default latency mode (normal, low, ultra-low)"
    )
    enable_dvr_by_default: bool = Field(
        default=True, description="Enable DVR by default"
    )
    simulcast_max_platforms: int = Field(
        default=5, ge=1, le=10, description="Max simulcast platforms"
    )
    playlist_max_videos: int = Field(
        default=100, ge=10, le=500, description="Max videos per playlist stream"
    )
    stream_start_tolerance_seconds: int = Field(
        default=30, ge=5, le=120, description="Stream start tolerance in seconds"
    )


class StreamingConfigUpdate(BaseModel):
    """Update schema for streaming configuration."""
    max_concurrent_streams_per_account: Optional[int] = Field(None, ge=1, le=10)
    max_stream_duration_hours: Optional[int] = Field(None, ge=1, le=48)
    health_check_interval_seconds: Optional[int] = Field(None, ge=5, le=60)
    reconnect_max_attempts: Optional[int] = Field(None, ge=1, le=20)
    reconnect_initial_delay_seconds: Optional[int] = Field(None, ge=1, le=30)
    reconnect_max_delay_seconds: Optional[int] = Field(None, ge=5, le=300)
    default_latency_mode: Optional[str] = None
    enable_dvr_by_default: Optional[bool] = None
    simulcast_max_platforms: Optional[int] = Field(None, ge=1, le=10)
    playlist_max_videos: Optional[int] = Field(None, ge=10, le=500)
    stream_start_tolerance_seconds: Optional[int] = Field(None, ge=5, le=120)


# ==================== AI Config Schemas (Requirements 22.1-22.5) ====================


class AIConfig(BaseModel):
    """AI Services configuration.
    
    Requirements: 22.1-22.5 - Global AI Service Configuration
    """
    openai_model: str = Field(
        default="gpt-4", description="OpenAI model version"
    )
    openai_max_tokens: int = Field(
        default=1000, ge=100, le=4000, description="Max tokens per request"
    )
    title_suggestions_count: int = Field(
        default=5, ge=1, le=10, description="Number of title suggestions"
    )
    thumbnail_variations_count: int = Field(
        default=3, ge=1, le=10, description="Number of thumbnail variations"
    )
    thumbnail_width: int = Field(
        default=1280, ge=640, le=1920, description="Thumbnail width in pixels"
    )
    thumbnail_height: int = Field(
        default=720, ge=360, le=1080, description="Thumbnail height in pixels"
    )
    chatbot_response_timeout_seconds: int = Field(
        default=3, ge=1, le=30, description="Chatbot response timeout"
    )
    chatbot_max_response_length: int = Field(
        default=500, ge=100, le=2000, description="Max chatbot response length"
    )
    sentiment_analysis_enabled: bool = Field(
        default=True, description="Enable sentiment analysis"
    )
    ai_monthly_budget_usd: float = Field(
        default=1000.0, ge=0, le=100000, description="Monthly AI budget in USD"
    )
    enable_content_moderation_ai: bool = Field(
        default=True, description="Enable AI content moderation"
    )


class AIConfigUpdate(BaseModel):
    """Update schema for AI configuration."""
    openai_model: Optional[str] = None
    openai_max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    title_suggestions_count: Optional[int] = Field(None, ge=1, le=10)
    thumbnail_variations_count: Optional[int] = Field(None, ge=1, le=10)
    thumbnail_width: Optional[int] = Field(None, ge=640, le=1920)
    thumbnail_height: Optional[int] = Field(None, ge=360, le=1080)
    chatbot_response_timeout_seconds: Optional[int] = Field(None, ge=1, le=30)
    chatbot_max_response_length: Optional[int] = Field(None, ge=100, le=2000)
    sentiment_analysis_enabled: Optional[bool] = None
    ai_monthly_budget_usd: Optional[float] = Field(None, ge=0, le=100000)
    enable_content_moderation_ai: Optional[bool] = None


# ==================== Moderation Config Schemas (Requirements 23.1-23.5) ====================


class ModerationConfig(BaseModel):
    """Chat & Comment Moderation configuration.
    
    Requirements: 23.1-23.5 - Global Moderation Configuration
    """
    moderation_analysis_timeout_seconds: int = Field(
        default=2, ge=1, le=10, description="Moderation analysis timeout"
    )
    auto_slow_mode_threshold: int = Field(
        default=50, ge=10, le=500, description="Messages per minute to trigger slow mode"
    )
    slow_mode_duration_seconds: int = Field(
        default=30, ge=5, le=300, description="Slow mode duration in seconds"
    )
    default_timeout_duration_seconds: int = Field(
        default=300, ge=60, le=86400, description="Default timeout duration"
    )
    max_warnings_before_ban: int = Field(
        default=3, ge=1, le=10, description="Warnings before automatic ban"
    )
    spam_detection_enabled: bool = Field(
        default=True, description="Enable spam detection"
    )
    profanity_filter_enabled: bool = Field(
        default=True, description="Enable profanity filter"
    )
    link_filter_enabled: bool = Field(
        default=True, description="Enable link filter"
    )
    caps_filter_threshold_percent: int = Field(
        default=70, ge=50, le=100, description="Caps filter threshold percentage"
    )


class ModerationConfigUpdate(BaseModel):
    """Update schema for moderation configuration."""
    moderation_analysis_timeout_seconds: Optional[int] = Field(None, ge=1, le=10)
    auto_slow_mode_threshold: Optional[int] = Field(None, ge=10, le=500)
    slow_mode_duration_seconds: Optional[int] = Field(None, ge=5, le=300)
    default_timeout_duration_seconds: Optional[int] = Field(None, ge=60, le=86400)
    max_warnings_before_ban: Optional[int] = Field(None, ge=1, le=10)
    spam_detection_enabled: Optional[bool] = None
    profanity_filter_enabled: Optional[bool] = None
    link_filter_enabled: Optional[bool] = None
    caps_filter_threshold_percent: Optional[int] = Field(None, ge=50, le=100)


# ==================== Notification Config Schemas (Requirements 24.1-24.5) ====================


class NotificationConfig(BaseModel):
    """Notification System configuration.
    
    Requirements: 24.1-24.5 - Global Notification Configuration
    """
    email_enabled: bool = Field(
        default=True, description="Enable email notifications"
    )
    sms_enabled: bool = Field(
        default=False, description="Enable SMS notifications"
    )
    slack_enabled: bool = Field(
        default=True, description="Enable Slack notifications"
    )
    telegram_enabled: bool = Field(
        default=True, description="Enable Telegram notifications"
    )
    whatsapp_enabled: bool = Field(
        default=False, description="Enable WhatsApp notifications"
    )
    notification_batch_interval_seconds: int = Field(
        default=60, ge=10, le=3600, description="Batch interval in seconds"
    )
    max_notifications_per_batch: int = Field(
        default=10, ge=1, le=100, description="Max notifications per batch"
    )
    critical_alert_channels: list[str] = Field(
        default=["email", "slack"], description="Channels for critical alerts"
    )
    notification_retention_days: int = Field(
        default=90, ge=7, le=365, description="Notification retention in days"
    )


class NotificationConfigUpdate(BaseModel):
    """Update schema for notification configuration."""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    notification_batch_interval_seconds: Optional[int] = Field(None, ge=10, le=3600)
    max_notifications_per_batch: Optional[int] = Field(None, ge=1, le=100)
    critical_alert_channels: Optional[list[str]] = None
    notification_retention_days: Optional[int] = Field(None, ge=7, le=365)


# ==================== Job Queue Config Schemas (Requirements 25.1-25.5) ====================


class JobQueueConfig(BaseModel):
    """Job Queue & Workers configuration.
    
    Requirements: 25.1-25.5 - Global Job Queue Configuration
    """
    max_job_retries: int = Field(
        default=3, ge=1, le=10, description="Max job retry attempts"
    )
    retry_backoff_multiplier: float = Field(
        default=2.0, ge=1.0, le=5.0, description="Retry backoff multiplier"
    )
    retry_initial_delay_seconds: int = Field(
        default=5, ge=1, le=60, description="Initial retry delay in seconds"
    )
    retry_max_delay_seconds: int = Field(
        default=300, ge=60, le=3600, description="Max retry delay in seconds"
    )
    job_timeout_minutes: int = Field(
        default=60, ge=1, le=1440, description="Job timeout in minutes"
    )
    dlq_alert_threshold: int = Field(
        default=10, ge=1, le=100, description="DLQ alert threshold"
    )
    worker_heartbeat_interval_seconds: int = Field(
        default=30, ge=10, le=120, description="Worker heartbeat interval"
    )
    worker_unhealthy_threshold_seconds: int = Field(
        default=60, ge=30, le=300, description="Worker unhealthy threshold"
    )
    max_jobs_per_worker: int = Field(
        default=5, ge=1, le=20, description="Max jobs per worker"
    )
    queue_priority_levels: int = Field(
        default=3, ge=1, le=10, description="Number of priority levels"
    )


class JobQueueConfigUpdate(BaseModel):
    """Update schema for job queue configuration."""
    max_job_retries: Optional[int] = Field(None, ge=1, le=10)
    retry_backoff_multiplier: Optional[float] = Field(None, ge=1.0, le=5.0)
    retry_initial_delay_seconds: Optional[int] = Field(None, ge=1, le=60)
    retry_max_delay_seconds: Optional[int] = Field(None, ge=60, le=3600)
    job_timeout_minutes: Optional[int] = Field(None, ge=1, le=1440)
    dlq_alert_threshold: Optional[int] = Field(None, ge=1, le=100)
    worker_heartbeat_interval_seconds: Optional[int] = Field(None, ge=10, le=120)
    worker_unhealthy_threshold_seconds: Optional[int] = Field(None, ge=30, le=300)
    max_jobs_per_worker: Optional[int] = Field(None, ge=1, le=20)
    queue_priority_levels: Optional[int] = Field(None, ge=1, le=10)


# ==================== Response Schemas ====================


class SystemConfigResponse(BaseModel):
    """Response schema for system configuration."""
    id: uuid.UUID
    key: str
    value: dict
    category: str
    description: Optional[str] = None
    updated_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfigUpdateResponse(BaseModel):
    """Response after updating configuration."""
    key: str
    category: str
    previous_value: dict
    new_value: dict
    updated_by: uuid.UUID
    updated_at: datetime
    message: str


# ==================== Plan Config Schemas (Requirements 26.1-26.5) ====================


class PlanConfig(BaseModel):
    """Subscription Plan configuration - maps to plans table.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    # Identification
    id: Optional[str] = Field(None, description="Plan UUID")
    slug: str = Field(description="Unique plan slug identifier")
    name: str = Field(description="Display name of the plan")
    description: Optional[str] = Field(None, description="Plan description")
    
    # Pricing (in dollars for display, stored as cents in DB)
    price_monthly: float = Field(default=0.0, ge=0, description="Monthly price in USD")
    price_yearly: float = Field(default=0.0, ge=0, description="Yearly price in USD")
    currency: str = Field(default="USD", description="Currency code")
    
    # Limits (-1 for unlimited)
    max_accounts: int = Field(default=1, ge=-1, description="Max YouTube accounts (-1 = unlimited)")
    max_videos_per_month: int = Field(default=5, ge=-1, description="Max videos per month")
    max_streams_per_month: int = Field(default=0, ge=-1, description="Max streams per month")
    max_storage_gb: int = Field(default=1, ge=-1, description="Max storage in GB")
    max_bandwidth_gb: int = Field(default=5, ge=-1, description="Max bandwidth in GB")
    ai_generations_per_month: int = Field(default=0, ge=-1, description="Max AI generations per month")
    api_calls_per_month: int = Field(default=1000, ge=-1, description="Max API calls per month")
    encoding_minutes_per_month: int = Field(default=60, ge=-1, description="Max encoding minutes per month")
    concurrent_streams: int = Field(default=1, ge=-1, description="Max concurrent streams")
    
    # Features (JSON arrays)
    features: list[str] = Field(default=[], description="Feature slugs for logic")
    display_features: list[dict] = Field(default=[], description="Display features for UI")
    
    # Stripe integration
    stripe_price_id_monthly: Optional[str] = Field(None, description="Stripe monthly price ID")
    stripe_price_id_yearly: Optional[str] = Field(None, description="Stripe yearly price ID")
    stripe_product_id: Optional[str] = Field(None, description="Stripe product ID")
    
    # UI Customization
    icon: str = Field(default="Sparkles", description="Lucide icon name")
    color: str = Field(default="slate", description="Tailwind color name")
    
    # Status
    is_active: bool = Field(default=True, description="Whether the plan is active")
    is_popular: bool = Field(default=False, description="Show popular badge")
    sort_order: int = Field(default=0, description="Display order")


class PlanConfigCreate(BaseModel):
    """Create schema for plan configuration."""
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    slug: Optional[str] = Field(None, min_length=2, max_length=50, description="Unique plan slug (auto-generated from name if not provided)")
    description: Optional[str] = None
    
    price_monthly: float = Field(default=0.0, ge=0)
    price_yearly: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD", max_length=3)
    
    max_accounts: int = Field(default=1, ge=-1)
    max_videos_per_month: int = Field(default=5, ge=-1)
    max_streams_per_month: int = Field(default=0, ge=-1)
    max_storage_gb: int = Field(default=1, ge=-1)
    max_bandwidth_gb: int = Field(default=5, ge=-1)
    ai_generations_per_month: int = Field(default=0, ge=-1)
    api_calls_per_month: int = Field(default=1000, ge=-1)
    encoding_minutes_per_month: int = Field(default=60, ge=-1)
    concurrent_streams: int = Field(default=1, ge=-1)
    
    features: list[str] = Field(default=[])
    display_features: list[dict] = Field(default=[])
    
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    stripe_product_id: Optional[str] = None
    
    icon: str = Field(default="Sparkles", max_length=50)
    color: str = Field(default="slate", max_length=20)
    
    is_active: bool = Field(default=True)
    is_popular: bool = Field(default=False)
    sort_order: int = Field(default=0)


class PlanConfigUpdate(BaseModel):
    """Update schema for plan configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    
    price_monthly: Optional[float] = Field(None, ge=0)
    price_yearly: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    
    max_accounts: Optional[int] = Field(None, ge=-1)
    max_videos_per_month: Optional[int] = Field(None, ge=-1)
    max_streams_per_month: Optional[int] = Field(None, ge=-1)
    max_storage_gb: Optional[int] = Field(None, ge=-1)
    max_bandwidth_gb: Optional[int] = Field(None, ge=-1)
    ai_generations_per_month: Optional[int] = Field(None, ge=-1)
    api_calls_per_month: Optional[int] = Field(None, ge=-1)
    encoding_minutes_per_month: Optional[int] = Field(None, ge=-1)
    concurrent_streams: Optional[int] = Field(None, ge=-1)
    
    features: Optional[list[str]] = None
    display_features: Optional[list[dict]] = None
    
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    stripe_product_id: Optional[str] = None
    
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanConfigListResponse(BaseModel):
    """Response for listing all plan configurations."""
    plans: list[PlanConfig]
    total: int


# ==================== Email Template Schemas (Requirements 27.1-27.5) ====================


class EmailTemplate(BaseModel):
    """Email Template configuration.
    
    Requirements: 27.1-27.5 - Email Template Management
    """
    template_id: str = Field(description="Unique template identifier")
    template_name: str = Field(description="Display name of the template")
    subject: str = Field(description="Email subject line")
    body_html: str = Field(description="HTML body content")
    body_text: str = Field(description="Plain text body content")
    variables: list[str] = Field(
        default=[], description="Available template variables"
    )
    is_active: bool = Field(
        default=True, description="Whether the template is active"
    )
    category: str = Field(
        default="general", description="Template category"
    )


class EmailTemplateUpdate(BaseModel):
    """Update schema for email template."""
    template_name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[list[str]] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None


class EmailTemplatePreview(BaseModel):
    """Preview request for email template."""
    sample_data: dict = Field(
        default={}, description="Sample data for template variables"
    )


class EmailTemplatePreviewResponse(BaseModel):
    """Response for email template preview."""
    subject: str
    body_html: str
    body_text: str


class EmailTemplateListResponse(BaseModel):
    """Response for listing all email templates."""
    templates: list[EmailTemplate]
    total: int


# ==================== Feature Flag Schemas (Requirements 28.1-28.5) ====================


class FeatureFlag(BaseModel):
    """Feature Flag configuration.
    
    Requirements: 28.1-28.5 - Feature Flag Management
    """
    flag_name: str = Field(description="Unique flag name")
    description: str = Field(
        default="", description="Description of the feature"
    )
    is_enabled: bool = Field(
        default=False, description="Whether the feature is enabled globally"
    )
    enabled_for_plans: list[str] = Field(
        default=[], description="Plans that have access to this feature"
    )
    enabled_for_users: list[str] = Field(
        default=[], description="Specific user IDs for beta testing"
    )
    rollout_percentage: int = Field(
        default=0, ge=0, le=100, description="Rollout percentage (0-100)"
    )


class FeatureFlagUpdate(BaseModel):
    """Update schema for feature flag."""
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    enabled_for_plans: Optional[list[str]] = None
    enabled_for_users: Optional[list[str]] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)


class FeatureFlagListResponse(BaseModel):
    """Response for listing all feature flags."""
    flags: list[FeatureFlag]
    total: int


# ==================== Branding Config Schemas (Requirements 29.1-29.5) ====================


class BrandingConfig(BaseModel):
    """Platform Branding configuration.
    
    Requirements: 29.1-29.5 - Platform Branding Configuration
    """
    platform_name: str = Field(
        default="YouTube Automation", description="Platform name"
    )
    tagline: str = Field(
        default="Automate Your YouTube Success", description="Platform tagline"
    )
    logo_url: Optional[str] = Field(
        default=None, description="Logo URL"
    )
    favicon_url: Optional[str] = Field(
        default=None, description="Favicon URL"
    )
    primary_color: str = Field(
        default="#EF4444", description="Primary brand color"
    )
    secondary_color: str = Field(
        default="#1F2937", description="Secondary brand color"
    )
    accent_color: str = Field(
        default="#10B981", description="Accent color"
    )
    support_email: str = Field(
        default="support@example.com", description="Support email address"
    )
    support_url: Optional[str] = Field(
        default=None, description="Support page URL"
    )
    documentation_url: Optional[str] = Field(
        default=None, description="Documentation URL"
    )
    terms_of_service_url: Optional[str] = Field(
        default=None, description="Terms of Service URL"
    )
    privacy_policy_url: Optional[str] = Field(
        default=None, description="Privacy Policy URL"
    )
    social_links: dict[str, str] = Field(
        default={}, description="Social media links"
    )
    footer_text: str = Field(
        default="© 2024 YouTube Automation. All rights reserved.",
        description="Footer text"
    )
    maintenance_mode: bool = Field(
        default=False, description="Enable maintenance mode"
    )
    maintenance_message: Optional[str] = Field(
        default=None, description="Maintenance mode message"
    )


class BrandingConfigUpdate(BaseModel):
    """Update schema for branding configuration."""
    platform_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    support_email: Optional[str] = None
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    social_links: Optional[dict[str, str]] = None
    footer_text: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None


# ==================== Resource Limit Warning Schemas (Requirements 16.2) ====================


class ResourceUsage(BaseModel):
    """Resource usage information for a user."""
    user_id: uuid.UUID
    resource_type: str
    current_usage: float
    limit: float
    percentage: float
    warning_level: Optional[str] = None  # "warning_75", "warning_90", or None


class ResourceLimitWarning(BaseModel):
    """Resource limit warning notification.
    
    Requirements: 16.2 - Send warning notification at 75% and 90% thresholds
    
    Property 14: Resource Limit Warnings
    - For any user resource usage check, warnings SHALL be sent at 75% and 90% of plan limits.
    """
    user_id: uuid.UUID
    resource_type: str
    current_usage: float
    limit: float
    percentage: float
    threshold: int  # 75 or 90
    message: str


class ResourceLimitCheckResult(BaseModel):
    """Result of checking resource limits for a user."""
    user_id: uuid.UUID
    warnings: list[ResourceLimitWarning]
    resources: list[ResourceUsage]
