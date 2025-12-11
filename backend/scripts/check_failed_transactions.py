"""Check failed payment transactions.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.check_failed_transactions
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine


async def check_failed_transactions():
    """Check failed payment transactions."""
    
    print(f"\n{'='*60}")
    print("Checking Failed Payment Transactions")
    print(f"{'='*60}")
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT id, user_id, gateway_provider, amount, currency, 
                       status, error_message, created_at
                FROM payment_transactions 
                WHERE status = 'failed'
                ORDER BY created_at DESC
                LIMIT 10
            """)
        )
        rows = result.fetchall()
        
        if not rows:
            print("\nNo failed transactions found.")
            return
        
        print(f"\nFound {len(rows)} failed transactions:\n")
        
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"  User ID: {row[1]}")
            print(f"  Gateway: {row[2]}")
            print(f"  Amount: {row[3]} {row[4]}")
            print(f"  Status: {row[5]}")
            print(f"  Error: {row[6]}")
            print(f"  Created: {row[7]}")
            print()


if __name__ == "__main__":
    asyncio.run(check_failed_transactions())
