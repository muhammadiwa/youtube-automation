"""Check live events status."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.stream.models import LiveEvent, LiveEventStatus

async def check():
    async with async_session_maker() as session:
        result = await session.execute(select(LiveEvent))
        events = result.scalars().all()
        print("All LiveEvents:")
        for e in events:
            print(f"  - {e.title[:30]}... | status: {e.status} | is_live: {e.status == LiveEventStatus.LIVE.value}")
        print(f"\nLiveEventStatus.LIVE.value = '{LiveEventStatus.LIVE.value}'")

if __name__ == "__main__":
    asyncio.run(check())
