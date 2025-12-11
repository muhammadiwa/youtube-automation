"""Test Midtrans payment flow through the service layer.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.test_midtrans_payment
"""

import asyncio
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, async_session_maker
from app.modules.payment_gateway.service import PaymentService


async def test_midtrans_payment():
    """Test Midtrans payment through service layer."""
    
    print(f"\n{'='*60}")
    print("Testing Midtrans Payment Flow")
    print(f"{'='*60}")
    
    async with async_session_maker() as session:
        service = PaymentService(session)
        
        # Test user ID (use a real user ID from your database)
        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        try:
            print("\n1. Creating payment transaction...")
            transaction = await service.create_payment(
                user_id=test_user_id,
                amount=50000,  # 50,000 IDR
                currency="IDR",
                description="Test Midtrans Payment",
                gateway_provider="midtrans",
                success_url="http://localhost:3000/dashboard/billing/checkout/success",
                cancel_url="http://localhost:3000/dashboard/billing/checkout/failed",
                metadata={"test": True},
            )
            
            print(f"   Transaction ID: {transaction.id}")
            print(f"   Gateway: {transaction.gateway_provider}")
            print(f"   Amount: {transaction.amount} {transaction.currency}")
            print(f"   Status: {transaction.status}")
            
            print("\n2. Processing payment...")
            transaction = await service.process_payment(transaction.id)
            
            print(f"   Status: {transaction.status}")
            print(f"   Checkout URL: {transaction.checkout_url}")
            print(f"   Gateway Payment ID: {transaction.gateway_payment_id}")
            
            if transaction.checkout_url:
                print(f"\n✓ Payment created successfully!")
                print(f"   Open this URL to complete payment:")
                print(f"   {transaction.checkout_url}")
            else:
                print(f"\n❌ No checkout URL returned")
                print(f"   Error: {transaction.error_message}")
            
            await session.commit()
            
        except Exception as e:
            import traceback
            print(f"\n❌ Error: {e}")
            print(f"\nTraceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_midtrans_payment())
