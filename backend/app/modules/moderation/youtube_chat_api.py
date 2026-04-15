"""YouTube Live Chat API client.

Provides methods for reading and moderating YouTube live chat.
Requirements: 12.1, 12.2, 12.3
"""

from datetime import datetime
from typing import Optional, Any
import httpx
import logging

logger = logging.getLogger(__name__)


class YouTubeChatAPIError(Exception):
    """Exception raised for YouTube Chat API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class YouTubeLiveChatClient:
    """Client for YouTube Live Chat API.

    Handles live chat message retrieval and moderation actions.
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

    async def get_live_chat_id(self, broadcast_id: str) -> Optional[str]:
        """Get the live chat ID for a broadcast.

        Args:
            broadcast_id: YouTube broadcast/video ID

        Returns:
            Optional[str]: Live chat ID if available

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/liveBroadcasts",
                params={
                    "id": broadcast_id,
                    "part": "snippet,status",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to get broadcast: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            data = response.json()
            items = data.get("items", [])
            if not items:
                return None

            snippet = items[0].get("snippet", {})
            return snippet.get("liveChatId")

    async def get_live_chat_messages(
        self,
        live_chat_id: str,
        page_token: Optional[str] = None,
        max_results: int = 200,
    ) -> dict[str, Any]:
        """Get live chat messages.

        Args:
            live_chat_id: YouTube live chat ID
            page_token: Token for pagination
            max_results: Maximum messages to retrieve (max 2000)

        Returns:
            dict: Response containing messages and pagination info
                - items: List of chat messages
                - nextPageToken: Token for next page
                - pollingIntervalMillis: Recommended polling interval

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        params = {
            "liveChatId": live_chat_id,
            "part": "id,snippet,authorDetails",
            "maxResults": min(max_results, 2000),
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/liveChat/messages",
                params=params,
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to get chat messages: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def delete_message(self, message_id: str) -> bool:
        """Delete a chat message.

        Args:
            message_id: YouTube chat message ID

        Returns:
            bool: True if deleted successfully

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/liveChat/messages",
                params={"id": message_id},
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to delete message: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return True

    async def ban_user(
        self,
        live_chat_id: str,
        channel_id: str,
        ban_duration_seconds: Optional[int] = None,
    ) -> dict[str, Any]:
        """Ban a user from live chat.

        Args:
            live_chat_id: YouTube live chat ID
            channel_id: Channel ID of user to ban
            ban_duration_seconds: Duration in seconds (None for permanent)

        Returns:
            dict: Ban resource

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        body = {
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "temporary" if ban_duration_seconds else "permanent",
                "bannedUserDetails": {
                    "channelId": channel_id,
                },
            },
        }

        if ban_duration_seconds:
            body["snippet"]["banDurationSeconds"] = ban_duration_seconds

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveChat/bans",
                params={"part": "snippet"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to ban user: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def unban_user(self, ban_id: str) -> bool:
        """Remove a ban from a user.

        Args:
            ban_id: YouTube ban resource ID

        Returns:
            bool: True if unbanned successfully

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/liveChat/bans",
                params={"id": ban_id},
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 204):
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to unban user: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return True

    async def send_message(
        self,
        live_chat_id: str,
        message_text: str,
    ) -> dict[str, Any]:
        """Send a message to live chat.

        Args:
            live_chat_id: YouTube live chat ID
            message_text: Message text to send

        Returns:
            dict: Created message resource

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        body = {
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": message_text,
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/liveChat/messages",
                params={"part": "snippet"},
                headers=self.headers,
                json=body,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to send message: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            return response.json()

    async def get_moderators(self, live_chat_id: str) -> list[dict[str, Any]]:
        """Get list of chat moderators.

        Args:
            live_chat_id: YouTube live chat ID

        Returns:
            list: List of moderator resources

        Raises:
            YouTubeChatAPIError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/liveChat/moderators",
                params={
                    "liveChatId": live_chat_id,
                    "part": "snippet",
                },
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise YouTubeChatAPIError(
                    f"Failed to get moderators: {response.status_code}",
                    status_code=response.status_code,
                    details=error_data,
                )

            data = response.json()
            return data.get("items", [])

    @staticmethod
    def parse_chat_message(item: dict) -> dict[str, Any]:
        """Parse a chat message item into a standardized format.

        Args:
            item: Raw YouTube chat message item

        Returns:
            dict: Parsed message with standardized fields
        """
        snippet = item.get("snippet", {})
        author_details = item.get("authorDetails", {})
        text_details = snippet.get("textMessageDetails", {})

        return {
            "id": item.get("id"),
            "youtube_message_id": item.get("id"),
            "content": text_details.get("messageText", ""),
            "author_channel_id": author_details.get("channelId", ""),
            "author_display_name": author_details.get("displayName", ""),
            "author_profile_image": author_details.get("profileImageUrl", ""),
            "is_chat_owner": author_details.get("isChatOwner", False),
            "is_chat_moderator": author_details.get("isChatModerator", False),
            "is_chat_sponsor": author_details.get("isChatSponsor", False),
            "is_verified": author_details.get("isVerified", False),
            "published_at": snippet.get("publishedAt"),
            "type": snippet.get("type", "textMessageEvent"),
        }
