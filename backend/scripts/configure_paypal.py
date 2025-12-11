"""Configure PayPal gateway for testing.

This script configures PayPal sandbox credentials and enables the gateway.

Usage:
    cd backend
    python -m scripts.configure_paypal

You need to set these environment variables or edit the values below:
    PAYPAL_CLIENT_ID - Your PayPal sandbox Client ID
    PAYPAL_CLIENT_SECRET - Your PayPal sandbox Client Secret
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.core.kms import kms_encrypt_simple


# PayPal Sandbox Credentials
# Get from: https://developer.paypal.com/dashboard/applications/sandbox
# Create a new app or use existing one
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")


async def configure_paypal():
    """Configure PayPal gateway with sandbox credentials."""
    
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("=" * 60)
        print("PayPal Configuration")
        print("=" * 60)
        print("\nPlease provide your PayPal Sandbox credentials.")
        print("Get them from: https://developer.paypal.com/dashboard/applications/sandbox")
        print("\nYou can either:")
        print("1. Set environment variables:")
        print("   set PAYPAL_CLIENT_ID=your_client_id")
        print("   set PAYPAL_CLIENT_SECRET=your_client_secret")
        print("\n2. Or edit this script and set the values directly.")
        print("\n" + "=" * 60)
        
        # Interactive input
        client_id = input("\nEnter PayPal Client ID (or press Enter to skip): ").strip()
        if not client_id:
            print("Skipped. No changes made.")
            return
        
        client_secret = input("Enter PayPal Client Secret: ").strip()
        if not client_secret:
            print("Skipped. No changes made.")
            return
    else:
        client_id = PAYPAL_CLIENT_ID
        client_secret = PAYPAL_CLIENT_SECRET
    
    print("\nConfiguring PayPal gateway...")
    
    # Encrypt credentials
    encrypted_client_id = kms_encrypt_simple(client_id)
    encrypted_client_secret = kms_encrypt_simple(client_secret)
    
    async with engine.begin() as conn:
        # Update PayPal gateway configuration
        await conn.execute(
            text("""
                UPDATE payment_gateway_configs 
                SET api_key_encrypted = :client_id,
                    api_secret_encrypted = :client_secret,
                    is_enabled = true,
                    is_default = true,
                    sandbox_mode = true
                WHERE provider = 'paypal'
            """),
            {
                "client_id": encrypted_client_id,
                "client_secret": encrypted_client_secret,
            }
        )
        
        # Disable other gateways as default
        await conn.execute(
            text("""
                UPDATE payment_gateway_configs 
                SET is_default = false
                WHERE provider != 'paypal'
            """)
        )
        
        print("✓ PayPal credentials configured")
        print("✓ PayPal gateway enabled")
        print("✓ PayPal set as default gateway")
        
        # Verify configuration
        result = await conn.execute(
            text("""
                SELECT provider, is_enabled, is_default, sandbox_mode,
                       api_key_encrypted IS NOT NULL as has_client_id,
                       api_secret_encrypted IS NOT NULL as has_client_secret
                FROM payment_gateway_configs
                WHERE provider = 'paypal'
            """)
        )
        row = result.fetchone()
        
        if row:
            print("\n" + "=" * 60)
            print("PayPal Gateway Status:")
            print(f"  Provider: {row[0]}")
            print(f"  Enabled: {row[1]}")
            print(f"  Default: {row[2]}")
            print(f"  Sandbox Mode: {row[3]}")
            print(f"  Has Client ID: {row[4]}")
            print(f"  Has Client Secret: {row[5]}")
            print("=" * 60)
            print("\nYou can now test PayPal payments in the checkout page!")


async def test_paypal_credentials():
    """Test PayPal credentials by getting an access token."""
    import httpx
    import base64
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT api_key_encrypted, api_secret_encrypted, sandbox_mode
                FROM payment_gateway_configs
                WHERE provider = 'paypal'
            """)
        )
        row = result.fetchone()
        
        if not row or not row[0] or not row[1]:
            print("PayPal credentials not configured. Run configure first.")
            return False
        
        from app.core.kms import kms_decrypt_simple
        client_id = kms_decrypt_simple(row[0])
        client_secret = kms_decrypt_simple(row[1])
        sandbox_mode = row[2]
        
        base_url = "https://api-m.sandbox.paypal.com" if sandbox_mode else "https://api-m.paypal.com"
        
        print(f"\nTesting PayPal credentials ({('sandbox' if sandbox_mode else 'production')})...")
        
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{base_url}/v1/oauth2/token",
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"grant_type": "client_credentials"},
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✓ PayPal credentials are valid!")
                    print(f"  Access token obtained (expires in {data.get('expires_in', 0)} seconds)")
                    return True
                else:
                    print(f"✗ PayPal authentication failed: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error testing PayPal credentials: {e}")
                return False


if __name__ == "__main__":
    print("=" * 60)
    print("PayPal Gateway Configuration Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_paypal_credentials())
    else:
        asyncio.run(configure_paypal())
        
        # Ask if user wants to test
        test = input("\nDo you want to test the credentials? (y/n): ").strip().lower()
        if test == 'y':
            asyncio.run(test_paypal_credentials())
