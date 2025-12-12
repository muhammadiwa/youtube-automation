"""SQLAlchemy models for AI module.

Stores AI feedback, user preferences, and API logs for personalization and monitoring.
Requirements: 13.1, 13.3, 14.5
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AILogStatus(str, Enum):
    """Status of AI API requests."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class AILog(Base):
    """Model for storing AI API request logs.
    
    Requirements: 13.1, 13.3 - AI dashboard and logs
    - Track API calls, costs, and usage by feature
    - Show request/response with latency and tokens
    """

    __tablename__ = "ai_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Request details
    feature = Column(String(50), nullable=False, index=True)  # titles, descriptions, thumbnails, chatbot, tags
    model = Column(String(100), nullable=False)  # gpt-4, gpt-3.5-turbo, etc.
    request_summary = Column(Text, nullable=True)  # Summary of the request
    response_summary = Column(Text, nullable=True)  # Summary of the response
    
    # Token usage
    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    latency_ms = Column(Float, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0)
    
    # Status
    status = Column(String(20), nullable=False, default=AILogStatus.SUCCESS.value, index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="ai_logs")


class AIFeedback(Base):
    """Model for storing user feedback on AI suggestions."""

    __tablename__ = "ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    suggestion_type = Column(String(50), nullable=False)  # title, description, tags, thumbnail
    suggestion_id = Column(String(100), nullable=False)
    was_selected = Column(Boolean, nullable=False, default=False)
    user_modification = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="ai_feedback")


class AIUserPreferences(Base):
    """Model for storing user AI preferences."""

    __tablename__ = "ai_user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    preferred_title_style = Column(String(50), nullable=True)
    preferred_description_length = Column(Integer, nullable=True)
    preferred_tag_count = Column(Integer, nullable=True)
    preferred_thumbnail_style = Column(String(50), nullable=True)
    brand_colors = Column(JSON, nullable=True)  # List of hex colors
    brand_keywords = Column(JSON, nullable=True)  # List of keywords
    avoid_keywords = Column(JSON, nullable=True)  # List of keywords to avoid
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="ai_preferences")


class ThumbnailLibrary(Base):
    """Model for storing generated/saved thumbnails."""

    __tablename__ = "thumbnail_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True, index=True)
    image_url = Column(String(500), nullable=False)
    style = Column(String(50), nullable=True)
    width = Column(Integer, nullable=False, default=1280)
    height = Column(Integer, nullable=False, default=720)
    file_size_bytes = Column(Integer, nullable=True)
    elements = Column(JSON, nullable=True)  # Thumbnail elements metadata
    tags = Column(JSON, nullable=True)  # Tags for searching
    is_generated = Column(Boolean, default=True)  # AI generated vs uploaded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="thumbnails")
