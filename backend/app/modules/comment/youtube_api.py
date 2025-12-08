"""YouTube Comments API client.

Provides methods for fetching and managing YouTube video comments.
Requirements: 13.1, 13.2
"""

from datetime import datetime
from typing import Optional, Any
import httpx


class YouTubeCommentsAPIError(Exception):
    """Exception raised for YouTube Comments API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class YouTubeCommentsClient:
    """Client for YouTube Comments API.

    Handles comment fetching and reply posting.
    Requirements: 13.1, 13.2
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

    async def get_comment_threads(
        self,
        video_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None,
        order: str = "time",
    ) -> dict[str, Any]:
        """Get comment threads for a video.

        Requirements: 13.1 - Aggregate comments

        Args:
            video_id: YouTube video ID
            max_results: Maximum results per page (max 100)
            page_token: Page token for pagination
            order: Sort order (time, relevance)

        Returns:
            dict: Comment threads response with items and pagination

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": min(max_results, 100),
            "order": order,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/commentThreads",
                params=params,
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeCommentsAPIError(
                    f"Failed to get comment threads: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def get_all_comments_for_video(
        self,
        video_id: str,
        max_comments: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get all comments for a video with pagination.

        Requirements: 13.1 - Aggregate comments

        Args:
            video_id: YouTube video ID
            max_comments: Maximum total comments to fetch

        Returns:
            list: All comment items

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        all_comments = []
        page_token = None

        while len(all_comments) < max_comments:
            response = await self.get_comment_threads(
                video_id=video_id,
                max_results=100,
                page_token=page_token,
            )

            items = response.get("items", [])
            all_comments.extend(items)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return all_comments[:max_comments]

    async def get_comments_for_channel(
        self,
        channel_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get all comments for a channel's videos.

        Requirements: 13.1 - Aggregate from all accounts

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results per page
            page_token: Page token for pagination

        Returns:
            dict: Comment threads response

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        params = {
            "part": "snippet,replies",
            "allThreadsRelatedToChannelId": channel_id,
            "maxResults": min(max_results, 100),
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/commentThreads",
                params=params,
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeCommentsAPIError(
                    f"Failed to get channel comments: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def post_reply(
        self,
        parent_comment_id: str,
        text: str,
    ) -> dict[str, Any]:
        """Post a reply to a comment.

        Requirements: 13.2 - Post replies to YouTube

        Args:
            parent_comment_id: Parent comment ID to reply to
            text: Reply text content

        Returns:
            dict: Created comment resource

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        body = {
            "snippet": {
                "parentId": parent_comment_id,
                "textOriginal": text,
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/comments",
                params={"part": "snippet"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code not in (200, 201):
                error_data = response.json() if response.content else {}
                raise YouTubeCommentsAPIError(
                    f"Failed to post reply: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def delete_comment(self, comment_id: str) -> None:
        """Delete a comment.

        Requirements: 13.5 - Bulk moderation

        Args:
            comment_id: YouTube comment ID

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/comments",
                params={"id": comment_id},
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                error_data = response.json() if response.content else {}
                raise YouTubeCommentsAPIError(
                    f"Failed to delete comment: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

    async def set_moderation_status(
        self,
        comment_id: str,
        moderation_status: str,
        ban_author: bool = False,
    ) -> None:
        """Set moderation status for a comment.

        Requirements: 13.5 - Bulk moderation

        Args:
            comment_id: YouTube comment ID
            moderation_status: Status (heldForReview, published, rejected)
            ban_author: Whether to ban the author

        Raises:
            YouTubeCommentsAPIError: If API call fails
        """
        params = {
            "id": comment_id,
            "moderationStatus": moderation_status,
            "banAuthor": str(ban_author).lower(),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/comments/setModerationStatus",
                params=params,
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                error_data = response.json() if response.content else {}
                raise YouTubeCommentsAPIError(
                    f"Failed to set moderation status: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

    @staticmethod
    def parse_comment_thread(thread: dict) -> dict[str, Any]:
        """Parse a comment thread into a standardized format.

        Args:
            thread: YouTube comment thread resource

        Returns:
            dict: Parsed comment data
        """
        snippet = thread.get("snippet", {})
        top_comment = snippet.get("topLevelComment", {})
        top_snippet = top_comment.get("snippet", {})

        return {
            "youtube_comment_id": top_comment.get("id", ""),
            "youtube_video_id": snippet.get("videoId", ""),
            "youtube_parent_id": None,  # Top-level comment
            "author_channel_id": top_snippet.get("authorChannelId", {}).get(
                "value", ""
            ),
            "author_display_name": top_snippet.get("authorDisplayName", ""),
            "author_profile_image_url": top_snippet.get("authorProfileImageUrl"),
            "text_original": top_snippet.get("textOriginal", ""),
            "text_display": top_snippet.get("textDisplay", ""),
            "like_count": top_snippet.get("likeCount", 0),
            "reply_count": snippet.get("totalReplyCount", 0),
            "is_public": snippet.get("isPublic", True),
            "can_reply": snippet.get("canReply", True),
            "published_at": datetime.fromisoformat(
                top_snippet.get("publishedAt", "").replace("Z", "+00:00")
            )
            if top_snippet.get("publishedAt")
            else datetime.utcnow(),
            "updated_at_youtube": datetime.fromisoformat(
                top_snippet.get("updatedAt", "").replace("Z", "+00:00")
            )
            if top_snippet.get("updatedAt")
            else None,
        }

    @staticmethod
    def parse_reply(reply: dict, parent_id: str) -> dict[str, Any]:
        """Parse a reply comment into a standardized format.

        Args:
            reply: YouTube comment resource
            parent_id: Parent comment ID

        Returns:
            dict: Parsed reply data
        """
        snippet = reply.get("snippet", {})

        return {
            "youtube_comment_id": reply.get("id", ""),
            "youtube_video_id": snippet.get("videoId", ""),
            "youtube_parent_id": parent_id,
            "author_channel_id": snippet.get("authorChannelId", {}).get("value", ""),
            "author_display_name": snippet.get("authorDisplayName", ""),
            "author_profile_image_url": snippet.get("authorProfileImageUrl"),
            "text_original": snippet.get("textOriginal", ""),
            "text_display": snippet.get("textDisplay", ""),
            "like_count": snippet.get("likeCount", 0),
            "reply_count": 0,  # Replies don't have replies
            "is_public": True,
            "can_reply": False,  # Can't reply to replies
            "published_at": datetime.fromisoformat(
                snippet.get("publishedAt", "").replace("Z", "+00:00")
            )
            if snippet.get("publishedAt")
            else datetime.utcnow(),
            "updated_at_youtube": datetime.fromisoformat(
                snippet.get("updatedAt", "").replace("Z", "+00:00")
            )
            if snippet.get("updatedAt")
            else None,
        }
