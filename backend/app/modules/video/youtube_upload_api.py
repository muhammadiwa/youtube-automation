"""YouTube Data API client for video upload.

Provides methods for uploading videos to YouTube using resumable upload.
Requirements: 3.1, 3.2, 3.3
"""

import os
import logging
from typing import Optional, Any, BinaryIO
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class YouTubeUploadError(Exception):
    """Exception raised for YouTube upload errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        details: Optional[dict] = None,
        is_retryable: bool = False,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        self.is_retryable = is_retryable
        super().__init__(self.message)


class QuotaExceededError(YouTubeUploadError):
    """Raised when YouTube API quota is exceeded."""

    def __init__(self, message: str = "YouTube API quota exceeded"):
        super().__init__(message, status_code=403, error_type="quotaExceeded", is_retryable=False)


class YouTubeUploadClient:
    """Client for YouTube Data API video upload.

    Implements resumable upload protocol for large video files.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks for resumable upload

    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        """Initialize client with access token.

        Args:
            access_token: OAuth2 access token for YouTube API
            refresh_token: OAuth2 refresh token (optional, for token refresh)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error response from YouTube API.

        Args:
            response: HTTP response object

        Raises:
            YouTubeUploadError: With appropriate error details
        """
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            errors = error.get("errors", [{}])
            first_error = errors[0] if errors else {}

            error_reason = first_error.get("reason", "unknown")
            error_message = error.get("message", response.text)

            # Check for quota exceeded
            if error_reason == "quotaExceeded" or response.status_code == 403:
                raise QuotaExceededError(error_message)

            # Check for retryable errors
            is_retryable = response.status_code in (500, 502, 503, 504) or error_reason in (
                "backendError",
                "rateLimitExceeded",
            )

            raise YouTubeUploadError(
                message=error_message,
                status_code=response.status_code,
                error_type=error_reason,
                details=error_data,
                is_retryable=is_retryable,
            )
        except (ValueError, KeyError):
            raise YouTubeUploadError(
                message=f"YouTube API error: {response.status_code}",
                status_code=response.status_code,
                is_retryable=response.status_code >= 500,
            )

    async def upload_video(
        self,
        file_path: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: str = "22",  # Default: People & Blogs
        privacy_status: str = "private",
        scheduled_publish_at: Optional[datetime] = None,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Upload a video to YouTube using resumable upload.

        Args:
            file_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of video tags
            category_id: YouTube category ID
            privacy_status: public, unlisted, or private
            scheduled_publish_at: Schedule publish time (for private videos)
            progress_callback: Callback function(progress_percent: int)

        Returns:
            dict: YouTube video resource with id, snippet, status

        Raises:
            YouTubeUploadError: If upload fails
            FileNotFoundError: If video file not found
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        file_size = os.path.getsize(file_path)

        # Prepare video metadata
        video_metadata = {
            "snippet": {
                "title": title,
                "description": description or "",
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Add scheduled publish time if provided
        if scheduled_publish_at and privacy_status == "private":
            video_metadata["status"]["publishAt"] = scheduled_publish_at.isoformat() + "Z"

        # Step 1: Initialize resumable upload session
        upload_url = await self._init_resumable_upload(video_metadata, file_size)

        # Step 2: Upload file in chunks
        youtube_video = await self._upload_file_chunks(
            upload_url, file_path, file_size, progress_callback
        )

        return youtube_video

    async def _init_resumable_upload(
        self, video_metadata: dict, file_size: int
    ) -> str:
        """Initialize a resumable upload session.

        Args:
            video_metadata: Video metadata (snippet, status)
            file_size: Size of video file in bytes

        Returns:
            str: Resumable upload URL

        Raises:
            YouTubeUploadError: If initialization fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.UPLOAD_URL,
                params={
                    "uploadType": "resumable",
                    "part": "snippet,status",
                },
                headers={
                    **self.headers,
                    "X-Upload-Content-Length": str(file_size),
                    "X-Upload-Content-Type": "video/*",
                },
                json=video_metadata,
                timeout=60.0,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            upload_url = response.headers.get("Location")
            if not upload_url:
                raise YouTubeUploadError(
                    "Failed to get upload URL from YouTube",
                    status_code=response.status_code,
                )

            return upload_url

    async def _upload_file_chunks(
        self,
        upload_url: str,
        file_path: str,
        file_size: int,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Upload file in chunks using resumable upload.

        Args:
            upload_url: Resumable upload URL
            file_path: Path to video file
            file_size: Total file size
            progress_callback: Progress callback function

        Returns:
            dict: YouTube video resource

        Raises:
            YouTubeUploadError: If upload fails
        """
        uploaded_bytes = 0

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                while uploaded_bytes < file_size:
                    # Read chunk
                    chunk = f.read(self.CHUNK_SIZE)
                    chunk_size = len(chunk)
                    end_byte = uploaded_bytes + chunk_size - 1

                    # Upload chunk
                    response = await client.put(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Length": str(chunk_size),
                            "Content-Range": f"bytes {uploaded_bytes}-{end_byte}/{file_size}",
                        },
                        content=chunk,
                        timeout=300.0,  # 5 minutes per chunk
                    )

                    if response.status_code == 308:
                        # Resume incomplete - continue uploading
                        uploaded_bytes += chunk_size
                        if progress_callback:
                            progress = int((uploaded_bytes / file_size) * 100)
                            progress_callback(progress)
                    elif response.status_code in (200, 201):
                        # Upload complete
                        if progress_callback:
                            progress_callback(100)
                        return response.json()
                    else:
                        self._handle_error_response(response)

        raise YouTubeUploadError("Upload failed: unexpected end of upload")

    async def resume_upload(
        self,
        upload_url: str,
        file_path: str,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Resume an interrupted upload.

        Args:
            upload_url: Resumable upload URL from previous session
            file_path: Path to video file
            progress_callback: Progress callback function

        Returns:
            dict: YouTube video resource

        Raises:
            YouTubeUploadError: If resume fails
        """
        file_size = os.path.getsize(file_path)

        # Check current upload status
        async with httpx.AsyncClient() as client:
            response = await client.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Length": "0",
                    "Content-Range": f"bytes */{file_size}",
                },
                timeout=60.0,
            )

            if response.status_code == 308:
                # Get uploaded range
                range_header = response.headers.get("Range", "")
                if range_header:
                    uploaded_bytes = int(range_header.split("-")[1]) + 1
                else:
                    uploaded_bytes = 0

                # Continue upload from where it left off
                return await self._continue_upload(
                    upload_url, file_path, file_size, uploaded_bytes, progress_callback
                )
            elif response.status_code in (200, 201):
                # Already complete
                return response.json()
            else:
                self._handle_error_response(response)

    async def _continue_upload(
        self,
        upload_url: str,
        file_path: str,
        file_size: int,
        start_byte: int,
        progress_callback: Optional[callable] = None,
    ) -> dict[str, Any]:
        """Continue upload from a specific byte position.

        Args:
            upload_url: Resumable upload URL
            file_path: Path to video file
            file_size: Total file size
            start_byte: Byte position to start from
            progress_callback: Progress callback function

        Returns:
            dict: YouTube video resource
        """
        uploaded_bytes = start_byte

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                f.seek(start_byte)

                while uploaded_bytes < file_size:
                    chunk = f.read(self.CHUNK_SIZE)
                    chunk_size = len(chunk)
                    end_byte = uploaded_bytes + chunk_size - 1

                    response = await client.put(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Length": str(chunk_size),
                            "Content-Range": f"bytes {uploaded_bytes}-{end_byte}/{file_size}",
                        },
                        content=chunk,
                        timeout=300.0,
                    )

                    if response.status_code == 308:
                        uploaded_bytes += chunk_size
                        if progress_callback:
                            progress = int((uploaded_bytes / file_size) * 100)
                            progress_callback(progress)
                    elif response.status_code in (200, 201):
                        if progress_callback:
                            progress_callback(100)
                        return response.json()
                    else:
                        self._handle_error_response(response)

        raise YouTubeUploadError("Upload failed: unexpected end of upload")

    async def get_video_status(self, video_id: str) -> dict[str, Any]:
        """Get video processing status from YouTube.

        Args:
            video_id: YouTube video ID

        Returns:
            dict: Video resource with processing status

        Raises:
            YouTubeUploadError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/videos",
                params={
                    "id": video_id,
                    "part": "status,processingDetails",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            items = data.get("items", [])
            if not items:
                raise YouTubeUploadError(f"Video not found: {video_id}")

            return items[0]

    async def set_thumbnail(
        self, video_id: str, thumbnail_path: str
    ) -> dict[str, Any]:
        """Upload custom thumbnail for a video.

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image (JPEG, PNG, GIF, BMP)

        Returns:
            dict: Thumbnail resource

        Raises:
            YouTubeUploadError: If upload fails
            FileNotFoundError: If thumbnail file not found
        """
        if not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail file not found: {thumbnail_path}")

        # Determine content type
        ext = os.path.splitext(thumbnail_path)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        content_type = content_types.get(ext, "image/jpeg")

        async with httpx.AsyncClient() as client:
            with open(thumbnail_path, "rb") as f:
                response = await client.post(
                    f"{self.BASE_URL}/thumbnails/set",
                    params={"videoId": video_id},
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": content_type,
                    },
                    content=f.read(),
                    timeout=60.0,
                )

            if response.status_code != 200:
                self._handle_error_response(response)

            return response.json()

    async def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update video metadata on YouTube.

        Args:
            video_id: YouTube video ID
            title: New title
            description: New description
            tags: New tags
            category_id: New category ID
            privacy_status: New privacy status

        Returns:
            dict: Updated video resource

        Raises:
            YouTubeUploadError: If update fails
        """
        # First get current video data
        current = await self.get_video_status(video_id)

        # Build update request
        update_data = {
            "id": video_id,
            "snippet": current.get("snippet", {}),
            "status": current.get("status", {}),
        }

        if title is not None:
            update_data["snippet"]["title"] = title
        if description is not None:
            update_data["snippet"]["description"] = description
        if tags is not None:
            update_data["snippet"]["tags"] = tags
        if category_id is not None:
            update_data["snippet"]["categoryId"] = category_id
        if privacy_status is not None:
            update_data["status"]["privacyStatus"] = privacy_status

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/videos",
                params={"part": "snippet,status"},
                headers=self.headers,
                json=update_data,
                timeout=30.0,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            return response.json()

    async def delete_video(self, video_id: str) -> bool:
        """Delete a video from YouTube.

        Args:
            video_id: YouTube video ID

        Returns:
            bool: True if deleted successfully

        Raises:
            YouTubeUploadError: If deletion fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/videos",
                params={"id": video_id},
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                self._handle_error_response(response)

            return True

    async def list_channel_videos(
        self,
        max_results: int = 50,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """List videos from the authenticated user's channel.

        Args:
            max_results: Maximum number of results (1-50)
            page_token: Token for pagination

        Returns:
            dict: Response with items and nextPageToken

        Raises:
            YouTubeUploadError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            # First get the channel's uploads playlist
            channel_response = await client.get(
                f"{self.BASE_URL}/channels",
                params={
                    "part": "contentDetails",
                    "mine": "true",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if channel_response.status_code != 200:
                self._handle_error_response(channel_response)

            channel_data = channel_response.json()
            channels = channel_data.get("items", [])
            if not channels:
                return {"items": [], "nextPageToken": None}

            uploads_playlist_id = (
                channels[0]
                .get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads")
            )

            if not uploads_playlist_id:
                return {"items": [], "nextPageToken": None}

            # Get videos from uploads playlist
            params = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": max_results,
            }
            if page_token:
                params["pageToken"] = page_token

            playlist_response = await client.get(
                f"{self.BASE_URL}/playlistItems",
                params=params,
                headers=self.headers,
                timeout=30.0,
            )

            if playlist_response.status_code != 200:
                self._handle_error_response(playlist_response)

            playlist_data = playlist_response.json()
            video_ids = [
                item.get("snippet", {}).get("resourceId", {}).get("videoId")
                for item in playlist_data.get("items", [])
                if item.get("snippet", {}).get("resourceId", {}).get("videoId")
            ]

            if not video_ids:
                return {
                    "items": [],
                    "nextPageToken": playlist_data.get("nextPageToken"),
                }

            # Get full video details
            videos_response = await client.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,statistics,contentDetails,status",
                    "id": ",".join(video_ids),
                },
                headers=self.headers,
                timeout=30.0,
            )

            if videos_response.status_code != 200:
                self._handle_error_response(videos_response)

            videos_data = videos_response.json()
            return {
                "items": videos_data.get("items", []),
                "nextPageToken": playlist_data.get("nextPageToken"),
            }

    async def get_video_details(self, video_id: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            dict: Video resource with full details, or None if not found

        Raises:
            YouTubeUploadError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,statistics,contentDetails,status",
                    "id": video_id,
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            items = data.get("items", [])
            return items[0] if items else None


# Alias for backward compatibility
YouTubeUploadAPI = YouTubeUploadClient
