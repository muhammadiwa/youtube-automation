"""
Reset Admin Password Script.

This script resets the admin user password to a known value.

Run: python scripts/reset_admin_password.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Load environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_admin_password():
    """Reset admin user password."""
    print("\n" + "=" * 60)
    print("🔐 RESETTING ADMIN PASSWORD")
    print("=" * 60)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    new_password = "Admin@123456"
    new_hash = pwd_context.hash(new_password)
    
    print(f"\nNew password: {new_password}")
    print(f"New hash: {new_hash}")
    
    async with async_session() as session:
        # Check if admin user exists
        result = await session.execute(
            text("SELECT id, email FROM users WHERE email = 'admin@youtubeautomation.com'")
        )
        user = result.fetchone()
        
        if not user:
            print("\n❌ Admin user NOT FOUND!")
            print("   Run migrations first: alembic upgrade head")
            await engine.dispose()
            return
        
        user_id, email = user
        print(f"\n✅ Found admin user: {email}")
        
        # Update password
        await session.execute(
            text("UPDATE users SET password_hash = :hash WHERE email = 'admin@youtubeautomation.com'"),
            {"hash": new_hash}
        )
        await session.commit()
        
        print(f"\n✅ Password updated successfully!")
        print("\n" + "=" * 60)
        print("📋 LOGIN CREDENTIALS:")
        print(f"   Email: admin@youtubeautomation.com")
        print(f"   Password: {new_password}")
        print("=" * 60)
        
        # Verify the password works
        result = await session.execute(
            text("SELECT password_hash FROM users WHERE email = 'admin@youtubeautomation.com'")
        )
        stored_hash = result.scalar()
        
        if pwd_context.verify(new_password, stored_hash):
            print("\n✅ Password verification: SUCCESS")
        else:
            print("\n❌ Password verification: FAILED")
        
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_admin_password())
