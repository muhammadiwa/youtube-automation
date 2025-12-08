"""Moderation models for chat moderation management.

Implements ModerationRule, ModerationAction, and ChatMessage models.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RuleType(str, Enum):
    """Types of moderation rules.
    
    Requirements: 12.1, 12.2
    """
    KEYWORD = "keyword"  # Match specific keywords
    REGEX = "regex"  # Match regex patterns
    SPAM = "spam"  # Spam detection patterns
    CAPS = "caps"  # Excessive caps detection
    LINKS = "links"  # Link filtering


class ModerationActionType(str, Enum):
    """Types of moderation actions.
    
    Requirements: 12.2
    """
    HIDE = "hide"  # Hide the message
    DELETE = "delete"  # Delete the message
    TIMEOUT = "timeout"  # Timeout the user
    WARN = "warn"  # Warn the user
    BAN = "ban"  # Ban the user


class SeverityLevel(str, Enum):
    """Severity levels for rule violations.
    
    Requirements: 12.2
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationRule(Base):
    """Moderation Rule model for chat moderation.

    Stores rule configuration including type, pattern, and action settings.
    Requirements: 12.1, 12.2
    """

    __tablename__ = "moderation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rule identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rule type and pattern (Requirements: 12.1, 12.2)
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    
    # Pattern configuration based on rule type
    # For KEYWORD: list of keywords to match
    # For REGEX: regex pattern string
    # For SPAM: spam detection settings
    # For CAPS: caps percentage threshold
    # For LINKS: link filtering settings
    pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    # Additional settings stored as JSON
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Caps-specific settings
    caps_threshold_percent: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=70
    )  # Percentage of caps to trigger
    min_message_length: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=5
    )  # Minimum message length to check

    # Action configuration (Requirements: 12.2)
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ModerationActionType.HIDE.value
    )
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SeverityLevel.MEDIUM.value
    )
    timeout_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # For TIMEOUT action

    # Rule state
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = checked first

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
    actions: Mapped[list["ModerationActionLog"]] = relationship(
        "ModerationActionLog",
        back_populates="rule",
        cascade="all, delete-orphan",
    )

    def is_keyword_rule(self) -> bool:
        """Check if this is a keyword-based rule."""
        return self.rule_type == RuleType.KEYWORD.value

    def is_regex_rule(self) -> bool:
        """Check if this is a regex-based rule."""
        return self.rule_type == RuleType.REGEX.value

    def is_spam_rule(self) -> bool:
        """Check if this is a spam detection rule."""
        return self.rule_type == RuleType.SPAM.value

    def is_caps_rule(self) -> bool:
        """Check if this is a caps detection rule."""
        return self.rule_type == RuleType.CAPS.value

    def is_links_rule(self) -> bool:
        """Check if this is a link filtering rule."""
        return self.rule_type == RuleType.LINKS.value

    def increment_trigger_count(self) -> None:
        """Increment trigger count and update last triggered time."""
        self.trigger_count += 1
        self.last_triggered_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ModerationRule(id={self.id}, name={self.name}, type={self.rule_type})>"



class ModerationActionLog(Base):
    """Moderation Action Log model for tracking moderation actions.

    Records all moderation actions taken with reason and affected user.
    Requirements: 12.2, 12.5
    """

    __tablename__ = "moderation_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderation_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action details (Requirements: 12.5)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SeverityLevel.MEDIUM.value
    )

    # Affected user information
    user_channel_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Message information
    message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Action reason and result
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    was_successful: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeout details
    timeout_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timeout_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Processing time tracking (Requirements: 12.1 - within 2 seconds)
    processing_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    processing_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    rule: Mapped[Optional["ModerationRule"]] = relationship(
        "ModerationRule", back_populates="actions"
    )

    def get_processing_time_ms(self) -> float:
        """Get processing time in milliseconds.
        
        Returns:
            float: Processing time in milliseconds
        """
        delta = self.processing_completed_at - self.processing_started_at
        return delta.total_seconds() * 1000

    def was_processed_within_limit(self, limit_seconds: float = 2.0) -> bool:
        """Check if action was processed within time limit.
        
        Args:
            limit_seconds: Time limit in seconds (default 2.0 per Requirements 12.1)
            
        Returns:
            bool: True if processed within limit
        """
        return self.get_processing_time_ms() <= (limit_seconds * 1000)

    def __repr__(self) -> str:
        return f"<ModerationActionLog(id={self.id}, action={self.action_type}, user={self.user_channel_id})>"


class ChatMessage(Base):
    """Chat Message model for storing and analyzing chat messages.

    Stores chat messages for moderation analysis and history.
    Requirements: 12.1
    """

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # YouTube message identifiers
    youtube_message_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    youtube_live_chat_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Sender information
    author_channel_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_profile_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_member: Mapped[bool] = mapped_column(Boolean, default=False)

    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="text"
    )  # text, super_chat, super_sticker, membership

    # Super chat/sticker details
    super_chat_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    super_chat_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Moderation status
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Analysis results
    analysis_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    violated_rules: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # List of rule IDs that were violated

    # Timestamps
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def mark_as_moderated(self, reason: str, is_hidden: bool = True) -> None:
        """Mark message as moderated.
        
        Args:
            reason: Reason for moderation
            is_hidden: Whether message was hidden
        """
        self.is_moderated = True
        self.is_hidden = is_hidden
        self.moderation_reason = reason
        self.moderated_at = datetime.utcnow()

    def mark_as_deleted(self, reason: str) -> None:
        """Mark message as deleted.
        
        Args:
            reason: Reason for deletion
        """
        self.is_moderated = True
        self.is_deleted = True
        self.moderation_reason = reason
        self.moderated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, author={self.author_display_name})>"


class SlowModeConfig(Base):
    """Slow Mode Configuration model for auto slow mode.

    Stores slow mode settings and auto-enable configuration.
    Requirements: 12.3
    """

    __tablename__ = "slow_mode_configs"

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

    # Slow mode settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=30)

    # Auto-enable settings (Requirements: 12.3)
    auto_enable: Mapped[bool] = mapped_column(Boolean, default=True)
    spam_threshold_per_minute: Mapped[int] = mapped_column(Integer, default=10)
    auto_disable_after_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=5
    )

    # Current state
    is_currently_active: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_disable_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Statistics
    activation_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def activate(self) -> None:
        """Activate slow mode."""
        self.is_currently_active = True
        self.activated_at = datetime.utcnow()
        self.last_activated_at = datetime.utcnow()
        self.activation_count += 1
        
        if self.auto_disable_after_minutes:
            from datetime import timedelta
            self.auto_disable_at = datetime.utcnow() + timedelta(
                minutes=self.auto_disable_after_minutes
            )

    def deactivate(self) -> None:
        """Deactivate slow mode."""
        self.is_currently_active = False
        self.activated_at = None
        self.auto_disable_at = None

    def should_auto_disable(self) -> bool:
        """Check if slow mode should be auto-disabled.
        
        Returns:
            bool: True if should auto-disable
        """
        if not self.is_currently_active:
            return False
        if self.auto_disable_at is None:
            return False
        return datetime.utcnow() >= self.auto_disable_at

    def __repr__(self) -> str:
        return f"<SlowModeConfig(id={self.id}, active={self.is_currently_active})>"


class CustomCommand(Base):
    """Custom Command model for chat commands.

    Stores custom command configuration and handlers.
    Requirements: 12.4
    """

    __tablename__ = "custom_commands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Command configuration
    trigger: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "!help", "!discord"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response configuration
    response_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="text"
    )  # text, action, webhook
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Access control
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    moderator_only: Mapped[bool] = mapped_column(Boolean, default=False)
    member_only: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=5)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def can_be_used_by(self, is_moderator: bool, is_member: bool, is_owner: bool) -> bool:
        """Check if command can be used by a user.
        
        Args:
            is_moderator: Whether user is a moderator
            is_member: Whether user is a member
            is_owner: Whether user is the channel owner
            
        Returns:
            bool: True if user can use command
        """
        if is_owner:
            return True
        if self.moderator_only and not is_moderator:
            return False
        if self.member_only and not is_member:
            return False
        return True

    def is_on_cooldown(self) -> bool:
        """Check if command is on cooldown.
        
        Returns:
            bool: True if on cooldown
        """
        if self.last_used_at is None:
            return False
        from datetime import timedelta
        cooldown_end = self.last_used_at + timedelta(seconds=self.cooldown_seconds)
        return datetime.utcnow() < cooldown_end

    def record_usage(self) -> None:
        """Record command usage."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<CustomCommand(id={self.id}, trigger={self.trigger})>"
