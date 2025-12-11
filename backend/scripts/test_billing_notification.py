"""Test billing notification service.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.test_billing_notification
"""

import asyncio
import uuid
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import async_session_maker
from app.modules.billing.notifications import BillingNotificationService


async def test_notifications():
    """Test billing notifications."""
    
    print("\n" + "=" * 60)
    print("Testing Billing Notification Service")
    print("=" * 60)
    
    # Use a test user ID (you can change this to a real user ID)
    test_user_id = uuid.UUID("4281aaf4-4a2b-4e79-9e24-b85ac9866514")
    
    async with async_session_maker() as session:
        notification_service = BillingNotificationService(session)
        
        print("\n1. Testing payment success notification...")
        try:
            await notification_service.notify_payment_success(
                user_id=test_user_id,
                amount=29.99,
                currency="USD",
                plan_name="Pro",
                billing_cycle="monthly",
                payment_id="test-payment-123",
                gateway="stripe",
            )
            print("   ✓ Payment success notification sent")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n2. Testing subscription activated notification...")
        try:
            await notification_service.notify_subscription_activated(
                user_id=test_user_id,
                plan_name="Pro",
                billing_cycle="monthly",
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            print("   ✓ Subscription activated notification sent")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n3. Testing subscription expiring notification...")
        try:
            await notification_service.notify_subscription_expiring(
                user_id=test_user_id,
                plan_name="Pro",
                expires_at=datetime.utcnow() + timedelta(days=3),
                days_remaining=3,
            )
            print("   ✓ Subscription expiring notification sent")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        await session.commit()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("Check the notification_logs table for results.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_notifications())
