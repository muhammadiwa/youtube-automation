"""Database configuration with SQLAlchemy 2.0 async support."""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Main async engine for FastAPI (with connection pooling)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,  # Base pool size (default was 5)
    max_overflow=30,  # Additional connections when pool is full (default was 10)
    pool_timeout=60,  # Wait time for connection from pool (default was 30)
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Celery-specific engine with NullPool (no connection reuse)
# This avoids event loop conflicts when Celery creates new loops per task
celery_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # No pooling - new connection each time
)

celery_session_maker = async_sessionmaker(
    celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for simple operations that need to run outside async context
# Used for progress updates in Celery tasks to avoid async session conflicts
_sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(
    _sync_db_url,
    echo=False,
    poolclass=NullPool,  # No pooling for Celery compatibility
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for consistency
get_session = get_db
