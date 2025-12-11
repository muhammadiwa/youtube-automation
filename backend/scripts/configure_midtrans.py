"""Configure Midtrans payment gateway.

Usage:
    cd backend
    python -m scripts.configure_midtrans

Environment variables required:
    MIDTRANS_SERVER_KEY - Midtrans Server Key
    MIDTRANS_CLIENT_KEY - Midtrans Client Key (optional, for frontend)
    MIDTRANS_SANDBOX - Set to 'false' for production (default: true)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine
from app.modules.payment_gateway.interface import encrypt_credential


async def configure_midtrans():
    """Configure Midtrans gateway with credentials from environment."""
    
    server_key = os.getenv("MIDTRANS_SERVER_KEY", "")
    client_key = os.getenv("MIDTRANS_CLIENT_KEY", "")
    sandbox_mode = os.getenv("MIDTRANS_SANDBOX", "true").lower() != "false"
    
    print(f"\n{'='*60}")
    print("Configuring Midtrans Payment Gateway")
    print(f"{'='*60}")
    
    if not server_key:
        print("\n⚠️  MIDTRANS_SERVER_KEY not found in environment")
        print("Please set it in backend/.env file:")
        print("  MIDTRANS_SERVER_KEY=your_server_key_here")
        print("  MIDTRANS_CLIENT_KEY=your_client_key_here")
        print("  MIDTRANS_SANDBOX=true")
        return
    
    print(f"\nServer Key: {server_key[:8]}...{server_key[-4:]}")
    print(f"Client Key: {client_key[:8]}...{client_key[-4:]}" if client_key else "Client Key: Not set")
    print(f"Mode: {'Sandbox' if sandbox_mode else 'Production'}")
    
    # Encrypt credentials
    # For Midtrans: api_key = client_key, api_secret = server_key
    api_key_encrypted = encrypt_credential(client_key) if client_key else encrypt_credential(server_key)
    api_secret_encrypted = encrypt_credential(server_key)
    
    async with engine.begin() as conn:
        # Check if gateway exists
        result = await conn.execute(
            text("SELECT id FROM payment_gateway_configs WHERE provider = 'midtrans'")
        )
        existing = result.fetchone()
        
        if existing:
            # Update existing
            await conn.execute(
                text("""
                    UPDATE payment_gateway_configs
                    SET api_key_encrypted = :api_key,
                        api_secret_encrypted = :api_secret,
                        sandbox_mode = :sandbox_mode,
                        is_enabled = true,
                        updated_at = NOW()
                    WHERE provider = 'midtrans'
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Updated Midtrans configuration")
        else:
            # Insert new
            await conn.execute(
                text("""
                    INSERT INTO payment_gateway_configs 
                    (provider, display_name, api_key_encrypted, api_secret_encrypted, 
                     sandbox_mode, is_enabled,
                     supported_currencies, supported_payment_methods,
                     transaction_fee_percent, fixed_fee, min_amount)
                    VALUES 
                    ('midtrans', 'Midtrans', :api_key, :api_secret, 
                     :sandbox_mode, true,
                     '["IDR"]',
                     '["gopay", "ovo", "dana", "shopeepay", "bank_transfer", "credit_card", "qris"]',
                     2.9, 0, 10000)
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Created Midtrans configuration")
        
        print("✓ Midtrans gateway is now enabled")
        
        print(f"\n{'='*60}")
        print("Midtrans Notification Setup")
        print(f"{'='*60}")
        print("\nTo receive payment notifications, configure in Midtrans Dashboard:")
        print("1. Go to Settings > Configuration")
        print("2. Set Payment Notification URL: https://your-domain.com/api/payments/webhook/midtrans")
        print("3. Set Finish Redirect URL: https://your-domain.com/dashboard/billing/checkout/success")
        print("4. Set Unfinish Redirect URL: https://your-domain.com/dashboard/billing/checkout/failed")
        print("5. Set Error Redirect URL: https://your-domain.com/dashboard/billing/checkout/failed")


if __name__ == "__main__":
    asyncio.run(configure_midtrans())
