"""Pydantic schemas for YouTube Account module.

Request/Response models for OAuth2 flow and account management.
Requirements: 2.1, 2.2
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OAuthInitiateResponse(BaseModel):
    """Response for OAuth initiation endpoint."""

    authorization_url: str = Field(..., description="URL to redirect user for OAuth consent")
    state: str = Field(..., description="State parameter for CSRF protection")


class OAuthCallbackRequest(BaseModel):
    """Request for OAuth callback endpoint."""

    code: str = Field(..., description="Authorization code from YouTube")
    state: str = Field(..., description="State parameter for verification")


class YouTubeAccountResponse(BaseModel):
    """Response model for YouTube account."""

    id: uuid.UUID
    user_id: uuid.UUID
    channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    is_monetized: bool = False
    has_live_streaming_enabled: bool = False
    strike_count: int = 0
    token_expires_at: Optional[datetime] = None
    daily_quota_used: int = 0
    status: str
    last_sync_at: Optional[datetime] = None
    # Stream key info (masked for security)
    has_stream_key: bool = False
    stream_key_masked: Optional[str] = None
    rtmp_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to add computed fields."""
        # Get base validation
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "channel_id": obj.channel_id,
            "channel_title": obj.channel_title,
            "thumbnail_url": obj.thumbnail_url,
            "subscriber_count": obj.subscriber_count,
            "video_count": obj.video_count,
            "view_count": obj.view_count,
            "is_monetized": obj.is_monetized,
            "has_live_streaming_enabled": obj.has_live_streaming_enabled,
            "strike_count": obj.strike_count,
            "token_expires_at": obj.token_expires_at,
            "daily_quota_used": obj.daily_quota_used,
            "status": obj.status,
            "last_sync_at": obj.last_sync_at,
            "has_stream_key": obj.has_stream_key() if hasattr(obj, 'has_stream_key') else False,
            "stream_key_masked": obj.get_masked_stream_key() if hasattr(obj, 'get_masked_stream_key') else None,
            "rtmp_url": obj.rtmp_url if hasattr(obj, 'rtmp_url') else None,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return cls(**data)


class AccountHealthResponse(BaseModel):
    """Response model for account health status."""

    account_id: uuid.UUID
    channel_title: str
    status: str
    is_token_expired: bool
    is_token_expiring_soon: bool
    token_expires_at: Optional[datetime] = None
    quota_usage_percent: float
    daily_quota_used: int
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None


class QuotaUsageResponse(BaseModel):
    """Response model for quota usage."""

    account_id: uuid.UUID
    daily_quota_used: int
    daily_limit: int = 10000
    usage_percent: float
    quota_reset_at: Optional[datetime] = None
    is_approaching_limit: bool


class ChannelMetadata(BaseModel):
    """Channel metadata from YouTube API."""

    channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    is_monetized: bool = False
    has_live_streaming_enabled: bool = False


class AccountListResponse(BaseModel):
    """Response model for list of accounts."""

    accounts: list[YouTubeAccountResponse]
    total: int
