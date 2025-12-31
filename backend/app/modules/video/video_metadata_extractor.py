"""Video metadata extraction service.

Uses ffprobe to extract video metadata and ffmpeg to generate thumbnails.
Requirements: 1.1
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VideoFileMetadata:
    """Video file metadata extracted from ffprobe."""
    duration: int  # seconds
    resolution: str  # e.g., "1920x1080"
    width: int
    height: int
    frame_rate: float  # e.g., 30.0, 60.0
    bitrate: int  # kbps
    codec: str  # e.g., "h264", "h265"
    format: str  # e.g., "mp4", "mov"
    file_size: int  # bytes


class VideoMetadataExtractor:
    """Extract metadata from video files using ffprobe and ffmpeg."""

    def __init__(
        self,
        ffprobe_path: str = "ffprobe",
        ffmpeg_path: str = "ffmpeg"
    ):
        """Initialize metadata extractor.
        
        Args:
            ffprobe_path: Path to ffprobe executable
            ffmpeg_path: Path to ffmpeg executable
        """
        self.ffprobe_path = ffprobe_path
        self.ffmpeg_path = ffmpeg_path

    async def extract_metadata(
        self,
        file_path: str
    ) -> VideoFileMetadata:
        """Extract metadata from video file using ffprobe.
        
        Args:
            file_path: Path to video file
            
        Returns:
            VideoFileMetadata: Extracted metadata
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If ffprobe fails or returns invalid data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Build ffprobe command
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path)
        ]

        try:
            # Run ffprobe using subprocess.run (more reliable on Windows)
            # Run in thread pool to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            def run_ffprobe():
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                return result
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_ffprobe)

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise RuntimeError(f"ffprobe failed: {error_msg}")

            # Parse JSON output
            data = json.loads(result.stdout)
            
            # Extract format info
            format_info = data.get("format", {})
            file_size = int(format_info.get("size", 0))
            duration = float(format_info.get("duration", 0))
            bitrate = int(format_info.get("bit_rate", 0)) // 1000  # Convert to kbps
            format_name = format_info.get("format_name", "").split(",")[0]

            # Find video stream
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                raise RuntimeError("No video stream found in file")

            # Extract video stream info
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            codec = video_stream.get("codec_name", "unknown")
            
            # Calculate frame rate
            fps_str = video_stream.get("r_frame_rate", "0/1")
            try:
                num, den = map(int, fps_str.split("/"))
                frame_rate = num / den if den != 0 else 0.0
            except (ValueError, ZeroDivisionError):
                frame_rate = 0.0

            resolution = f"{width}x{height}"

            return VideoFileMetadata(
                duration=int(duration),
                resolution=resolution,
                width=width,
                height=height,
                frame_rate=round(frame_rate, 2),
                bitrate=bitrate,
                codec=codec,
                format=format_name,
                file_size=file_size
            )

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse ffprobe output: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract metadata: {e}")

    async def generate_thumbnail(
        self,
        file_path: str,
        output_path: str,
        timestamp: int = 5,
        width: int = 1280,
        height: int = 720
    ) -> str:
        """Generate thumbnail from video using ffmpeg.
        
        Args:
            file_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Timestamp in seconds to extract frame (default: 5)
            width: Thumbnail width (default: 1280)
            height: Thumbnail height (default: 720)
            
        Returns:
            str: Path to generated thumbnail
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If ffmpeg fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Create output directory if needed
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Build ffmpeg command
        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),  # Seek to timestamp
            "-i", str(path),  # Input file
            "-vframes", "1",  # Extract 1 frame
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",  # Scale and pad
            "-q:v", "2",  # Quality (2 is high quality)
            "-y",  # Overwrite output file
            str(output)
        ]

        try:
            # Run ffmpeg using subprocess.run (more reliable on Windows)
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            def run_ffmpeg():
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                return result
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_ffmpeg)

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise RuntimeError(f"ffmpeg failed: {error_msg}")

            if not output.exists():
                raise RuntimeError("Thumbnail file was not created")

            return str(output)

        except Exception as e:
            raise RuntimeError(f"Failed to generate thumbnail: {e}")

    def extract_metadata_sync(self, file_path: str) -> VideoFileMetadata:
        """Synchronous version of extract_metadata.
        
        Args:
            file_path: Path to video file
            
        Returns:
            VideoFileMetadata: Extracted metadata
        """
        return asyncio.run(self.extract_metadata(file_path))

    def generate_thumbnail_sync(
        self,
        file_path: str,
        output_path: str,
        timestamp: int = 5,
        width: int = 1280,
        height: int = 720
    ) -> str:
        """Synchronous version of generate_thumbnail.
        
        Args:
            file_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Timestamp in seconds
            width: Thumbnail width
            height: Thumbnail height
            
        Returns:
            str: Path to generated thumbnail
        """
        return asyncio.run(
            self.generate_thumbnail(file_path, output_path, timestamp, width, height)
        )


# Global metadata extractor instance
video_metadata_extractor = VideoMetadataExtractor()
