"""Test video stream endpoint.

Check if video exists and has file_path.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.video.models import Video
import uuid


async def test_video_stream():
    """Test video stream endpoint."""
    
    # Video ID from the error
    video_id_str = "cdfbd741-722e-49ee-9f0d-c4e2097d506f"
    
    try:
        video_id = uuid.UUID(video_id_str)
    except ValueError:
        print(f"❌ Invalid video ID: {video_id_str}")
        return
    
    async with async_session_maker() as session:
        print("=" * 60)
        print("VIDEO STREAM ENDPOINT TEST")
        print("=" * 60)
        print(f"\n🔍 Checking video: {video_id}")
        
        # Get video
        result = await session.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            print(f"\n❌ Video not found in database")
            print(f"   Video ID: {video_id}")
            print(f"\n💡 Possible reasons:")
            print(f"   1. Video was deleted")
            print(f"   2. Wrong video ID")
            print(f"   3. Video belongs to different user")
            return
        
        print(f"\n✅ Video found!")
        print(f"   Title: {video.title}")
        print(f"   User ID: {video.user_id}")
        print(f"   Status: {video.status}")
        print(f"   Created: {video.created_at}")
        
        # Check if soft deleted
        if video.deleted_at:
            print(f"\n⚠️  Video is SOFT DELETED")
            print(f"   Deleted at: {video.deleted_at}")
            print(f"   Status: {video.status}")
            print(f"\n💡 Soft deleted videos are excluded from queries")
            return
        
        # Check file_path
        if not video.file_path:
            print(f"\n❌ Video has NO file_path")
            print(f"   This video may have been:")
            print(f"   1. Imported from YouTube (no local file)")
            print(f"   2. File was deleted from storage")
            print(f"\n💡 Cannot stream video without file_path")
            return
        
        print(f"\n✅ Video has file_path")
        print(f"   File path: {video.file_path}")
        print(f"   File size: {video.file_size} bytes ({video.file_size / 1024 / 1024:.2f} MB)")
        print(f"   Duration: {video.duration} seconds" if video.duration else "   Duration: Unknown")
        print(f"   Format: {video.format}" if video.format else "   Format: Unknown")
        
        # Check storage
        from app.core.storage import get_storage, is_cloud_storage
        
        storage = get_storage()
        print(f"\n📦 Storage Configuration:")
        print(f"   Backend: {'Cloud (R2/S3)' if is_cloud_storage() else 'Local'}")
        
        if is_cloud_storage():
            # Check if file exists in cloud storage
            try:
                exists = storage.exists(video.file_path)
                if exists:
                    print(f"   ✅ File exists in cloud storage")
                    
                    # Get URL
                    url = storage.get_url(video.file_path, expires_in=3600)
                    print(f"   📎 URL: {url[:100]}...")
                else:
                    print(f"   ❌ File NOT found in cloud storage")
                    print(f"   💡 File may have been deleted or moved")
            except Exception as e:
                print(f"   ⚠️  Cannot check file existence: {e}")
        else:
            # Check local file
            import os
            from app.core.config import settings
            
            file_path = video.file_path
            if not os.path.isabs(file_path):
                local_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
                file_path = os.path.join(local_storage_path, file_path)
            
            if os.path.exists(file_path):
                print(f"   ✅ File exists locally")
                print(f"   📁 Full path: {file_path}")
            else:
                print(f"   ❌ File NOT found locally")
                print(f"   📁 Expected path: {file_path}")
        
        print("\n" + "=" * 60)
        print("ENDPOINT TEST RESULT")
        print("=" * 60)
        
        if video.deleted_at:
            print("❌ FAIL - Video is soft deleted")
        elif not video.file_path:
            print("❌ FAIL - Video has no file_path")
        else:
            print("✅ PASS - Video should be streamable")
            print(f"\n📺 Stream URL:")
            print(f"   GET /api/v1/videos/library/{video_id}/stream?token=YOUR_TOKEN")
        
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_video_stream())
