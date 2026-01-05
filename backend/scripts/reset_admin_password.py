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

# Load environment from backend/.env
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n❌ ERROR: DATABASE_URL not found in .env file")
    print(f"   Looking for .env at: {env_path}")
    sys.exit(1)

# Convert psycopg2 URL to asyncpg if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_admin_password():
    """Reset admin user password."""
    print("\n" + "=" * 60)
    print("🔐 RESETTING ADMIN PASSWORD")
    print("=" * 60)
    
    # Validate DATABASE_URL
    if not DATABASE_URL or len(DATABASE_URL) < 20:
        print("\n❌ ERROR: Invalid DATABASE_URL")
        print(f"   Current value: {DATABASE_URL}")
        print("\n   Please set DATABASE_URL in .env file with format:")
        print("   DATABASE_URL=postgresql://user:password@host:port/database")
        print("\n   Example:")
        print("   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/youtube_automation")
        return
    
    print(f"\nDatabase URL: {DATABASE_URL}")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to database")
        print(f"   {str(e)}")
        print("\n   Please check your DATABASE_URL in .env file")
        return
    
    new_password = "Admin@123456"
    new_hash = pwd_context.hash(new_password)
    
    print(f"\nNew password will be: {new_password}")
    
    try:
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
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n   Please check:")
        print("   1. Database is running")
        print("   2. DATABASE_URL is correct in .env file")
        print("   3. Migrations have been run: alembic upgrade head")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_admin_password())
