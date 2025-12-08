"""Pydantic schemas for AI Chatbot module.

Defines request/response schemas for chatbot configuration and responses.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.modules.ai.chatbot.models import PersonalityType, ResponseStyle, TriggerType


# Trigger Schemas
class TriggerCreate(BaseModel):
    """Schema for creating a chatbot trigger."""

    name: str = Field(..., min_length=1, max_length=100)
    trigger_type: TriggerType = Field(default=TriggerType.KEYWORD)
    pattern: Optional[str] = Field(None, max_length=1000)
    keywords: Optional[list[str]] = Field(None, max_length=50)
    custom_response_prompt: Optional[str] = Field(None, max_length=2000)
    priority: int = Field(default=0, ge=0, le=100)
    is_enabled: bool = Field(default=True)


class TriggerUpdate(BaseModel):
    """Schema for updating a chatbot trigger."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    trigger_type: Optional[TriggerType] = None
    pattern: Optional[str] = Field(None, max_length=1000)
    keywords: Optional[list[str]] = Field(None, max_length=50)
    custom_response_prompt: Optional[str] = Field(None, max_length=2000)
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_enabled: Optional[bool] = None


class TriggerResponse(BaseModel):
    """Schema for trigger response."""

    id: uuid.UUID
    config_id: uuid.UUID
    name: str
    trigger_type: str
    pattern: Optional[str]
    keywords: Optional[list[str]]
    custom_response_prompt: Optional[str]
    priority: int
    is_enabled: bool
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True



# Chatbot Config Schemas
class ChatbotConfigCreate(BaseModel):
    """Schema for creating chatbot configuration.
    
    Requirements: 11.2 - Personality customization, Response style settings
    """

    bot_name: str = Field(default="StreamBot", min_length=1, max_length=100)
    bot_prefix: str = Field(default="[BOT]", min_length=1, max_length=50)
    personality: PersonalityType = Field(default=PersonalityType.FRIENDLY)
    response_style: ResponseStyle = Field(default=ResponseStyle.CONCISE)
    custom_personality_prompt: Optional[str] = Field(None, max_length=2000)
    max_response_length: int = Field(default=200, ge=50, le=500)
    response_language: str = Field(default="en", min_length=2, max_length=10)
    use_emojis: bool = Field(default=True)
    response_delay_ms: int = Field(default=500, ge=0, le=5000)
    cooldown_seconds: int = Field(default=5, ge=0, le=300)
    content_filter_enabled: bool = Field(default=True)
    blocked_topics: Optional[list[str]] = Field(None, max_length=50)
    blocked_keywords: Optional[list[str]] = Field(None, max_length=100)
    takeover_command: str = Field(default="!botpause", min_length=1, max_length=50)
    resume_command: str = Field(default="!botresume", min_length=1, max_length=50)


class ChatbotConfigUpdate(BaseModel):
    """Schema for updating chatbot configuration."""

    bot_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bot_prefix: Optional[str] = Field(None, min_length=1, max_length=50)
    personality: Optional[PersonalityType] = None
    response_style: Optional[ResponseStyle] = None
    custom_personality_prompt: Optional[str] = Field(None, max_length=2000)
    max_response_length: Optional[int] = Field(None, ge=50, le=500)
    response_language: Optional[str] = Field(None, min_length=2, max_length=10)
    use_emojis: Optional[bool] = None
    is_enabled: Optional[bool] = None
    response_delay_ms: Optional[int] = Field(None, ge=0, le=5000)
    cooldown_seconds: Optional[int] = Field(None, ge=0, le=300)
    content_filter_enabled: Optional[bool] = None
    blocked_topics: Optional[list[str]] = Field(None, max_length=50)
    blocked_keywords: Optional[list[str]] = Field(None, max_length=100)
    takeover_command: Optional[str] = Field(None, min_length=1, max_length=50)
    resume_command: Optional[str] = Field(None, min_length=1, max_length=50)


class ChatbotConfigResponse(BaseModel):
    """Schema for chatbot configuration response."""

    id: uuid.UUID
    account_id: uuid.UUID
    bot_name: str
    bot_prefix: str
    personality: str
    response_style: str
    custom_personality_prompt: Optional[str]
    max_response_length: int
    response_language: str
    use_emojis: bool
    is_enabled: bool
    is_paused: bool
    response_delay_ms: int
    cooldown_seconds: int
    content_filter_enabled: bool
    blocked_topics: Optional[list[str]]
    blocked_keywords: Optional[list[str]]
    takeover_command: str
    resume_command: str
    paused_at: Optional[datetime]
    paused_by: Optional[str]
    total_responses: int
    total_declined: int
    avg_response_time_ms: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chat Response Schemas
class ChatResponseRequest(BaseModel):
    """Schema for requesting a chat response.
    
    Requirements: 11.1 - Generate responses within 3 seconds
    """

    message_id: str = Field(..., min_length=1, max_length=255)
    message_content: str = Field(..., min_length=1, max_length=2000)
    user_channel_id: str = Field(..., min_length=1, max_length=255)
    user_display_name: str = Field(..., min_length=1, max_length=255)
    is_moderator: bool = Field(default=False)
    is_member: bool = Field(default=False)
    is_owner: bool = Field(default=False)
    session_id: Optional[uuid.UUID] = None


class ChatResponseResult(BaseModel):
    """Schema for chat response result.
    
    Requirements: 11.1, 11.3, 11.4
    """

    should_respond: bool
    response_content: Optional[str] = None
    prefixed_response: Optional[str] = None  # With bot prefix (Requirements: 11.3)
    matched_trigger: Optional[str] = None
    matched_trigger_type: Optional[str] = None
    was_declined: bool = False
    decline_reason: Optional[str] = None
    response_time_ms: float
    interaction_id: Optional[uuid.UUID] = None


# Streamer Takeover Schemas (Requirements: 11.5)
class TakeoverRequest(BaseModel):
    """Schema for streamer takeover request."""

    command_by_channel_id: str = Field(..., min_length=1, max_length=255)


class TakeoverResponse(BaseModel):
    """Schema for streamer takeover response."""

    is_paused: bool
    paused_at: Optional[datetime]
    paused_by: Optional[str]
    pending_messages_count: int = 0


# Interaction Log Schemas
class InteractionLogResponse(BaseModel):
    """Schema for interaction log response."""

    id: uuid.UUID
    config_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    user_channel_id: str
    user_display_name: str
    input_message_id: str
    input_content: str
    was_responded: bool
    response_content: Optional[str]
    was_declined: bool
    decline_reason: Optional[str]
    response_time_ms: Optional[float]
    matched_trigger_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
