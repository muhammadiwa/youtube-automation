"""Database configuration with SQLAlchemy 2.0 async support."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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


def _create_celery_engine():
    """Create a fresh async engine for Celery tasks.
    
    Each call creates a new engine to avoid event loop binding issues.
    Uses NullPool so connections are not reused across different event loops.
    """
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # No pooling - new connection each time
    )


@asynccontextmanager
async def celery_session_maker():
    """Create a fresh session with a fresh engine for Celery tasks.
    
    This creates a new engine and session for each task to avoid
    'bound to a different event loop' errors when multiple Celery
    tasks run concurrently with asyncio.run().
    
    Usage:
        async with celery_session_maker() as session:
            # use session
    """
    # Create fresh engine for this event loop
    task_engine = _create_celery_engine()
    
    # Create session maker bound to this engine
    task_session_maker = async_sessionmaker(
        task_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with task_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Dispose engine after use to clean up
    await task_engine.dispose()


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
