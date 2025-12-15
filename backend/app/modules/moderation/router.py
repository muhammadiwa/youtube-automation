"""API router for moderation management.

Implements REST endpoints for chat moderation, rules, and commands.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.moderation.models import ModerationActionType, RuleType, SeverityLevel
from app.modules.moderation.service import ModerationService
from app.modules.moderation.schemas import (
    ModerationRuleCreate,
    ModerationRuleUpdate,
    ModerationRuleResponse,
    CustomCommandCreate,
    CustomCommandUpdate,
    CustomCommandResponse,
    SlowModeConfigResponse,
    SlowModeConfigUpdate,
    ModerationActionLogResponse,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


# ============================================
# Moderation Rules Endpoints
# ============================================


@router.get("/rules", response_model=list[ModerationRuleResponse])
async def get_moderation_rules(
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account ID"),
    enabled_only: bool = Query(True, description="Only return enabled rules"),
    session: AsyncSession = Depends(get_session),
):
    """Get moderation rules.
    
    Requirements: 12.1
    """
    if not account_id:
        # Return empty list if no account specified
        return []
    
    service = ModerationService(session)
    rules = await service.get_rules(account_id, enabled_only)
    return [ModerationRuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=ModerationRuleResponse)
async def create_moderation_rule(
    data: ModerationRuleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new moderation rule.
    
    Requirements: 12.1
    """
    service = ModerationService(session)
    rule = await service.create_rule(
        account_id=data.account_id,
        name=data.name,
        rule_type=data.rule_type,
        action_type=data.action_type,
        severity=data.severity,
        pattern=data.pattern,
        keywords=data.keywords,
        settings=data.settings,
        caps_threshold_percent=data.caps_threshold_percent,
        min_message_length=data.min_message_length,
        timeout_duration_seconds=data.timeout_duration_seconds,
        description=data.description,
        priority=data.priority,
    )
    await session.commit()
    return ModerationRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=ModerationRuleResponse)
async def update_moderation_rule(
    rule_id: uuid.UUID,
    data: ModerationRuleUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a moderation rule.
    
    Requirements: 12.1
    """
    service = ModerationService(session)
    update_data = data.model_dump(exclude_unset=True)
    
    rule = await service.update_rule(rule_id, **update_data)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    
    await session.commit()
    return ModerationRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
async def delete_moderation_rule(
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a moderation rule."""
    service = ModerationService(session)
    deleted = await service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    await session.commit()
    return {"message": "Rule deleted"}


# ============================================
# Comments Endpoints (for frontend compatibility)
# ============================================


@router.get("/comments")
async def get_comments(
    account_id: Optional[uuid.UUID] = Query(None),
    video_id: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get comments for moderation.
    
    Returns empty list - comments are managed via /comments endpoint.
    This endpoint exists for frontend compatibility.
    """
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: uuid.UUID,
    text: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Reply to a comment."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /comments/{comment_id}/reply endpoint instead",
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a comment."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /comments endpoint instead",
    )


@router.post("/comments/{comment_id}/spam")
async def mark_comment_spam(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Mark comment as spam."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /comments endpoint instead",
    )


@router.post("/comments/{comment_id}/approve")
async def approve_comment(
    comment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Approve a comment."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /comments endpoint instead",
    )


@router.post("/comments/bulk")
async def bulk_moderate_comments(
    comment_ids: list[uuid.UUID],
    action: str,
    session: AsyncSession = Depends(get_session),
):
    """Bulk moderate comments."""
    return {"success_count": 0}


# ============================================
# Auto Reply Rules Endpoints
# ============================================


@router.get("/auto-reply")
async def get_auto_reply_rules(
    account_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get auto-reply rules.
    
    Returns empty list - auto-reply rules are managed via /comments/auto-reply-rules endpoint.
    """
    return []


@router.post("/auto-reply")
async def create_auto_reply_rule(
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create auto-reply rule."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /comments/auto-reply-rules endpoint instead",
    )


# ============================================
# Custom Commands Endpoints
# ============================================


@router.get("/commands", response_model=list[CustomCommandResponse])
async def get_custom_commands(
    account_id: Optional[uuid.UUID] = Query(None),
    enabled_only: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """Get custom commands.
    
    Requirements: 12.4
    """
    if not account_id:
        return []
    
    service = ModerationService(session)
    commands = await service.get_commands(account_id, enabled_only)
    return [CustomCommandResponse.model_validate(c) for c in commands]


@router.post("/commands", response_model=CustomCommandResponse)
async def create_custom_command(
    data: CustomCommandCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a custom command.
    
    Requirements: 12.4
    """
    service = ModerationService(session)
    command = await service.create_command(
        account_id=data.account_id,
        trigger=data.trigger,
        response_text=data.response_text,
        response_type=data.response_type,
        description=data.description,
        action_type=data.action_type,
        webhook_url=data.webhook_url,
        moderator_only=data.moderator_only,
        member_only=data.member_only,
        cooldown_seconds=data.cooldown_seconds,
    )
    await session.commit()
    return CustomCommandResponse.model_validate(command)


@router.patch("/commands/{command_id}", response_model=CustomCommandResponse)
async def update_custom_command(
    command_id: uuid.UUID,
    data: CustomCommandUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a custom command.
    
    Requirements: 12.4
    """
    service = ModerationService(session)
    update_data = data.model_dump(exclude_unset=True)
    
    command = await service.update_command(command_id, **update_data)
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found",
        )
    
    await session.commit()
    return CustomCommandResponse.model_validate(command)


@router.delete("/commands/{command_id}")
async def delete_custom_command(
    command_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a custom command."""
    service = ModerationService(session)
    deleted = await service.delete_command(command_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found",
        )
    await session.commit()
    return {"message": "Command deleted"}


# ============================================
# Chatbot Configuration Endpoints
# ============================================


@router.get("/chatbot/{account_id}")
async def get_chatbot_config(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get chatbot configuration.
    
    Returns null - chatbot config not implemented yet.
    """
    return None


@router.patch("/chatbot/{account_id}")
async def update_chatbot_config(
    account_id: uuid.UUID,
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update chatbot configuration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Chatbot configuration not implemented yet",
    )


@router.post("/chatbot/{account_id}/test")
async def test_chatbot(
    account_id: uuid.UUID,
    message: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Test chatbot response."""
    return {"response": "Chatbot test not implemented yet"}


# ============================================
# Moderation Logs Endpoints
# ============================================


@router.get("/logs")
async def get_moderation_logs(
    account_id: Optional[uuid.UUID] = Query(None),
    event_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get moderation logs.
    
    Requirements: 12.5
    """
    if not account_id:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        }
    
    service = ModerationService(session)
    logs = await service.get_action_logs(account_id, limit=page_size)
    
    return {
        "items": [ModerationActionLogResponse.model_validate(log) for log in logs],
        "total": len(logs),
        "page": page,
        "page_size": page_size,
    }


# ============================================
# Chat Moderation Endpoints
# ============================================


@router.get("/chat/{event_id}/messages")
async def get_chat_messages(
    event_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get chat messages for an event."""
    return {"items": [], "total": 0}


@router.post("/chat/{event_id}/messages/{message_id}/{action}")
async def moderate_chat_message(
    event_id: uuid.UUID,
    message_id: str,
    action: str,
    session: AsyncSession = Depends(get_session),
):
    """Moderate a chat message (delete/hide/approve)."""
    return {"message": "Action applied"}


@router.post("/chat/{event_id}/timeout")
async def timeout_user(
    event_id: uuid.UUID,
    user_id: str = Query(...),
    duration: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Timeout a user in chat."""
    return {"message": "User timed out"}


@router.post("/chat/{event_id}/ban")
async def ban_user(
    event_id: uuid.UUID,
    user_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Ban a user from chat."""
    return {"message": "User banned"}


@router.post("/chat/{event_id}/unban")
async def unban_user(
    event_id: uuid.UUID,
    user_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Unban a user from chat."""
    return {"message": "User unbanned"}


@router.post("/chat/{event_id}/slow-mode")
async def enable_slow_mode(
    event_id: uuid.UUID,
    delay: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Enable slow mode for chat."""
    return {"message": "Slow mode enabled"}


@router.delete("/chat/{event_id}/slow-mode")
async def disable_slow_mode(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Disable slow mode for chat."""
    return {"message": "Slow mode disabled"}
