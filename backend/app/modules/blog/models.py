"""Blog models for CMS functionality."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ArticleStatus(str, Enum):
    """Article publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(Base):
    """Blog article model."""

    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    featured_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=ArticleStatus.DRAFT.value, index=True
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    read_time_minutes: Mapped[int] = mapped_column(Integer, default=5)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index('ix_article_status_published', 'status', 'published_at'),
        Index('ix_article_category_status', 'category', 'status'),
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title={self.title}, status={self.status})>"
