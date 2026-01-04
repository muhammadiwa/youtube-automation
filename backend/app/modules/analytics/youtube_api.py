"""YouTube Analytics API integration.

Fetches analytics data from YouTube Analytics API and YouTube Data API.
Requirements: 17.1, 17.2
"""

import logging
from datetime import date, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_ANALYTICS_API_BASE = "https://youtubeanalytics.googleapis.com/v2"


class YouTubeAnalyticsError(Exception):
    """Exception for YouTube Analytics API errors."""
    pass


class YouTubeAnalyticsClient:
    """Client for fetching analytics data from YouTube APIs."""

    def __init__(self, access_token: str):
        """Initialize client with access token.
        
        Args:
            access_token: Valid OAuth2 access token with analytics scope
        """
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def get_channel_statistics(self, channel_id: str) -> dict:
        """Fetch basic channel statistics from YouTube Data API.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            dict: Channel statistics including subscribers, views, videos
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "part": "statistics,snippet",
                    "id": channel_id,
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to fetch channel stats: {error_msg}")
                raise YouTubeAnalyticsError(f"Failed to fetch channel statistics: {error_msg}")

            data = response.json()
            if not data.get("items"):
                raise YouTubeAnalyticsError(f"Channel {channel_id} not found")

            channel = data["items"][0]
            statistics = channel.get("statistics", {})

            return {
                "subscriber_count": int(statistics.get("subscriberCount", 0)),
                "view_count": int(statistics.get("viewCount", 0)),
                "video_count": int(statistics.get("videoCount", 0)),
                "hidden_subscriber_count": statistics.get("hiddenSubscriberCount", False),
            }

    async def get_channel_analytics(
        self,
        channel_id: str,
        start_date: date,
        end_date: date,
        metrics: Optional[list[str]] = None,
    ) -> dict:
        """Fetch analytics data from YouTube Analytics API.
        
        Args:
            channel_id: YouTube channel ID
            start_date: Start date for analytics
            end_date: End date for analytics
            metrics: List of metrics to fetch (default: views, estimatedMinutesWatched, etc.)
            
        Returns:
            dict: Analytics data with totals and daily breakdown
        """
        if metrics is None:
            metrics = [
                "views",
                "estimatedMinutesWatched",
                "averageViewDuration",
                "subscribersGained",
                "subscribersLost",
                "likes",
                "dislikes",
                "comments",
                "shares",
            ]

        metrics_str = ",".join(metrics)

        async with httpx.AsyncClient() as client:
            # Get totals for the period
            response = await client.get(
                f"{YOUTUBE_ANALYTICS_API_BASE}/reports",
                params={
                    "ids": f"channel=={channel_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": metrics_str,
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code == 403:
                # Analytics API not enabled or no permission
                logger.warning(f"YouTube Analytics API access denied for channel {channel_id}")
                return self._empty_analytics_response()

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Failed to fetch analytics: {error_msg}")
                # Return empty data instead of raising error
                return self._empty_analytics_response()

            data = response.json()
            return self._parse_analytics_response(data, metrics)

    async def get_daily_analytics(
        self,
        channel_id: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Fetch daily analytics breakdown.
        
        Args:
            channel_id: YouTube channel ID
            start_date: Start date
            end_date: End date
            
        Returns:
            list[dict]: Daily analytics data
        """
        metrics = ["views", "estimatedMinutesWatched", "subscribersGained", "subscribersLost", "likes", "comments"]
        metrics_str = ",".join(metrics)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_ANALYTICS_API_BASE}/reports",
                params={
                    "ids": f"channel=={channel_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": metrics_str,
                    "dimensions": "day",
                    "sort": "day",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch daily analytics for channel {channel_id}")
                return []

            data = response.json()
            return self._parse_daily_analytics(data, metrics)

    async def get_traffic_sources(
        self,
        channel_id: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Fetch traffic source breakdown.
        
        Args:
            channel_id: YouTube channel ID
            start_date: Start date
            end_date: End date
            
        Returns:
            dict: Traffic sources data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_ANALYTICS_API_BASE}/reports",
                params={
                    "ids": f"channel=={channel_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": "views,estimatedMinutesWatched",
                    "dimensions": "insightTrafficSourceType",
                    "sort": "-views",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            return self._parse_traffic_sources(data)

    async def get_demographics(
        self,
        channel_id: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Fetch audience demographics.
        
        Args:
            channel_id: YouTube channel ID
            start_date: Start date
            end_date: End date
            
        Returns:
            dict: Demographics data (age groups and gender)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_ANALYTICS_API_BASE}/reports",
                params={
                    "ids": f"channel=={channel_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": "viewerPercentage",
                    "dimensions": "ageGroup,gender",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            return self._parse_demographics(data)

    async def get_top_videos(
        self,
        channel_id: str,
        start_date: date,
        end_date: date,
        max_results: int = 10,
    ) -> list[dict]:
        """Fetch top performing videos.
        
        Args:
            channel_id: YouTube channel ID
            start_date: Start date
            end_date: End date
            max_results: Maximum number of videos to return
            
        Returns:
            list[dict]: Top videos with metrics
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_ANALYTICS_API_BASE}/reports",
                params={
                    "ids": f"channel=={channel_id}",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,comments",
                    "dimensions": "video",
                    "sort": "-views",
                    "maxResults": max_results,
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            videos = self._parse_top_videos(data)

            # Fetch video titles
            if videos:
                video_ids = [v["video_id"] for v in videos]
                titles = await self._get_video_titles(video_ids)
                for video in videos:
                    video["title"] = titles.get(video["video_id"], "Unknown")

            return videos

    async def _get_video_titles(self, video_ids: list[str]) -> dict[str, str]:
        """Fetch video titles from YouTube Data API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/videos",
                params={
                    "part": "snippet",
                    "id": ",".join(video_ids),
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                return {}

            data = response.json()
            return {
                item["id"]: item["snippet"]["title"]
                for item in data.get("items", [])
            }

    def _empty_analytics_response(self) -> dict:
        """Return empty analytics response structure."""
        return {
            "views": 0,
            "watch_time_minutes": 0,
            "average_view_duration": 0,
            "subscribers_gained": 0,
            "subscribers_lost": 0,
            "likes": 0,
            "dislikes": 0,
            "comments": 0,
            "shares": 0,
        }

    def _parse_analytics_response(self, data: dict, metrics: list[str]) -> dict:
        """Parse YouTube Analytics API response."""
        result = self._empty_analytics_response()

        rows = data.get("rows", [])
        if not rows:
            return result

        row = rows[0]
        column_headers = data.get("columnHeaders", [])

        for i, header in enumerate(column_headers):
            name = header.get("name", "")
            value = row[i] if i < len(row) else 0

            if name == "views":
                result["views"] = int(value)
            elif name == "estimatedMinutesWatched":
                result["watch_time_minutes"] = int(value)
            elif name == "averageViewDuration":
                result["average_view_duration"] = float(value)
            elif name == "subscribersGained":
                result["subscribers_gained"] = int(value)
            elif name == "subscribersLost":
                result["subscribers_lost"] = int(value)
            elif name == "likes":
                result["likes"] = int(value)
            elif name == "dislikes":
                result["dislikes"] = int(value)
            elif name == "comments":
                result["comments"] = int(value)
            elif name == "shares":
                result["shares"] = int(value)

        return result

    def _parse_daily_analytics(self, data: dict, metrics: list[str]) -> list[dict]:
        """Parse daily analytics response."""
        result = []
        rows = data.get("rows", [])
        column_headers = data.get("columnHeaders", [])

        for row in rows:
            day_data = {}
            for i, header in enumerate(column_headers):
                name = header.get("name", "")
                value = row[i] if i < len(row) else 0

                if name == "day":
                    day_data["date"] = value
                elif name == "views":
                    day_data["views"] = int(value)
                elif name == "estimatedMinutesWatched":
                    day_data["watch_time_minutes"] = int(value)
                elif name == "subscribersGained":
                    day_data["subscribers_gained"] = int(value)
                elif name == "subscribersLost":
                    day_data["subscribers_lost"] = int(value)
                elif name == "likes":
                    day_data["likes"] = int(value)
                elif name == "comments":
                    day_data["comments"] = int(value)

            if day_data:
                result.append(day_data)

        return result

    def _parse_traffic_sources(self, data: dict) -> dict:
        """Parse traffic sources response."""
        result = {}
        rows = data.get("rows", [])

        for row in rows:
            if len(row) >= 3:
                source_type = row[0]
                views = int(row[1])
                watch_time = int(row[2])
                result[source_type] = {
                    "views": views,
                    "watch_time_minutes": watch_time,
                }

        return result

    def _parse_demographics(self, data: dict) -> dict:
        """Parse demographics response."""
        result = {"age_groups": {}, "gender": {"male": 0, "female": 0}}
        rows = data.get("rows", [])

        for row in rows:
            if len(row) >= 3:
                age_group = row[0]
                gender = row[1]
                percentage = float(row[2])

                if age_group not in result["age_groups"]:
                    result["age_groups"][age_group] = {"male": 0, "female": 0}

                if gender.lower() == "male":
                    result["age_groups"][age_group]["male"] = percentage
                    result["gender"]["male"] += percentage
                elif gender.lower() == "female":
                    result["age_groups"][age_group]["female"] = percentage
                    result["gender"]["female"] += percentage

        return result

    def _parse_top_videos(self, data: dict) -> list[dict]:
        """Parse top videos response."""
        result = []
        rows = data.get("rows", [])
        column_headers = data.get("columnHeaders", [])

        for row in rows:
            video_data = {}
            for i, header in enumerate(column_headers):
                name = header.get("name", "")
                value = row[i] if i < len(row) else 0

                if name == "video":
                    video_data["video_id"] = value
                elif name == "views":
                    video_data["views"] = int(value)
                elif name == "estimatedMinutesWatched":
                    video_data["watch_time_minutes"] = int(value)
                elif name == "averageViewDuration":
                    video_data["average_view_duration"] = float(value)
                elif name == "likes":
                    video_data["likes"] = int(value)
                elif name == "comments":
                    video_data["comments"] = int(value)

            if video_data.get("video_id"):
                result.append(video_data)

        return result
