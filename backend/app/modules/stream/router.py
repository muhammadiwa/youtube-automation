"""Stream router for live event API endpoints.

Provides REST API endpoints for live event management.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.stream.models import LiveEventStatus
from app.modules.stream.schemas import (
    CreateLiveEventRequest,
    ScheduleLiveEventRequest,
    UpdateLiveEventRequest,
    CreateRecurringEventRequest,
    LiveEventResponse,
    LiveEventWithRtmpResponse,
    LiveEventListResponse,
    StreamSessionResponse,
    RecurrencePatternResponse,
    ScheduleConflictError,
)
from app.modules.stream.service import (
    StreamService,
    AccountNotFoundError,
    LiveEventNotFoundError,
    ScheduleConflictException,
)
from app.modules.stream.youtube_api import YouTubeAPIError


router = APIRouter(prefix="/stream", tags=["stream"])


def get_stream_service(session: AsyncSession = Depends(get_db)) -> StreamService:
    """Dependency for getting stream service."""
    return StreamService(session)


@router.post(
    "/events",
    response_model=LiveEventWithRtmpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a live event",
    description="Create a new live event with optional YouTube broadcast creation.",
)
async def create_live_event(
    request: CreateLiveEventRequest,
    create_on_youtube: bool = Query(True, description="Create broadcast on YouTube"),
    service: StreamService = Depends(get_stream_service),
) -> LiveEventWithRtmpResponse:
    """Create a new live event.

    Creates a live event in the database and optionally creates
    the corresponding broadcast and stream on YouTube.

    Args:
        request: Live event creation request
        create_on_youtube: Whether to create on YouTube
        service: Stream service instance

    Returns:
        LiveEventWithRtmpResponse: Created live event with RTMP info

    Raises:
        HTTPException: If account not found or schedule conflict
    """
    try:
        event = await service.create_live_event(request, create_on_youtube)
        return LiveEventWithRtmpResponse(
            id=event.id,
            account_id=event.account_id,
            youtube_broadcast_id=event.youtube_broadcast_id,
            youtube_stream_id=event.youtube_stream_id,
            rtmp_url=event.rtmp_url,
            rtmp_key=event.rtmp_key,
            title=event.title,
            description=event.description,
            thumbnail_url=event.thumbnail_url,
            category_id=event.category_id,
            tags=event.tags,
            latency_mode=event.latency_mode,
            enable_dvr=event.enable_dvr,
            enable_auto_start=event.enable_auto_start,
            enable_auto_stop=event.enable_auto_stop,
            privacy_status=event.privacy_status,
            made_for_kids=event.made_for_kids,
            scheduled_start_at=event.scheduled_start_at,
            scheduled_end_at=event.scheduled_end_at,
            actual_start_at=event.actual_start_at,
            actual_end_at=event.actual_end_at,
            is_recurring=event.is_recurring,
            parent_event_id=event.parent_event_id,
            status=event.status,
            last_error=event.last_error,
            peak_viewers=event.peak_viewers,
            total_chat_messages=event.total_chat_messages,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": e.message,
                "conflicting_event_id": str(e.conflicting_event.id),
                "conflicting_event_title": e.conflicting_event.title,
                "conflicting_start_at": (
                    e.conflicting_event.scheduled_start_at.isoformat()
                    if e.conflicting_event.scheduled_start_at
                    else None
                ),
            },
        )
    except YouTubeAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube API error: {e.message}",
        )


@router.post(
    "/events/schedule",
    response_model=LiveEventWithRtmpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a live event",
    description="Schedule a live event for future broadcast.",
)
async def schedule_live_event(
    request: ScheduleLiveEventRequest,
    service: StreamService = Depends(get_stream_service),
) -> LiveEventWithRtmpResponse:
    """Schedule a live event for future broadcast.

    Args:
        request: Schedule live event request
        service: Stream service instance

    Returns:
        LiveEventWithRtmpResponse: Scheduled live event with RTMP info
    """
    try:
        event = await service.schedule_live_event(request)
        return LiveEventWithRtmpResponse(
            id=event.id,
            account_id=event.account_id,
            youtube_broadcast_id=event.youtube_broadcast_id,
            youtube_stream_id=event.youtube_stream_id,
            rtmp_url=event.rtmp_url,
            rtmp_key=event.rtmp_key,
            title=event.title,
            description=event.description,
            thumbnail_url=event.thumbnail_url,
            category_id=event.category_id,
            tags=event.tags,
            latency_mode=event.latency_mode,
            enable_dvr=event.enable_dvr,
            enable_auto_start=event.enable_auto_start,
            enable_auto_stop=event.enable_auto_stop,
            privacy_status=event.privacy_status,
            made_for_kids=event.made_for_kids,
            scheduled_start_at=event.scheduled_start_at,
            scheduled_end_at=event.scheduled_end_at,
            actual_start_at=event.actual_start_at,
            actual_end_at=event.actual_end_at,
            is_recurring=event.is_recurring,
            parent_event_id=event.parent_event_id,
            status=event.status,
            last_error=event.last_error,
            peak_viewers=event.peak_viewers,
            total_chat_messages=event.total_chat_messages,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": e.message,
                "conflicting_event_id": str(e.conflicting_event.id),
                "conflicting_event_title": e.conflicting_event.title,
            },
        )
    except YouTubeAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube API error: {e.message}",
        )


@router.post(
    "/events/recurring",
    response_model=LiveEventListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a recurring live event",
    description="Create a recurring live event with future instances.",
)
async def create_recurring_event(
    request: CreateRecurringEventRequest,
    generate_count: int = Query(4, ge=1, le=52, description="Number of instances to generate"),
    service: StreamService = Depends(get_stream_service),
) -> LiveEventListResponse:
    """Create a recurring live event with future instances.

    Args:
        request: Recurring event creation request
        generate_count: Number of future instances to generate
        service: Stream service instance

    Returns:
        LiveEventListResponse: Parent event and generated child events
    """
    try:
        parent_event, child_events = await service.create_recurring_event(
            request, generate_count
        )
        all_events = [parent_event] + child_events
        return LiveEventListResponse(
            events=[
                LiveEventResponse(
                    id=e.id,
                    account_id=e.account_id,
                    youtube_broadcast_id=e.youtube_broadcast_id,
                    youtube_stream_id=e.youtube_stream_id,
                    rtmp_url=e.rtmp_url,
                    title=e.title,
                    description=e.description,
                    thumbnail_url=e.thumbnail_url,
                    category_id=e.category_id,
                    tags=e.tags,
                    latency_mode=e.latency_mode,
                    enable_dvr=e.enable_dvr,
                    enable_auto_start=e.enable_auto_start,
                    enable_auto_stop=e.enable_auto_stop,
                    privacy_status=e.privacy_status,
                    made_for_kids=e.made_for_kids,
                    scheduled_start_at=e.scheduled_start_at,
                    scheduled_end_at=e.scheduled_end_at,
                    actual_start_at=e.actual_start_at,
                    actual_end_at=e.actual_end_at,
                    is_recurring=e.is_recurring,
                    parent_event_id=e.parent_event_id,
                    status=e.status,
                    last_error=e.last_error,
                    peak_viewers=e.peak_viewers,
                    total_chat_messages=e.total_chat_messages,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                )
                for e in all_events
            ],
            total=len(all_events),
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message},
        )


@router.get(
    "/events/{event_id}",
    response_model=LiveEventWithRtmpResponse,
    summary="Get a live event",
    description="Get live event details by ID.",
)
async def get_live_event(
    event_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> LiveEventWithRtmpResponse:
    """Get live event by ID.

    Args:
        event_id: Event UUID
        service: Stream service instance

    Returns:
        LiveEventWithRtmpResponse: Live event details with RTMP info
    """
    event = await service.get_live_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    return LiveEventWithRtmpResponse(
        id=event.id,
        account_id=event.account_id,
        youtube_broadcast_id=event.youtube_broadcast_id,
        youtube_stream_id=event.youtube_stream_id,
        rtmp_url=event.rtmp_url,
        rtmp_key=event.rtmp_key,
        title=event.title,
        description=event.description,
        thumbnail_url=event.thumbnail_url,
        category_id=event.category_id,
        tags=event.tags,
        latency_mode=event.latency_mode,
        enable_dvr=event.enable_dvr,
        enable_auto_start=event.enable_auto_start,
        enable_auto_stop=event.enable_auto_stop,
        privacy_status=event.privacy_status,
        made_for_kids=event.made_for_kids,
        scheduled_start_at=event.scheduled_start_at,
        scheduled_end_at=event.scheduled_end_at,
        actual_start_at=event.actual_start_at,
        actual_end_at=event.actual_end_at,
        is_recurring=event.is_recurring,
        parent_event_id=event.parent_event_id,
        status=event.status,
        last_error=event.last_error,
        peak_viewers=event.peak_viewers,
        total_chat_messages=event.total_chat_messages,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.get(
    "/accounts/{account_id}/events",
    response_model=LiveEventListResponse,
    summary="List account events",
    description="Get all live events for a YouTube account.",
)
async def list_account_events(
    account_id: uuid.UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    include_past: bool = Query(False, description="Include ended/cancelled events"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: StreamService = Depends(get_stream_service),
) -> LiveEventListResponse:
    """List all live events for an account.

    Args:
        account_id: YouTube account UUID
        status_filter: Optional status filter
        include_past: Include ended/cancelled events
        limit: Maximum number of results
        offset: Number of results to skip
        service: Stream service instance

    Returns:
        LiveEventListResponse: List of live events
    """
    status_enum = None
    if status_filter:
        try:
            status_enum = LiveEventStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    events = await service.get_account_events(
        account_id=account_id,
        status=status_enum,
        include_past=include_past,
        limit=limit,
        offset=offset,
    )

    return LiveEventListResponse(
        events=[
            LiveEventResponse(
                id=e.id,
                account_id=e.account_id,
                youtube_broadcast_id=e.youtube_broadcast_id,
                youtube_stream_id=e.youtube_stream_id,
                rtmp_url=e.rtmp_url,
                title=e.title,
                description=e.description,
                thumbnail_url=e.thumbnail_url,
                category_id=e.category_id,
                tags=e.tags,
                latency_mode=e.latency_mode,
                enable_dvr=e.enable_dvr,
                enable_auto_start=e.enable_auto_start,
                enable_auto_stop=e.enable_auto_stop,
                privacy_status=e.privacy_status,
                made_for_kids=e.made_for_kids,
                scheduled_start_at=e.scheduled_start_at,
                scheduled_end_at=e.scheduled_end_at,
                actual_start_at=e.actual_start_at,
                actual_end_at=e.actual_end_at,
                is_recurring=e.is_recurring,
                parent_event_id=e.parent_event_id,
                status=e.status,
                last_error=e.last_error,
                peak_viewers=e.peak_viewers,
                total_chat_messages=e.total_chat_messages,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in events
        ],
        total=len(events),
    )


@router.put(
    "/events/{event_id}",
    response_model=LiveEventResponse,
    summary="Update a live event",
    description="Update live event details.",
)
async def update_live_event(
    event_id: uuid.UUID,
    request: UpdateLiveEventRequest,
    update_on_youtube: bool = Query(True, description="Update on YouTube"),
    service: StreamService = Depends(get_stream_service),
) -> LiveEventResponse:
    """Update a live event.

    Args:
        event_id: Event UUID
        request: Update request
        update_on_youtube: Whether to update on YouTube
        service: Stream service instance

    Returns:
        LiveEventResponse: Updated live event
    """
    try:
        event = await service.update_live_event(event_id, request, update_on_youtube)
        return LiveEventResponse(
            id=event.id,
            account_id=event.account_id,
            youtube_broadcast_id=event.youtube_broadcast_id,
            youtube_stream_id=event.youtube_stream_id,
            rtmp_url=event.rtmp_url,
            title=event.title,
            description=event.description,
            thumbnail_url=event.thumbnail_url,
            category_id=event.category_id,
            tags=event.tags,
            latency_mode=event.latency_mode,
            enable_dvr=event.enable_dvr,
            enable_auto_start=event.enable_auto_start,
            enable_auto_stop=event.enable_auto_stop,
            privacy_status=event.privacy_status,
            made_for_kids=event.made_for_kids,
            scheduled_start_at=event.scheduled_start_at,
            scheduled_end_at=event.scheduled_end_at,
            actual_start_at=event.actual_start_at,
            actual_end_at=event.actual_end_at,
            is_recurring=event.is_recurring,
            parent_event_id=event.parent_event_id,
            status=event.status,
            last_error=event.last_error,
            peak_viewers=event.peak_viewers,
            total_chat_messages=event.total_chat_messages,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
    except LiveEventNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ScheduleConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message},
        )


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a live event",
    description="Delete a live event.",
)
async def delete_live_event(
    event_id: uuid.UUID,
    delete_on_youtube: bool = Query(True, description="Delete on YouTube"),
    service: StreamService = Depends(get_stream_service),
) -> None:
    """Delete a live event.

    Args:
        event_id: Event UUID
        delete_on_youtube: Whether to delete on YouTube
        service: Stream service instance
    """
    try:
        await service.delete_live_event(event_id, delete_on_youtube)
    except LiveEventNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/events/{event_id}/generate-instances",
    response_model=LiveEventListResponse,
    summary="Generate recurring instances",
    description="Generate future instances for a recurring event.",
)
async def generate_recurring_instances(
    event_id: uuid.UUID,
    count: int = Query(4, ge=1, le=52, description="Number of instances to generate"),
    service: StreamService = Depends(get_stream_service),
) -> LiveEventListResponse:
    """Generate future instances for a recurring event.

    Args:
        event_id: Parent event UUID
        count: Number of instances to generate
        service: Stream service instance

    Returns:
        LiveEventListResponse: Generated child events
    """
    try:
        events = await service.generate_recurring_instances(event_id, count)
        return LiveEventListResponse(
            events=[
                LiveEventResponse(
                    id=e.id,
                    account_id=e.account_id,
                    youtube_broadcast_id=e.youtube_broadcast_id,
                    youtube_stream_id=e.youtube_stream_id,
                    rtmp_url=e.rtmp_url,
                    title=e.title,
                    description=e.description,
                    thumbnail_url=e.thumbnail_url,
                    category_id=e.category_id,
                    tags=e.tags,
                    latency_mode=e.latency_mode,
                    enable_dvr=e.enable_dvr,
                    enable_auto_start=e.enable_auto_start,
                    enable_auto_stop=e.enable_auto_stop,
                    privacy_status=e.privacy_status,
                    made_for_kids=e.made_for_kids,
                    scheduled_start_at=e.scheduled_start_at,
                    scheduled_end_at=e.scheduled_end_at,
                    actual_start_at=e.actual_start_at,
                    actual_end_at=e.actual_end_at,
                    is_recurring=e.is_recurring,
                    parent_event_id=e.parent_event_id,
                    status=e.status,
                    last_error=e.last_error,
                    peak_viewers=e.peak_viewers,
                    total_chat_messages=e.total_chat_messages,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                )
                for e in events
            ],
            total=len(events),
        )
    except LiveEventNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
