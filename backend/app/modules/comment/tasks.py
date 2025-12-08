"""Celery tasks for comment management.

Implements background tasks for comment sync and auto-reply processing.
Requirements: 13.1, 13.4
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import async_session_maker


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="comment.sync_comments",
)
def sync_comments_task(
    self,
    account_id: str,
    access_token: str,
    channel_id: str,
    max_comments: int = 1000,
) -> dict:
    """Sync comments for a YouTube account.

    Requirements: 13.1 - Aggregate from all accounts within 5 minutes

    Args:
        account_id: YouTube account ID
        access_token: OAuth access token
        channel_id: YouTube channel ID
        max_comments: Maximum comments to sync

    Returns:
        dict: Sync status
    """
    import asyncio
    from app.modules.comment.service import CommentService

    async def _sync():
        async with async_session_maker() as session:
            service = CommentService(session)
            result = await service.sync_comments_for_account(
                account_id=uuid.UUID(account_id),
                access_token=access_token,
                channel_id=channel_id,
                max_comments=max_comments,
            )
            return {
                "account_id": str(result.account_id),
                "comments_synced": result.comments_synced,
                "new_comments": result.new_comments,
                "status": result.status,
                "error_message": result.error_message,
            }

    try:
        return asyncio.get_event_loop().run_until_complete(_sync())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="comment.analyze_sentiment",
)
def analyze_sentiment_task(
    self,
    comment_ids: list[str],
) -> dict:
    """Analyze sentiment for comments.

    Requirements: 13.3 - Categorize comments by sentiment

    Args:
        comment_ids: List of comment IDs to analyze

    Returns:
        dict: Analysis results
    """
    import asyncio
    from app.modules.comment.service import CommentService

    async def _analyze():
        async with async_session_maker() as session:
            service = CommentService(session)
            result = await service.analyze_sentiment(
                comment_ids=[uuid.UUID(cid) for cid in comment_ids]
            )
            return {
                "analyzed_count": result.analyzed_count,
                "attention_required_count": result.attention_required_count,
                "processing_time_ms": result.processing_time_ms,
            }

    try:
        return asyncio.get_event_loop().run_until_complete(_analyze())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="comment.process_auto_replies",
)
def process_auto_replies_task(
    self,
    account_id: str,
    access_token: str,
    comment_ids: list[str],
) -> dict:
    """Process auto-reply rules for comments.

    Requirements: 13.4 - Auto-respond to matching comments

    Args:
        account_id: YouTube account ID
        access_token: OAuth access token
        comment_ids: List of comment IDs to check

    Returns:
        dict: Processing results
    """
    import asyncio
    from app.modules.comment.service import CommentService
    from app.modules.comment.repository import CommentRepository

    async def _process():
        async with async_session_maker() as session:
            service = CommentService(session)
            comment_repo = CommentRepository(session)
            
            replies_sent = 0
            for comment_id in comment_ids:
                comment = await comment_repo.get_by_id(uuid.UUID(comment_id))
                if comment:
                    reply = await service.check_auto_reply_rules(
                        comment=comment,
                        access_token=access_token,
                    )
                    if reply:
                        replies_sent += 1

            return {
                "comments_processed": len(comment_ids),
                "replies_sent": replies_sent,
            }

    try:
        return asyncio.get_event_loop().run_until_complete(_process())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    name="comment.sync_all_accounts",
)
def sync_all_accounts_task() -> dict:
    """Sync comments for all active accounts.

    Requirements: 13.1 - Aggregate from all accounts within 5 minutes

    This task should be scheduled to run every 5 minutes.

    Returns:
        dict: Sync summary
    """
    import asyncio
    from app.modules.account.repository import YouTubeAccountRepository
    from app.modules.account.encryption import decrypt_token

    async def _sync_all():
        async with async_session_maker() as session:
            account_repo = YouTubeAccountRepository(session)
            
            # Get all active accounts
            accounts = await account_repo.get_all_active()
            
            synced_count = 0
            failed_count = 0
            
            for account in accounts:
                try:
                    # Decrypt access token
                    access_token = decrypt_token(account.access_token)
                    
                    # Queue sync task for each account
                    sync_comments_task.delay(
                        account_id=str(account.id),
                        access_token=access_token,
                        channel_id=account.channel_id,
                    )
                    synced_count += 1
                except Exception:
                    failed_count += 1

            return {
                "accounts_queued": synced_count,
                "accounts_failed": failed_count,
            }

    return asyncio.get_event_loop().run_until_complete(_sync_all())


@celery_app.task(
    name="comment.reset_daily_auto_reply_counts",
)
def reset_daily_auto_reply_counts_task() -> dict:
    """Reset daily auto-reply counts for all rules.

    This task should be scheduled to run daily at midnight.

    Returns:
        dict: Reset summary
    """
    import asyncio
    from app.modules.comment.repository import AutoReplyRuleRepository
    from app.modules.account.repository import YouTubeAccountRepository

    async def _reset():
        async with async_session_maker() as session:
            account_repo = YouTubeAccountRepository(session)
            rule_repo = AutoReplyRuleRepository(session)
            
            accounts = await account_repo.get_all_active()
            reset_count = 0
            
            for account in accounts:
                await rule_repo.reset_daily_counts(account.id)
                reset_count += 1
            
            await session.commit()
            
            return {"accounts_reset": reset_count}

    return asyncio.get_event_loop().run_until_complete(_reset())
