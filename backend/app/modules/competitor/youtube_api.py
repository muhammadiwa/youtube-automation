"""YouTube API client for competitor data fetching.

Fetches public channel metrics and content from YouTube Data API.
Requirements: 19.1, 19.2, 19.3
"""

from datetime import datetime
from typing import Optional
import httpx

from app.core.config import settings


class YouTubeAPIError(Exception):
    """Exception for YouTube API errors."""
    pass


class ChannelNotFoundError(YouTubeAPIError):
    """Exception when channel is not found."""
    pass


class QuotaExceededError(YouTubeAPIError):
    """Exception when API quota is exceeded."""
    pass


class ChannelData:
    """Data class for YouTube channel information."""

    def __init__(
        self,
        channel_id: str,
        title: str,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        custom_url: Optional[str] = None,
        country: Optional[str] = None,
        subscriber_count: int = 0,
        video_count: int = 0,
        view_count: int = 0,
        published_at: Optional[datetime] = None,
    ):
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.custom_url = custom_url
        self.country = country
        self.subscriber_count = subscriber_count
        self.video_count = video_count
        self.view_count = view_count
        self.published_at = published_at


class VideoData:
    """Data class for YouTube video information."""

    def __init__(
        self,
        video_id: str,
        title: str,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        view_count: int = 0,
        like_count: int = 0,
        comment_count: int = 0,
        duration_seconds: int = 0,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        content_type: str = "video",
    ):
        self.video_id = video_id
        self.title = title
        self.description = description
        self.thumbnail_url = thumbnail_url
        self.published_at = published_at
        self.view_count = view_count
        self.like_count = like_count
        self.comment_count = comment_count
        self.duration_seconds = duration_seconds
        self.tags = tags or []
        self.category_id = category_id
        self.content_type = content_type


class YouTubeCompetitorAPI:
    """Client for fetching competitor data from YouTube API."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube API client.

        Args:
            api_key: YouTube Data API key (uses settings if not provided)
        """
        self.api_key = api_key or getattr(settings, "YOUTUBE_API_KEY", None)
        if not self.api_key:
            raise YouTubeAPIError("YouTube API key not configured")

    async def get_channel_by_id(self, channel_id: str) -> ChannelData:
        """Fetch channel data by channel ID.

        Args:
            channel_id: YouTube channel ID

        Returns:
            ChannelData: Channel information

        Raises:
            ChannelNotFoundError: If channel not found
            YouTubeAPIError: If API request fails
        """
        params = {
            "key": self.api_key,
            "id": channel_id,
            "part": "snippet,statistics,brandingSettings",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/channels",
                params=params,
                timeout=30.0,
            )

        if response.status_code == 403:
            error_data = response.json()
            if "quotaExceeded" in str(error_data):
                raise QuotaExceededError("YouTube API quota exceeded")
            raise YouTubeAPIError(f"API access forbidden: {error_data}")

        if response.status_code != 200:
            raise YouTubeAPIError(f"API request failed: {response.status_code}")

        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")

        return self._parse_channel_data(items[0])

    async def get_channel_by_username(self, username: str) -> ChannelData:
        """Fetch channel data by username or custom URL.

        Args:
            username: YouTube username or custom URL

        Returns:
            ChannelData: Channel information

        Raises:
            ChannelNotFoundError: If channel not found
            YouTubeAPIError: If API request fails
        """
        # Try forUsername first
        params = {
            "key": self.api_key,
            "forUsername": username,
            "part": "snippet,statistics,brandingSettings",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/channels",
                params=params,
                timeout=30.0,
            )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                return self._parse_channel_data(items[0])

        # Try search if forUsername didn't work
        return await self._search_channel(username)

    async def _search_channel(self, query: str) -> ChannelData:
        """Search for a channel by query.

        Args:
            query: Search query

        Returns:
            ChannelData: Channel information

        Raises:
            ChannelNotFoundError: If channel not found
        """
        params = {
            "key": self.api_key,
            "q": query,
            "type": "channel",
            "part": "snippet",
            "maxResults": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise YouTubeAPIError(f"Search failed: {response.status_code}")

        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ChannelNotFoundError(f"Channel not found: {query}")

        channel_id = items[0]["snippet"]["channelId"]
        return await self.get_channel_by_id(channel_id)

    async def get_recent_videos(
        self,
        channel_id: str,
        max_results: int = 10,
        published_after: Optional[datetime] = None,
    ) -> list[VideoData]:
        """Fetch recent videos from a channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            published_after: Only fetch videos published after this datetime

        Returns:
            list[VideoData]: List of video information

        Raises:
            YouTubeAPIError: If API request fails
        """
        # First, search for videos from the channel
        params = {
            "key": self.api_key,
            "channelId": channel_id,
            "type": "video",
            "part": "snippet",
            "order": "date",
            "maxResults": max_results,
        }

        if published_after:
            params["publishedAfter"] = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise YouTubeAPIError(f"Search failed: {response.status_code}")

        data = response.json()
        items = data.get("items", [])

        if not items:
            return []

        # Get video IDs for detailed info
        video_ids = [item["id"]["videoId"] for item in items]
        return await self._get_video_details(video_ids)

    async def _get_video_details(self, video_ids: list[str]) -> list[VideoData]:
        """Fetch detailed video information.

        Args:
            video_ids: List of video IDs

        Returns:
            list[VideoData]: List of video information
        """
        if not video_ids:
            return []

        params = {
            "key": self.api_key,
            "id": ",".join(video_ids),
            "part": "snippet,statistics,contentDetails",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/videos",
                params=params,
                timeout=30.0,
            )

        if response.status_code != 200:
            raise YouTubeAPIError(f"Video details failed: {response.status_code}")

        data = response.json()
        items = data.get("items", [])

        return [self._parse_video_data(item) for item in items]

    def _parse_channel_data(self, item: dict) -> ChannelData:
        """Parse channel data from API response.

        Args:
            item: API response item

        Returns:
            ChannelData: Parsed channel data
        """
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        branding = item.get("brandingSettings", {}).get("channel", {})

        # Get thumbnail URL (prefer high quality)
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url") or
            thumbnails.get("medium", {}).get("url") or
            thumbnails.get("default", {}).get("url")
        )

        # Parse published date
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return ChannelData(
            channel_id=item["id"],
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            thumbnail_url=thumbnail_url,
            custom_url=snippet.get("customUrl"),
            country=branding.get("country") or snippet.get("country"),
            subscriber_count=int(statistics.get("subscriberCount", 0)),
            video_count=int(statistics.get("videoCount", 0)),
            view_count=int(statistics.get("viewCount", 0)),
            published_at=published_at,
        )

    def _parse_video_data(self, item: dict) -> VideoData:
        """Parse video data from API response.

        Args:
            item: API response item

        Returns:
            VideoData: Parsed video data
        """
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        # Get thumbnail URL
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url") or
            thumbnails.get("medium", {}).get("url") or
            thumbnails.get("default", {}).get("url")
        )

        # Parse published date
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        # Parse duration (ISO 8601 format)
        duration_seconds = self._parse_duration(content_details.get("duration", ""))

        # Determine content type
        content_type = "video"
        if duration_seconds <= 60:
            content_type = "short"

        return VideoData(
            video_id=item["id"],
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            thumbnail_url=thumbnail_url,
            published_at=published_at,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            duration_seconds=duration_seconds,
            tags=snippet.get("tags", []),
            category_id=snippet.get("categoryId"),
            content_type=content_type,
        )

    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds.

        Args:
            duration: ISO 8601 duration string (e.g., "PT1H2M3S")

        Returns:
            int: Duration in seconds
        """
        if not duration or not duration.startswith("PT"):
            return 0

        duration = duration[2:]  # Remove "PT"
        seconds = 0

        # Parse hours
        if "H" in duration:
            hours, duration = duration.split("H")
            seconds += int(hours) * 3600

        # Parse minutes
        if "M" in duration:
            minutes, duration = duration.split("M")
            seconds += int(minutes) * 60

        # Parse seconds
        if "S" in duration:
            secs = duration.replace("S", "")
            seconds += int(secs)

        return seconds
