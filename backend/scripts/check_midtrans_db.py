"""Check Midtrans configuration in database.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.check_midtrans_db
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine


async def check_midtrans():
    """Check Midtrans configuration in database."""
    
    print(f"\n{'='*60}")
    print("Checking Midtrans Configuration in Database")
    print(f"{'='*60}")
    
    async with engine.begin() as conn:
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
            print("\n❌ Midtrans gateway not found!")
            return
        
        print(f"\nProvider: {row[0]}")
        print(f"Display Name: {row[1]}")
        print(f"Enabled: {row[2]}")
        print(f"Sandbox Mode: {row[3]}")
        print(f"Supported Currencies: {row[6]}")
        print(f"Min Amount: {row[7]}")
        
        api_key = row[4]
        api_secret = row[5]
        
        print(f"\nAPI Key (raw): {api_key[:50] if api_key else 'None'}...")
        print(f"API Secret (raw): {api_secret[:50] if api_secret else 'None'}...")
        
        # Check if it looks encrypted or plain text
        if api_secret:
            if api_secret.startswith(('SB-', 'Mid-')):
                print("\n⚠️  API Secret appears to be PLAIN TEXT (not encrypted)")
            elif api_secret.startswith('gAAAAA'):
                print("\n✓ API Secret appears to be encrypted (Fernet format)")
            else:
                print(f"\n⚠️  API Secret format unknown: starts with '{api_secret[:10]}'")


if __name__ == "__main__":
    asyncio.run(check_midtrans())
