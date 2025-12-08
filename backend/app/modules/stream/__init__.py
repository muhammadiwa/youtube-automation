"""Stream module for live streaming management.

Provides LiveEvent and StreamSession models, repositories, and services
for managing YouTube live streams.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from app.modules.stream.models import (
    LiveEvent,
    LiveEventStatus,
    LatencyMode,
    StreamSession,
    ConnectionStatus,
    RecurrencePattern,
    RecurrenceFrequency,
)
from app.modules.stream.repository import (
    LiveEventRepository,
    StreamSessionRepository,
    RecurrencePatternRepository,
)
from app.modules.stream.service import (
    StreamService,
    StreamServiceError,
    AccountNotFoundError,
    LiveEventNotFoundError,
    ScheduleConflictException,
)
from app.modules.stream.youtube_api import (
    YouTubeLiveStreamingClient,
    YouTubeAPIError,
)
from app.modules.stream.router import router

__all__ = [
    # Models
    "LiveEvent",
    "LiveEventStatus",
    "LatencyMode",
    "StreamSession",
    "ConnectionStatus",
    "RecurrencePattern",
    "RecurrenceFrequency",
    # Repositories
    "LiveEventRepository",
    "StreamSessionRepository",
    "RecurrencePatternRepository",
    # Service
    "StreamService",
    "StreamServiceError",
    "AccountNotFoundError",
    "LiveEventNotFoundError",
    "ScheduleConflictException",
    # YouTube API
    "YouTubeLiveStreamingClient",
    "YouTubeAPIError",
    # Router
    "router",
]
