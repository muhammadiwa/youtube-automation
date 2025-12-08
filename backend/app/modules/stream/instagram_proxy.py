"""Instagram RTMP Proxy module for simulcast streaming.

Implements proxy routing for Instagram Live streaming.
Requirements: 9.5

Instagram Live has specific requirements that differ from standard RTMP:
- Different authentication mechanism
- Specific stream key format
- Rate limiting considerations
- Platform-specific error handling
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class InstagramProxyStatus(str, Enum):
    """Status of Instagram proxy connection."""

    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class InstagramProxyConfig:
    """Configuration for Instagram RTMP proxy.
    
    Requirements: 9.5 - Platform-specific requirements for Instagram Live.
    """

    # Default proxy server URL
    proxy_server_url: str = "rtmp://proxy.example.com/instagram"
    
    # Connection settings
    connection_timeout_seconds: int = 30
    reconnect_attempts: int = 3
    reconnect_delay_seconds: int = 5
    
    # Stream settings
    max_bitrate_kbps: int = 4000  # Instagram recommended max
    recommended_resolution: str = "1080p"
    recommended_fps: int = 30
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    
    # Health check interval
    health_check_interval_seconds: int = 10


@dataclass
class InstagramStreamInfo:
    """Information about an Instagram Live stream."""

    stream_url: str
    stream_key: str
    broadcast_id: Optional[str] = None
    status: InstagramProxyStatus = InstagramProxyStatus.IDLE
    started_at: Optional[datetime] = None
    viewer_count: int = 0
    error_message: Optional[str] = None


class InstagramRTMPProxy:
    """Instagram RTMP Proxy for handling Instagram Live streaming.
    
    Requirements: 9.5 - Route through RTMP proxy for Instagram Live.
    
    Instagram Live requires special handling because:
    1. It uses a different authentication flow
    2. Stream keys have a specific format
    3. There are platform-specific rate limits
    4. Error responses differ from standard RTMP
    """

    def __init__(self, config: Optional[InstagramProxyConfig] = None):
        """Initialize Instagram RTMP proxy.
        
        Args:
            config: Optional proxy configuration
        """
        self.config = config or InstagramProxyConfig()
        self._active_streams: dict[uuid.UUID, InstagramStreamInfo] = {}

    def get_proxy_url(self, target_id: uuid.UUID) -> str:
        """Get the proxy URL for an Instagram stream.
        
        Requirements: 9.5 - Proxy routing for Instagram Live.
        
        Args:
            target_id: Simulcast target UUID
            
        Returns:
            str: Proxy URL to use for streaming
        """
        # In production, this would return a unique proxy endpoint
        # that routes to Instagram's RTMP servers
        return f"{self.config.proxy_server_url}/{target_id}"

    def create_proxy_stream(
        self,
        target_id: uuid.UUID,
        instagram_stream_url: str,
        instagram_stream_key: str,
    ) -> InstagramStreamInfo:
        """Create a proxy stream for Instagram Live.
        
        Requirements: 9.5
        
        Args:
            target_id: Simulcast target UUID
            instagram_stream_url: Instagram's RTMP URL
            instagram_stream_key: Instagram's stream key
            
        Returns:
            InstagramStreamInfo: Stream information
        """
        stream_info = InstagramStreamInfo(
            stream_url=instagram_stream_url,
            stream_key=instagram_stream_key,
            status=InstagramProxyStatus.IDLE,
        )
        
        self._active_streams[target_id] = stream_info
        return stream_info

    def start_proxy_stream(self, target_id: uuid.UUID) -> bool:
        """Start proxying stream to Instagram.
        
        Requirements: 9.5
        
        Args:
            target_id: Simulcast target UUID
            
        Returns:
            bool: True if stream started successfully
        """
        if target_id not in self._active_streams:
            return False
        
        stream_info = self._active_streams[target_id]
        stream_info.status = InstagramProxyStatus.CONNECTING
        
        # In production, this would:
        # 1. Establish connection to Instagram's RTMP server
        # 2. Authenticate with the stream key
        # 3. Start forwarding the incoming stream
        
        # Simulate successful connection
        stream_info.status = InstagramProxyStatus.STREAMING
        stream_info.started_at = datetime.utcnow()
        
        return True

    def stop_proxy_stream(self, target_id: uuid.UUID) -> bool:
        """Stop proxying stream to Instagram.
        
        Args:
            target_id: Simulcast target UUID
            
        Returns:
            bool: True if stream stopped successfully
        """
        if target_id not in self._active_streams:
            return False
        
        stream_info = self._active_streams[target_id]
        stream_info.status = InstagramProxyStatus.DISCONNECTED
        
        return True

    def get_stream_status(self, target_id: uuid.UUID) -> Optional[InstagramStreamInfo]:
        """Get status of a proxy stream.
        
        Args:
            target_id: Simulcast target UUID
            
        Returns:
            Optional[InstagramStreamInfo]: Stream info if found
        """
        return self._active_streams.get(target_id)

    def handle_instagram_error(
        self,
        target_id: uuid.UUID,
        error_code: str,
        error_message: str,
    ) -> dict:
        """Handle Instagram-specific errors.
        
        Requirements: 9.5 - Platform-specific error handling.
        
        Args:
            target_id: Simulcast target UUID
            error_code: Instagram error code
            error_message: Error message
            
        Returns:
            dict: Error handling result
        """
        if target_id in self._active_streams:
            stream_info = self._active_streams[target_id]
            stream_info.status = InstagramProxyStatus.ERROR
            stream_info.error_message = error_message
        
        # Map Instagram-specific errors to actions
        error_actions = {
            "RATE_LIMITED": {
                "action": "retry_later",
                "delay_seconds": 60,
                "message": "Instagram rate limit reached, retry in 60 seconds",
            },
            "AUTH_FAILED": {
                "action": "reauthenticate",
                "delay_seconds": 0,
                "message": "Instagram authentication failed, need to reauthenticate",
            },
            "STREAM_ENDED": {
                "action": "stop",
                "delay_seconds": 0,
                "message": "Instagram stream was ended by the platform",
            },
            "CONNECTION_LOST": {
                "action": "reconnect",
                "delay_seconds": self.config.reconnect_delay_seconds,
                "message": "Connection to Instagram lost, attempting reconnect",
            },
        }
        
        return error_actions.get(error_code, {
            "action": "unknown",
            "delay_seconds": 0,
            "message": f"Unknown Instagram error: {error_message}",
        })

    def validate_stream_settings(
        self,
        bitrate_kbps: int,
        resolution: str,
        fps: int,
    ) -> dict:
        """Validate stream settings against Instagram requirements.
        
        Requirements: 9.5 - Platform-specific requirements.
        
        Args:
            bitrate_kbps: Stream bitrate in kbps
            resolution: Video resolution
            fps: Frames per second
            
        Returns:
            dict: Validation result with warnings/errors
        """
        warnings = []
        errors = []
        
        # Check bitrate
        if bitrate_kbps > self.config.max_bitrate_kbps:
            warnings.append(
                f"Bitrate {bitrate_kbps}kbps exceeds Instagram recommended max "
                f"of {self.config.max_bitrate_kbps}kbps"
            )
        
        # Check resolution
        valid_resolutions = ["720p", "1080p"]
        if resolution not in valid_resolutions:
            warnings.append(
                f"Resolution {resolution} may not be optimal for Instagram. "
                f"Recommended: {', '.join(valid_resolutions)}"
            )
        
        # Check FPS
        if fps > 30:
            warnings.append(
                f"FPS {fps} exceeds Instagram recommended max of 30fps"
            )
        
        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "recommended_settings": {
                "bitrate_kbps": min(bitrate_kbps, self.config.max_bitrate_kbps),
                "resolution": self.config.recommended_resolution,
                "fps": min(fps, self.config.recommended_fps),
            },
        }

    def get_proxy_health(self, target_id: uuid.UUID) -> dict:
        """Get health status of the proxy connection.
        
        Args:
            target_id: Simulcast target UUID
            
        Returns:
            dict: Health status
        """
        stream_info = self._active_streams.get(target_id)
        
        if not stream_info:
            return {
                "healthy": False,
                "status": "not_found",
                "message": "Stream not found",
            }
        
        is_healthy = stream_info.status in [
            InstagramProxyStatus.CONNECTED,
            InstagramProxyStatus.STREAMING,
        ]
        
        return {
            "healthy": is_healthy,
            "status": stream_info.status.value,
            "started_at": stream_info.started_at.isoformat() if stream_info.started_at else None,
            "viewer_count": stream_info.viewer_count,
            "error_message": stream_info.error_message,
        }

    def cleanup_stream(self, target_id: uuid.UUID) -> None:
        """Clean up resources for a stream.
        
        Args:
            target_id: Simulcast target UUID
        """
        if target_id in self._active_streams:
            del self._active_streams[target_id]


class InstagramProxyManager:
    """Manager for Instagram RTMP proxy instances.
    
    Requirements: 9.5 - Centralized management of Instagram proxy routing.
    """

    _instance: Optional["InstagramProxyManager"] = None
    _proxy: Optional[InstagramRTMPProxy] = None

    @classmethod
    def get_instance(cls) -> "InstagramProxyManager":
        """Get singleton instance of the proxy manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_proxy(cls) -> InstagramRTMPProxy:
        """Get the Instagram RTMP proxy instance."""
        if cls._proxy is None:
            cls._proxy = InstagramRTMPProxy()
        return cls._proxy

    @classmethod
    def configure_proxy(cls, config: InstagramProxyConfig) -> None:
        """Configure the Instagram RTMP proxy.
        
        Args:
            config: Proxy configuration
        """
        cls._proxy = InstagramRTMPProxy(config)

    @classmethod
    def is_instagram_platform(cls, platform: str) -> bool:
        """Check if a platform is Instagram.
        
        Args:
            platform: Platform identifier
            
        Returns:
            bool: True if platform is Instagram
        """
        return platform.lower() == "instagram"

    @classmethod
    def needs_proxy_routing(cls, platform: str) -> bool:
        """Check if a platform needs proxy routing.
        
        Requirements: 9.5 - Instagram requires RTMP proxy.
        
        Args:
            platform: Platform identifier
            
        Returns:
            bool: True if proxy routing is needed
        """
        # Currently only Instagram requires proxy routing
        return cls.is_instagram_platform(platform)

    @classmethod
    def get_effective_rtmp_url(
        cls,
        platform: str,
        original_url: str,
        target_id: uuid.UUID,
    ) -> str:
        """Get the effective RTMP URL for a platform.
        
        Requirements: 9.5 - Route Instagram through proxy.
        
        Args:
            platform: Platform identifier
            original_url: Original RTMP URL
            target_id: Simulcast target UUID
            
        Returns:
            str: Effective RTMP URL (proxy URL for Instagram)
        """
        if cls.needs_proxy_routing(platform):
            proxy = cls.get_proxy()
            return proxy.get_proxy_url(target_id)
        return original_url
