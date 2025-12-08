"""Pydantic schemas for moderation module.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.moderation.models import (
    ModerationActionType,
    RuleType,
    SeverityLevel,
)


# ============================================
# Moderation Rule Schemas
# ============================================


class ModerationRuleBase(BaseModel):
    """Base schema for moderation rules."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: RuleType
    pattern: Optional[str] = None
    keywords: Optional[list[str]] = None
    settings: Optional[dict] = None
    caps_threshold_percent: Optional[int] = Field(default=70, ge=0, le=100)
    min_message_length: Optional[int] = Field(default=5, ge=1)
    action_type: ModerationActionType = ModerationActionType.HIDE
    severity: SeverityLevel = SeverityLevel.MEDIUM
    timeout_duration_seconds: Optional[int] = Field(default=None, ge=1)
    is_enabled: bool = True
    priority: int = Field(default=0, ge=0)


class ModerationRuleCreate(ModerationRuleBase):
    """Schema for creating a moderation rule."""

    account_id: uuid.UUID


class ModerationRuleUpdate(BaseModel):
    """Schema for updating a moderation rule."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    pattern: Optional[str] = None
    keywords: Optional[list[str]] = None
    settings: Optional[dict] = None
    caps_threshold_percent: Optional[int] = Field(default=None, ge=0, le=100)
    min_message_length: Optional[int] = Field(default=None, ge=1)
    action_type: Optional[ModerationActionType] = None
    severity: Optional[SeverityLevel] = None
    timeout_duration_seconds: Optional[int] = Field(default=None, ge=1)
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0)


class ModerationRuleResponse(ModerationRuleBase):
    """Schema for moderation rule response."""

    id: uuid.UUID
    account_id: uuid.UUID
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Chat Message Schemas
# ============================================


class ChatMessageBase(BaseModel):
    """Base schema for chat messages."""

    youtube_message_id: str
    youtube_live_chat_id: str
    author_channel_id: str
    author_display_name: str
    author_profile_image_url: Optional[str] = None
    is_moderator: bool = False
    is_owner: bool = False
    is_member: bool = False
    content: str
    message_type: str = "text"
    super_chat_amount: Optional[float] = None
    super_chat_currency: Optional[str] = None
    published_at: datetime


class ChatMessageCreate(ChatMessageBase):
    """Schema for creating a chat message."""

    account_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class ChatMessageResponse(ChatMessageBase):
    """Schema for chat message response."""

    id: uuid.UUID
    account_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    is_moderated: bool
    is_hidden: bool
    is_deleted: bool
    moderation_reason: Optional[str]
    moderated_at: Optional[datetime]
    analysis_completed: bool
    violated_rules: Optional[list[str]]
    received_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Moderation Analysis Schemas
# ============================================


class ModerationAnalysisRequest(BaseModel):
    """Schema for requesting moderation analysis."""

    message: ChatMessageCreate
    rules: Optional[list[uuid.UUID]] = None  # Specific rules to check, or all if None


class RuleViolation(BaseModel):
    """Schema for a rule violation."""

    rule_id: uuid.UUID
    rule_name: str
    rule_type: RuleType
    severity: SeverityLevel
    action_type: ModerationActionType
    matched_pattern: Optional[str] = None
    timeout_duration_seconds: Optional[int] = None


class ModerationAnalysisResult(BaseModel):
    """Schema for moderation analysis result."""

    message_id: str
    is_violation: bool
    violations: list[RuleViolation]
    processing_time_ms: float
    recommended_action: Optional[ModerationActionType] = None
    recommended_severity: Optional[SeverityLevel] = None


# ============================================
# Moderation Action Schemas
# ============================================


class ModerationActionRequest(BaseModel):
    """Schema for requesting a moderation action."""

    message_id: str
    action_type: ModerationActionType
    reason: str
    timeout_duration_seconds: Optional[int] = None


class ModerationActionLogResponse(BaseModel):
    """Schema for moderation action log response."""

    id: uuid.UUID
    rule_id: Optional[uuid.UUID]
    account_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    action_type: str
    severity: str
    user_channel_id: str
    user_display_name: Optional[str]
    message_id: Optional[str]
    message_content: Optional[str]
    reason: str
    was_successful: bool
    error_message: Optional[str]
    timeout_duration_seconds: Optional[int]
    timeout_expires_at: Optional[datetime]
    processing_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Slow Mode Schemas
# ============================================


class SlowModeConfigBase(BaseModel):
    """Base schema for slow mode configuration."""

    is_enabled: bool = False
    delay_seconds: int = Field(default=30, ge=1, le=300)
    auto_enable: bool = True
    spam_threshold_per_minute: int = Field(default=10, ge=1)
    auto_disable_after_minutes: Optional[int] = Field(default=5, ge=1)


class SlowModeConfigCreate(SlowModeConfigBase):
    """Schema for creating slow mode configuration."""

    account_id: uuid.UUID


class SlowModeConfigUpdate(BaseModel):
    """Schema for updating slow mode configuration."""

    is_enabled: Optional[bool] = None
    delay_seconds: Optional[int] = Field(default=None, ge=1, le=300)
    auto_enable: Optional[bool] = None
    spam_threshold_per_minute: Optional[int] = Field(default=None, ge=1)
    auto_disable_after_minutes: Optional[int] = Field(default=None, ge=1)


class SlowModeConfigResponse(SlowModeConfigBase):
    """Schema for slow mode configuration response."""

    id: uuid.UUID
    account_id: uuid.UUID
    is_currently_active: bool
    activated_at: Optional[datetime]
    auto_disable_at: Optional[datetime]
    activation_count: int
    last_activated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Custom Command Schemas
# ============================================


class CustomCommandBase(BaseModel):
    """Base schema for custom commands."""

    trigger: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    response_type: str = "text"
    response_text: Optional[str] = None
    action_type: Optional[str] = None
    webhook_url: Optional[str] = None
    is_enabled: bool = True
    moderator_only: bool = False
    member_only: bool = False
    cooldown_seconds: int = Field(default=5, ge=0)


class CustomCommandCreate(CustomCommandBase):
    """Schema for creating a custom command."""

    account_id: uuid.UUID


class CustomCommandUpdate(BaseModel):
    """Schema for updating a custom command."""

    trigger: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    response_type: Optional[str] = None
    response_text: Optional[str] = None
    action_type: Optional[str] = None
    webhook_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    moderator_only: Optional[bool] = None
    member_only: Optional[bool] = None
    cooldown_seconds: Optional[int] = Field(default=None, ge=0)


class CustomCommandResponse(CustomCommandBase):
    """Schema for custom command response."""

    id: uuid.UUID
    account_id: uuid.UUID
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
