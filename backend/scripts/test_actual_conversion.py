"""Test actual video conversion with a real file."""

import asyncio
import os
import sys
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.video.video_converter import VideoConverter
from app.modules.video.video_metadata_extractor import video_metadata_extractor


async def test_actual_conversion():
    """Test conversion with a real MOV file if available."""
    
    # Check for any video files in storage/videos
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'videos')
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'temp')
    
    print(f"Storage dir: {storage_dir}")
    print(f"Temp dir: {temp_dir}")
    
    # Create temp dir if not exists
    os.makedirs(temp_dir, exist_ok=True)
    
    # Find a video file to test with
    test_file = None
    for root, dirs, files in os.walk(storage_dir):
        for f in files:
            if f.endswith(('.mov', '.MOV', '.mp4', '.MP4')):
                test_file = os.path.join(root, f)
                print(f"Found video file: {test_file}")
                break
        if test_file:
            break
    
    if not test_file:
        print("No video files found in storage/videos")
        print("Please upload a video first or place a test video in storage/videos")
        return
    
    # Extract metadata
    print("\n" + "=" * 50)
    print("Extracting metadata...")
    print("=" * 50)
    
    try:
        metadata = await video_metadata_extractor.extract_metadata(test_file)
        print(f"  Format: {metadata.format}")
        print(f"  Duration: {metadata.duration}s")
        print(f"  Resolution: {metadata.resolution}")
        print(f"  Codec: {metadata.codec}")
        print(f"  File size: {metadata.file_size / 1024 / 1024:.2f} MB")
        
        # Check if needs conversion
        needs_conversion = VideoConverter.needs_conversion(metadata.format)
        print(f"\n  Needs conversion: {needs_conversion}")
        
    except Exception as e:
        print(f"  Error extracting metadata: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test conversion
    if needs_conversion or input("\nDo you want to test conversion anyway? (y/n): ").lower() == 'y':
        print("\n" + "=" * 50)
        print("Testing conversion...")
        print("=" * 50)
        
        # Copy file to temp for testing
        test_input = os.path.join(temp_dir, f"test_input{os.path.splitext(test_file)[1]}")
        test_output = os.path.join(temp_dir, "test_output.mp4")
        
        print(f"  Copying {test_file} to {test_input}...")
        shutil.copy2(test_file, test_input)
        
        print(f"  Converting to {test_output}...")
        
        success, output_path, error = await VideoConverter.convert_to_mp4(
            input_path=test_input,
            output_path=test_output,
            preset='fast',  # Use fast for testing
            crf=23,
            remove_input=False
        )
        
        print(f"\n  Success: {success}")
        print(f"  Output path: {output_path}")
        print(f"  Error: {error}")
        
        if success and output_path and os.path.exists(output_path):
            output_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"  Output file size: {output_size:.2f} MB")
            
            # Verify output is valid MP4
            print("\n  Verifying output...")
            try:
                output_metadata = await video_metadata_extractor.extract_metadata(output_path)
                print(f"  Output format: {output_metadata.format}")
                print(f"  Output codec: {output_metadata.codec}")
                print(f"  Output duration: {output_metadata.duration}s")
            except Exception as e:
                print(f"  Error verifying output: {e}")
        
        # Cleanup
        print("\n  Cleaning up test files...")
        if os.path.exists(test_input):
            os.remove(test_input)
        # Keep output for inspection
        print(f"  Output file kept at: {test_output}")
    
    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_actual_conversion())
