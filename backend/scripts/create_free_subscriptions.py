"""Create FREE subscriptions for existing users who don't have one.

Run with: python -m scripts.create_free_subscriptions
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker

# Import all models to ensure relationships are resolved
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.video.models import Video
from app.modules.stream.models import LiveEvent
from app.modules.billing.models import Subscription, PlanTier
from app.modules.billing.service import BillingService


async def create_free_subscriptions():
    """Create FREE subscriptions for users without one."""
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users")
        
        created_count = 0
        skipped_count = 0
        
        for user in users:
            # Check if user has subscription
            sub_result = await session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            existing = sub_result.scalar_one_or_none()
            
            if existing:
                print(f"  User {user.email}: Already has {existing.plan_tier} subscription")
                skipped_count += 1
            else:
                # Create FREE subscription
                billing_service = BillingService(session)
                await billing_service.ensure_free_subscription(user.id)
                print(f"  User {user.email}: Created FREE subscription ✓")
                created_count += 1
        
        print("\n" + "=" * 50)
        print(f"Created: {created_count} subscriptions")
        print(f"Skipped: {skipped_count} (already had subscription)")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(create_free_subscriptions())
