"""Test Midtrans payment gateway.

Usage:
    cd backend
    python -m scripts.test_midtrans
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine


async def test_midtrans():
    """Test Midtrans gateway configuration and credentials."""
    
    print(f"\n{'='*60}")
    print("Testing Midtrans Payment Gateway")
    print(f"{'='*60}")
    
    async with engine.begin() as conn:
        # Get Midtrans config
        result = await conn.execute(
            text("""
                SELECT provider, display_name, is_enabled, sandbox_mode,
                       api_key_encrypted, api_secret_encrypted,
                       supported_currencies, min_amount
                FROM payment_gateway_configs 
                WHERE provider = 'midtrans'
            """)
        )
        row = result.fetchone()
        
        if not row:
            print("\n❌ Midtrans gateway not found in database!")
            print("Run: python -m scripts.configure_midtrans")
            return
        
        print(f"\nProvider: {row[0]}")
        print(f"Display Name: {row[1]}")
        print(f"Enabled: {row[2]}")
        print(f"Sandbox Mode: {row[3]}")
        print(f"Supported Currencies: {row[6]}")
        print(f"Min Amount: {row[7]}")
        
        # Decrypt credentials
        api_key_encrypted = row[4]
        api_secret_encrypted = row[5]
        
        if not api_secret_encrypted:
            print("\n❌ No API secret (server key) configured!")
            return
        
        from app.modules.payment_gateway.interface import decrypt_credential
        api_key = decrypt_credential(api_key_encrypted) if api_key_encrypted else None
        api_secret = decrypt_credential(api_secret_encrypted) if api_secret_encrypted else None
        
        print(f"\nAPI Key (Client Key): {api_key[:8]}...{api_key[-4:]}" if api_key else "\nAPI Key: Not set")
        print(f"API Secret (Server Key): {api_secret[:8]}...{api_secret[-4:]}" if api_secret else "API Secret: Not set")
        
        if not api_secret:
            print("\n❌ Failed to decrypt API secret!")
            return
        
        # Test API connection
        print(f"\n{'='*60}")
        print("Testing Midtrans API Connection")
        print(f"{'='*60}")
        
        import base64
        import httpx
        
        sandbox_mode = row[3]
        base_url = "https://api.sandbox.midtrans.com" if sandbox_mode else "https://api.midtrans.com"
        
        # Create auth header
        auth = base64.b64encode(f"{api_secret}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            # Test with a status check for non-existent order
            test_url = f"{base_url}/v2/test-order-12345/status"
            print(f"\nTesting: GET {test_url}")
            
            response = await client.get(test_url, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 401:
                print("\n❌ Authentication failed! Check your Server Key.")
            elif response.status_code == 404:
                print("\n✓ Authentication successful! (404 is expected for non-existent order)")
            else:
                print(f"\n⚠️  Unexpected status code: {response.status_code}")
        
        # Test Snap API
        print(f"\n{'='*60}")
        print("Testing Midtrans Snap API")
        print(f"{'='*60}")
        
        snap_url = "https://app.sandbox.midtrans.com/snap/v1" if sandbox_mode else "https://app.midtrans.com/snap/v1"
        
        test_transaction = {
            "transaction_details": {
                "order_id": f"test-order-{asyncio.get_event_loop().time()}",
                "gross_amount": 50000,  # 50,000 IDR
            },
            "customer_details": {
                "email": "test@example.com",
                "first_name": "Test",
            },
        }
        
        async with httpx.AsyncClient() as client:
            test_url = f"{snap_url}/transactions"
            print(f"\nTesting: POST {test_url}")
            print(f"Request: {test_transaction}")
            
            response = await client.post(
                test_url,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=test_transaction,
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"\n✓ Snap transaction created successfully!")
                print(f"Token: {data.get('token', 'N/A')}")
                print(f"Redirect URL: {data.get('redirect_url', 'N/A')}")
            elif response.status_code == 401:
                print("\n❌ Authentication failed! Check your Server Key.")
            else:
                print(f"\n❌ Failed to create Snap transaction")


if __name__ == "__main__":
    asyncio.run(test_midtrans())
