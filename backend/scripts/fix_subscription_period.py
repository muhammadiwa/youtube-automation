"""Fix subscription period to include existing data.

Run with: python -m scripts.fix_subscription_period
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.core.database import async_session_maker
from app.core.datetime_utils import utcnow, to_naive_utc

# Import all models
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.video.models import Video
from app.modules.stream.models import LiveEvent
from app.modules.billing.models import Subscription


async def fix_subscription_period():
    """Fix subscription period to include existing data."""
    async with async_session_maker() as session:
        # Get all subscriptions
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()
        
        print("=" * 60)
        print("FIXING SUBSCRIPTION PERIODS")
        print("=" * 60)
        
        now = utcnow()
        # Set period start to December 1st to include all existing data
        period_start = datetime(2025, 12, 1, 0, 0, 0, tzinfo=now.tzinfo)
        # Set period end to end of January
        period_end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=now.tzinfo)
        
        for sub in subscriptions:
            print(f"\n📋 Subscription for user: {sub.user_id}")
            print(f"   Old period: {sub.current_period_start} - {sub.current_period_end}")
            
            # Update period
            sub.current_period_start = to_naive_utc(period_start)
            sub.current_period_end = to_naive_utc(period_end)
            
            print(f"   New period: {sub.current_period_start} - {sub.current_period_end}")
        
        await session.commit()
        print("\n✅ All subscription periods updated!")


if __name__ == "__main__":
    asyncio.run(fix_subscription_period())
