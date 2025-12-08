"""Comment service for comment management.

Implements comment sync, reply, sentiment analysis, auto-reply, and bulk moderation.
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

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
    CommentListResponse,
    BulkModerationRequest,
    BulkModerationResponse,
    BulkModerationResult,
    SentimentAnalysisResult,
    SentimentResult,
    CommentSyncResponse,
    CommentSyncStatus,
)
from app.modules.comment.youtube_api import (
    YouTubeCommentsClient,
    YouTubeCommentsAPIError,
)


class CommentServiceError(Exception):
    """Base exception for comment service errors."""
    pass


class CommentService:
    """Service for comment management.

    Handles comment sync, replies, sentiment analysis, auto-reply, and bulk moderation.
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize comment service.

        Args:
            session: Database session
        """
        self.session = session
        self.comment_repo = CommentRepository(session)
        self.auto_reply_repo = AutoReplyRuleRepository(session)
        self.reply_repo = CommentReplyRepository(session)

    async def sync_comments_for_account(
        self,
        account_id: uuid.UUID,
        access_token: str,
        channel_id: str,
        max_comments: int = 1000,
    ) -> CommentSyncStatus:
        """Sync comments for a YouTube account.

        Requirements: 13.1 - Aggregate from all accounts within 5 minutes

        Args:
            account_id: YouTube account ID
            access_token: OAuth access token
            channel_id: YouTube channel ID
            max_comments: Maximum comments to sync

        Returns:
            CommentSyncStatus: Sync status with counts
        """
        client = YouTubeCommentsClient(access_token)
        comments_synced = 0
        new_comments = 0

        try:
            # Get comments for the channel
            page_token = None
            while comments_synced < max_comments:
                response = await client.get_comments_for_channel(
                    channel_id=channel_id,
                    max_results=100,
                    page_token=page_token,
                )

                items = response.get("items", [])
                if not items:
                    break

                for thread in items:
                    # Parse and store top-level comment
                    comment_data = YouTubeCommentsClient.parse_comment_thread(thread)
                    
                    # Check if comment already exists
                    existing = await self.comment_repo.get_by_youtube_id(
                        comment_data["youtube_comment_id"]
                    )

                    if existing:
                        # Update existing comment
                        await self.comment_repo.update(
                            existing.id,
                            like_count=comment_data["like_count"],
                            reply_count=comment_data["reply_count"],
                            updated_at_youtube=comment_data["updated_at_youtube"],
                            synced_at=datetime.utcnow(),
                        )
                    else:
                        # Create new comment
                        comment = Comment(
                            account_id=account_id,
                            **comment_data,
                        )
                        await self.comment_repo.create(comment)
                        new_comments += 1

                    comments_synced += 1

                    # Process replies if any
                    replies = thread.get("replies", {}).get("comments", [])
                    for reply_data in replies:
                        parsed_reply = YouTubeCommentsClient.parse_reply(
                            reply_data,
                            comment_data["youtube_comment_id"],
                        )

                        existing_reply = await self.comment_repo.get_by_youtube_id(
                            parsed_reply["youtube_comment_id"]
                        )

                        if not existing_reply:
                            reply_comment = Comment(
                                account_id=account_id,
                                **parsed_reply,
                            )
                            await self.comment_repo.create(reply_comment)
                            new_comments += 1

                        comments_synced += 1

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            await self.session.commit()

            return CommentSyncStatus(
                account_id=account_id,
                last_sync_at=datetime.utcnow(),
                comments_synced=comments_synced,
                new_comments=new_comments,
                status="completed",
            )

        except YouTubeCommentsAPIError as e:
            return CommentSyncStatus(
                account_id=account_id,
                last_sync_at=datetime.utcnow(),
                comments_synced=comments_synced,
                new_comments=new_comments,
                status="failed",
                error_message=str(e),
            )

    async def get_unified_inbox(
        self,
        user_id: uuid.UUID,
        account_ids: Optional[list[uuid.UUID]] = None,
        status: Optional[CommentStatus] = None,
        sentiment: Optional[CommentSentiment] = None,
        requires_attention: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CommentListResponse:
        """Get unified inbox of comments from all accounts.

        Requirements: 13.1 - Create unified inbox

        Args:
            user_id: User ID
            account_ids: Optional specific account IDs
            status: Filter by status
            sentiment: Filter by sentiment
            requires_attention: Filter by attention required
            page: Page number
            page_size: Items per page

        Returns:
            CommentListResponse: Paginated comments
        """
        comments, total = await self.comment_repo.get_unified_inbox(
            user_id=user_id,
            account_ids=account_ids,
            status=status,
            sentiment=sentiment,
            requires_attention=requires_attention,
            page=page,
            page_size=page_size,
        )

        return CommentListResponse(
            comments=[CommentResponse.model_validate(c) for c in comments],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )

    async def reply_to_comment(
        self,
        comment_id: uuid.UUID,
        account_id: uuid.UUID,
        access_token: str,
        text: str,
        is_auto_reply: bool = False,
        auto_reply_rule_id: Optional[uuid.UUID] = None,
    ) -> CommentReply:
        """Reply to a comment.

        Requirements: 13.2 - Post replies to YouTube and update local status

        Args:
            comment_id: Comment ID to reply to
            account_id: YouTube account ID
            access_token: OAuth access token
            text: Reply text
            is_auto_reply: Whether this is an auto-reply
            auto_reply_rule_id: Auto-reply rule ID if applicable

        Returns:
            CommentReply: Created reply

        Raises:
            CommentServiceError: If reply fails
        """
        # Get the comment
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise CommentServiceError(f"Comment not found: {comment_id}")

        if not comment.can_reply:
            raise CommentServiceError("Cannot reply to this comment")

        # Create local reply record
        reply = CommentReply(
            comment_id=comment_id,
            account_id=account_id,
            text=text,
            is_auto_reply=is_auto_reply,
            auto_reply_rule_id=auto_reply_rule_id,
            status="pending",
        )
        await self.reply_repo.create(reply)

        # Post to YouTube
        client = YouTubeCommentsClient(access_token)
        try:
            response = await client.post_reply(
                parent_comment_id=comment.youtube_comment_id,
                text=text,
            )

            # Update reply with YouTube ID
            youtube_reply_id = response.get("id", "")
            await self.reply_repo.mark_as_posted(reply.id, youtube_reply_id)

            # Update comment status
            await self.comment_repo.update(
                comment_id,
                status=CommentStatus.REPLIED.value,
                auto_replied=is_auto_reply,
                auto_reply_rule_id=auto_reply_rule_id,
            )

            await self.session.commit()
            return reply

        except YouTubeCommentsAPIError as e:
            await self.reply_repo.mark_as_failed(reply.id, str(e))
            await self.session.commit()
            raise CommentServiceError(f"Failed to post reply: {e}")

    async def analyze_sentiment(
        self,
        comment_ids: list[uuid.UUID],
    ) -> SentimentAnalysisResult:
        """Analyze sentiment for comments.

        Requirements: 13.3 - Categorize comments by sentiment

        Args:
            comment_ids: List of comment IDs to analyze

        Returns:
            SentimentAnalysisResult: Analysis results
        """
        start_time = datetime.utcnow()
        results = []
        attention_count = 0

        for comment_id in comment_ids:
            comment = await self.comment_repo.get_by_id(comment_id)
            if not comment:
                continue

            # Simple sentiment analysis based on keywords
            # In production, this would use AI/ML service
            sentiment, score, requires_attention = self._analyze_text_sentiment(
                comment.text_original
            )

            # Update comment with sentiment
            await self.comment_repo.update_sentiment(
                comment_id,
                sentiment=sentiment,
                score=score,
                requires_attention=requires_attention,
            )

            if requires_attention:
                attention_count += 1

            results.append(
                SentimentResult(
                    comment_id=comment_id,
                    sentiment=sentiment,
                    score=score,
                    requires_attention=requires_attention,
                    confidence=0.8,  # Placeholder confidence
                    keywords=self._extract_sentiment_keywords(comment.text_original),
                )
            )

        await self.session.commit()

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SentimentAnalysisResult(
            results=results,
            analyzed_count=len(results),
            attention_required_count=attention_count,
            processing_time_ms=processing_time,
        )

    def _analyze_text_sentiment(
        self,
        text: str,
    ) -> tuple[CommentSentiment, float, bool]:
        """Analyze text sentiment using keyword matching.

        This is a simple implementation. In production, use AI/ML.

        Args:
            text: Text to analyze

        Returns:
            tuple: (sentiment, score, requires_attention)
        """
        text_lower = text.lower()

        # Positive keywords
        positive_keywords = [
            "love", "great", "awesome", "amazing", "excellent", "fantastic",
            "wonderful", "best", "thank", "thanks", "helpful", "good", "nice",
        ]

        # Negative keywords
        negative_keywords = [
            "hate", "terrible", "awful", "worst", "bad", "horrible", "poor",
            "disappointing", "waste", "boring", "stupid", "sucks",
        ]

        # Attention-required keywords (questions, complaints, urgent)
        attention_keywords = [
            "help", "problem", "issue", "bug", "broken", "doesn't work",
            "not working", "please fix", "urgent", "asap", "?",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        attention_count = sum(1 for kw in attention_keywords if kw in text_lower)

        # Calculate score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
            sentiment = CommentSentiment.NEUTRAL
        else:
            score = (positive_count - negative_count) / total
            if score > 0.3:
                sentiment = CommentSentiment.POSITIVE
            elif score < -0.3:
                sentiment = CommentSentiment.NEGATIVE
            else:
                sentiment = CommentSentiment.NEUTRAL

        # Check if requires attention
        requires_attention = attention_count > 0 or sentiment == CommentSentiment.NEGATIVE

        if requires_attention:
            sentiment = CommentSentiment.ATTENTION_REQUIRED

        return sentiment, score, requires_attention

    def _extract_sentiment_keywords(self, text: str) -> list[str]:
        """Extract sentiment-related keywords from text.

        Args:
            text: Text to analyze

        Returns:
            list: Found keywords
        """
        text_lower = text.lower()
        all_keywords = [
            "love", "great", "awesome", "amazing", "excellent", "hate",
            "terrible", "awful", "worst", "bad", "help", "problem", "issue",
        ]
        return [kw for kw in all_keywords if kw in text_lower]

    async def check_auto_reply_rules(
        self,
        comment: Comment,
        access_token: str,
    ) -> Optional[CommentReply]:
        """Check and apply auto-reply rules to a comment.

        Requirements: 13.4 - Auto-respond to matching comments

        Args:
            comment: Comment to check
            access_token: OAuth access token

        Returns:
            CommentReply if auto-reply was triggered, None otherwise
        """
        if comment.auto_replied or not comment.can_reply:
            return None

        # Get enabled rules for the account
        rules = await self.auto_reply_repo.get_by_account(
            comment.account_id,
            enabled_only=True,
        )

        for rule in rules:
            if not rule.can_reply():
                continue

            if self._matches_rule(comment, rule):
                # Check per-video limit
                if rule.max_replies_per_video:
                    video_count = await self.reply_repo.get_auto_reply_count_for_video(
                        rule.id,
                        comment.youtube_video_id,
                    )
                    if video_count >= rule.max_replies_per_video:
                        continue

                # Trigger auto-reply
                try:
                    reply = await self.reply_to_comment(
                        comment_id=comment.id,
                        account_id=comment.account_id,
                        access_token=access_token,
                        text=rule.response_text,
                        is_auto_reply=True,
                        auto_reply_rule_id=rule.id,
                    )

                    # Update rule statistics
                    await self.auto_reply_repo.increment_trigger_count(rule.id)
                    await self.session.commit()

                    return reply

                except CommentServiceError:
                    continue

        return None

    def _matches_rule(self, comment: Comment, rule: AutoReplyRule) -> bool:
        """Check if a comment matches an auto-reply rule.

        Args:
            comment: Comment to check
            rule: Rule to match against

        Returns:
            bool: True if comment matches rule
        """
        text = comment.text_original
        if not rule.case_sensitive:
            text = text.lower()

        if rule.trigger_type == "all":
            return True

        if rule.trigger_type == "keyword" and rule.trigger_keywords:
            keywords = rule.trigger_keywords
            if not rule.case_sensitive:
                keywords = [kw.lower() for kw in keywords]
            return any(kw in text for kw in keywords)

        if rule.trigger_type == "regex" and rule.trigger_pattern:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(rule.trigger_pattern, comment.text_original, flags))
            except re.error:
                return False

        if rule.trigger_type == "sentiment" and rule.trigger_sentiment:
            return comment.sentiment == rule.trigger_sentiment

        return False

    async def bulk_moderate(
        self,
        request: BulkModerationRequest,
        access_token: Optional[str] = None,
    ) -> BulkModerationResponse:
        """Apply bulk moderation actions to comments.

        Requirements: 13.5 - Apply actions to selected comments and report completion count

        Args:
            request: Bulk moderation request
            access_token: Optional OAuth token for YouTube API actions

        Returns:
            BulkModerationResponse: Results with completion count
        """
        results = []
        successful = 0
        failed = 0

        client = YouTubeCommentsClient(access_token) if access_token else None

        for action in request.actions:
            try:
                comment = await self.comment_repo.get_by_id(action.comment_id)
                if not comment:
                    results.append(
                        BulkModerationResult(
                            comment_id=action.comment_id,
                            action=action.action,
                            success=False,
                            error_message="Comment not found",
                        )
                    )
                    failed += 1
                    continue

                # Map action to status
                status_map = {
                    "approve": CommentStatus.APPROVED,
                    "hide": CommentStatus.HIDDEN,
                    "delete": CommentStatus.DELETED,
                    "spam": CommentStatus.SPAM,
                }
                new_status = status_map.get(action.action)

                if not new_status:
                    results.append(
                        BulkModerationResult(
                            comment_id=action.comment_id,
                            action=action.action,
                            success=False,
                            error_message=f"Unknown action: {action.action}",
                        )
                    )
                    failed += 1
                    continue

                # Apply YouTube API action if token provided
                if client and action.action in ("hide", "delete", "spam"):
                    try:
                        if action.action == "delete":
                            await client.delete_comment(comment.youtube_comment_id)
                        else:
                            moderation_status = (
                                "rejected" if action.action == "spam" else "heldForReview"
                            )
                            await client.set_moderation_status(
                                comment.youtube_comment_id,
                                moderation_status,
                            )
                    except YouTubeCommentsAPIError as e:
                        results.append(
                            BulkModerationResult(
                                comment_id=action.comment_id,
                                action=action.action,
                                success=False,
                                error_message=str(e),
                            )
                        )
                        failed += 1
                        continue

                # Update local status
                await self.comment_repo.update_status(action.comment_id, new_status)

                results.append(
                    BulkModerationResult(
                        comment_id=action.comment_id,
                        action=action.action,
                        success=True,
                    )
                )
                successful += 1

            except Exception as e:
                results.append(
                    BulkModerationResult(
                        comment_id=action.comment_id,
                        action=action.action,
                        success=False,
                        error_message=str(e),
                    )
                )
                failed += 1

        await self.session.commit()

        return BulkModerationResponse(
            results=results,
            total_processed=len(results),
            successful_count=successful,
            failed_count=failed,
        )

    async def get_attention_required_comments(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Comment]:
        """Get comments that require attention.

        Requirements: 13.3 - Highlight attention-required comments

        Args:
            account_id: YouTube account ID
            limit: Maximum comments to return

        Returns:
            list: Comments requiring attention
        """
        return await self.comment_repo.get_attention_required(account_id, limit)

    async def get_comments_by_sentiment(
        self,
        account_id: uuid.UUID,
        sentiment: CommentSentiment,
        limit: int = 100,
    ) -> list[Comment]:
        """Get comments by sentiment category.

        Requirements: 13.3 - Categorize by sentiment

        Args:
            account_id: YouTube account ID
            sentiment: Sentiment to filter by
            limit: Maximum comments to return

        Returns:
            list: Comments with specified sentiment
        """
        return await self.comment_repo.get_by_sentiment(account_id, sentiment, limit)
