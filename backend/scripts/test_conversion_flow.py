"""Test video conversion flow."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.video.video_converter import VideoConverter
from app.modules.video.video_metadata_extractor import video_metadata_extractor


async def test_conversion():
    """Test the conversion detection and process."""
    
    # Test 1: Check needs_conversion logic
    print("=" * 50)
    print("TEST 1: needs_conversion() logic")
    print("=" * 50)
    
    test_formats = [
        'mov',
        'mp4',
        'mov,mp4,m4a,3gp,3g2,mj2',  # Common ffprobe output for MOV
        'mp4,mov',
        'webm',
        'avi',
        'quicktime',
    ]
    
    for fmt in test_formats:
        result = VideoConverter.needs_conversion(fmt)
        print(f"  '{fmt}' -> needs_conversion: {result}")
    
    # Test 2: Check if ffmpeg is available
    print("\n" + "=" * 50)
    print("TEST 2: FFmpeg availability")
    print("=" * 50)
    
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        print(f"  FFmpeg available: {result.returncode == 0}")
        if result.returncode == 0:
            print(f"  Version: {result.stdout.split(chr(10))[0]}")
    except Exception as e:
        print(f"  FFmpeg NOT available: {e}")
    
    # Test 3: Test actual conversion with a sample file (if exists)
    print("\n" + "=" * 50)
    print("TEST 3: Sample conversion test")
    print("=" * 50)
    
    # Check storage/temp for any MOV files
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'temp')
    print(f"  Temp directory: {temp_dir}")
    print(f"  Exists: {os.path.exists(temp_dir)}")
    
    if os.path.exists(temp_dir):
        files = os.listdir(temp_dir)
        print(f"  Files in temp: {files}")
    
    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_conversion())
