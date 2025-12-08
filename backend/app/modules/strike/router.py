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
