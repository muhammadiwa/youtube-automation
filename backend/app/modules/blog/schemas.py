"""Blog schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    """Schema for creating an article."""
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=500)
    excerpt: Optional[str] = None
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    tags: Optional[list[str]] = None
    featured_image: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    featured: bool = False
    read_time_minutes: int = Field(default=5, ge=1)


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = Field(None, min_length=1, max_length=500)
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    featured_image: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    featured: Optional[bool] = None
    read_time_minutes: Optional[int] = Field(None, ge=1)


class ArticleResponse(BaseModel):
    """Schema for article response."""
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    category: str
    tags: Optional[list[str]]
    featured_image: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    status: str
    featured: bool
    author_id: UUID
    author_name: str
    view_count: int
    read_time_minutes: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Schema for paginated article list."""
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ArticlePublicResponse(BaseModel):
    """Schema for public article response (no admin fields)."""
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    category: str
    tags: Optional[list[str]]
    featured_image: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    featured: bool
    author_name: str
    view_count: int
    read_time_minutes: int
    published_at: Optional[datetime]

    class Config:
        from_attributes = True
