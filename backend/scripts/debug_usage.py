"""Debug script to check usage data in database.

Run with: python -m scripts.debug_usage
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func as sql_func
from app.core.database import async_session_maker

# Import all models
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.video.models import Video
from app.modules.stream.models import LiveEvent, LiveEventStatus
from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
from app.modules.billing.models import Subscription


async def debug_usage():
    """Debug usage data for all users."""
    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print("=" * 70)
        print("DEBUG USAGE DATA")
        print("=" * 70)
        
        for user in users:
            print(f"\n👤 User: {user.email} (ID: {user.id})")
            print("-" * 50)
            
            # Get subscription
            sub_result = await session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            subscription = sub_result.scalar_one_or_none()
            
            if subscription:
                print(f"  📋 Subscription: {subscription.plan_tier}")
                print(f"     Period: {subscription.current_period_start} - {subscription.current_period_end}")
            else:
                print(f"  ❌ No subscription!")
            
            # Count accounts
            accounts_result = await session.execute(
                select(sql_func.count(YouTubeAccount.id))
                .where(YouTubeAccount.user_id == user.id)
            )
            accounts_count = accounts_result.scalar() or 0
            
            # Count active accounts
            active_accounts_result = await session.execute(
                select(sql_func.count(YouTubeAccount.id))
                .where(YouTubeAccount.user_id == user.id)
                .where(YouTubeAccount.status == "active")
            )
            active_accounts_count = active_accounts_result.scalar() or 0
            
            print(f"  📺 YouTube Accounts: {accounts_count} total, {active_accounts_count} active")
            
            # List accounts
            accounts_list_result = await session.execute(
                select(YouTubeAccount).where(YouTubeAccount.user_id == user.id)
            )
            accounts = accounts_list_result.scalars().all()
            for acc in accounts:
                print(f"     - {acc.channel_title} (ID: {acc.id}, status: {acc.status})")
            
            # Count videos
            videos_result = await session.execute(
                select(sql_func.count(Video.id))
                .where(Video.user_id == user.id)
            )
            videos_count = videos_result.scalar() or 0
            print(f"  🎬 Videos (total): {videos_count}")
            
            # Count videos via account join
            if subscription:
                videos_via_account_result = await session.execute(
                    select(sql_func.count(Video.id))
                    .join(YouTubeAccount, Video.account_id == YouTubeAccount.id)
                    .where(YouTubeAccount.user_id == user.id)
                    .where(Video.created_at >= subscription.current_period_start)
                )
                videos_via_account = videos_via_account_result.scalar() or 0
                print(f"  🎬 Videos (via account, this period): {videos_via_account}")
            
            # Count videos directly by user_id
            if subscription:
                videos_direct_result = await session.execute(
                    select(sql_func.count(Video.id))
                    .where(Video.user_id == user.id)
                    .where(Video.created_at >= subscription.current_period_start)
                )
                videos_direct = videos_direct_result.scalar() or 0
                print(f"  🎬 Videos (direct user_id, this period): {videos_direct}")
            
            # Count LiveEvent streams
            live_events_result = await session.execute(
                select(sql_func.count(LiveEvent.id))
                .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
                .where(YouTubeAccount.user_id == user.id)
            )
            live_events_count = live_events_result.scalar() or 0
            print(f"  📺 LiveEvents (total): {live_events_count}")
            
            # Count StreamJob streams
            stream_jobs_result = await session.execute(
                select(sql_func.count(StreamJob.id))
                .where(StreamJob.user_id == user.id)
            )
            stream_jobs_count = stream_jobs_result.scalar() or 0
            print(f"  📺 StreamJobs (total): {stream_jobs_count}")
            
            # Count live LiveEvents
            live_result = await session.execute(
                select(sql_func.count(LiveEvent.id))
                .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
                .where(YouTubeAccount.user_id == user.id)
                .where(LiveEvent.status == LiveEventStatus.LIVE.value)
            )
            live_count = live_result.scalar() or 0
            print(f"  🔴 LiveEvents (LIVE): {live_count}")
            
            # Count running StreamJobs
            running_jobs_result = await session.execute(
                select(sql_func.count(StreamJob.id))
                .where(StreamJob.user_id == user.id)
                .where(StreamJob.status == StreamJobStatus.RUNNING.value)
            )
            running_jobs_count = running_jobs_result.scalar() or 0
            print(f"  🔴 StreamJobs (RUNNING): {running_jobs_count}")
            
            print(f"  ⚡ Total Concurrent: {live_count + running_jobs_count}")
        
        print("\n" + "=" * 70)
        print("RAW DATA CHECK")
        print("=" * 70)
        
        # Check raw counts
        total_accounts = await session.execute(select(sql_func.count(YouTubeAccount.id)))
        print(f"\nTotal YouTubeAccounts in DB: {total_accounts.scalar()}")
        
        total_videos = await session.execute(select(sql_func.count(Video.id)))
        print(f"Total Videos in DB: {total_videos.scalar()}")
        
        total_live_events = await session.execute(select(sql_func.count(LiveEvent.id)))
        print(f"Total LiveEvents in DB: {total_live_events.scalar()}")
        
        total_stream_jobs = await session.execute(select(sql_func.count(StreamJob.id)))
        print(f"Total StreamJobs in DB: {total_stream_jobs.scalar()}")
        
        # List all StreamJobs with status
        print("\n📹 All StreamJobs:")
        jobs_all = await session.execute(select(StreamJob))
        for j in jobs_all.scalars().all():
            print(f"  - {j.title[:30]}... | user_id: {j.user_id} | status: {j.status}")
        
        # List all videos with their user_id and account_id
        print("\n📹 All Videos:")
        videos_all = await session.execute(select(Video))
        for v in videos_all.scalars().all():
            print(f"  - {v.title[:30]}... | user_id: {v.user_id} | account_id: {v.account_id} | created: {v.created_at}")


if __name__ == "__main__":
    asyncio.run(debug_usage())
