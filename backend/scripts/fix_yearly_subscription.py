"""Fix yearly subscription period.

This script fixes subscriptions where billing_cycle is 'yearly' but period is only 30 days.

Usage:
    cd backend
    python -m scripts.fix_yearly_subscription
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def fix_yearly_subscriptions():
    """Fix all yearly subscriptions that have wrong period."""
    
    async with engine.begin() as conn:
        print(f"\n{'='*60}")
        print("Finding yearly subscriptions with wrong period...")
        print(f"{'='*60}")
        
        # Find subscriptions where billing_cycle is yearly but period is < 60 days
        result = await conn.execute(
            text("""
                SELECT id, user_id, plan_tier, billing_cycle,
                       current_period_start, current_period_end,
                       EXTRACT(DAY FROM (current_period_end - current_period_start)) as period_days
                FROM subscriptions
                WHERE billing_cycle = 'yearly'
            """)
        )
        subscriptions = result.fetchall()
        
        if not subscriptions:
            print("\nNo yearly subscriptions found.")
            return
        
        fixed_count = 0
        for sub in subscriptions:
            sub_id, user_id, plan_tier, billing_cycle, period_start, period_end, period_days = sub
            
            print(f"\nSubscription: {sub_id}")
            print(f"  User: {user_id}")
            print(f"  Plan: {plan_tier}")
            print(f"  Billing Cycle: {billing_cycle}")
            print(f"  Period: {period_start} to {period_end}")
            print(f"  Period Days: {period_days}")
            
            if period_days and period_days < 60:
                print(f"  ⚠️  Period is only {period_days} days, should be 365 days!")
                
                # Calculate new period_end (365 days from period_start)
                new_period_end = period_start + timedelta(days=365)
                
                await conn.execute(
                    text("""
                        UPDATE subscriptions
                        SET current_period_end = :period_end
                        WHERE id = :sub_id
                    """),
                    {
                        "sub_id": str(sub_id),
                        "period_end": new_period_end,
                    }
                )
                
                print(f"  ✓ Fixed! New period end: {new_period_end}")
                fixed_count += 1
            else:
                print(f"  ✓ Period is correct ({period_days} days)")
        
        print(f"\n{'='*60}")
        print(f"Fixed {fixed_count} subscription(s)")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(fix_yearly_subscriptions())
