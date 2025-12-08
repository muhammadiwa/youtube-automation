"""SQLAlchemy models for AI Chatbot module.

Stores chatbot configuration, triggers, and interaction logs.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PersonalityType(str, Enum):
    """Chatbot personality types.
    
    Requirements: 11.2 - Personality customization
    """
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    INFORMATIVE = "informative"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"


class ResponseStyle(str, Enum):
    """Chatbot response style settings.
    
    Requirements: 11.2 - Response style settings
    """
    CONCISE = "concise"  # Short, to-the-point responses
    DETAILED = "detailed"  # More elaborate responses
    CASUAL = "casual"  # Informal language
    FORMAL = "formal"  # Professional language
    EMOJI_RICH = "emoji_rich"  # Uses emojis frequently


class TriggerType(str, Enum):
    """Types of chatbot triggers.
    
    Requirements: 11.1 - Matching configured triggers
    """
    KEYWORD = "keyword"  # Match specific keywords
    QUESTION = "question"  # Match question patterns
    GREETING = "greeting"  # Match greetings
    COMMAND = "command"  # Match command patterns (e.g., !ask)
    MENTION = "mention"  # Match bot mentions
    REGEX = "regex"  # Match regex patterns


class ChatbotConfig(Base):
    """Chatbot Configuration model.

    Stores chatbot settings including personality and response style.
    Requirements: 11.2
    """

    __tablename__ = "chatbot_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Bot identification (Requirements: 11.3)
    bot_name: Mapped[str] = mapped_column(String(100), nullable=False, default="StreamBot")
    bot_prefix: Mapped[str] = mapped_column(String(50), nullable=False, default="[BOT]")

    # Personality settings (Requirements: 11.2)
    personality: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PersonalityType.FRIENDLY.value
    )
    response_style: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ResponseStyle.CONCISE.value
    )
    custom_personality_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response settings
    max_response_length: Mapped[int] = mapped_column(Integer, default=200)
    response_language: Mapped[str] = mapped_column(String(10), default="en")
    use_emojis: Mapped[bool] = mapped_column(Boolean, default=True)

    # Behavior settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)  # For streamer takeover
    response_delay_ms: Mapped[int] = mapped_column(Integer, default=500)  # Min delay before responding
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=5)  # Per-user cooldown

    # Content filtering (Requirements: 11.4)
    content_filter_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    blocked_topics: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    blocked_keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Streamer takeover (Requirements: 11.5)
    takeover_command: Mapped[str] = mapped_column(String(50), default="!botpause")
    resume_command: Mapped[str] = mapped_column(String(50), default="!botresume")
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Statistics
    total_responses: Mapped[int] = mapped_column(Integer, default=0)
    total_declined: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    triggers: Mapped[list["ChatbotTrigger"]] = relationship(
        "ChatbotTrigger",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    interactions: Mapped[list["ChatbotInteractionLog"]] = relationship(
        "ChatbotInteractionLog",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    def pause(self, paused_by: str) -> None:
        """Pause the chatbot (streamer takeover).
        
        Requirements: 11.5
        
        Args:
            paused_by: Channel ID of who paused the bot
        """
        self.is_paused = True
        self.paused_at = datetime.utcnow()
        self.paused_by = paused_by

    def resume(self) -> None:
        """Resume the chatbot after takeover.
        
        Requirements: 11.5
        """
        self.is_paused = False
        self.paused_at = None
        self.paused_by = None

    def is_active(self) -> bool:
        """Check if chatbot is active and can respond."""
        return self.is_enabled and not self.is_paused

    def increment_response_count(self, response_time_ms: float) -> None:
        """Increment response count and update average response time."""
        total = self.total_responses * self.avg_response_time_ms
        self.total_responses += 1
        self.avg_response_time_ms = (total + response_time_ms) / self.total_responses

    def increment_declined_count(self) -> None:
        """Increment declined response count."""
        self.total_declined += 1

    def __repr__(self) -> str:
        return f"<ChatbotConfig(id={self.id}, bot_name={self.bot_name}, enabled={self.is_enabled})>"



class ChatbotTrigger(Base):
    """Chatbot Trigger model for defining when the bot responds.

    Stores trigger patterns that activate the chatbot.
    Requirements: 11.1
    """

    __tablename__ = "chatbot_triggers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chatbot_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Trigger configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TriggerType.KEYWORD.value
    )
    pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For regex
    keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Response customization
    custom_response_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = checked first

    # State
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    config: Mapped["ChatbotConfig"] = relationship(
        "ChatbotConfig", back_populates="triggers"
    )

    def increment_trigger_count(self) -> None:
        """Increment trigger count and update last triggered time."""
        self.trigger_count += 1
        self.last_triggered_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ChatbotTrigger(id={self.id}, name={self.name}, type={self.trigger_type})>"


class ChatbotInteractionLog(Base):
    """Chatbot Interaction Log model for tracking all interactions.

    Records all chatbot interactions including declined requests.
    Requirements: 11.4
    """

    __tablename__ = "chatbot_interaction_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chatbot_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trigger_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chatbot_triggers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # User information
    user_channel_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Message information
    input_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    input_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Response information
    was_responded: Mapped[bool] = mapped_column(Boolean, default=False)
    response_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Decline information (Requirements: 11.4)
    was_declined: Mapped[bool] = mapped_column(Boolean, default=False)
    decline_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timing (Requirements: 11.1 - within 3 seconds)
    processing_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Metadata
    matched_trigger_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    matched_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    config: Mapped["ChatbotConfig"] = relationship(
        "ChatbotConfig", back_populates="interactions"
    )

    def complete_response(self, response_content: str, response_message_id: str) -> None:
        """Mark interaction as responded.
        
        Args:
            response_content: The response sent
            response_message_id: YouTube message ID of response
        """
        self.was_responded = True
        self.response_content = response_content
        self.response_message_id = response_message_id
        self.processing_completed_at = datetime.utcnow()
        if self.processing_started_at:
            delta = self.processing_completed_at - self.processing_started_at
            self.response_time_ms = delta.total_seconds() * 1000

    def mark_declined(self, reason: str) -> None:
        """Mark interaction as declined.
        
        Requirements: 11.4
        
        Args:
            reason: Reason for declining
        """
        self.was_declined = True
        self.decline_reason = reason
        self.processing_completed_at = datetime.utcnow()
        if self.processing_started_at:
            delta = self.processing_completed_at - self.processing_started_at
            self.response_time_ms = delta.total_seconds() * 1000

    def was_within_time_limit(self, limit_seconds: float = 3.0) -> bool:
        """Check if response was within time limit.
        
        Requirements: 11.1 - within 3 seconds
        
        Args:
            limit_seconds: Time limit in seconds (default 3.0)
            
        Returns:
            bool: True if within limit
        """
        if self.response_time_ms is None:
            return False
        return self.response_time_ms <= (limit_seconds * 1000)

    def __repr__(self) -> str:
        return f"<ChatbotInteractionLog(id={self.id}, responded={self.was_responded})>"
