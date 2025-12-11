"""Check notification logs in database.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.check_notification_logs
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import engine


async def check_logs():
    """Check notification logs."""
    
    print("\n" + "=" * 60)
    print("Recent Notification Logs")
    print("=" * 60)
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT id, user_id, event_type, title, channel, status, created_at
                FROM notification_logs
                ORDER BY created_at DESC
                LIMIT 10
            """)
        )
        rows = result.fetchall()
        
        if not rows:
            print("\nNo notification logs found.")
            return
        
        print(f"\nFound {len(rows)} recent notifications:\n")
        
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"  User: {row[1]}")
            print(f"  Event: {row[2]}")
            print(f"  Title: {row[3]}")
            print(f"  Channel: {row[4]}")
            print(f"  Status: {row[5]}")
            print(f"  Created: {row[6]}")
            print()


if __name__ == "__main__":
    asyncio.run(check_logs())
