"""Configure Stripe payment gateway.

Usage:
    cd backend
    python -m scripts.configure_stripe

Environment variables required:
    STRIPE_API_KEY - Stripe Secret Key (sk_test_... or sk_live_...)
    STRIPE_WEBHOOK_SECRET - Stripe Webhook Secret (whsec_...)
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


async def configure_stripe():
    """Configure Stripe gateway with credentials from environment."""
    
    api_key = os.getenv("STRIPE_API_KEY", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    sandbox_mode = api_key.startswith("sk_test_") if api_key else True
    
    print(f"\n{'='*60}")
    print("Configuring Stripe Payment Gateway")
    print(f"{'='*60}")
    
    if not api_key:
        print("\n⚠️  STRIPE_API_KEY not found in environment")
        print("Please set it in backend/.env file:")
        print("  STRIPE_API_KEY=sk_test_your_key_here")
        print("  STRIPE_WEBHOOK_SECRET=whsec_your_secret_here")
        return
    
    print(f"\nAPI Key: {api_key[:12]}...{api_key[-4:]}")
    print(f"Webhook Secret: {'Set' if webhook_secret else 'Not set'}")
    print(f"Mode: {'Sandbox/Test' if sandbox_mode else 'Production/Live'}")
    
    # Encrypt credentials
    api_key_encrypted = encrypt_credential(api_key)
    # For Stripe, api_secret is the same as api_key
    api_secret_encrypted = encrypt_credential(api_key)
    webhook_secret_encrypted = encrypt_credential(webhook_secret) if webhook_secret else None
    
    async with engine.begin() as conn:
        # Check if gateway exists
        result = await conn.execute(
            text("SELECT id FROM payment_gateway_configs WHERE provider = 'stripe'")
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
                    WHERE provider = 'stripe'
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "webhook_secret": webhook_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Updated Stripe configuration")
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
                    ('stripe', 'Stripe', :api_key, :api_secret, :webhook_secret, 
                     :sandbox_mode, true,
                     '["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "SGD"]',
                     '["card", "apple_pay", "google_pay"]',
                     2.9, 0.30, 0.50)
                """),
                {
                    "api_key": api_key_encrypted,
                    "api_secret": api_secret_encrypted,
                    "webhook_secret": webhook_secret_encrypted,
                    "sandbox_mode": sandbox_mode,
                }
            )
            print("\n✓ Created Stripe configuration")
        
        print("✓ Stripe gateway is now enabled")
        
        print(f"\n{'='*60}")
        print("Stripe Webhook Setup")
        print(f"{'='*60}")
        print("\nTo receive payment notifications, set up a webhook in Stripe Dashboard:")
        print("1. Go to https://dashboard.stripe.com/webhooks")
        print("2. Click 'Add endpoint'")
        print("3. Enter your webhook URL: https://your-domain.com/api/payments/webhook/stripe")
        print("4. Select events: checkout.session.completed, payment_intent.succeeded, payment_intent.payment_failed")
        print("5. Copy the webhook signing secret and add to .env as STRIPE_WEBHOOK_SECRET")


if __name__ == "__main__":
    asyncio.run(configure_stripe())
