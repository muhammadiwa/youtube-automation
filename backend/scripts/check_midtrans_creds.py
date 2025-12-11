"""Check Midtrans credentials decryption.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.check_midtrans_creds
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine
from app.modules.payment_gateway.interface import decrypt_credential


async def check_creds():
    """Check Midtrans credentials decryption."""
    
    print(f"\n{'='*60}")
    print("Checking Midtrans Credentials Decryption")
    print(f"{'='*60}")
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT api_key_encrypted, api_secret_encrypted FROM payment_gateway_configs WHERE provider = 'midtrans'")
        )
        row = result.fetchone()
        
        if not row:
            print("\n❌ Midtrans not found in database")
            return
        
        api_key_enc = row[0]
        api_secret_enc = row[1]
        
        print(f"\nEncrypted API Key: {api_key_enc[:50] if api_key_enc else 'None'}...")
        print(f"Encrypted API Secret: {api_secret_enc[:50] if api_secret_enc else 'None'}...")
        
        api_key = decrypt_credential(api_key_enc) if api_key_enc else None
        api_secret = decrypt_credential(api_secret_enc) if api_secret_enc else None
        
        print(f"\nDecrypted API Key: {api_key}")
        print(f"Decrypted API Secret: {api_secret}")
        
        if api_secret:
            # Test with Midtrans API
            import base64
            import httpx
            
            auth = base64.b64encode(f"{api_secret}:".encode()).decode()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.sandbox.midtrans.com/v2/test-order/status",
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Accept": "application/json",
                    },
                )
                print(f"\nAPI Test Response: {response.status_code}")
                if response.status_code == 401:
                    print("❌ Credentials are INVALID")
                else:
                    print("✓ Credentials are VALID")


if __name__ == "__main__":
    asyncio.run(check_creds())
