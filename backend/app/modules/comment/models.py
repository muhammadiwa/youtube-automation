"""Comment models for comment management.

Implements Comment, AutoReplyRule, and CommentReply models.
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
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


class CommentSentiment(str, Enum):
    """Sentiment categories for comments.
    
    Requirements: 13.3
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ATTENTION_REQUIRED = "attention_required"  # Highlights comments needing attention


class CommentStatus(str, Enum):
    """Status of a comment.
    
    Requirements: 13.1, 13.5
    """
    PENDING = "pending"  # Not yet reviewed
    APPROVED = "approved"  # Approved/visible
    HIDDEN = "hidden"  # Hidden by moderation
    DELETED = "deleted"  # Deleted
    REPLIED = "replied"  # Has been replied to
    SPAM = "spam"  # Marked as spam


class Comment(Base):
    """Comment model for storing YouTube video comments.

    Aggregates comments from all connected accounts into unified inbox.
    Requirements: 13.1, 13.3
    """

    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # YouTube identifiers
    youtube_comment_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    youtube_video_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    youtube_parent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )  # For reply threads

    # Author information
    author_channel_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    author_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_profile_image_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # Comment content
    text_original: Mapped[str] = mapped_column(Text, nullable=False)
    text_display: Mapped[str] = mapped_column(Text, nullable=False)

    # Engagement metrics
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status and moderation (Requirements: 13.1, 13.5)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CommentStatus.PENDING.value, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    can_reply: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sentiment analysis (Requirements: 13.3)
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # -1.0 to 1.0
    requires_attention: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )  # Highlights attention-required comments
    sentiment_analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Auto-reply tracking (Requirements: 13.4)
    auto_replied: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_reply_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_reply_rules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at_youtube: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    replies: Mapped[list["CommentReply"]] = relationship(
        "CommentReply",
        back_populates="comment",
        cascade="all, delete-orphan",
    )
    auto_reply_rule: Mapped[Optional["AutoReplyRule"]] = relationship(
        "AutoReplyRule",
        back_populates="triggered_comments",
    )

    def is_reply(self) -> bool:
        """Check if this comment is a reply to another comment."""
        return self.youtube_parent_id is not None

    def mark_as_attention_required(self) -> None:
        """Mark comment as requiring attention."""
        self.requires_attention = True
        self.sentiment = CommentSentiment.ATTENTION_REQUIRED.value

    def update_sentiment(
        self,
        sentiment: CommentSentiment,
        score: float,
        requires_attention: bool = False,
    ) -> None:
        """Update sentiment analysis results.
        
        Args:
            sentiment: Sentiment category
            score: Sentiment score (-1.0 to 1.0)
            requires_attention: Whether comment requires attention
        """
        self.sentiment = sentiment.value
        self.sentiment_score = max(-1.0, min(1.0, score))
        self.requires_attention = requires_attention
        self.sentiment_analyzed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, author={self.author_display_name})>"


class AutoReplyRule(Base):
    """Auto-reply rule model for automatic comment responses.

    Configures trigger patterns and auto-responses for matching comments.
    Requirements: 13.4
    """

    __tablename__ = "auto_reply_rules"

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

    # Trigger configuration (Requirements: 13.4)
    trigger_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="keyword"
    )  # keyword, regex, sentiment, all
    trigger_keywords: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    trigger_pattern: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Regex pattern
    trigger_sentiment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Trigger on specific sentiment
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

    # Response configuration
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_delay_seconds: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Delay before auto-reply

    # Rule state
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = checked first

    # Limits
    max_replies_per_video: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Limit replies per video
    max_replies_per_day: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Daily limit

    # Statistics
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replies_today: Mapped[int] = mapped_column(Integer, default=0)
    replies_today_reset_at: Mapped[Optional[datetime]] = mapped_column(
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
    triggered_comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="auto_reply_rule",
    )

    def increment_trigger_count(self) -> None:
        """Increment trigger count and update last triggered time."""
        self.trigger_count += 1
        self.last_triggered_at = datetime.utcnow()
        self.replies_today += 1

    def can_reply(self) -> bool:
        """Check if rule can still send replies based on limits.
        
        Returns:
            bool: True if rule can send more replies
        """
        if not self.is_enabled:
            return False
        
        # Check daily limit
        if self.max_replies_per_day is not None:
            # Reset counter if new day
            if self.replies_today_reset_at:
                if datetime.utcnow().date() > self.replies_today_reset_at.date():
                    self.replies_today = 0
                    self.replies_today_reset_at = datetime.utcnow()
            
            if self.replies_today >= self.max_replies_per_day:
                return False
        
        return True

    def __repr__(self) -> str:
        return f"<AutoReplyRule(id={self.id}, name={self.name})>"


class CommentReply(Base):
    """Comment reply model for tracking replies posted to YouTube.

    Stores replies posted through the system to YouTube comments.
    Requirements: 13.2
    """

    __tablename__ = "comment_replies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # YouTube identifiers
    youtube_reply_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )

    # Reply content
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Reply status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, posted, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Auto-reply tracking
    is_auto_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_reply_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_reply_rules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    comment: Mapped["Comment"] = relationship(
        "Comment",
        back_populates="replies",
    )

    def mark_as_posted(self, youtube_reply_id: str) -> None:
        """Mark reply as successfully posted.
        
        Args:
            youtube_reply_id: YouTube's ID for the posted reply
        """
        self.status = "posted"
        self.youtube_reply_id = youtube_reply_id
        self.posted_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """Mark reply as failed.
        
        Args:
            error_message: Error message describing the failure
        """
        self.status = "failed"
        self.error_message = error_message

    def __repr__(self) -> str:
        return f"<CommentReply(id={self.id}, status={self.status})>"
