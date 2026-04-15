"""Video Converter Module.

Converts videos to browser-compatible formats (MP4 H.264).
Requirements: 1.1 (Video Library Management)
"""

import subprocess
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Temp directory for conversion - relative to backend folder
TEMP_DIR = Path(__file__).parent.parent.parent.parent / "storage" / "temp"


def get_temp_dir() -> Path:
    """Get temp directory path, creating it if it doesn't exist."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_DIR


class VideoConverter:
    """Video converter for browser compatibility."""
    
    # Formats that need conversion
    NEEDS_CONVERSION = ['mov', 'avi', 'mkv', 'wmv', 'flv']
    
    # Browser-compatible formats (no conversion needed)
    COMPATIBLE_FORMATS = ['mp4', 'webm', 'ogg']
    
    @staticmethod
    def needs_conversion(format_name: str) -> bool:
        """Check if video format needs conversion.
        
        Args:
            format_name: Video format (e.g., 'mov', 'mp4', 'mov,mp4,m4a')
                        Can be comma-separated list from ffprobe
            
        Returns:
            bool: True if conversion needed
        """
        if not format_name:
            return False
            
        # ffprobe can return comma-separated formats like "mov,mp4,m4a,3gp,3g2,mj2"
        # Check if ANY of the formats need conversion
        formats = [f.strip().lower() for f in format_name.split(',')]
        
        for fmt in formats:
            if fmt in VideoConverter.NEEDS_CONVERSION:
                return True
        
        # Also check if none of the formats are browser-compatible
        has_compatible = any(fmt in VideoConverter.COMPATIBLE_FORMATS for fmt in formats)
        if not has_compatible and formats:
            # If no compatible format found, needs conversion
            return True
            
        return False
    
    @staticmethod
    async def convert_to_mp4(
        input_path: str,
        output_path: Optional[str] = None,
        preset: str = 'medium',
        crf: int = 23,
        remove_input: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Convert video to MP4 H.264 format.
        
        Args:
            input_path: Path to input video file
            output_path: Path for output MP4 file (optional, auto-generated if None)
            preset: FFmpeg preset (ultrafast, fast, medium, slow, veryslow)
            crf: Constant Rate Factor for quality (18-28, lower = better quality)
            remove_input: Whether to remove input file after successful conversion
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
                (success, output_path, error_message)
        """
        import asyncio
        import concurrent.futures
        
        try:
            # Generate output path if not provided
            if output_path is None:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.mp4'))
            
            logger.info(f"Converting video: {input_path} → {output_path}")
            logger.info(f"Settings: preset={preset}, crf={crf}")
            
            # FFmpeg command for conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',  # H.264 video codec
                '-c:a', 'aac',      # AAC audio codec
                '-movflags', '+faststart',  # Enable streaming (moov atom at start)
                '-preset', preset,  # Encoding speed vs compression
                '-crf', str(crf),   # Quality level
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Run FFmpeg in thread pool to avoid blocking event loop
            def run_ffmpeg():
                return subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=3600,  # 1 hour timeout
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_ffmpeg)
            
            # Verify output file exists
            if not os.path.exists(output_path):
                error_msg = "Output file not created"
                logger.error(error_msg)
                return False, None, error_msg
            
            # Get output file size
            output_size = os.path.getsize(output_path)
            input_size = os.path.getsize(input_path)
            
            logger.info(f"Conversion successful!")
            logger.info(f"Input size: {input_size / 1024 / 1024:.2f} MB")
            logger.info(f"Output size: {output_size / 1024 / 1024:.2f} MB")
            logger.info(f"Compression: {(1 - output_size / input_size) * 100:.1f}%")
            
            # Remove input file if requested
            if remove_input:
                try:
                    os.remove(input_path)
                    logger.info(f"Removed input file: {input_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove input file: {e}")
            
            return True, output_path, None
            
        except subprocess.TimeoutExpired:
            error_msg = "Conversion timeout (exceeded 1 hour)"
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg error: {e.stderr}"
            logger.error(f"Conversion failed: {error_msg}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Conversion failed: {error_msg}")
            return False, None, error_msg
    
    @staticmethod
    async def convert_with_temp_output(
        input_path: str,
        preset: str = 'medium',
        crf: int = 23
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Convert video to MP4 using temporary output file.
        
        Useful when you want to verify conversion before replacing original.
        Output is saved to storage/temp folder.
        
        Args:
            input_path: Path to input video file
            preset: FFmpeg preset
            crf: Quality level
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
                (success, temp_output_path, error_message)
        """
        # Create temp file in storage/temp folder
        temp_dir = get_temp_dir()
        temp_output_path = str(temp_dir / f"converted_{uuid.uuid4().hex}.mp4")
        
        success, output_path, error = await VideoConverter.convert_to_mp4(
            input_path=input_path,
            output_path=temp_output_path,
            preset=preset,
            crf=crf,
            remove_input=False
        )
        
        if not success:
            # Clean up temp file on failure
            try:
                os.remove(temp_output_path)
            except:
                pass
        
        return success, output_path, error
    
    @staticmethod
    def get_recommended_settings(file_size_mb: float) -> dict:
        """Get recommended conversion settings based on file size.
        
        Args:
            file_size_mb: Input file size in MB
            
        Returns:
            dict: Recommended settings (preset, crf)
        """
        if file_size_mb < 50:
            # Small files: prioritize quality
            return {'preset': 'slow', 'crf': 20}
        elif file_size_mb < 200:
            # Medium files: balance
            return {'preset': 'medium', 'crf': 23}
        else:
            # Large files: prioritize speed
            return {'preset': 'fast', 'crf': 25}


# Convenience function
async def convert_video_to_mp4(
    input_path: str,
    output_path: Optional[str] = None,
    **kwargs
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Convert video to MP4 format.
    
    Convenience wrapper around VideoConverter.convert_to_mp4().
    
    Args:
        input_path: Path to input video
        output_path: Path for output (optional)
        **kwargs: Additional arguments for conversion
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: 
            (success, output_path, error_message)
    """
    return await VideoConverter.convert_to_mp4(input_path, output_path, **kwargs)
