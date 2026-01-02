"""YouTube OAuth2 utilities.

Handles OAuth2 flow for YouTube account connection.
Requirements: 2.1, 2.2
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings


# OAuth2 endpoints
YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Required scopes for YouTube API
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner",
]


class OAuthStateStore:
    """In-memory store for OAuth state parameters.
    
    In production, use Redis for distributed state storage.
    """
    
    _states: dict[str, dict] = {}
    
    @classmethod
    def create_state(cls, user_id: uuid.UUID, expires_minutes: int = 10) -> str:
        """Create a new OAuth state parameter.
        
        Args:
            user_id: User initiating OAuth flow
            expires_minutes: State expiration time
            
        Returns:
            str: Generated state parameter
        """
        state = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        cls._states[state] = {
            "user_id": user_id,
            "expires_at": expires_at,
        }
        
        # Clean up expired states
        cls._cleanup_expired()
        
        return state
    
    @classmethod
    def validate_state(cls, state: str) -> Optional[uuid.UUID]:
        """Validate and consume OAuth state.
        
        Args:
            state: State parameter to validate
            
        Returns:
            Optional[uuid.UUID]: User ID if valid, None otherwise
        """
        if state not in cls._states:
            return None
            
        state_data = cls._states.pop(state)
        
        if datetime.utcnow() > state_data["expires_at"]:
            return None
            
        return state_data["user_id"]
    
    @classmethod
    def _cleanup_expired(cls) -> None:
        """Remove expired states."""
        now = datetime.utcnow()
        expired = [
            s for s, data in cls._states.items()
            if now > data["expires_at"]
        ]
        for s in expired:
            cls._states.pop(s, None)


class OAuthError(Exception):
    """Exception for OAuth-related errors."""
    pass


class YouTubeOAuthClient:
    """Client for YouTube OAuth2 operations."""
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
    ):
        """Initialize OAuth client.
        
        Args:
            client_id: YouTube OAuth client ID
            client_secret: YouTube OAuth client secret
            redirect_uri: OAuth callback URI
        """
        self.client_id = client_id or settings.YOUTUBE_CLIENT_ID
        self.client_secret = client_secret or settings.YOUTUBE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.YOUTUBE_REDIRECT_URI
    
    def get_authorization_url(self, state: str) -> str:
        """Generate YouTube OAuth authorization URL.
        
        Args:
            state: State parameter for CSRF protection
            
        Returns:
            str: Authorization URL to redirect user
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(YOUTUBE_SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{YOUTUBE_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            dict: Token response containing access_token, refresh_token, expires_in
            
        Raises:
            OAuthError: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                YOUTUBE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise OAuthError(
                    f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}"
                )
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            dict: Token response with new access_token and expires_in
            
        Raises:
            OAuthError: If token refresh fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                YOUTUBE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise OAuthError(
                    f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}"
                )
            
            return response.json()
    
    async def get_channel_info(self, access_token: str) -> dict:
        """Fetch channel information from YouTube API.
        
        Args:
            access_token: Valid access token
            
        Returns:
            dict: Channel information
            
        Raises:
            OAuthError: If API call fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "part": "snippet,statistics,status,contentDetails",
                    "mine": "true",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise OAuthError(
                    f"Failed to fetch channel info: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )
            
            data = response.json()
            
            if not data.get("items"):
                raise OAuthError("No YouTube channel found for this account")
            
            channel = data["items"][0]
            snippet = channel.get("snippet", {})
            statistics = channel.get("statistics", {})
            status = channel.get("status", {})
            
            return {
                "channel_id": channel["id"],
                "channel_title": snippet.get("title", "Unknown"),
                "thumbnail_url": (
                    snippet.get("thumbnails", {}).get("high", {}).get("url") or
                    snippet.get("thumbnails", {}).get("medium", {}).get("url") or
                    snippet.get("thumbnails", {}).get("default", {}).get("url")
                ),
                "subscriber_count": int(statistics.get("subscriberCount", 0)),
                "video_count": int(statistics.get("videoCount", 0)),
                "view_count": int(statistics.get("viewCount", 0)),
                "is_monetized": status.get("isLinked", False),
                "has_live_streaming_enabled": status.get("longUploadsStatus") == "allowed",
            }

    async def get_live_stream_info(self, access_token: str) -> dict:
        """Fetch live stream information including stream key from YouTube API.
        
        This fetches the default/bound live stream for the channel.
        The stream key is in cdn.ingestionInfo.streamName.
        
        Args:
            access_token: Valid access token
            
        Returns:
            dict: Live stream information including stream_key and rtmp_url
            
        Raises:
            OAuthError: If API call fails or no streams found
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/liveStreams",
                params={
                    "part": "snippet,cdn,status",
                    "mine": "true",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            
            if response.status_code == 403:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                # Check if it's a live streaming not enabled error
                if 'liveStreamingNotEnabled' in str(error_data):
                    raise OAuthError(
                        "Live streaming is not enabled for this channel. "
                        "Please enable live streaming in YouTube Studio first."
                    )
                raise OAuthError(f"Access denied: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json()
                raise OAuthError(
                    f"Failed to fetch live streams: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )
            
            data = response.json()
            
            if not data.get("items"):
                # No streams found - user needs to create one in YouTube Studio
                return {
                    "stream_key": None,
                    "rtmp_url": None,
                    "stream_id": None,
                    "stream_title": None,
                    "has_streams": False,
                    "message": "No live streams found. Please create a stream in YouTube Studio first.",
                }
            
            # Get the first (default) stream
            stream = data["items"][0]
            cdn = stream.get("cdn", {})
            ingestion_info = cdn.get("ingestionInfo", {})
            snippet = stream.get("snippet", {})
            
            return {
                "stream_key": ingestion_info.get("streamName"),
                "rtmp_url": ingestion_info.get("ingestionAddress"),
                "backup_rtmp_url": ingestion_info.get("backupIngestionAddress"),
                "stream_id": stream.get("id"),
                "stream_title": snippet.get("title"),
                "has_streams": True,
                "resolution": cdn.get("resolution"),
                "frame_rate": cdn.get("frameRate"),
            }
