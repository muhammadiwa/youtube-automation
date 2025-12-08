"""YouTube Live Streaming API client.

Provides methods for creating and managing YouTube live broadcasts.
Requirements: 5.1, 5.2, 5.3, 5.4
"""

from datetime import datetime
from typing import Optional, Any
import httpx

from app.core.config import settings


class YouTubeAPIError(Exception):
    """Exception raised for YouTube API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class YouTubeLiveStreamingClient:
    """Client for YouTube Live Streaming API.

    Handles broadcast and stream resource creation and management.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, access_token: str):
        """Initialize client with access token.

        Args:
            access_token: OAuth2 access token for YouTube API
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def create_broadcast(
        self,
        title: str,
        description: Optional[str] = None,
        scheduled_start_time: Optional[datetime] = None,
        privacy_status: str = "private",
        latency_mode: str = "normal",
        enable_dvr: bool = True,
        enable_content_encryption: bool = False,
        enable_embed: bool = True,
        record_from_start: bool = True,
        made_for_kids: bool = False,
    ) -> dict[str, Any]:
        """Create a YouTube live broadcast.

        Args:
            title: Broadcast title
            description: Broadcast description
            scheduled_start_time: Scheduled start time (UTC)
            privacy_status: Privacy status (public, unlisted, private)
            latency_mode: Latency preference (normal, low, ultraLow)
            enable_dvr: Enable DVR functionality
            enable_content_encryption: Enable content encryption
            enable_embed: Allow embedding
            record_from_start: Record from start
            made_for_kids: Made for kids content

        Returns:
            dict: Broadcast resource with id and other details

        Raises:
            YouTubeAPIError: If API call fails
        """
        # Map latency mode to YouTube API format
        latency_preference = {
            "normal": "normal",
            "low": "low",
            "ultraLow": "ultraLow",
        }.get(latency_mode, "normal")

        # Build request body
        body = {
            "snippet": {
                "title": title,
                "description": description or "",
                "scheduledStartTime": (
                    scheduled_start_time.isoformat() + "Z"
                    if scheduled_start_time
                    else datetime.utcnow().isoformat() + "Z"
                ),
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": made_for_kids,
            },
            "contentDetails": {
                "enableDvr": enable_dvr,
                "enableContentEncryption": enable_content_encryption,
                "enableEmbed": enable_embed,
                "recordFromStart": record_from_start,
                "latencyPreference": latency_preference,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveBroadcasts",
                params={"part": "snippet,status,contentDetails"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to create broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def create_stream(
        self,
        title: str,
        resolution: str = "1080p",
        frame_rate: str = "30fps",
        ingestion_type: str = "rtmp",
    ) -> dict[str, Any]:
        """Create a YouTube live stream resource.

        Args:
            title: Stream title
            resolution: Video resolution (1080p, 720p, 480p, 360p, 240p)
            frame_rate: Frame rate (30fps, 60fps)
            ingestion_type: Ingestion type (rtmp, dash, webrtc, hls)

        Returns:
            dict: Stream resource with id and ingestion info

        Raises:
            YouTubeAPIError: If API call fails
        """
        body = {
            "snippet": {
                "title": title,
            },
            "cdn": {
                "frameRate": frame_rate,
                "resolution": resolution,
                "ingestionType": ingestion_type,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveStreams",
                params={"part": "snippet,cdn,status"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to create stream: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def bind_broadcast_to_stream(
        self,
        broadcast_id: str,
        stream_id: str,
    ) -> dict[str, Any]:
        """Bind a broadcast to a stream.

        Args:
            broadcast_id: YouTube broadcast ID
            stream_id: YouTube stream ID

        Returns:
            dict: Updated broadcast resource

        Raises:
            YouTubeAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveBroadcasts/bind",
                params={
                    "id": broadcast_id,
                    "streamId": stream_id,
                    "part": "id,snippet,contentDetails,status",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to bind broadcast to stream: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def transition_broadcast(
        self,
        broadcast_id: str,
        status: str,
    ) -> dict[str, Any]:
        """Transition broadcast to a new status.

        Args:
            broadcast_id: YouTube broadcast ID
            status: Target status (testing, live, complete)

        Returns:
            dict: Updated broadcast resource

        Raises:
            YouTubeAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveBroadcasts/transition",
                params={
                    "id": broadcast_id,
                    "broadcastStatus": status,
                    "part": "id,snippet,contentDetails,status",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to transition broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def get_broadcast(self, broadcast_id: str) -> dict[str, Any]:
        """Get broadcast details.

        Args:
            broadcast_id: YouTube broadcast ID

        Returns:
            dict: Broadcast resource

        Raises:
            YouTubeAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/liveBroadcasts",
                params={
                    "id": broadcast_id,
                    "part": "id,snippet,contentDetails,status",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to get broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            data = response.json()
            if not data.get("items"):
                raise YouTubeAPIError(
                    f"Broadcast not found: {broadcast_id}",
                    status_code=404,
                )

            return data["items"][0]

    async def get_stream(self, stream_id: str) -> dict[str, Any]:
        """Get stream details including RTMP info.

        Args:
            stream_id: YouTube stream ID

        Returns:
            dict: Stream resource with ingestion info

        Raises:
            YouTubeAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/liveStreams",
                params={
                    "id": stream_id,
                    "part": "id,snippet,cdn,status",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to get stream: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            data = response.json()
            if not data.get("items"):
                raise YouTubeAPIError(
                    f"Stream not found: {stream_id}",
                    status_code=404,
                )

            return data["items"][0]

    async def update_broadcast(
        self,
        broadcast_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_start_time: Optional[datetime] = None,
        privacy_status: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update broadcast details.

        Args:
            broadcast_id: YouTube broadcast ID
            title: New title
            description: New description
            scheduled_start_time: New scheduled start time
            privacy_status: New privacy status

        Returns:
            dict: Updated broadcast resource

        Raises:
            YouTubeAPIError: If API call fails
        """
        # First get current broadcast
        current = await self.get_broadcast(broadcast_id)

        # Build update body
        body = {
            "id": broadcast_id,
            "snippet": current["snippet"].copy(),
            "status": current["status"].copy(),
        }

        if title is not None:
            body["snippet"]["title"] = title
        if description is not None:
            body["snippet"]["description"] = description
        if scheduled_start_time is not None:
            body["snippet"]["scheduledStartTime"] = scheduled_start_time.isoformat() + "Z"
        if privacy_status is not None:
            body["status"]["privacyStatus"] = privacy_status

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/liveBroadcasts",
                params={"part": "snippet,status"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to update broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def delete_broadcast(self, broadcast_id: str) -> None:
        """Delete a broadcast.

        Args:
            broadcast_id: YouTube broadcast ID

        Raises:
            YouTubeAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/liveBroadcasts",
                params={"id": broadcast_id},
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                error_data = response.json() if response.content else {}
                raise YouTubeAPIError(
                    f"Failed to delete broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

    @staticmethod
    def extract_rtmp_info(stream_resource: dict) -> tuple[str, str]:
        """Extract RTMP URL and key from stream resource.

        Args:
            stream_resource: YouTube stream resource

        Returns:
            tuple: (rtmp_url, rtmp_key)

        Raises:
            YouTubeAPIError: If RTMP info not found
        """
        try:
            cdn = stream_resource.get("cdn", {})
            ingestion_info = cdn.get("ingestionInfo", {})
            rtmp_url = ingestion_info.get("ingestionAddress", "")
            rtmp_key = ingestion_info.get("streamName", "")

            if not rtmp_url or not rtmp_key:
                raise YouTubeAPIError("RTMP information not available in stream resource")

            return rtmp_url, rtmp_key
        except KeyError as e:
            raise YouTubeAPIError(f"Failed to extract RTMP info: {e}")
