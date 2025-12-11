"""Fix payment gateway JSON data that was double-encoded.

This script fixes the issue where JSON columns (supported_currencies, 
supported_payment_methods, config_metadata) were stored as JSON strings 
instead of proper JSON arrays/objects.

Run this script if payment gateways are not showing up in the checkout page
after migration 027.

Usage:
    cd backend
    python -m scripts.fix_gateway_json_data
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import async_engine


async def fix_gateway_json_data():
    """Fix double-encoded JSON data in payment_gateway_configs table."""
    
    async with async_engine.begin() as conn:
        # First, check current data
        result = await conn.execute(
            text("SELECT id, provider, supported_currencies, supported_payment_methods, config_metadata FROM payment_gateway_configs")
        )
        rows = result.fetchall()
        
        if not rows:
            print("No payment gateway configs found in database.")
            print("Run 'alembic upgrade head' to create them.")
            return
        
        print(f"Found {len(rows)} payment gateway configs:")
        print("-" * 60)
        
        fixed_count = 0
        
        for row in rows:
            gateway_id, provider, currencies, methods, metadata = row
            print(f"\nProvider: {provider}")
            print(f"  Currencies type: {type(currencies)}")
            print(f"  Currencies value: {currencies}")
            
            needs_fix = False
            new_currencies = currencies
            new_methods = methods
            new_metadata = metadata
            
            # Check if currencies is a string (double-encoded)
            if isinstance(currencies, str):
                try:
                    new_currencies = json.loads(currencies)
                    needs_fix = True
                    print(f"  -> Will fix currencies to: {new_currencies}")
                except json.JSONDecodeError:
                    print(f"  -> Currencies is invalid JSON string")
            
            # Check if methods is a string (double-encoded)
            if isinstance(methods, str):
                try:
                    new_methods = json.loads(methods)
                    needs_fix = True
                    print(f"  -> Will fix methods to: {new_methods}")
                except json.JSONDecodeError:
                    print(f"  -> Methods is invalid JSON string")
            
            # Check if metadata is a string (double-encoded)
            if isinstance(metadata, str):
                try:
                    new_metadata = json.loads(metadata)
                    needs_fix = True
                    print(f"  -> Will fix metadata to: {new_metadata}")
                except json.JSONDecodeError:
                    print(f"  -> Metadata is invalid JSON string")
            
            if needs_fix:
                # Update the row with proper JSON
                await conn.execute(
                    text("""
                        UPDATE payment_gateway_configs 
                        SET supported_currencies = :currencies::jsonb,
                            supported_payment_methods = :methods::jsonb,
                            config_metadata = :metadata::jsonb
                        WHERE id = :id
                    """),
                    {
                        "id": gateway_id,
                        "currencies": json.dumps(new_currencies),
                        "methods": json.dumps(new_methods),
                        "metadata": json.dumps(new_metadata) if new_metadata else "{}",
                    }
                )
                fixed_count += 1
                print(f"  -> FIXED!")
            else:
                print(f"  -> OK (no fix needed)")
        
        print("\n" + "=" * 60)
        print(f"Fixed {fixed_count} gateway configs.")
        
        if fixed_count > 0:
            print("\nPayment gateways should now appear in the checkout page.")
            print("Refresh the page to see the changes.")


async def verify_gateway_data():
    """Verify that gateway data is correct after fix."""
    
    async with async_engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT provider, is_enabled, 
                       supported_currencies,
                       'USD' = ANY(SELECT jsonb_array_elements_text(supported_currencies)) as supports_usd
                FROM payment_gateway_configs
                WHERE is_enabled = true
            """)
        )
        rows = result.fetchall()
        
        print("\nEnabled gateways that support USD:")
        print("-" * 40)
        
        if not rows:
            print("No enabled gateways found!")
            print("\nTo enable a gateway, you can:")
            print("1. Use the admin panel")
            print("2. Or run SQL: UPDATE payment_gateway_configs SET is_enabled = true WHERE provider = 'stripe';")
        else:
            for row in rows:
                provider, is_enabled, currencies, supports_usd = row
                print(f"  {provider}: enabled={is_enabled}, supports_usd={supports_usd}")
                print(f"    currencies: {currencies}")


if __name__ == "__main__":
    print("=" * 60)
    print("Payment Gateway JSON Data Fixer")
    print("=" * 60)
    
    asyncio.run(fix_gateway_json_data())
    asyncio.run(verify_gateway_data())
