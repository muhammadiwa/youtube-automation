"""Blog repository for database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.blog.models import Article, ArticleStatus


class ArticleRepository:
    """Repository for article database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, article: Article) -> Article:
        """Create a new article."""
        self.session.add(article)
        await self.session.commit()
        await self.session.refresh(article)
        return article

    async def get_by_id(self, article_id: UUID) -> Optional[Article]:
        """Get article by ID."""
        result = await self.session.execute(
            select(Article).where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Article]:
        """Get article by slug."""
        result = await self.session.execute(
            select(Article).where(Article.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_published_by_slug(self, slug: str) -> Optional[Article]:
        """Get published article by slug."""
        result = await self.session.execute(
            select(Article).where(
                Article.slug == slug,
                Article.status == ArticleStatus.PUBLISHED.value
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Article], int]:
        """List all articles with pagination."""
        query = select(Article)
        count_query = select(func.count(Article.id))

        if category:
            query = query.where(Article.category == category)
            count_query = count_query.where(Article.category == category)
        if status:
            query = query.where(Article.status == status)
            count_query = count_query.where(Article.status == status)

        query = query.order_by(Article.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)

        return list(result.scalars().all()), count_result.scalar() or 0

    async def list_published(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
    ) -> tuple[list[Article], int]:
        """List published articles."""
        return await self.list_all(
            page=page,
            page_size=page_size,
            category=category,
            status=ArticleStatus.PUBLISHED.value,
        )

    async def update(self, article: Article) -> Article:
        """Update an article."""
        await self.session.commit()
        await self.session.refresh(article)
        return article

    async def delete(self, article: Article) -> None:
        """Delete an article."""
        await self.session.delete(article)
        await self.session.commit()

    async def increment_view_count(self, article_id: UUID) -> None:
        """Increment article view count."""
        await self.session.execute(
            update(Article)
            .where(Article.id == article_id)
            .values(view_count=Article.view_count + 1)
        )
        await self.session.commit()

    async def get_categories(self) -> list[str]:
        """Get all unique categories."""
        result = await self.session.execute(
            select(Article.category)
            .where(Article.status == ArticleStatus.PUBLISHED.value)
            .distinct()
        )
        return [row[0] for row in result.all()]
