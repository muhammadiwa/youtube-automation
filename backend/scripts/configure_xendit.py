"""Configure Xendit payment gateway.

Usage:
    cd backend
    python -m scripts.configure_xendit

Environment variables required:
    XENDIT_SECRET_KEY - Xendit Secret API Key
    XENDIT_CALLBACK_TOKEN - Xendit Callback Verification Token
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


async def configure_xendit():
    """Configure Xendit gateway with credentials from environment."""
    
    secret_key = os.getenv("XENDIT_SECRET_KEY", "")
    callback_token = os.getenv("XENDIT_CALLBACK_TOKEN", "")
    # Xendit test keys start with 'xnd_development_'
    sandbox_mode = secret_key.startswith("xnd_development_") if secret_key else True
    
    print(f"\n{'='*60}")
    print("Configuring Xendit Payment Gateway")
    print(f"{'='*60}")
    
    if not secret_key:
        print("\n⚠️  XENDIT_SECRET_KEY not found in environment")
        print("Please set it in backend/.env file:")
        print("  XENDIT_SECRET_KEY=xnd_development_your_key_here")
        print("  XENDIT_CALLBACK_TOKEN=your_callback_token_here")
        return
    
    print(f"\nSecret Key: {secret_key[:20]}...{secret_key[-4:]}")
    print(f"Callback Token: {'Set' if callback_token else 'Not set'}")
    print(f"Mode: {'Development/Test' if sandbox_mode else 'Production'}")
    
    # Encrypt credentials
    # For Xendit: api_key and api_secret are both the secret key
    api_key_encrypted = encrypt_credential(secret_key)
    api_secret_encrypted = encrypt_credential(secret_key)
    webhook_secret_encrypted = encrypt_credential(callback_token) if callback_token else None
    
    async with engine.begin() as conn:
        # Check if gateway exists
        result = await conn.execute(
            text("SELECT id FROM payment_gateway_configs WHERE provider = 'xendit'")
        )
        existing = result.fetchone()
        
        if existing:
            # Update existing
            await conn.execute(
                text("""
                    UPDATE payment_gateway_configs
                    SET api_key_encrypted = :api_key,
                        api_secret_encrypted = :api_secret,
                        webhook_secret_encrypted = :webhook_secret,
                        sandbox_mode = :sandbox_mode,
                        is_enabled = true,
                        updated_at = NOW()
                    WHERE provider = 'xendit'
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "webhook_secret": webhook_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Updated Xendit configuration")
        else:
            # Insert new
            await conn.execute(
                text("""
                    INSERT INTO payment_gateway_configs 
                    (provider, display_name, api_key_encrypted, api_secret_encrypted, 
                     webhook_secret_encrypted, sandbox_mode, is_enabled,
                     supported_currencies, supported_payment_methods,
                     transaction_fee_percent, fixed_fee, min_amount)
                    VALUES 
                    ('xendit', 'Xendit', :api_key, :api_secret, :webhook_secret,
                     :sandbox_mode, true,
                     '["IDR", "PHP", "USD"]',
                     '["ovo", "dana", "linkaja", "shopeepay", "gcash", "grabpay", "bank_transfer", "credit_card", "qr_code"]',
                     2.9, 0, 10000)
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "webhook_secret": webhook_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Created Xendit configuration")
        
        print("✓ Xendit gateway is now enabled")
        
        print(f"\n{'='*60}")
        print("Xendit Callback Setup")
        print(f"{'='*60}")
        print("\nTo receive payment notifications, configure in Xendit Dashboard:")
        print("1. Go to Settings > Developers > Callbacks")
        print("2. Set Invoice Callback URL: https://your-domain.com/api/payments/webhook/xendit")
        print("3. Copy the Callback Verification Token and add to .env as XENDIT_CALLBACK_TOKEN")
        print("\nFor Invoice settings:")
        print("1. Go to Settings > Invoice")
        print("2. Set Success Redirect URL: https://your-domain.com/dashboard/billing/checkout/success")
        print("3. Set Failure Redirect URL: https://your-domain.com/dashboard/billing/checkout/failed")


if __name__ == "__main__":
    asyncio.run(configure_xendit())
