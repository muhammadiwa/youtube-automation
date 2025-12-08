"""Repository for comment data access.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comment.models import (
    Comment,
    CommentSentiment,
    CommentStatus,
    AutoReplyRule,
    CommentReply,
)


class CommentRepository:
    """Repository for Comment CRUD operations.
    
    Requirements: 13.1, 13.3, 13.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, comment: Comment) -> Comment:
        """Create a new comment."""
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def create_many(self, comments: list[Comment]) -> list[Comment]:
        """Create multiple comments at once."""
        self.session.add_all(comments)
        await self.session.flush()
        return comments

    async def get_by_id(self, comment_id: uuid.UUID) -> Optional[Comment]:
        """Get a comment by ID."""
        result = await self.session.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_youtube_id(
        self,
        youtube_comment_id: str,
    ) -> Optional[Comment]:
        """Get a comment by YouTube comment ID."""
        result = await self.session.execute(
            select(Comment).where(Comment.youtube_comment_id == youtube_comment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: uuid.UUID,
        status: Optional[CommentStatus] = None,
        sentiment: Optional[CommentSentiment] = None,
        requires_attention: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Comment], int]:
        """Get comments for an account with filtering and pagination.
        
        Args:
            account_id: YouTube account ID
            status: Filter by status
            sentiment: Filter by sentiment
            requires_attention: Filter by attention required
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (comments list, total count)
        """
        query = select(Comment).where(Comment.account_id == account_id)
        count_query = select(func.count(Comment.id)).where(
            Comment.account_id == account_id
        )

        if status:
            query = query.where(Comment.status == status.value)
            count_query = count_query.where(Comment.status == status.value)

        if sentiment:
            query = query.where(Comment.sentiment == sentiment.value)
            count_query = count_query.where(Comment.sentiment == sentiment.value)

        if requires_attention is not None:
            query = query.where(Comment.requires_attention == requires_attention)
            count_query = count_query.where(
                Comment.requires_attention == requires_attention
            )

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(Comment.published_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        comments = list(result.scalars().all())

        return comments, total

    async def get_unified_inbox(
        self,
        user_id: uuid.UUID,
        account_ids: Optional[list[uuid.UUID]] = None,
        status: Optional[CommentStatus] = None,
        sentiment: Optional[CommentSentiment] = None,
        requires_attention: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Comment], int]:
        """Get unified inbox of comments from multiple accounts.
        
        Requirements: 13.1 - Aggregate from all accounts into unified inbox
        
        Args:
            user_id: User ID (for account filtering)
            account_ids: Optional list of specific account IDs
            status: Filter by status
            sentiment: Filter by sentiment
            requires_attention: Filter by attention required
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (comments list, total count)
        """
        # Build base query - join with youtube_accounts to filter by user
        from app.modules.account.models import YouTubeAccount
        
        base_condition = YouTubeAccount.user_id == user_id
        
        if account_ids:
            base_condition = and_(base_condition, Comment.account_id.in_(account_ids))

        query = (
            select(Comment)
            .join(YouTubeAccount, Comment.account_id == YouTubeAccount.id)
            .where(base_condition)
        )
        count_query = (
            select(func.count(Comment.id))
            .join(YouTubeAccount, Comment.account_id == YouTubeAccount.id)
            .where(base_condition)
        )

        if status:
            query = query.where(Comment.status == status.value)
            count_query = count_query.where(Comment.status == status.value)

        if sentiment:
            query = query.where(Comment.sentiment == sentiment.value)
            count_query = count_query.where(Comment.sentiment == sentiment.value)

        if requires_attention is not None:
            query = query.where(Comment.requires_attention == requires_attention)
            count_query = count_query.where(
                Comment.requires_attention == requires_attention
            )

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(Comment.published_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        comments = list(result.scalars().all())

        return comments, total

    async def get_by_video(
        self,
        youtube_video_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Comment], int]:
        """Get comments for a specific video."""
        query = select(Comment).where(Comment.youtube_video_id == youtube_video_id)
        count_query = select(func.count(Comment.id)).where(
            Comment.youtube_video_id == youtube_video_id
        )

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(Comment.published_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        comments = list(result.scalars().all())

        return comments, total

    async def get_attention_required(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Comment]:
        """Get comments that require attention.
        
        Requirements: 13.3 - Highlight attention-required comments
        """
        result = await self.session.execute(
            select(Comment)
            .where(
                and_(
                    Comment.account_id == account_id,
                    Comment.requires_attention == True,
                )
            )
            .order_by(Comment.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_sentiment(
        self,
        account_id: uuid.UUID,
        sentiment: CommentSentiment,
        limit: int = 100,
    ) -> list[Comment]:
        """Get comments by sentiment category.
        
        Requirements: 13.3 - Categorize by sentiment
        """
        result = await self.session.execute(
            select(Comment)
            .where(
                and_(
                    Comment.account_id == account_id,
                    Comment.sentiment == sentiment.value,
                )
            )
            .order_by(Comment.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unanalyzed(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Comment]:
        """Get comments that haven't been analyzed for sentiment."""
        result = await self.session.execute(
            select(Comment)
            .where(
                and_(
                    Comment.account_id == account_id,
                    Comment.sentiment_analyzed_at.is_(None),
                )
            )
            .order_by(Comment.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        comment_id: uuid.UUID,
        **kwargs,
    ) -> Optional[Comment]:
        """Update a comment."""
        comment = await self.get_by_id(comment_id)
        if comment:
            for key, value in kwargs.items():
                if hasattr(comment, key) and value is not None:
                    setattr(comment, key, value)
            await self.session.flush()
        return comment

    async def update_status(
        self,
        comment_id: uuid.UUID,
        status: CommentStatus,
    ) -> Optional[Comment]:
        """Update comment status."""
        return await self.update(comment_id, status=status.value)

    async def update_sentiment(
        self,
        comment_id: uuid.UUID,
        sentiment: CommentSentiment,
        score: float,
        requires_attention: bool = False,
    ) -> Optional[Comment]:
        """Update comment sentiment analysis results.
        
        Requirements: 13.3
        """
        comment = await self.get_by_id(comment_id)
        if comment:
            comment.update_sentiment(sentiment, score, requires_attention)
            await self.session.flush()
        return comment

    async def bulk_update_status(
        self,
        comment_ids: list[uuid.UUID],
        status: CommentStatus,
    ) -> int:
        """Bulk update comment status.
        
        Requirements: 13.5 - Apply action to selected comments
        
        Returns:
            Number of comments updated
        """
        result = await self.session.execute(
            update(Comment)
            .where(Comment.id.in_(comment_ids))
            .values(status=status.value, updated_at=datetime.utcnow())
        )
        await self.session.flush()
        return result.rowcount

    async def delete(self, comment_id: uuid.UUID) -> bool:
        """Delete a comment."""
        comment = await self.get_by_id(comment_id)
        if comment:
            await self.session.delete(comment)
            await self.session.flush()
            return True
        return False

    async def get_recent_sync_count(
        self,
        account_id: uuid.UUID,
        minutes: int = 5,
    ) -> int:
        """Get count of comments synced within the last N minutes.
        
        Requirements: 13.1 - Aggregate within 5 minutes
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        result = await self.session.execute(
            select(func.count(Comment.id)).where(
                and_(
                    Comment.account_id == account_id,
                    Comment.synced_at >= cutoff,
                )
            )
        )
        return result.scalar() or 0


class AutoReplyRuleRepository:
    """Repository for AutoReplyRule CRUD operations.
    
    Requirements: 13.4
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, rule: AutoReplyRule) -> AutoReplyRule:
        """Create a new auto-reply rule."""
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> Optional[AutoReplyRule]:
        """Get an auto-reply rule by ID."""
        result = await self.session.execute(
            select(AutoReplyRule).where(AutoReplyRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[AutoReplyRule]:
        """Get all auto-reply rules for an account.
        
        Args:
            account_id: YouTube account ID
            enabled_only: Only return enabled rules
            
        Returns:
            List of auto-reply rules ordered by priority (descending)
        """
        query = select(AutoReplyRule).where(AutoReplyRule.account_id == account_id)
        if enabled_only:
            query = query.where(AutoReplyRule.is_enabled == True)
        query = query.order_by(AutoReplyRule.priority.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        rule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[AutoReplyRule]:
        """Update an auto-reply rule."""
        rule = await self.get_by_id(rule_id)
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key) and value is not None:
                    setattr(rule, key, value)
            await self.session.flush()
        return rule

    async def delete(self, rule_id: uuid.UUID) -> bool:
        """Delete an auto-reply rule."""
        rule = await self.get_by_id(rule_id)
        if rule:
            await self.session.delete(rule)
            await self.session.flush()
            return True
        return False

    async def increment_trigger_count(self, rule_id: uuid.UUID) -> None:
        """Increment the trigger count for a rule."""
        await self.session.execute(
            update(AutoReplyRule)
            .where(AutoReplyRule.id == rule_id)
            .values(
                trigger_count=AutoReplyRule.trigger_count + 1,
                last_triggered_at=datetime.utcnow(),
                replies_today=AutoReplyRule.replies_today + 1,
            )
        )

    async def reset_daily_counts(self, account_id: uuid.UUID) -> None:
        """Reset daily reply counts for all rules of an account."""
        await self.session.execute(
            update(AutoReplyRule)
            .where(AutoReplyRule.account_id == account_id)
            .values(
                replies_today=0,
                replies_today_reset_at=datetime.utcnow(),
            )
        )


class CommentReplyRepository:
    """Repository for CommentReply CRUD operations.
    
    Requirements: 13.2
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reply: CommentReply) -> CommentReply:
        """Create a new comment reply."""
        self.session.add(reply)
        await self.session.flush()
        return reply

    async def get_by_id(self, reply_id: uuid.UUID) -> Optional[CommentReply]:
        """Get a comment reply by ID."""
        result = await self.session.execute(
            select(CommentReply).where(CommentReply.id == reply_id)
        )
        return result.scalar_one_or_none()

    async def get_by_comment(
        self,
        comment_id: uuid.UUID,
    ) -> list[CommentReply]:
        """Get all replies for a comment."""
        result = await self.session.execute(
            select(CommentReply)
            .where(CommentReply.comment_id == comment_id)
            .order_by(CommentReply.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[CommentReply]:
        """Get pending replies that need to be posted."""
        result = await self.session.execute(
            select(CommentReply)
            .where(
                and_(
                    CommentReply.account_id == account_id,
                    CommentReply.status == "pending",
                )
            )
            .order_by(CommentReply.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        reply_id: uuid.UUID,
        **kwargs,
    ) -> Optional[CommentReply]:
        """Update a comment reply."""
        reply = await self.get_by_id(reply_id)
        if reply:
            for key, value in kwargs.items():
                if hasattr(reply, key) and value is not None:
                    setattr(reply, key, value)
            await self.session.flush()
        return reply

    async def mark_as_posted(
        self,
        reply_id: uuid.UUID,
        youtube_reply_id: str,
    ) -> Optional[CommentReply]:
        """Mark a reply as successfully posted."""
        reply = await self.get_by_id(reply_id)
        if reply:
            reply.mark_as_posted(youtube_reply_id)
            await self.session.flush()
        return reply

    async def mark_as_failed(
        self,
        reply_id: uuid.UUID,
        error_message: str,
    ) -> Optional[CommentReply]:
        """Mark a reply as failed."""
        reply = await self.get_by_id(reply_id)
        if reply:
            reply.mark_as_failed(error_message)
            await self.session.flush()
        return reply

    async def delete(self, reply_id: uuid.UUID) -> bool:
        """Delete a comment reply."""
        reply = await self.get_by_id(reply_id)
        if reply:
            await self.session.delete(reply)
            await self.session.flush()
            return True
        return False

    async def get_auto_reply_count_for_video(
        self,
        rule_id: uuid.UUID,
        youtube_video_id: str,
    ) -> int:
        """Get count of auto-replies for a specific rule and video."""
        result = await self.session.execute(
            select(func.count(CommentReply.id))
            .join(Comment, CommentReply.comment_id == Comment.id)
            .where(
                and_(
                    CommentReply.auto_reply_rule_id == rule_id,
                    CommentReply.is_auto_reply == True,
                    Comment.youtube_video_id == youtube_video_id,
                )
            )
        )
        return result.scalar() or 0
