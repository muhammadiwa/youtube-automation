"""Check video file sizes in database."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.video.models import Video

async def check():
    async with async_session_maker() as session:
        result = await session.execute(select(Video))
        videos = result.scalars().all()
        
        print("Videos with file_size:")
        total_bytes = 0
        for v in videos:
            size_mb = (v.file_size / (1024*1024)) if v.file_size else 0
            total_bytes += v.file_size or 0
            print(f"  - {v.title[:40]}... | file_size: {v.file_size} bytes ({size_mb:.2f} MB) | path: {v.file_path}")
        
        total_gb = total_bytes / (1024*1024*1024)
        print(f"\nTotal storage: {total_bytes} bytes = {total_gb:.4f} GB")

if __name__ == "__main__":
    asyncio.run(check())
