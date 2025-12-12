"""API router for strike management endpoints.

Implements REST API endpoints for strike tracking and management.
Requirements: 20.1, 20.2, 20.3, 20.4, 20.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.modules.strike.service import (
    StrikeService,
    StrikeServiceError,
    AccountNotFoundError,
    StrikeNotFoundError,
)
from app.modules.strike.schemas import (
    StrikeCreate,
    StrikeUpdate,
    StrikeResponse,
    StrikeListResponse,
    StrikeSummary,
    StrikeAlertResponse,
    StrikeAlertAcknowledge,
    PausedStreamResponse,
    PausedStreamListResponse,
    ResumeStreamRequest,
    StrikeSyncResult,
    StrikeTimeline,
    AccountStrikeTimeline,
)
from app.modules.strike.models import StrikeStatus, AppealStatus
from app.modules.strike.tasks import (
    sync_account_strikes,
    check_and_alert_strikes,
    process_new_strike,
)

router = APIRouter(prefix="/strikes", tags=["strikes"])


# ============================================
# Strike Endpoints
# ============================================

@router.get("/account/{account_id}", response_model=StrikeListResponse)
async def get_account_strikes(
    account_id: uuid.UUID,
    include_expired: bool = False,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all strikes for a YouTube account.

    Requirements: 20.1, 20.4
    """
    service = StrikeService(session)
    try:
        strikes = await service.get_account_strikes(account_id, include_expired)
        active_count = sum(1 for s in strikes if s.status == StrikeStatus.ACTIVE.value)
        return StrikeListResponse(
            strikes=[StrikeResponse.model_validate(s) for s in strikes],
            total=len(strikes),
            active_count=active_count,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/account/{account_id}/summary", response_model=StrikeSummary)
async def get_account_strike_summary(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get strike summary for a YouTube account.

    Requirements: 20.1
    """
    service = StrikeService(session)
    try:
        return await service.get_strike_summary(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/account/{account_id}/timeline", response_model=AccountStrikeTimeline)
async def get_account_strike_timeline(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get strike timeline for a YouTube account.

    Requirements: 20.4
    """
    service = StrikeService(session)
    try:
        return await service.get_account_strike_timeline(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{strike_id}", response_model=StrikeResponse)
async def get_strike(
    strike_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get strike by ID.

    Requirements: 20.1
    """
    service = StrikeService(session)
    strike = await service.get_strike(strike_id)
    if not strike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strike {strike_id} not found",
        )
    return StrikeResponse.model_validate(strike)


@router.get("/{strike_id}/timeline", response_model=StrikeTimeline)
async def get_strike_timeline(
    strike_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get timeline for a specific strike.

    Requirements: 20.4
    """
    service = StrikeService(session)
    try:
        return await service.get_strike_timeline(strike_id)
    except StrikeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=StrikeResponse, status_code=status.HTTP_201_CREATED)
async def create_strike(
    request: StrikeCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new strike record (manual entry).

    Requirements: 20.1
    """
    service = StrikeService(session)
    try:
        strike = await service.create_strike(request)
        # Queue background processing
        process_new_strike.delay(str(strike.id))
        return StrikeResponse.model_validate(strike)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================
# Strike Sync Endpoints
# ============================================

@router.post("/account/{account_id}/sync", response_model=StrikeSyncResult)
async def sync_strikes(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Sync strike status from YouTube for an account.

    Requirements: 20.1
    """
    service = StrikeService(session)
    try:
        result = await service.sync_strikes(account_id)
        # Queue alert check
        check_and_alert_strikes.delay(str(account_id))
        return result
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/account/{account_id}/sync/async")
async def sync_strikes_async(account_id: uuid.UUID):
    """Queue strike sync for an account (async).

    Requirements: 20.1
    """
    task = sync_account_strikes.delay(str(account_id))
    return {"task_id": task.id, "status": "queued"}


# ============================================
# Appeal Endpoints
# ============================================

@router.post("/{strike_id}/appeal", response_model=StrikeResponse)
async def submit_appeal(
    strike_id: uuid.UUID,
    appeal_reason: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Submit an appeal for a strike.

    Requirements: 20.4
    """
    service = StrikeService(session)
    try:
        strike = await service.submit_appeal(strike_id, appeal_reason)
        return StrikeResponse.model_validate(strike)
    except StrikeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StrikeServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{strike_id}/appeal", response_model=StrikeResponse)
async def update_appeal_status(
    strike_id: uuid.UUID,
    appeal_status: AppealStatus,
    appeal_response: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
):
    """Update appeal status for a strike.

    Requirements: 20.4
    """
    service = StrikeService(session)
    try:
        strike = await service.update_appeal_status(
            strike_id, appeal_status, appeal_response
        )
        return StrikeResponse.model_validate(strike)
    except StrikeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================
# Paused Streams Endpoints
# ============================================

@router.get("/account/{account_id}/paused-streams", response_model=PausedStreamListResponse)
async def get_paused_streams(
    account_id: uuid.UUID,
    include_resumed: bool = False,
    session: AsyncSession = Depends(get_async_session),
):
    """Get paused streams for an account.

    Requirements: 20.3, 20.5
    """
    service = StrikeService(session)
    paused_streams = await service.get_paused_streams(account_id, include_resumed)
    return PausedStreamListResponse(
        paused_streams=[PausedStreamResponse.model_validate(ps) for ps in paused_streams],
        total=len(paused_streams),
    )


@router.post("/paused-streams/{paused_stream_id}/resume", response_model=PausedStreamResponse)
async def resume_paused_stream(
    paused_stream_id: uuid.UUID,
    request: ResumeStreamRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Resume a paused stream with user confirmation.

    Requirements: 20.5
    """
    service = StrikeService(session)
    try:
        paused_stream = await service.resume_paused_stream(
            paused_stream_id, request.user_id, request.confirmation
        )
        return PausedStreamResponse.model_validate(paused_stream)
    except StrikeServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/account/{account_id}/paused-streams/resume-all", response_model=PausedStreamListResponse)
async def resume_all_paused_streams(
    account_id: uuid.UUID,
    request: ResumeStreamRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Resume all paused streams for an account.

    Requirements: 20.5
    """
    service = StrikeService(session)
    try:
        resumed_streams = await service.resume_all_paused_streams(
            account_id, request.user_id, request.confirmation
        )
        return PausedStreamListResponse(
            paused_streams=[PausedStreamResponse.model_validate(ps) for ps in resumed_streams],
            total=len(resumed_streams),
        )
    except StrikeServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================
# Alert Endpoints
# ============================================

@router.get("/alerts")
async def get_all_alerts(
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 10,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all strike alerts for the current user.

    Requirements: 20.2
    """
    service = StrikeService(session)
    # Get alerts - if unread_only, filter by acknowledged=False
    acknowledged = False if unread_only else None
    alerts = await service.alert_repository.get_all(
        acknowledged=acknowledged,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    total = await service.alert_repository.count_all(acknowledged=acknowledged)
    unread_count = await service.alert_repository.count_all(acknowledged=False)
    
    return {
        "items": [StrikeAlertResponse.model_validate(a) for a in alerts],
        "total": total,
        "unread_count": unread_count,
    }


@router.post("/alerts/{alert_id}/read", response_model=StrikeAlertResponse)
async def mark_alert_as_read(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Mark a strike alert as read.

    Requirements: 20.2
    """
    from datetime import datetime
    
    service = StrikeService(session)
    alert = await service.alert_repository.get_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    await service.session.commit()
    await service.session.refresh(alert)
    return StrikeAlertResponse.model_validate(alert)


@router.post("/alerts/read-all")
async def mark_all_alerts_as_read(
    session: AsyncSession = Depends(get_async_session),
):
    """Mark all strike alerts as read.

    Requirements: 20.2
    """
    service = StrikeService(session)
    await service.alert_repository.mark_all_as_read()
    await service.session.commit()
    return {"success": True}


@router.delete("/alerts/{alert_id}")
async def dismiss_alert(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Dismiss/delete a strike alert.

    Requirements: 20.2
    """
    service = StrikeService(session)
    alert = await service.alert_repository.get_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    await service.alert_repository.delete(alert)
    await service.session.commit()
    return {"success": True}


@router.get("/account/{account_id}/alerts", response_model=list[StrikeAlertResponse])
async def get_account_alerts(
    account_id: uuid.UUID,
    acknowledged: Optional[bool] = None,
    session: AsyncSession = Depends(get_async_session),
):
    """Get strike alerts for an account.

    Requirements: 20.2
    """
    service = StrikeService(session)
    alerts = await service.alert_repository.get_by_account_id(
        account_id, acknowledged=acknowledged
    )
    return [StrikeAlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge", response_model=StrikeAlertResponse)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    request: StrikeAlertAcknowledge,
    session: AsyncSession = Depends(get_async_session),
):
    """Acknowledge a strike alert.

    Requirements: 20.2
    """
    service = StrikeService(session)
    alert = await service.alert_repository.get_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    alert = await service.alert_repository.acknowledge(alert, request.user_id)
    await service.session.commit()
    return StrikeAlertResponse.model_validate(alert)
