"""Convert MOV videos to MP4 for browser compatibility.

This script finds all videos with MOV format and converts them to MP4 H.264.
"""

import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.video.models import Video
from app.core.storage import get_storage, is_cloud_storage


async def convert_to_mp4(input_path: str, output_path: str) -> bool:
    """Convert video to MP4 H.264 format."""
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',  # H.264 video codec
        '-c:a', 'aac',      # AAC audio codec
        '-movflags', '+faststart',  # Enable streaming
        '-preset', 'medium',  # Balance speed vs quality
        '-crf', '23',  # Quality (18-28, lower = better)
        '-y',  # Overwrite output
        output_path
    ]
    
    try:
        print(f"   Converting: {Path(input_path).name} → {Path(output_path).name}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ Conversion successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Conversion failed: {e.stderr}")
        return False


async def convert_videos():
    """Convert all MOV videos to MP4."""
    
    async with async_session_maker() as session:
        print("=" * 60)
        print("CONVERT MOV TO MP4")
        print("=" * 60)
        
        # Find all videos with MOV format
        result = await session.execute(
            select(Video).where(
                Video.format == 'mov',
                Video.deleted_at.is_(None),
                Video.file_path.isnot(None)
            )
        )
        videos = result.scalars().all()
        
        if not videos:
            print("\n✅ No MOV videos found")
            return
        
        print(f"\n📹 Found {len(videos)} MOV video(s) to convert")
        
        storage = get_storage()
        converted_count = 0
        failed_count = 0
        
        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] Processing: {video.title}")
            print(f"   Video ID: {video.id}")
            print(f"   Format: {video.format}")
            print(f"   File path: {video.file_path}")
            
            try:
                # Download from storage to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mov') as tmp_input:
                    input_path = tmp_input.name
                
                print(f"   📥 Downloading from storage...")
                if is_cloud_storage():
                    success = storage.download(video.file_path, input_path)
                    if not success:
                        print(f"   ❌ Failed to download from storage")
                        failed_count += 1
                        continue
                else:
                    # Local storage
                    from app.core.config import settings
                    local_path = video.file_path
                    if not os.path.isabs(local_path):
                        local_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
                        local_path = os.path.join(local_storage_path, local_path)
                    
                    if not os.path.exists(local_path):
                        print(f"   ❌ File not found: {local_path}")
                        failed_count += 1
                        continue
                    
                    import shutil
                    shutil.copy2(local_path, input_path)
                
                # Convert to MP4
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_output:
                    output_path = tmp_output.name
                
                success = await convert_to_mp4(input_path, output_path)
                
                if not success:
                    failed_count += 1
                    os.unlink(input_path)
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                    continue
                
                # Upload converted file back to storage
                print(f"   📤 Uploading to storage...")
                
                # Generate new file path with .mp4 extension
                new_file_path = str(Path(video.file_path).with_suffix('.mp4'))
                
                if is_cloud_storage():
                    result = storage.upload(
                        file_path=output_path,
                        key=new_file_path,
                        content_type='video/mp4'
                    )
                    if not result.success:
                        print(f"   ❌ Failed to upload: {result.error_message}")
                        failed_count += 1
                        os.unlink(input_path)
                        os.unlink(output_path)
                        continue
                else:
                    # Local storage
                    from app.core.config import settings
                    local_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
                    dest_path = os.path.join(local_storage_path, new_file_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    import shutil
                    shutil.copy2(output_path, dest_path)
                
                # Update video record
                video.file_path = new_file_path
                video.format = 'mp4'
                video.file_size = os.path.getsize(output_path)
                
                await session.commit()
                
                # Delete old file from storage
                if video.file_path != new_file_path:
                    print(f"   🗑️  Deleting old file...")
                    storage.delete(video.file_path)
                
                # Cleanup temp files
                os.unlink(input_path)
                os.unlink(output_path)
                
                converted_count += 1
                print(f"   ✅ Conversion complete!")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed_count += 1
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("CONVERSION SUMMARY")
        print("=" * 60)
        print(f"Total videos: {len(videos)}")
        print(f"✅ Converted: {converted_count}")
        print(f"❌ Failed: {failed_count}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(convert_videos())
