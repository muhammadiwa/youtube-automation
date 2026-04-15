"""Test script for bandwidth calculation.

Run with: python -m scripts.test_bandwidth_calculation
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func as sql_func
from app.core.database import async_session_maker
from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
from app.modules.billing.models import Subscription
from app.modules.auth.models import User


async def test_bandwidth_calculation():
    """Test bandwidth calculation from stream jobs."""
    async with async_session_maker() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("Test user not found!")
            return
        
        print(f"User: {user.email} (ID: {user.id})")
        
        # Get subscription
        sub_result = await session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = sub_result.scalar_one_or_none()
        
        if subscription:
            print(f"Subscription: {subscription.plan_tier}")
            print(f"Period: {subscription.current_period_start} - {subscription.current_period_end}")
        else:
            print("No subscription found!")
            return
        
        # Get all stream jobs for this user
        jobs_result = await session.execute(
            select(StreamJob)
            .where(StreamJob.user_id == user.id)
            .order_by(StreamJob.created_at.desc())
        )
        jobs = jobs_result.scalars().all()
        
        print(f"\n=== Stream Jobs ({len(jobs)} total) ===")
        
        total_bandwidth = 0.0
        for job in jobs:
            # Calculate bandwidth: bitrate (kbps) * duration (s) / 8 / 1024 / 1024 = GB
            if job.total_duration_seconds > 0:
                bandwidth_gb = (job.target_bitrate * job.total_duration_seconds) / 8 / 1024 / 1024
            else:
                bandwidth_gb = 0
            
            total_bandwidth += bandwidth_gb
            
            print(f"\nJob: {job.title}")
            print(f"  Status: {job.status}")
            print(f"  Target Bitrate: {job.target_bitrate} kbps")
            print(f"  Duration: {job.total_duration_seconds} seconds ({job.total_duration_seconds / 3600:.2f} hours)")
            print(f"  Bandwidth: {bandwidth_gb:.4f} GB")
            print(f"  Created: {job.created_at}")
            if job.actual_start_at:
                print(f"  Started: {job.actual_start_at}")
            if job.actual_end_at:
                print(f"  Ended: {job.actual_end_at}")
        
        print(f"\n=== Total Bandwidth: {total_bandwidth:.4f} GB ===")
        
        # Calculate bandwidth in current billing period
        period_jobs_result = await session.execute(
            select(StreamJob)
            .where(StreamJob.user_id == user.id)
            .where(StreamJob.created_at >= subscription.current_period_start)
        )
        period_jobs = period_jobs_result.scalars().all()
        
        period_bandwidth = 0.0
        for job in period_jobs:
            if job.total_duration_seconds > 0:
                bandwidth_gb = (job.target_bitrate * job.total_duration_seconds) / 8 / 1024 / 1024
                period_bandwidth += bandwidth_gb
        
        print(f"\n=== Bandwidth in Current Period: {period_bandwidth:.4f} GB ===")
        
        # Test using FeatureGateService
        print("\n=== Testing FeatureGateService ===")
        from app.modules.billing.feature_gate import FeatureGateService
        
        feature_gate = FeatureGateService(session)
        bandwidth_used, bandwidth_limit, plan_name = await feature_gate.get_bandwidth_usage(user.id)
        
        print(f"Plan: {plan_name}")
        print(f"Bandwidth Used: {bandwidth_used:.4f} GB")
        print(f"Bandwidth Limit: {bandwidth_limit} GB")
        
        # Get full usage summary
        print("\n=== Full Usage Summary ===")
        summary = await feature_gate.get_usage_summary(user.id)
        
        import json
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(test_bandwidth_calculation())
