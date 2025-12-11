"""Check gateway config timestamps.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.check_gateway_timestamps
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine


async def check():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT provider, created_at, updated_at FROM payment_gateway_configs ORDER BY provider")
        )
        rows = result.fetchall()
        
        print("\nGateway Config Timestamps:")
        for row in rows:
            print(f"  {row[0]}: created={row[1]}, updated={row[2]}")


if __name__ == "__main__":
    asyncio.run(check())
