"""Script to run all notification-related background tasks.

This script runs:
1. Billing tasks (subscription expiring/expired notifications)
2. Account tasks (token expiring/expired, quota warnings)

Usage:
    python -m scripts.run_notification_tasks
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_maker


async def main():
    """Run all notification background tasks."""
    print("=" * 60)
    print("Running Notification Background Tasks")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # Run billing tasks
        print("\n1. Running Billing Tasks...")
        try:
            from app.modules.billing.tasks import run_billing_tasks
            billing_result = await run_billing_tasks(session)
            print(f"   Billing tasks completed: {billing_result}")
        except Exception as e:
            print(f"   Error running billing tasks: {e}")
        
        # Run account tasks
        print("\n2. Running Account Tasks...")
        try:
            from app.modules.account.tasks import run_account_tasks
            account_result = await run_account_tasks(session)
            print(f"   Account tasks completed: {account_result}")
        except Exception as e:
            print(f"   Error running account tasks: {e}")
    
    print("\n" + "=" * 60)
    print("All notification tasks completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
