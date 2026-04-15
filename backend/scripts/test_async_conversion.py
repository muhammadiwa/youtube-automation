"""Test async video conversion."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.video.video_converter import VideoConverter


async def test_async_conversion():
    """Test async conversion."""
    
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'temp')
    input_file = os.path.join(temp_dir, 'test_source.mp4')
    output_file = os.path.join(temp_dir, 'test_converted.mp4')
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        print("Run: ffmpeg -f lavfi -i testsrc=duration=5:size=640x480:rate=30 -f lavfi -i sine=frequency=1000:duration=5 -c:v libx264 -c:a aac -y storage/temp/test_source.mp4")
        return
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Input size: {os.path.getsize(input_file) / 1024:.2f} KB")
    
    print("\nStarting async conversion...")
    
    success, output_path, error = await VideoConverter.convert_to_mp4(
        input_path=input_file,
        output_path=output_file,
        preset='fast',
        crf=23,
        remove_input=False
    )
    
    print(f"\nResult:")
    print(f"  Success: {success}")
    print(f"  Output path: {output_path}")
    print(f"  Error: {error}")
    
    if success and output_path and os.path.exists(output_path):
        print(f"  Output size: {os.path.getsize(output_path) / 1024:.2f} KB")
        print("\n✅ Async conversion works!")
    else:
        print("\n❌ Async conversion failed!")


if __name__ == "__main__":
    asyncio.run(test_async_conversion())
