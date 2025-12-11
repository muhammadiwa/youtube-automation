"""Fix subscription period based on payment transaction metadata.

This script checks if the subscription period matches the billing_cycle
from the payment transaction metadata and fixes it if needed.

Usage:
    cd backend
    python -m scripts.fix_subscription_period <user_id>
    
Example:
    python -m scripts.fix_subscription_period 4281aaf4-4a2b-4e79-9e24-b85ac9866514
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def fix_subscription_period(user_id: str):
    """Fix subscription period based on billing_cycle from transaction metadata."""
    
    async with engine.begin() as conn:
        print(f"\n{'='*60}")
        print(f"Checking subscription period for user: {user_id}")
        print(f"{'='*60}")
        
        # Get subscription
        result = await conn.execute(
            text("""
                SELECT id, plan_tier, status, 
                       current_period_start, current_period_end
                FROM subscriptions
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        sub = result.fetchone()
        
        if not sub:
            print(f"\n✗ No subscription found for user")
            return
        
        sub_id, plan_tier, status, period_start, period_end = sub
        print(f"\nCurrent Subscription:")
        print(f"  ID: {sub_id}")
        print(f"  Plan: {plan_tier}")
        print(f"  Status: {status}")
        print(f"  Period Start: {period_start}")
        print(f"  Period End: {period_end}")
        
        # Calculate current period length
        if period_start and period_end:
            period_days = (period_end - period_start).days
            print(f"  Period Length: {period_days} days")
        
        # Get latest completed transaction for this user
        result = await conn.execute(
            text("""
                SELECT id, amount, description, metadata, created_at
                FROM payment_transactions
                WHERE user_id = :user_id AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 1
            """),
            {"user_id": user_id}
        )
        tx = result.fetchone()
        
        if not tx:
            print(f"\n✗ No completed transaction found")
            return
        
        tx_id, amount, description, metadata, tx_created = tx
        print(f"\nLatest Completed Transaction:")
        print(f"  ID: {tx_id}")
        print(f"  Amount: {amount}")
        print(f"  Description: {description}")
        print(f"  Metadata: {metadata}")
        print(f"  Created: {tx_created}")
        
        # Get billing_cycle from metadata
        billing_cycle = None
        if metadata:
            billing_cycle = metadata.get("billing_cycle")
        
        if not billing_cycle:
            # Try to detect from description
            if description:
                if "yearly" in description.lower() or "annual" in description.lower():
                    billing_cycle = "yearly"
                elif "monthly" in description.lower():
                    billing_cycle = "monthly"
        
        if not billing_cycle:
            # Try to detect from amount
            # Pro plan: monthly=$29.99, yearly=$299.99
            # Basic plan: monthly=$9.99, yearly=$99.99
            if amount in [299.99, 99.99, 999.99]:
                billing_cycle = "yearly"
            elif amount in [29.99, 9.99, 99.99]:
                billing_cycle = "monthly"
        
        print(f"\nDetected billing_cycle: {billing_cycle}")
        
        if not billing_cycle:
            print(f"\n⚠️  Could not determine billing_cycle")
            billing_cycle = input("Enter billing_cycle (monthly/yearly): ").strip().lower()
            if billing_cycle not in ["monthly", "yearly"]:
                print("Invalid input. Exiting.")
                return
        
        # Calculate expected period
        expected_days = 365 if billing_cycle == "yearly" else 30
        
        print(f"\nExpected period: {expected_days} days")
        print(f"Current period: {period_days} days")
        
        if period_days != expected_days:
            print(f"\n⚠️  Period mismatch detected!")
            
            fix = input(f"\nDo you want to fix the period to {expected_days} days? (y/n): ").strip().lower()
            if fix == 'y':
                # Use the transaction created time as period start
                new_period_start = tx_created
                if billing_cycle == "yearly":
                    new_period_end = new_period_start + timedelta(days=365)
                else:
                    new_period_end = new_period_start + timedelta(days=30)
                
                await conn.execute(
                    text("""
                        UPDATE subscriptions
                        SET billing_cycle = :billing_cycle,
                            current_period_start = :period_start,
                            current_period_end = :period_end
                        WHERE id = :sub_id
                    """),
                    {
                        "sub_id": str(sub_id),
                        "billing_cycle": billing_cycle,
                        "period_start": new_period_start,
                        "period_end": new_period_end,
                    }
                )
                
                print(f"\n✓ Updated subscription:")
                print(f"  Billing Cycle: {billing_cycle}")
                print(f"  New Period Start: {new_period_start}")
                print(f"  New Period End: {new_period_end}")
                print(f"  Period Length: {expected_days} days")
        else:
            print(f"\n✓ Period is correct!")


async def auto_fix_subscription_period(user_id: str):
    """Automatically fix subscription period based on billing_cycle from transaction metadata."""
    
    async with engine.begin() as conn:
        print(f"\n{'='*60}")
        print(f"Auto-fixing subscription period for user: {user_id}")
        print(f"{'='*60}")
        
        # Get subscription
        result = await conn.execute(
            text("""
                SELECT id, plan_tier, status, 
                       current_period_start, current_period_end
                FROM subscriptions
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        sub = result.fetchone()
        
        if not sub:
            print(f"\n✗ No subscription found for user")
            return False
        
        sub_id, plan_tier, status, period_start, period_end = sub
        
        # Get latest completed transaction for this user
        result = await conn.execute(
            text("""
                SELECT id, amount, description, metadata, created_at
                FROM payment_transactions
                WHERE user_id = :user_id AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 1
            """),
            {"user_id": user_id}
        )
        tx = result.fetchone()
        
        if not tx:
            print(f"\n✗ No completed transaction found")
            return False
        
        tx_id, amount, description, metadata, tx_created = tx
        
        # Get billing_cycle from metadata
        billing_cycle = None
        if metadata:
            billing_cycle = metadata.get("billing_cycle")
        
        if not billing_cycle:
            # Try to detect from description
            if description:
                if "yearly" in description.lower() or "annual" in description.lower():
                    billing_cycle = "yearly"
                elif "monthly" in description.lower():
                    billing_cycle = "monthly"
        
        if not billing_cycle:
            # Try to detect from amount
            if amount in [299.99, 99.99, 999.99]:
                billing_cycle = "yearly"
            else:
                billing_cycle = "monthly"
        
        # Calculate expected period
        expected_days = 365 if billing_cycle == "yearly" else 30
        
        # Calculate current period length
        if period_start and period_end:
            period_days = (period_end - period_start).days
        else:
            period_days = 0
        
        print(f"\nSubscription: {plan_tier} ({status})")
        print(f"Billing cycle: {billing_cycle}")
        print(f"Current period: {period_days} days")
        print(f"Expected period: {expected_days} days")
        
        if period_days != expected_days:
            # Use the transaction created time as period start
            new_period_start = tx_created
            if billing_cycle == "yearly":
                new_period_end = new_period_start + timedelta(days=365)
            else:
                new_period_end = new_period_start + timedelta(days=30)
            
            await conn.execute(
                text("""
                    UPDATE subscriptions
                    SET billing_cycle = :billing_cycle,
                        current_period_start = :period_start,
                        current_period_end = :period_end
                    WHERE id = :sub_id
                """),
                {
                    "sub_id": str(sub_id),
                    "billing_cycle": billing_cycle,
                    "period_start": new_period_start,
                    "period_end": new_period_end,
                }
            )
            
            print(f"\n✓ Fixed subscription:")
            print(f"  Billing Cycle: {billing_cycle}")
            print(f"  New Period Start: {new_period_start}")
            print(f"  New Period End: {new_period_end}")
            return True
        else:
            print(f"\n✓ Period is already correct!")
            return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.fix_subscription_period <user_id>")
        print("       python -m scripts.fix_subscription_period <user_id> --auto")
        print("\nExample:")
        print("  python -m scripts.fix_subscription_period 4281aaf4-4a2b-4e79-9e24-b85ac9866514")
        print("  python -m scripts.fix_subscription_period 4281aaf4-4a2b-4e79-9e24-b85ac9866514 --auto")
        sys.exit(1)
    
    user_id = sys.argv[1]
    auto_mode = len(sys.argv) > 2 and sys.argv[2] == "--auto"
    
    if auto_mode:
        asyncio.run(auto_fix_subscription_period(user_id))
    else:
        asyncio.run(fix_subscription_period(user_id))
