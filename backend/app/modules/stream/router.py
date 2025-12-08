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
    CreatePlaylistRequest,
    UpdatePlaylistRequest,
    PlaylistItemCreate,
    PlaylistItemUpdate,
    PlaylistResponse,
    PlaylistWithItemsResponse,
    PlaylistItemResponse,
    PlaylistStreamStatus,
    ReorderPlaylistRequest,
)
from app.modules.stream.service import (
    StreamService,
    AccountNotFoundError,
    LiveEventNotFoundError,
    ScheduleConflictException,
    StreamServiceError,
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


# ============================================
# Playlist Endpoints (Requirements: 7.1, 7.2, 7.3, 7.4, 7.5)
# ============================================


@router.post(
    "/playlists",
    response_model=PlaylistWithItemsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a playlist stream",
    description="Create a playlist for streaming videos in sequence with loop support.",
)
async def create_playlist(
    request: CreatePlaylistRequest,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistWithItemsResponse:
    """Create a playlist stream for a live event.

    Requirements: 7.1, 7.2, 7.3

    Args:
        request: Playlist creation request
        service: Stream service instance

    Returns:
        PlaylistWithItemsResponse: Created playlist with items
    """
    try:
        playlist = await service.create_playlist_stream(request)
        # Reload with items
        playlist = await service.get_playlist(playlist.id, include_items=True)
        
        items = []
        if playlist.items:
            for item in playlist.items:
                items.append(PlaylistItemResponse(
                    id=item.id,
                    playlist_id=item.playlist_id,
                    video_id=item.video_id,
                    video_url=item.video_url,
                    video_title=item.video_title,
                    video_duration_seconds=item.video_duration_seconds,
                    position=item.position,
                    transition_type=item.transition_type,
                    transition_duration_ms=item.transition_duration_ms,
                    start_offset_seconds=item.start_offset_seconds,
                    end_offset_seconds=item.end_offset_seconds,
                    status=item.status,
                    play_count=item.play_count,
                    last_played_at=item.last_played_at,
                    last_error=item.last_error,
                    effective_duration=item.get_effective_duration(),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                ))
        
        return PlaylistWithItemsResponse(
            id=playlist.id,
            live_event_id=playlist.live_event_id,
            name=playlist.name,
            loop_mode=playlist.loop_mode,
            loop_count=playlist.loop_count,
            current_loop=playlist.current_loop,
            default_transition=playlist.default_transition,
            default_transition_duration_ms=playlist.default_transition_duration_ms,
            current_item_index=playlist.current_item_index,
            is_active=playlist.is_active,
            total_plays=playlist.total_plays,
            total_skips=playlist.total_skips,
            total_failures=playlist.total_failures,
            total_items=len(items),
            items=items,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
        )
    except LiveEventNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/playlists/{playlist_id}",
    response_model=PlaylistWithItemsResponse,
    summary="Get a playlist",
    description="Get playlist details with all items.",
)
async def get_playlist(
    playlist_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistWithItemsResponse:
    """Get playlist by ID.

    Args:
        playlist_id: Playlist UUID
        service: Stream service instance

    Returns:
        PlaylistWithItemsResponse: Playlist with items
    """
    playlist = await service.get_playlist(playlist_id, include_items=True)
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist {playlist_id} not found",
        )

    items = []
    if playlist.items:
        for item in playlist.items:
            items.append(PlaylistItemResponse(
                id=item.id,
                playlist_id=item.playlist_id,
                video_id=item.video_id,
                video_url=item.video_url,
                video_title=item.video_title,
                video_duration_seconds=item.video_duration_seconds,
                position=item.position,
                transition_type=item.transition_type,
                transition_duration_ms=item.transition_duration_ms,
                start_offset_seconds=item.start_offset_seconds,
                end_offset_seconds=item.end_offset_seconds,
                status=item.status,
                play_count=item.play_count,
                last_played_at=item.last_played_at,
                last_error=item.last_error,
                effective_duration=item.get_effective_duration(),
                created_at=item.created_at,
                updated_at=item.updated_at,
            ))

    return PlaylistWithItemsResponse(
        id=playlist.id,
        live_event_id=playlist.live_event_id,
        name=playlist.name,
        loop_mode=playlist.loop_mode,
        loop_count=playlist.loop_count,
        current_loop=playlist.current_loop,
        default_transition=playlist.default_transition,
        default_transition_duration_ms=playlist.default_transition_duration_ms,
        current_item_index=playlist.current_item_index,
        is_active=playlist.is_active,
        total_plays=playlist.total_plays,
        total_skips=playlist.total_skips,
        total_failures=playlist.total_failures,
        total_items=len(items),
        items=items,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


@router.get(
    "/events/{event_id}/playlist",
    response_model=PlaylistWithItemsResponse,
    summary="Get event playlist",
    description="Get playlist for a live event.",
)
async def get_event_playlist(
    event_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistWithItemsResponse:
    """Get playlist for a live event.

    Args:
        event_id: Live event UUID
        service: Stream service instance

    Returns:
        PlaylistWithItemsResponse: Playlist with items
    """
    playlist = await service.get_playlist_by_event(event_id, include_items=True)
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist not found for event {event_id}",
        )

    items = []
    if playlist.items:
        for item in playlist.items:
            items.append(PlaylistItemResponse(
                id=item.id,
                playlist_id=item.playlist_id,
                video_id=item.video_id,
                video_url=item.video_url,
                video_title=item.video_title,
                video_duration_seconds=item.video_duration_seconds,
                position=item.position,
                transition_type=item.transition_type,
                transition_duration_ms=item.transition_duration_ms,
                start_offset_seconds=item.start_offset_seconds,
                end_offset_seconds=item.end_offset_seconds,
                status=item.status,
                play_count=item.play_count,
                last_played_at=item.last_played_at,
                last_error=item.last_error,
                effective_duration=item.get_effective_duration(),
                created_at=item.created_at,
                updated_at=item.updated_at,
            ))

    return PlaylistWithItemsResponse(
        id=playlist.id,
        live_event_id=playlist.live_event_id,
        name=playlist.name,
        loop_mode=playlist.loop_mode,
        loop_count=playlist.loop_count,
        current_loop=playlist.current_loop,
        default_transition=playlist.default_transition,
        default_transition_duration_ms=playlist.default_transition_duration_ms,
        current_item_index=playlist.current_item_index,
        is_active=playlist.is_active,
        total_plays=playlist.total_plays,
        total_skips=playlist.total_skips,
        total_failures=playlist.total_failures,
        total_items=len(items),
        items=items,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
    )


@router.put(
    "/playlists/{playlist_id}",
    response_model=PlaylistResponse,
    summary="Update a playlist",
    description="Update playlist settings. Changes apply after current video completes.",
)
async def update_playlist(
    playlist_id: uuid.UUID,
    request: UpdatePlaylistRequest,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistResponse:
    """Update playlist settings.

    Requirements: 7.5 - Allow playlist modification during stream.
    Changes apply after current video completes.

    Args:
        playlist_id: Playlist UUID
        request: Update request
        service: Stream service instance

    Returns:
        PlaylistResponse: Updated playlist
    """
    try:
        playlist = await service.update_playlist(playlist_id, request)
        return PlaylistResponse(
            id=playlist.id,
            live_event_id=playlist.live_event_id,
            name=playlist.name,
            loop_mode=playlist.loop_mode,
            loop_count=playlist.loop_count,
            current_loop=playlist.current_loop,
            default_transition=playlist.default_transition,
            default_transition_duration_ms=playlist.default_transition_duration_ms,
            current_item_index=playlist.current_item_index,
            is_active=playlist.is_active,
            total_plays=playlist.total_plays,
            total_skips=playlist.total_skips,
            total_failures=playlist.total_failures,
            total_items=playlist.get_total_items(),
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
        )
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/playlists/{playlist_id}/items",
    response_model=PlaylistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to playlist",
    description="Add a video to the playlist. Changes apply after current video completes.",
)
async def add_playlist_item(
    playlist_id: uuid.UUID,
    item_data: PlaylistItemCreate,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistItemResponse:
    """Add item to playlist.

    Requirements: 7.1, 7.5 - Allow playlist modification during stream.

    Args:
        playlist_id: Playlist UUID
        item_data: Item creation data
        service: Stream service instance

    Returns:
        PlaylistItemResponse: Created item
    """
    try:
        item = await service.add_playlist_item(playlist_id, item_data)
        return PlaylistItemResponse(
            id=item.id,
            playlist_id=item.playlist_id,
            video_id=item.video_id,
            video_url=item.video_url,
            video_title=item.video_title,
            video_duration_seconds=item.video_duration_seconds,
            position=item.position,
            transition_type=item.transition_type,
            transition_duration_ms=item.transition_duration_ms,
            start_offset_seconds=item.start_offset_seconds,
            end_offset_seconds=item.end_offset_seconds,
            status=item.status,
            play_count=item.play_count,
            last_played_at=item.last_played_at,
            last_error=item.last_error,
            effective_duration=item.get_effective_duration(),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/playlists/items/{item_id}",
    response_model=PlaylistItemResponse,
    summary="Update playlist item",
    description="Update a playlist item. Changes apply after current video completes.",
)
async def update_playlist_item(
    item_id: uuid.UUID,
    request: PlaylistItemUpdate,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistItemResponse:
    """Update playlist item.

    Requirements: 7.5 - Allow playlist modification during stream.

    Args:
        item_id: Item UUID
        request: Update request
        service: Stream service instance

    Returns:
        PlaylistItemResponse: Updated item
    """
    try:
        item = await service.update_playlist_item(item_id, request)
        return PlaylistItemResponse(
            id=item.id,
            playlist_id=item.playlist_id,
            video_id=item.video_id,
            video_url=item.video_url,
            video_title=item.video_title,
            video_duration_seconds=item.video_duration_seconds,
            position=item.position,
            transition_type=item.transition_type,
            transition_duration_ms=item.transition_duration_ms,
            start_offset_seconds=item.start_offset_seconds,
            end_offset_seconds=item.end_offset_seconds,
            status=item.status,
            play_count=item.play_count,
            last_played_at=item.last_played_at,
            last_error=item.last_error,
            effective_duration=item.get_effective_duration(),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/playlists/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove playlist item",
    description="Remove an item from the playlist. Changes apply after current video completes.",
)
async def remove_playlist_item(
    item_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> None:
    """Remove item from playlist.

    Requirements: 7.5 - Allow playlist modification during stream.

    Args:
        item_id: Item UUID
        service: Stream service instance
    """
    try:
        await service.remove_playlist_item(item_id)
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/playlists/{playlist_id}/reorder",
    response_model=list[PlaylistItemResponse],
    summary="Reorder playlist items",
    description="Reorder playlist items. Changes apply after current video completes.",
)
async def reorder_playlist(
    playlist_id: uuid.UUID,
    request: ReorderPlaylistRequest,
    service: StreamService = Depends(get_stream_service),
) -> list[PlaylistItemResponse]:
    """Reorder playlist items.

    Requirements: 7.5 - Allow playlist modification during stream.

    Args:
        playlist_id: Playlist UUID
        request: Reorder request with item IDs in new order
        service: Stream service instance

    Returns:
        list[PlaylistItemResponse]: Reordered items
    """
    try:
        items = await service.reorder_playlist(playlist_id, request.item_ids)
        return [
            PlaylistItemResponse(
                id=item.id,
                playlist_id=item.playlist_id,
                video_id=item.video_id,
                video_url=item.video_url,
                video_title=item.video_title,
                video_duration_seconds=item.video_duration_seconds,
                position=item.position,
                transition_type=item.transition_type,
                transition_duration_ms=item.transition_duration_ms,
                start_offset_seconds=item.start_offset_seconds,
                end_offset_seconds=item.end_offset_seconds,
                status=item.status,
                play_count=item.play_count,
                last_played_at=item.last_played_at,
                last_error=item.last_error,
                effective_duration=item.get_effective_duration(),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ]
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/playlists/{playlist_id}/start",
    response_model=PlaylistStreamStatus,
    summary="Start playlist streaming",
    description="Start streaming the playlist from the beginning.",
)
async def start_playlist_stream(
    playlist_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistStreamStatus:
    """Start streaming a playlist.

    Requirements: 7.1, 7.2

    Args:
        playlist_id: Playlist UUID
        service: Stream service instance

    Returns:
        PlaylistStreamStatus: Current stream status
    """
    try:
        return await service.start_playlist_stream(playlist_id)
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/playlists/{playlist_id}/advance",
    response_model=PlaylistStreamStatus,
    summary="Advance to next item",
    description="Advance playlist to the next item. Handles loop logic and skip on failure.",
)
async def advance_playlist(
    playlist_id: uuid.UUID,
    skip_on_failure: bool = Query(False, description="Whether current item failed"),
    failure_error: str = Query(None, description="Error message if failed"),
    service: StreamService = Depends(get_stream_service),
) -> PlaylistStreamStatus:
    """Advance playlist to next item.

    Requirements: 7.2, 7.4 - Loop logic and skip on failure.

    Args:
        playlist_id: Playlist UUID
        skip_on_failure: Whether current item failed
        failure_error: Error message if failed
        service: Stream service instance

    Returns:
        PlaylistStreamStatus: Updated stream status
    """
    try:
        return await service.advance_playlist(playlist_id, skip_on_failure, failure_error)
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/playlists/{playlist_id}/stop",
    response_model=PlaylistStreamStatus,
    summary="Stop playlist streaming",
    description="Stop streaming the playlist.",
)
async def stop_playlist_stream(
    playlist_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistStreamStatus:
    """Stop playlist streaming.

    Args:
        playlist_id: Playlist UUID
        service: Stream service instance

    Returns:
        PlaylistStreamStatus: Final stream status
    """
    try:
        return await service.stop_playlist_stream(playlist_id)
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/playlists/{playlist_id}/status",
    response_model=PlaylistStreamStatus,
    summary="Get playlist status",
    description="Get current playlist streaming status.",
)
async def get_playlist_status(
    playlist_id: uuid.UUID,
    service: StreamService = Depends(get_stream_service),
) -> PlaylistStreamStatus:
    """Get current playlist streaming status.

    Args:
        playlist_id: Playlist UUID
        service: Stream service instance

    Returns:
        PlaylistStreamStatus: Current stream status
    """
    try:
        return await service.get_playlist_status(playlist_id)
    except StreamServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
