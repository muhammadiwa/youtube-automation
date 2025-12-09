"""Pydantic schemas for Integration Service.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class APIKeyScope(str, Enum):
    """API key permission scopes."""
    READ_ACCOUNTS = "read:accounts"
    READ_VIDEOS = "read:videos"
    READ_STREAMS = "read:streams"
    READ_ANALYTICS = "read:analytics"
    READ_COMMENTS = "read:comments"
    WRITE_VIDEOS = "write:videos"
    WRITE_STREAMS = "write:streams"
    WRITE_COMMENTS = "write:comments"
    ADMIN_ACCOUNTS = "admin:accounts"
    ADMIN_WEBHOOKS = "admin:webhooks"
    FULL_ACCESS = "*"


class WebhookEventType(str, Enum):
    """Types of events that can trigger webhooks."""
    VIDEO_UPLOADED = "video.uploaded"
    VIDEO_PUBLISHED = "video.published"
    VIDEO_DELETED = "video.deleted"
    VIDEO_METADATA_UPDATED = "video.metadata_updated"
    STREAM_STARTED = "stream.started"
    STREAM_ENDED = "stream.ended"
    STREAM_HEALTH_CHANGED = "stream.health_changed"
    ACCOUNT_CONNECTED = "account.connected"
    ACCOUNT_DISCONNECTED = "account.disconnected"
    ACCOUNT_TOKEN_EXPIRED = "account.token_expired"
    COMMENT_RECEIVED = "comment.received"
    COMMENT_REPLIED = "comment.replied"
    ANALYTICS_UPDATED = "analytics.updated"
    REVENUE_UPDATED = "revenue.updated"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"


class WebhookDeliveryStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# ==================== API Key Schemas (29.1, 29.2) ====================

class APIKeyCreate(BaseModel):
    """Schema for creating an API key.
    
    Requirements: 29.1 - Generate scoped keys
    """
    name: str = Field(..., min_length=1, max_length=255, description="Key name")
    description: Optional[str] = Field(None, max_length=1000, description="Key description")
    scopes: list[str] = Field(..., min_length=1, description="Permission scopes")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(1000, ge=1, le=100000, description="Rate limit per hour")
    rate_limit_per_day: int = Field(10000, ge=1, le=1000000, description="Rate limit per day")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    allowed_ips: Optional[list[str]] = Field(None, description="Allowed IP addresses")

    @field_validator('scopes')
    @classmethod
    def validate_scopes(cls, v):
        valid_scopes = {s.value for s in APIKeyScope}
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}")
        return v


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: Optional[list[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    expires_at: Optional[datetime] = None
    allowed_ips: Optional[list[str]] = None
    is_active: Optional[bool] = None


class APIKeyResponse(BaseModel):
    """Response schema for API key (without full key)."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    key_prefix: str
    scopes: list[str]
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_per_day: int
    total_requests: int
    last_used_at: Optional[datetime]
    is_active: bool
    revoked_at: Optional[datetime]
    expires_at: Optional[datetime]
    allowed_ips: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    """Response schema for newly created API key (includes full key).
    
    The full key is only shown once at creation time.
    """
    key: str = Field(..., description="Full API key (only shown once)")


class APIKeyListResponse(BaseModel):
    """Paginated list of API keys."""
    keys: list[APIKeyResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class APIKeyRevokeRequest(BaseModel):
    """Request to revoke an API key.
    
    Requirements: 29.1 - Revocation support
    """
    reason: Optional[str] = Field(None, max_length=500, description="Revocation reason")


# ==================== Rate Limiting Schemas (29.2) ====================

class RateLimitStatus(BaseModel):
    """Current rate limit status for an API key.
    
    Requirements: 29.2 - Rate limiting per key
    """
    api_key_id: uuid.UUID
    minute_limit: int
    minute_used: int
    minute_remaining: int
    hour_limit: int
    hour_used: int
    hour_remaining: int
    day_limit: int
    day_used: int
    day_remaining: int
    is_rate_limited: bool
    reset_at: datetime


class RateLimitExceededResponse(BaseModel):
    """Response when rate limit is exceeded.
    
    Requirements: 29.2 - Reject exceeded requests
    """
    error: str = "rate_limit_exceeded"
    message: str
    retry_after_seconds: int
    limit_type: str  # 'minute', 'hour', 'day'


# ==================== Webhook Schemas (29.3, 29.4) ====================

class WebhookCreate(BaseModel):
    """Schema for creating a webhook.
    
    Requirements: 29.3 - Configure webhook
    """
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., max_length=2048, description="Webhook URL")
    events: list[str] = Field(..., min_length=1, description="Event types to subscribe to")
    custom_headers: Optional[dict[str, str]] = Field(None, description="Custom headers")
    max_retries: int = Field(5, ge=1, le=10, description="Max retry attempts")
    retry_delay_seconds: int = Field(60, ge=10, le=3600, description="Initial retry delay")

    @field_validator('events')
    @classmethod
    def validate_events(cls, v):
        valid_events = {e.value for e in WebhookEventType}
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}")
        return v

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(None, max_length=2048)
    events: Optional[list[str]] = None
    custom_headers: Optional[dict[str, str]] = None
    max_retries: Optional[int] = Field(None, ge=1, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=10, le=3600)
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Response schema for webhook."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    url: str
    events: list[str]
    custom_headers: Optional[dict[str, str]]
    is_active: bool
    max_retries: int
    retry_delay_seconds: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: Optional[datetime]
    last_delivery_status: Optional[str]
    created_at: datetime
    updated_at: datetime
    # Secret is only shown at creation
    secret: Optional[str] = None

    class Config:
        from_attributes = True


class WebhookCreateResponse(WebhookResponse):
    """Response for newly created webhook (includes secret)."""
    secret: str = Field(..., description="Webhook secret (only shown once)")


class WebhookListResponse(BaseModel):
    """Paginated list of webhooks."""
    webhooks: list[WebhookResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class WebhookTestRequest(BaseModel):
    """Request to test a webhook."""
    event_type: str = Field(default="test.ping", description="Event type for test")


class WebhookTestResponse(BaseModel):
    """Response from webhook test."""
    success: bool
    status_code: Optional[int]
    response_time_ms: Optional[int]
    error: Optional[str]


# ==================== Webhook Delivery Schemas ====================

class WebhookDeliveryInfo(BaseModel):
    """Webhook delivery information."""
    id: uuid.UUID
    webhook_id: uuid.UUID
    event_type: str
    event_id: uuid.UUID
    status: str
    attempts: int
    max_attempts: int
    next_retry_at: Optional[datetime]
    response_status_code: Optional[int]
    response_time_ms: Optional[int]
    last_error: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookDeliveryListResponse(BaseModel):
    """Paginated list of webhook deliveries."""
    deliveries: list[WebhookDeliveryInfo]
    total: int
    page: int
    page_size: int
    has_more: bool


class WebhookDeliveryFilters(BaseModel):
    """Filters for webhook delivery listing."""
    status: Optional[WebhookDeliveryStatus] = None
    event_type: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# ==================== Webhook Event Payload ====================

class WebhookEventPayload(BaseModel):
    """Standard webhook event payload structure."""
    id: uuid.UUID = Field(..., description="Unique event ID")
    type: str = Field(..., description="Event type")
    created_at: datetime = Field(..., description="Event timestamp")
    data: dict = Field(..., description="Event data")
    user_id: uuid.UUID = Field(..., description="User ID")
    account_id: Optional[uuid.UUID] = Field(None, description="Associated account ID")


# ==================== API Documentation Schemas (29.5) ====================

class APIEndpointInfo(BaseModel):
    """Information about an API endpoint."""
    path: str
    method: str
    summary: str
    description: Optional[str]
    required_scopes: list[str]
    rate_limited: bool


class APIDocumentationResponse(BaseModel):
    """API documentation overview.
    
    Requirements: 29.5 - OpenAPI specification with examples
    """
    version: str
    title: str
    description: str
    base_url: str
    endpoints: list[APIEndpointInfo]
    available_scopes: list[dict[str, str]]
    available_events: list[dict[str, str]]
