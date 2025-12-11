"""Check and fix subscription for a user.

Usage:
    cd backend
    python -m scripts.check_subscription <user_id>
    
Example:
    python -m scripts.check_subscription 4281aaf4-4a2b-4e79-9e24-b85ac9866514
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def check_subscription(user_id: str):
    """Check subscription status for a user."""
    
    async with engine.begin() as conn:
        print(f"\n{'='*60}")
        print(f"Checking subscription for user: {user_id}")
        print(f"{'='*60}")
        
        # Check subscription
        result = await conn.execute(
            text("""
                SELECT id, user_id, plan_tier, status, 
                       current_period_start, current_period_end,
                       cancel_at_period_end, created_at
                FROM subscriptions
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        sub = result.fetchone()
        
        if sub:
            print(f"\n✓ Subscription found:")
            print(f"  ID: {sub[0]}")
            print(f"  Plan: {sub[2]}")
            print(f"  Status: {sub[3]}")
            print(f"  Period: {sub[4]} to {sub[5]}")
            print(f"  Cancel at period end: {sub[6]}")
            print(f"  Created: {sub[7]}")
        else:
            print(f"\n✗ No subscription found for user")
        
        # Check payment transactions
        print(f"\n{'='*60}")
        print("Payment Transactions:")
        print(f"{'='*60}")
        
        result = await conn.execute(
            text("""
                SELECT id, gateway_provider, amount, currency, status,
                       subscription_id, description, created_at, completed_at,
                       metadata
                FROM payment_transactions
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"user_id": user_id}
        )
        transactions = result.fetchall()
        
        if transactions:
            for tx in transactions:
                print(f"\n  Transaction: {tx[0]}")
                print(f"    Gateway: {tx[1]}")
                print(f"    Amount: {tx[2]} {tx[3]}")
                print(f"    Status: {tx[4]}")
                print(f"    Subscription ID: {tx[5]}")
                print(f"    Description: {tx[6]}")
                print(f"    Created: {tx[7]}")
                print(f"    Completed: {tx[8]}")
                print(f"    Metadata: {tx[9]}")
        else:
            print("  No transactions found")
        
        # Check if there's a completed transaction without subscription
        print(f"\n{'='*60}")
        print("Analysis:")
        print(f"{'='*60}")
        
        completed_tx = None
        for tx in transactions:
            if tx[4] == "completed":
                completed_tx = tx
                break
        
        if completed_tx and not sub:
            print(f"\n⚠️  Found completed transaction but no subscription!")
            print(f"   Transaction ID: {completed_tx[0]}")
            
            # Get plan info from metadata
            metadata = completed_tx[9] or {}
            plan_slug = metadata.get("plan_slug")
            billing_cycle = metadata.get("billing_cycle", "monthly")
            
            if plan_slug:
                print(f"   Plan from metadata: {plan_slug}")
                print(f"   Billing cycle: {billing_cycle}")
                
                fix = input("\nDo you want to create subscription? (y/n): ").strip().lower()
                if fix == 'y':
                    from datetime import datetime, timedelta
                    
                    now = datetime.utcnow()
                    if billing_cycle == "yearly":
                        period_end = now + timedelta(days=365)
                    else:
                        period_end = now + timedelta(days=30)
                    
                    # Create subscription
                    import uuid
                    sub_id = str(uuid.uuid4())
                    
                    await conn.execute(
                        text("""
                            INSERT INTO subscriptions 
                            (id, user_id, plan_tier, status, current_period_start, current_period_end)
                            VALUES (:id, :user_id, :plan_tier, 'active', :period_start, :period_end)
                        """),
                        {
                            "id": sub_id,
                            "user_id": user_id,
                            "plan_tier": plan_slug,
                            "period_start": now,
                            "period_end": period_end,
                        }
                    )
                    
                    # Update transaction with subscription_id
                    await conn.execute(
                        text("""
                            UPDATE payment_transactions
                            SET subscription_id = :sub_id
                            WHERE id = :tx_id
                        """),
                        {"sub_id": sub_id, "tx_id": str(completed_tx[0])}
                    )
                    
                    print(f"\n✓ Created subscription: {sub_id}")
                    print(f"✓ Updated transaction with subscription_id")
            else:
                print(f"   ⚠️  No plan_slug in transaction metadata")
        
        elif completed_tx and sub:
            if completed_tx[5] is None:
                print(f"\n⚠️  Completed transaction missing subscription_id")
                print(f"   Transaction ID: {completed_tx[0]}")
                print(f"   Subscription ID: {sub[0]}")
                
                fix = input("\nDo you want to link transaction to subscription? (y/n): ").strip().lower()
                if fix == 'y':
                    await conn.execute(
                        text("""
                            UPDATE payment_transactions
                            SET subscription_id = :sub_id
                            WHERE id = :tx_id
                        """),
                        {"sub_id": str(sub[0]), "tx_id": str(completed_tx[0])}
                    )
                    print(f"✓ Updated transaction with subscription_id")
            else:
                print(f"\n✓ Everything looks good!")
                print(f"   Subscription: {sub[2]} ({sub[3]})")
                print(f"   Latest completed transaction linked to subscription")
        
        elif not completed_tx:
            print(f"\n  No completed transactions found")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.check_subscription <user_id>")
        print("\nExample:")
        print("  python -m scripts.check_subscription 4281aaf4-4a2b-4e79-9e24-b85ac9866514")
        sys.exit(1)
    
    user_id = sys.argv[1]
    asyncio.run(check_subscription(user_id))
