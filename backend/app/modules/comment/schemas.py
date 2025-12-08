"""Pydantic schemas for comment module.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.modules.comment.models import CommentSentiment, CommentStatus


# ============================================
# Comment Schemas
# ============================================


class CommentBase(BaseModel):
    """Base schema for comments."""

    youtube_comment_id: str
    youtube_video_id: str
    youtube_parent_id: Optional[str] = None
    author_channel_id: str
    author_display_name: str
    author_profile_image_url: Optional[str] = None
    text_original: str
    text_display: str
    like_count: int = 0
    reply_count: int = 0
    is_public: bool = True
    can_reply: bool = True
    published_at: datetime


class CommentCreate(CommentBase):
    """Schema for creating a comment."""

    account_id: uuid.UUID
    video_id: Optional[uuid.UUID] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    status: Optional[CommentStatus] = None
    sentiment: Optional[CommentSentiment] = None
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    requires_attention: Optional[bool] = None
    like_count: Optional[int] = None
    reply_count: Optional[int] = None


class CommentResponse(CommentBase):
    """Schema for comment response."""

    id: uuid.UUID
    account_id: uuid.UUID
    video_id: Optional[uuid.UUID]
    status: str
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    requires_attention: bool
    sentiment_analyzed_at: Optional[datetime]
    auto_replied: bool
    auto_reply_rule_id: Optional[uuid.UUID]
    synced_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Schema for paginated comment list response."""

    comments: list[CommentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# Sentiment Analysis Schemas
# ============================================


class SentimentAnalysisRequest(BaseModel):
    """Schema for sentiment analysis request."""

    comment_ids: list[uuid.UUID]


class SentimentResult(BaseModel):
    """Schema for individual sentiment result."""

    comment_id: uuid.UUID
    sentiment: CommentSentiment
    score: float = Field(..., ge=-1.0, le=1.0)
    requires_attention: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    keywords: list[str] = []


class SentimentAnalysisResult(BaseModel):
    """Schema for sentiment analysis result."""

    results: list[SentimentResult]
    analyzed_count: int
    attention_required_count: int
    processing_time_ms: float


# ============================================
# Auto-Reply Rule Schemas
# ============================================


class AutoReplyRuleBase(BaseModel):
    """Base schema for auto-reply rules."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: Literal["keyword", "regex", "sentiment", "all"] = "keyword"
    trigger_keywords: Optional[list[str]] = None
    trigger_pattern: Optional[str] = None
    trigger_sentiment: Optional[CommentSentiment] = None
    case_sensitive: bool = False
    response_text: str = Field(..., min_length=1)
    response_delay_seconds: int = Field(default=0, ge=0)
    is_enabled: bool = True
    priority: int = Field(default=0, ge=0)
    max_replies_per_video: Optional[int] = Field(default=None, ge=1)
    max_replies_per_day: Optional[int] = Field(default=None, ge=1)


class AutoReplyRuleCreate(AutoReplyRuleBase):
    """Schema for creating an auto-reply rule."""

    account_id: uuid.UUID


class AutoReplyRuleUpdate(BaseModel):
    """Schema for updating an auto-reply rule."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[Literal["keyword", "regex", "sentiment", "all"]] = None
    trigger_keywords: Optional[list[str]] = None
    trigger_pattern: Optional[str] = None
    trigger_sentiment: Optional[CommentSentiment] = None
    case_sensitive: Optional[bool] = None
    response_text: Optional[str] = Field(default=None, min_length=1)
    response_delay_seconds: Optional[int] = Field(default=None, ge=0)
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0)
    max_replies_per_video: Optional[int] = Field(default=None, ge=1)
    max_replies_per_day: Optional[int] = Field(default=None, ge=1)


class AutoReplyRuleResponse(AutoReplyRuleBase):
    """Schema for auto-reply rule response."""

    id: uuid.UUID
    account_id: uuid.UUID
    trigger_count: int
    last_triggered_at: Optional[datetime]
    replies_today: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Comment Reply Schemas
# ============================================


class CommentReplyBase(BaseModel):
    """Base schema for comment replies."""

    text: str = Field(..., min_length=1)


class CommentReplyCreate(CommentReplyBase):
    """Schema for creating a comment reply."""

    comment_id: uuid.UUID
    account_id: uuid.UUID
    is_auto_reply: bool = False
    auto_reply_rule_id: Optional[uuid.UUID] = None


class CommentReplyResponse(CommentReplyBase):
    """Schema for comment reply response."""

    id: uuid.UUID
    comment_id: uuid.UUID
    account_id: uuid.UUID
    youtube_reply_id: Optional[str]
    status: str
    error_message: Optional[str]
    is_auto_reply: bool
    auto_reply_rule_id: Optional[uuid.UUID]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Bulk Moderation Schemas
# ============================================


class BulkModerationAction(BaseModel):
    """Schema for a single bulk moderation action."""

    comment_id: uuid.UUID
    action: Literal["approve", "hide", "delete", "spam"]


class BulkModerationRequest(BaseModel):
    """Schema for bulk moderation request.
    
    Requirements: 13.5
    """

    actions: list[BulkModerationAction] = Field(..., min_length=1)


class BulkModerationResult(BaseModel):
    """Schema for individual bulk moderation result."""

    comment_id: uuid.UUID
    action: str
    success: bool
    error_message: Optional[str] = None


class BulkModerationResponse(BaseModel):
    """Schema for bulk moderation response.
    
    Requirements: 13.5
    """

    results: list[BulkModerationResult]
    total_processed: int
    successful_count: int
    failed_count: int


# ============================================
# Comment Sync Schemas
# ============================================


class CommentSyncRequest(BaseModel):
    """Schema for comment sync request."""

    account_ids: Optional[list[uuid.UUID]] = None  # None = all accounts
    video_ids: Optional[list[str]] = None  # Specific videos to sync
    since: Optional[datetime] = None  # Only sync comments after this time


class CommentSyncStatus(BaseModel):
    """Schema for comment sync status."""

    account_id: uuid.UUID
    last_sync_at: Optional[datetime]
    comments_synced: int
    new_comments: int
    status: Literal["pending", "in_progress", "completed", "failed"]
    error_message: Optional[str] = None


class CommentSyncResponse(BaseModel):
    """Schema for comment sync response."""

    sync_statuses: list[CommentSyncStatus]
    total_comments_synced: int
    total_new_comments: int
