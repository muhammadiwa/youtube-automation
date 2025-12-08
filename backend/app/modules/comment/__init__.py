"""Comment management module.

Implements comment aggregation, sentiment analysis, auto-reply, and bulk moderation.
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

from app.modules.comment.models import (
    Comment,
    CommentSentiment,
    CommentStatus,
    AutoReplyRule,
    CommentReply,
)
from app.modules.comment.repository import (
    CommentRepository,
    AutoReplyRuleRepository,
    CommentReplyRepository,
)
from app.modules.comment.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    AutoReplyRuleCreate,
    AutoReplyRuleResponse,
    AutoReplyRuleUpdate,
    CommentReplyCreate,
    CommentReplyResponse,
    BulkModerationRequest,
    BulkModerationResponse,
    SentimentAnalysisResult,
)
from app.modules.comment.service import CommentService, CommentServiceError
from app.modules.comment.youtube_api import YouTubeCommentsClient, YouTubeCommentsAPIError

__all__ = [
    # Models
    "Comment",
    "CommentSentiment",
    "CommentStatus",
    "AutoReplyRule",
    "CommentReply",
    # Repository
    "CommentRepository",
    "AutoReplyRuleRepository",
    "CommentReplyRepository",
    # Service
    "CommentService",
    "CommentServiceError",
    # YouTube API
    "YouTubeCommentsClient",
    "YouTubeCommentsAPIError",
    # Schemas
    "CommentCreate",
    "CommentResponse",
    "CommentUpdate",
    "AutoReplyRuleCreate",
    "AutoReplyRuleResponse",
    "AutoReplyRuleUpdate",
    "CommentReplyCreate",
    "CommentReplyResponse",
    "BulkModerationRequest",
    "BulkModerationResponse",
    "SentimentAnalysisResult",
]
