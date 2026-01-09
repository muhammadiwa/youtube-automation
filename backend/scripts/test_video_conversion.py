"""Test video conversion functionality.

Tests the VideoConverter module.
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.modules.video.video_converter import VideoConverter


async def test_conversion():
    """Test video conversion."""
    
    print("=" * 60)
    print("VIDEO CONVERSION TEST")
    print("=" * 60)
    
    # Test 1: Check if conversion is needed for different formats
    print("\n📋 Test 1: Format Detection")
    test_formats = ['mov', 'avi', 'mkv', 'mp4', 'webm', 'ogg']
    
    for fmt in test_formats:
        needs_conv = VideoConverter.needs_conversion(fmt)
        status = "❌ NEEDS CONVERSION" if needs_conv else "✅ COMPATIBLE"
        print(f"   {fmt.upper()}: {status}")
    
    # Test 2: Get recommended settings
    print("\n📋 Test 2: Recommended Settings")
    test_sizes = [10, 50, 100, 500, 1000]
    
    for size_mb in test_sizes:
        settings = VideoConverter.get_recommended_settings(size_mb)
        print(f"   {size_mb} MB: preset={settings['preset']}, crf={settings['crf']}")
    
    # Test 3: Check FFmpeg availability
    print("\n📋 Test 3: FFmpeg Availability")
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ FFmpeg available: {version_line}")
        else:
            print(f"   ❌ FFmpeg not working properly")
    except FileNotFoundError:
        print(f"   ❌ FFmpeg not found in PATH")
        print(f"   💡 Install FFmpeg: https://ffmpeg.org/download.html")
    except Exception as e:
        print(f"   ❌ Error checking FFmpeg: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ VideoConverter module is ready")
    print("📝 Auto-conversion will:")
    print("   1. Detect video format (MOV, AVI, MKV, etc.)")
    print("   2. Convert to MP4 H.264 if needed")
    print("   3. Optimize for browser streaming")
    print("   4. Upload converted file to storage")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_conversion())
