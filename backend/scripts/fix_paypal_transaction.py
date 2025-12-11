"""Fix PayPal transaction that was incorrectly marked as failed.

This script checks PayPal order status and fixes the transaction if it was actually completed.

Usage:
    cd backend
    python -m scripts.fix_paypal_transaction <transaction_id>
    
Example:
    python -m scripts.fix_paypal_transaction 6de0a191-245f-434a-8754-a3277d2eb1aa
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def fix_transaction(transaction_id: str):
    """Check and fix a PayPal transaction."""
    
    async with engine.begin() as conn:
        # Get transaction details
        result = await conn.execute(
            text("""
                SELECT id, gateway_provider, gateway_payment_id, status, amount, currency
                FROM payment_transactions
                WHERE id = :id
            """),
            {"id": transaction_id}
        )
        row = result.fetchone()
        
        if not row:
            print(f"Transaction {transaction_id} not found")
            return
        
        tx_id, provider, gateway_payment_id, status, amount, currency = row
        
        print(f"Transaction found:")
        print(f"  ID: {tx_id}")
        print(f"  Provider: {provider}")
        print(f"  Gateway Payment ID: {gateway_payment_id}")
        print(f"  Current Status: {status}")
        print(f"  Amount: {amount} {currency}")
        
        if provider != "paypal":
            print(f"\nThis is not a PayPal transaction")
            return
        
        if not gateway_payment_id:
            print(f"\nNo gateway payment ID found")
            return
        
        # Check PayPal order status
        print(f"\nChecking PayPal order status...")
        
        # Get PayPal credentials
        gateway_result = await conn.execute(
            text("""
                SELECT api_key_encrypted, api_secret_encrypted, sandbox_mode
                FROM payment_gateway_configs
                WHERE provider = 'paypal'
            """)
        )
        gateway_row = gateway_result.fetchone()
        
        if not gateway_row or not gateway_row[0]:
            print("PayPal credentials not configured")
            return
        
        from app.core.kms import kms_decrypt_simple
        import httpx
        import base64
        
        client_id = kms_decrypt_simple(gateway_row[0])
        client_secret = kms_decrypt_simple(gateway_row[1])
        sandbox_mode = gateway_row[2]
        
        base_url = "https://api-m.sandbox.paypal.com" if sandbox_mode else "https://api-m.paypal.com"
        
        # Get access token
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get order status
            order_response = await client.get(
                f"{base_url}/v2/checkout/orders/{gateway_payment_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            
            if order_response.status_code != 200:
                print(f"Failed to get order: {order_response.text}")
                return
            
            order_data = order_response.json()
            paypal_status = order_data.get("status", "UNKNOWN")
            
            print(f"PayPal Order Status: {paypal_status}")
            print(f"PayPal Response: {order_data}")
            
            if paypal_status == "COMPLETED":
                if status != "completed":
                    print(f"\n⚠️  Transaction status mismatch!")
                    print(f"   Database: {status}")
                    print(f"   PayPal: COMPLETED")
                    
                    fix = input("\nDo you want to fix this transaction? (y/n): ").strip().lower()
                    if fix == 'y':
                        await conn.execute(
                            text("""
                                UPDATE payment_transactions
                                SET status = 'completed',
                                    error_message = NULL,
                                    completed_at = NOW()
                                WHERE id = :id
                            """),
                            {"id": transaction_id}
                        )
                        print("✓ Transaction status updated to 'completed'")
                else:
                    print("\n✓ Transaction status is correct")
            elif paypal_status == "APPROVED":
                print(f"\n⚠️  Order is approved but not captured!")
                print("   The order needs to be captured to complete the payment.")
                
                capture = input("\nDo you want to capture this order? (y/n): ").strip().lower()
                if capture == 'y':
                    capture_response = await client.post(
                        f"{base_url}/v2/checkout/orders/{gateway_payment_id}/capture",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    if capture_response.status_code == 201:
                        capture_data = capture_response.json()
                        if capture_data.get("status") == "COMPLETED":
                            await conn.execute(
                                text("""
                                    UPDATE payment_transactions
                                    SET status = 'completed',
                                        error_message = NULL,
                                        completed_at = NOW()
                                    WHERE id = :id
                                """),
                                {"id": transaction_id}
                            )
                            print("✓ Order captured and transaction updated to 'completed'")
                        else:
                            print(f"Capture response: {capture_data}")
                    else:
                        print(f"Capture failed: {capture_response.text}")
            else:
                print(f"\nPayPal order status: {paypal_status}")
                print("No action needed or possible.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.fix_paypal_transaction <transaction_id>")
        print("\nExample:")
        print("  python -m scripts.fix_paypal_transaction 6de0a191-245f-434a-8754-a3277d2eb1aa")
        sys.exit(1)
    
    transaction_id = sys.argv[1]
    asyncio.run(fix_transaction(transaction_id))
