"""Unit tests for VideoMetadataExtractor.

Tests video metadata extraction with mocked ffprobe/ffmpeg.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from app.modules.video.video_metadata_extractor import (
    VideoMetadataExtractor,
    VideoFileMetadata
)


@pytest.fixture
def metadata_extractor():
    """Create VideoMetadataExtractor instance."""
    return VideoMetadataExtractor()


@pytest.fixture
def mock_ffprobe_output():
    """Mock ffprobe JSON output."""
    return {
        "format": {
            "size": "104857600",  # 100MB
            "duration": "120.5",
            "bit_rate": "7000000",  # 7 Mbps
            "format_name": "mp4,m4a,3gp"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "codec_name": "aac"
            }
        ]
    }


@pytest.mark.asyncio
class TestVideoMetadataExtractor:
    """Test VideoMetadataExtractor methods."""

    async def test_extract_metadata_success(
        self,
        metadata_extractor,
        mock_ffprobe_output,
        tmp_path
    ):
        """Test successful metadata extraction."""
        # Create temporary video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(
                json.dumps(mock_ffprobe_output).encode(),
                b""
            )
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            metadata = await metadata_extractor.extract_metadata(str(video_file))

            # Assertions
            assert metadata.duration == 120
            assert metadata.resolution == "1920x1080"
            assert metadata.width == 1920
            assert metadata.height == 1080
            assert metadata.frame_rate == 30.0
            assert metadata.bitrate == 7000  # kbps
            assert metadata.codec == "h264"
            assert metadata.format == "mp4"
            assert metadata.file_size == 104857600

    async def test_extract_metadata_file_not_found(self, metadata_extractor):
        """Test metadata extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await metadata_extractor.extract_metadata("/nonexistent/file.mp4")

    async def test_extract_metadata_ffprobe_failure(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test metadata extraction when ffprobe fails."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        # Mock failed subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"ffprobe error")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await metadata_extractor.extract_metadata(str(video_file))
            
            assert "ffprobe failed" in str(exc_info.value)

    async def test_extract_metadata_invalid_json(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test metadata extraction with invalid JSON output."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        # Mock subprocess with invalid JSON
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(b"invalid json", b"")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await metadata_extractor.extract_metadata(str(video_file))
            
            assert "Failed to parse ffprobe output" in str(exc_info.value)

    async def test_extract_metadata_no_video_stream(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test metadata extraction with no video stream."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        # Mock output with no video stream
        output = {
            "format": {"size": "1000", "duration": "10", "bit_rate": "1000"},
            "streams": [{"codec_type": "audio", "codec_name": "aac"}]
        }

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(json.dumps(output).encode(), b"")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await metadata_extractor.extract_metadata(str(video_file))
            
            assert "No video stream found" in str(exc_info.value)

    async def test_extract_metadata_variable_frame_rate(
        self,
        metadata_extractor,
        mock_ffprobe_output,
        tmp_path
    ):
        """Test metadata extraction with variable frame rate."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        # Modify frame rate to 59.94 fps (60000/1001)
        mock_ffprobe_output["streams"][0]["r_frame_rate"] = "60000/1001"

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(json.dumps(mock_ffprobe_output).encode(), b"")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            metadata = await metadata_extractor.extract_metadata(str(video_file))
            
            # Should be approximately 59.94
            assert 59.9 < metadata.frame_rate < 60.0

    async def test_generate_thumbnail_success(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test successful thumbnail generation."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        output_file = tmp_path / "thumbnail.jpg"

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            # Create the output file to simulate ffmpeg success
            output_file.write_bytes(b"fake thumbnail")
            
            result = await metadata_extractor.generate_thumbnail(
                str(video_file),
                str(output_file)
            )

            assert result == str(output_file)
            assert output_file.exists()

    async def test_generate_thumbnail_file_not_found(self, metadata_extractor):
        """Test thumbnail generation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await metadata_extractor.generate_thumbnail(
                "/nonexistent/file.mp4",
                "/tmp/thumb.jpg"
            )

    async def test_generate_thumbnail_ffmpeg_failure(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test thumbnail generation when ffmpeg fails."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        output_file = tmp_path / "thumbnail.jpg"

        # Mock failed subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"ffmpeg error")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await metadata_extractor.generate_thumbnail(
                    str(video_file),
                    str(output_file)
                )
            
            assert "ffmpeg failed" in str(exc_info.value)

    async def test_generate_thumbnail_custom_params(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test thumbnail generation with custom parameters."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        output_file = tmp_path / "thumbnail.jpg"

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ) as mock_exec:
            output_file.write_bytes(b"fake thumbnail")
            
            await metadata_extractor.generate_thumbnail(
                str(video_file),
                str(output_file),
                timestamp=10,
                width=640,
                height=360
            )

            # Verify ffmpeg was called with correct parameters
            call_args = mock_exec.call_args[0]
            assert "-ss" in call_args
            assert "10" in call_args
            assert "scale=640:360" in str(call_args)

    def test_extract_metadata_sync(
        self,
        metadata_extractor,
        mock_ffprobe_output,
        tmp_path
    ):
        """Test synchronous metadata extraction."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(json.dumps(mock_ffprobe_output).encode(), b"")
        )

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            metadata = metadata_extractor.extract_metadata_sync(str(video_file))
            
            assert isinstance(metadata, VideoFileMetadata)
            assert metadata.resolution == "1920x1080"

    def test_generate_thumbnail_sync(
        self,
        metadata_extractor,
        tmp_path
    ):
        """Test synchronous thumbnail generation."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        output_file = tmp_path / "thumbnail.jpg"

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            'asyncio.create_subprocess_exec',
            return_value=mock_process
        ):
            output_file.write_bytes(b"fake thumbnail")
            
            result = metadata_extractor.generate_thumbnail_sync(
                str(video_file),
                str(output_file)
            )

            assert result == str(output_file)
