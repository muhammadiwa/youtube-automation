"""Moderation module for chat moderation management.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

from app.modules.moderation.models import (
    ChatMessage,
    CustomCommand,
    ModerationActionLog,
    ModerationActionType,
    ModerationRule,
    RuleType,
    SeverityLevel,
    SlowModeConfig,
)
from app.modules.moderation.service import (
    ChatAnalyzer,
    ModerationService,
)
from app.modules.moderation.actions import (
    ModerationActionExecutor,
    UserModerationHistory,
    get_action_for_severity,
    get_timeout_duration_for_severity,
)
from app.modules.moderation.spam_detection import (
    SpamDetector,
    SpamPattern,
    MessageRateTracker,
    DuplicateMessageDetector,
    SlowModeManager,
)
from app.modules.moderation.commands import (
    CommandContext,
    CommandHandler,
    CommandProcessor,
    CommandResult,
)

__all__ = [
    # Models
    "ChatMessage",
    "CustomCommand",
    "ModerationActionLog",
    "ModerationActionType",
    "ModerationRule",
    "RuleType",
    "SeverityLevel",
    "SlowModeConfig",
    # Service
    "ChatAnalyzer",
    "ModerationService",
    # Actions
    "ModerationActionExecutor",
    "UserModerationHistory",
    "get_action_for_severity",
    "get_timeout_duration_for_severity",
    # Spam Detection
    "SpamDetector",
    "SpamPattern",
    "MessageRateTracker",
    "DuplicateMessageDetector",
    "SlowModeManager",
    # Commands
    "CommandContext",
    "CommandHandler",
    "CommandProcessor",
    "CommandResult",
]
