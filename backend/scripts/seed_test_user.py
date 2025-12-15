"""Seed script to create test user for development.

This creates a placeholder user that can be used for OAuth testing.
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL - adjust as needed
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation"


async def create_test_user():
    """Create test user if not exists."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        result = await session.execute(
            text("SELECT id FROM users WHERE id = :user_id"),
            {"user_id": test_user_id}
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Test user already exists: {test_user_id}")
            return
        
        # Create test user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, name, is_active, is_verified, created_at, updated_at)
                VALUES (:id, :email, :hashed_password, :name, :is_active, :is_verified, :created_at, :updated_at)
            """),
            {
                "id": test_user_id,
                "email": "test@example.com",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYn.Pw1qK6Uy",  # "password123"
                "name": "Test User",
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        
        await session.commit()
        print(f"Created test user: {test_user_id}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())
