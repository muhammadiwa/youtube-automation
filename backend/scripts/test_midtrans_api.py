"""Test Midtrans payment via API endpoint.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.test_midtrans_api
"""

import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_midtrans_api():
    """Test Midtrans payment via API endpoint."""
    
    print(f"\n{'='*60}")
    print("Testing Midtrans Payment via API")
    print(f"{'='*60}")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test user ID
    user_id = "00000000-0000-0000-0000-000000000001"
    
    # Payment data (simulating frontend request)
    payment_data = {
        "amount": 500122,  # ~$29.99 in IDR
        "currency": "IDR",
        "description": "Pro Plan - monthly subscription",
        "preferred_gateway": "midtrans",
        "success_url": "http://localhost:3000/dashboard/billing/checkout/success?plan=pro&cycle=monthly",
        "cancel_url": "http://localhost:3000/dashboard/billing/checkout/failed?plan=pro&reason=cancelled",
        "metadata": {
            "plan_id": "test-plan-id",
            "plan_slug": "pro",
            "billing_cycle": "monthly",
            "original_amount_usd": 29.99,
        }
    }
    
    print(f"\nRequest data:")
    print(f"  Amount: {payment_data['amount']} {payment_data['currency']}")
    print(f"  Gateway: {payment_data['preferred_gateway']}")
    print(f"  Description: {payment_data['description']}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/payments",
                json=payment_data,
                headers={
                    "X-User-ID": user_id,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("checkout_url"):
                    print(f"\n✓ Payment created successfully!")
                    print(f"  Checkout URL: {data['checkout_url']}")
                else:
                    print(f"\n❌ No checkout URL returned")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Error: {data.get('error_message')}")
            else:
                print(f"\n❌ API error: {response.status_code}")
                
        except httpx.ConnectError:
            print(f"\n❌ Cannot connect to backend at {base_url}")
            print("   Make sure the backend server is running:")
            print("   cd backend && venv\\Scripts\\activate && uvicorn app.main:app --reload")
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_midtrans_api())
