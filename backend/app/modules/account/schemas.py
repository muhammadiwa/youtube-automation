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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
