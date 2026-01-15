"""Blog service for business logic."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow
from app.core.config import settings
from app.core.storage import get_public_url
from app.modules.blog.models import Article, ArticleStatus
from app.modules.blog.repository import ArticleRepository
from app.modules.blog.schemas import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    ArticlePublicResponse,
)


def get_image_url(storage_key: Optional[str]) -> Optional[str]:
    """Convert storage key to public URL based on storage backend."""
    if not storage_key:
        return None
    # Already a full URL
    if storage_key.startswith(("http://", "https://")):
        return storage_key
    
    # For cloud storage (S3/MinIO/R2), use presigned URL
    if settings.STORAGE_BACKEND.lower() in ("s3", "minio", "aws", "r2"):
        return get_public_url(storage_key, expires_in=86400)  # 24 hours
    
    # For local storage, return API endpoint URL
    filename = storage_key.split("/")[-1]
    return f"/api/v1/blog/images/{filename}"


class ArticleService:
    """Service for article management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ArticleRepository(session)

    async def create_article(
        self,
        data: ArticleCreate,
        author_id: UUID,
        author_name: str,
    ) -> ArticleResponse:
        """Create a new article."""
        article = Article(
            title=data.title,
            slug=data.slug,
            excerpt=data.excerpt,
            content=data.content,
            category=data.category,
            tags=data.tags,
            featured_image=data.featured_image,
            meta_title=data.meta_title or data.title,
            meta_description=data.meta_description or data.excerpt,
            featured=data.featured,
            read_time_minutes=data.read_time_minutes,
            author_id=author_id,
            author_name=author_name,
            status=ArticleStatus.DRAFT.value,
        )
        article = await self.repo.create(article)
        return self._to_response(article)

    async def get_article(self, article_id: UUID) -> Optional[ArticleResponse]:
        """Get article by ID."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None
        return self._to_response(article)

    async def get_article_by_slug(self, slug: str) -> Optional[ArticlePublicResponse]:
        """Get published article by slug (public)."""
        article = await self.repo.get_published_by_slug(slug)
        if not article:
            return None
        await self.repo.increment_view_count(article.id)
        return self._to_public_response(article)

    async def list_articles(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ArticleListResponse:
        """List all articles (admin)."""
        articles, total = await self.repo.list_all(
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
        return ArticleListResponse(
            items=[self._to_response(a) for a in articles],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def list_published_articles(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
    ) -> ArticleListResponse:
        """List published articles (public)."""
        articles, total = await self.repo.list_published(
            page=page,
            page_size=page_size,
            category=category,
        )
        return ArticleListResponse(
            items=[self._to_response(a) for a in articles],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def update_article(
        self,
        article_id: UUID,
        data: ArticleUpdate,
    ) -> Optional[ArticleResponse]:
        """Update an article."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(article, field, value)

        article = await self.repo.update(article)
        return self._to_response(article)

    async def publish_article(self, article_id: UUID) -> Optional[ArticleResponse]:
        """Publish an article."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        article.status = ArticleStatus.PUBLISHED.value
        article.published_at = utcnow()
        article = await self.repo.update(article)
        return self._to_response(article)

    async def unpublish_article(self, article_id: UUID) -> Optional[ArticleResponse]:
        """Unpublish an article."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return None

        article.status = ArticleStatus.DRAFT.value
        article = await self.repo.update(article)
        return self._to_response(article)

    async def delete_article(self, article_id: UUID) -> bool:
        """Delete an article."""
        article = await self.repo.get_by_id(article_id)
        if not article:
            return False
        await self.repo.delete(article)
        return True

    async def get_categories(self) -> list[str]:
        """Get all categories."""
        return await self.repo.get_categories()

    def _to_response(self, article: Article) -> ArticleResponse:
        """Convert article to response schema."""
        return ArticleResponse(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            content=article.content,
            category=article.category,
            tags=article.tags,
            featured_image=get_image_url(article.featured_image),
            meta_title=article.meta_title,
            meta_description=article.meta_description,
            status=article.status,
            featured=article.featured,
            author_id=article.author_id,
            author_name=article.author_name,
            view_count=article.view_count,
            read_time_minutes=article.read_time_minutes,
            created_at=article.created_at,
            updated_at=article.updated_at,
            published_at=article.published_at,
        )

    def _to_public_response(self, article: Article) -> ArticlePublicResponse:
        """Convert article to public response schema."""
        return ArticlePublicResponse(
            id=article.id,
            title=article.title,
            slug=article.slug,
            excerpt=article.excerpt,
            content=article.content,
            category=article.category,
            tags=article.tags,
            featured_image=get_image_url(article.featured_image),
            meta_title=article.meta_title,
            meta_description=article.meta_description,
            featured=article.featured,
            author_name=article.author_name,
            view_count=article.view_count,
            read_time_minutes=article.read_time_minutes,
            published_at=article.published_at,
        )
