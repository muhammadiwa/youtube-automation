"""Test full Midtrans payment flow through service layer.

This simulates exactly what happens when frontend calls the API.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.test_full_midtrans_flow
"""

import asyncio
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import async_session_maker
from app.modules.payment_gateway.service import PaymentService, PaymentGatewayFactory
from app.modules.payment_gateway.repository import PaymentGatewayRepository


async def test_full_flow():
    """Test full Midtrans payment flow."""
    
    print(f"\n{'='*60}")
    print("Testing Full Midtrans Payment Flow")
    print(f"{'='*60}")
    
    async with async_session_maker() as session:
        # Step 1: Get gateway config
        print("\n1. Getting Midtrans gateway config...")
        repo = PaymentGatewayRepository(session)
        config = await repo.get_config_by_provider("midtrans")
        
        if not config:
            print("   ❌ Midtrans config not found!")
            return
        
        print(f"   Provider: {config.provider}")
        print(f"   Enabled: {config.is_enabled}")
        print(f"   Sandbox: {config.sandbox_mode}")
        print(f"   API Key Encrypted: {config.api_key_encrypted[:30] if config.api_key_encrypted else 'None'}...")
        print(f"   API Secret Encrypted: {config.api_secret_encrypted[:30] if config.api_secret_encrypted else 'None'}...")
        
        # Step 2: Create gateway instance
        print("\n2. Creating gateway instance...")
        gateway = PaymentGatewayFactory.create(config)
        
        print(f"   Gateway class: {gateway.__class__.__name__}")
        print(f"   API Key: {gateway.api_key[:20] if gateway.api_key else 'None'}...")
        print(f"   API Secret: {gateway.api_secret[:20] if gateway.api_secret else 'None'}...")
        
        if not gateway.api_secret:
            print("   ❌ API Secret is None! Credentials not decrypted properly.")
            return
        
        # Step 3: Test credentials
        print("\n3. Validating credentials...")
        validation = await gateway.validate_credentials()
        print(f"   Valid: {validation.is_valid}")
        print(f"   Message: {validation.message}")
        
        if not validation.is_valid:
            print("   ❌ Credentials validation failed!")
            return
        
        # Step 4: Create test payment
        print("\n4. Creating test payment...")
        from app.modules.payment_gateway.interface import CreatePaymentDTO
        
        payment_dto = CreatePaymentDTO(
            order_id=str(uuid.uuid4()),
            amount=50000,  # 50,000 IDR
            currency="IDR",
            description="Test Payment",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        
        result = await gateway.create_payment(payment_dto)
        
        print(f"   Status: {result.status}")
        print(f"   Payment ID: {result.payment_id}")
        print(f"   Checkout URL: {result.checkout_url}")
        print(f"   Error: {result.error_message}")
        
        if result.checkout_url:
            print("\n✓ Full flow test PASSED!")
        else:
            print("\n❌ Full flow test FAILED!")


if __name__ == "__main__":
    asyncio.run(test_full_flow())
