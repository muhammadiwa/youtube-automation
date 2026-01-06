"""Update video file sizes from actual files on disk.

Run with: python -m scripts.update_video_sizes
"""
import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.config import settings
from app.modules.video.models import Video

async def update_video_sizes():
    """Update file_size for videos that have file_path but no file_size."""
    async with async_session_maker() as session:
        # Get videos with file_path but no file_size
        result = await session.execute(
            select(Video).where(
                Video.file_path.isnot(None),
                Video.file_size.is_(None)
            )
        )
        videos = result.scalars().all()
        
        print(f"Found {len(videos)} videos without file_size")
        
        updated = 0
        for video in videos:
            # Try to find the file
            file_path = video.file_path
            
            # Check various possible locations
            possible_paths = [
                file_path,  # Absolute path
                os.path.join(settings.STORAGE_PATH, file_path),  # Relative to storage
                os.path.join("storage", file_path),  # Local storage folder
            ]
            
            for path in possible_paths:
                if path and os.path.exists(path):
                    file_size = os.path.getsize(path)
                    video.file_size = file_size
                    updated += 1
                    print(f"  Updated: {video.title[:40]}... -> {file_size} bytes ({file_size/(1024*1024):.2f} MB)")
                    break
            else:
                print(f"  Not found: {video.title[:40]}... (path: {file_path})")
        
        await session.commit()
        print(f"\n✅ Updated {updated} videos with file sizes")
        
        # Show summary
        result = await session.execute(select(Video))
        all_videos = result.scalars().all()
        
        total_with_size = sum(1 for v in all_videos if v.file_size)
        total_bytes = sum(v.file_size or 0 for v in all_videos)
        
        print(f"\nSummary:")
        print(f"  Total videos: {len(all_videos)}")
        print(f"  Videos with file_size: {total_with_size}")
        print(f"  Total storage: {total_bytes/(1024*1024*1024):.4f} GB")

if __name__ == "__main__":
    asyncio.run(update_video_sizes())
