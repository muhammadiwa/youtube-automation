"""Script to create default notification preferences for existing users.

This script creates notification preferences for all event types for users
who don't have any preferences yet.

Usage:
    python -m scripts.create_default_notification_preferences
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker

# Import all models to ensure relationships are resolved
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.notification.models import NotificationPreference
from app.modules.notification.service import NotificationService


async def create_preferences_for_user(
    session: AsyncSession,
    user_id,
    email: str,
) -> int:
    """Create default preferences for a single user."""
    service = NotificationService(session)
    
    # Check if user already has preferences
    result = await session.execute(
        select(func.count(NotificationPreference.id)).where(
            NotificationPreference.user_id == user_id
        )
    )
    existing_count = result.scalar() or 0
    
    if existing_count > 0:
        print(f"  User {email} already has {existing_count} preferences, skipping...")
        return 0
    
    # Create default preferences
    preferences = await service.create_default_preferences(user_id, email)
    print(f"  Created {len(preferences)} preferences for {email}")
    return len(preferences)


async def main():
    """Main function to create preferences for all users."""
    print("Creating default notification preferences for existing users...")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
        
        print(f"Found {len(users)} active users")
        print()
        
        total_created = 0
        users_updated = 0
        
        for user in users:
            created = await create_preferences_for_user(session, user.id, user.email)
            if created > 0:
                total_created += created
                users_updated += 1
        
        await session.commit()
        
        print()
        print("=" * 60)
        print(f"Done! Created {total_created} preferences for {users_updated} users")


if __name__ == "__main__":
    asyncio.run(main())
