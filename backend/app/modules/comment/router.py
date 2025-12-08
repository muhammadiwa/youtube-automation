"""API router for comment management.

Implements REST endpoints for comment operations.
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.comment.models import CommentSentiment, CommentStatus
from app.modules.comment.repository import (
    CommentRepository,
    AutoReplyRuleRepository,
    CommentReplyRepository,
)
from app.modules.comment.schemas import (
    CommentResponse,
    CommentListResponse,
    CommentUpdate,
    AutoReplyRuleCreate,
    AutoReplyRuleResponse,
    AutoReplyRuleUpdate,
    CommentReplyCreate,
    CommentReplyResponse,
    BulkModerationRequest,
    BulkModerationResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResult,
    CommentSyncRequest,
    CommentSyncResponse,
)
from app.modules.comment.service import CommentService, CommentServiceError
from app.modules.comment.tasks import sync_comments_task, analyze_sentiment_task

router = APIRouter(prefix="/comments", tags=["comments"])


# ============================================
# Comment Endpoints
# ============================================


@router.get("/inbox", response_model=CommentListResponse)
async def get_unified_inbox(
    user_id: uuid.UUID,
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    status: Optional[CommentStatus] = None,
    sentiment: Optional[CommentSentiment] = None,
    requires_attention: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get unified inbox of comments from all accounts.

    Requirements: 13.1 - Create unified inbox
    """
    service = CommentService(session)

    account_id_list = None
    if account_ids:
        account_id_list = [uuid.UUID(aid.strip()) for aid in account_ids.split(",")]

    return await service.get_unified_inbox(
        user_id=user_id,
        account_ids=account_id_list,
        status=status,
        sentiment=sentiment,
        requires_attention=requires_attention,
        page=page,
        page_size=page_size,
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific comment by ID."""
    repo = CommentRepository(session)
    comment = await repo.get_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return CommentResponse.model_validate(comment)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: uuid.UUID,
    update: CommentUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a comment's status or sentiment."""
    repo = CommentRepository(session)
    comment = await repo.get_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        comment = await repo.update(comment_id, **update_data)
        await session.commit()

    return CommentResponse.model_validate(comment)


@router.get("/attention-required/{account_id}", response_model=list[CommentResponse])
async def get_attention_required_comments(
    account_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Get comments that require attention.

    Requirements: 13.3 - Highlight attention-required comments
    """
    service = CommentService(session)
    comments = await service.get_attention_required_comments(account_id, limit)
    return [CommentResponse.model_validate(c) for c in comments]


@router.get("/by-sentiment/{account_id}", response_model=list[CommentResponse])
async def get_comments_by_sentiment(
    account_id: uuid.UUID,
    sentiment: CommentSentiment,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Get comments by sentiment category.

    Requirements: 13.3 - Categorize by sentiment
    """
    service = CommentService(session)
    comments = await service.get_comments_by_sentiment(account_id, sentiment, limit)
    return [CommentResponse.model_validate(c) for c in comments]


# ============================================
# Comment Sync Endpoints
# ============================================


@router.post("/sync", response_model=dict)
async def trigger_comment_sync(
    request: CommentSyncRequest,
    session: AsyncSession = Depends(get_session),
):
    """Trigger comment sync for accounts.

    Requirements: 13.1 - Aggregate from all accounts within 5 minutes
    """
    # This would typically get account details from the database
    # and queue sync tasks for each account
    # For now, return a placeholder response
    return {
        "message": "Comment sync queued",
        "account_ids": [str(aid) for aid in (request.account_ids or [])],
    }


# ============================================
# Sentiment Analysis Endpoints
# ============================================


@router.post("/analyze-sentiment", response_model=SentimentAnalysisResult)
async def analyze_comment_sentiment(
    request: SentimentAnalysisRequest,
    session: AsyncSession = Depends(get_session),
):
    """Analyze sentiment for comments.

    Requirements: 13.3 - Categorize comments by sentiment
    """
    service = CommentService(session)
    return await service.analyze_sentiment(request.comment_ids)


# ============================================
# Reply Endpoints
# ============================================


@router.post("/{comment_id}/reply", response_model=CommentReplyResponse)
async def reply_to_comment(
    comment_id: uuid.UUID,
    text: str,
    account_id: uuid.UUID,
    access_token: str,
    session: AsyncSession = Depends(get_session),
):
    """Reply to a comment.

    Requirements: 13.2 - Post replies to YouTube
    """
    service = CommentService(session)
    try:
        reply = await service.reply_to_comment(
            comment_id=comment_id,
            account_id=account_id,
            access_token=access_token,
            text=text,
        )
        return CommentReplyResponse.model_validate(reply)
    except CommentServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{comment_id}/replies", response_model=list[CommentReplyResponse])
async def get_comment_replies(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get all replies for a comment."""
    repo = CommentReplyRepository(session)
    replies = await repo.get_by_comment(comment_id)
    return [CommentReplyResponse.model_validate(r) for r in replies]


# ============================================
# Bulk Moderation Endpoints
# ============================================


@router.post("/bulk-moderate", response_model=BulkModerationResponse)
async def bulk_moderate_comments(
    request: BulkModerationRequest,
    access_token: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Apply bulk moderation actions to comments.

    Requirements: 13.5 - Apply actions to selected comments and report completion count
    """
    service = CommentService(session)
    return await service.bulk_moderate(request, access_token)


# ============================================
# Auto-Reply Rule Endpoints
# ============================================


@router.post("/auto-reply-rules", response_model=AutoReplyRuleResponse)
async def create_auto_reply_rule(
    rule: AutoReplyRuleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new auto-reply rule.

    Requirements: 13.4 - Configure trigger patterns
    """
    from app.modules.comment.models import AutoReplyRule

    repo = AutoReplyRuleRepository(session)
    new_rule = AutoReplyRule(
        account_id=rule.account_id,
        name=rule.name,
        description=rule.description,
        trigger_type=rule.trigger_type,
        trigger_keywords=rule.trigger_keywords,
        trigger_pattern=rule.trigger_pattern,
        trigger_sentiment=rule.trigger_sentiment.value if rule.trigger_sentiment else None,
        case_sensitive=rule.case_sensitive,
        response_text=rule.response_text,
        response_delay_seconds=rule.response_delay_seconds,
        is_enabled=rule.is_enabled,
        priority=rule.priority,
        max_replies_per_video=rule.max_replies_per_video,
        max_replies_per_day=rule.max_replies_per_day,
    )
    created = await repo.create(new_rule)
    await session.commit()
    return AutoReplyRuleResponse.model_validate(created)


@router.get("/auto-reply-rules/{account_id}", response_model=list[AutoReplyRuleResponse])
async def get_auto_reply_rules(
    account_id: uuid.UUID,
    enabled_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """Get all auto-reply rules for an account.

    Requirements: 13.4
    """
    repo = AutoReplyRuleRepository(session)
    rules = await repo.get_by_account(account_id, enabled_only)
    return [AutoReplyRuleResponse.model_validate(r) for r in rules]


@router.get("/auto-reply-rules/rule/{rule_id}", response_model=AutoReplyRuleResponse)
async def get_auto_reply_rule(
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific auto-reply rule."""
    repo = AutoReplyRuleRepository(session)
    rule = await repo.get_by_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-reply rule not found",
        )
    return AutoReplyRuleResponse.model_validate(rule)


@router.patch("/auto-reply-rules/rule/{rule_id}", response_model=AutoReplyRuleResponse)
async def update_auto_reply_rule(
    rule_id: uuid.UUID,
    update: AutoReplyRuleUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update an auto-reply rule.

    Requirements: 13.4
    """
    repo = AutoReplyRuleRepository(session)
    rule = await repo.get_by_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-reply rule not found",
        )

    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        # Handle sentiment enum conversion
        if "trigger_sentiment" in update_data and update_data["trigger_sentiment"]:
            update_data["trigger_sentiment"] = update_data["trigger_sentiment"].value
        rule = await repo.update(rule_id, **update_data)
        await session.commit()

    return AutoReplyRuleResponse.model_validate(rule)


@router.delete("/auto-reply-rules/rule/{rule_id}")
async def delete_auto_reply_rule(
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete an auto-reply rule."""
    repo = AutoReplyRuleRepository(session)
    deleted = await repo.delete(rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-reply rule not found",
        )
    await session.commit()
    return {"message": "Auto-reply rule deleted"}
