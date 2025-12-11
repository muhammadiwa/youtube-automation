"""Run billing background tasks manually.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.run_billing_tasks
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import async_session_maker
from app.modules.billing.tasks import run_billing_tasks


async def main():
    """Run billing tasks."""
    print("\n" + "=" * 60)
    print("Running Billing Background Tasks")
    print("=" * 60)
    
    async with async_session_maker() as session:
        summary = await run_billing_tasks(session)
        
        print(f"\nResults:")
        print(f"  Expiring notifications sent: {summary['expiring_notifications_sent']}")
        print(f"  Subscriptions expired: {summary['subscriptions_expired']}")
        print(f"  Run at: {summary['run_at']}")


if __name__ == "__main__":
    asyncio.run(main())
