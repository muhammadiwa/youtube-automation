"""API Router for User Support module."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.jwt import get_current_user
from app.modules.auth.models import User
from app.modules.support.schemas import (
    TicketCreateRequest,
    TicketMessageCreate,
    TicketMessageResponse,
    SupportTicketResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    TicketStatsResponse,
)
from app.modules.support.service import (
    UserSupportService,
    TicketNotFoundError,
    TicketAccessDeniedError,
)

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new support ticket.
    
    Users can create tickets to request help or report issues.
    """
    service = UserSupportService(session)
    return await service.create_ticket(current_user.id, data)


@router.get("/tickets", response_model=SupportTicketListResponse)
async def get_tickets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get list of user's support tickets.
    
    Returns paginated list of tickets with optional status filter.
    """
    service = UserSupportService(session)
    return await service.get_tickets(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/tickets/stats", response_model=TicketStatsResponse)
async def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get ticket statistics for current user."""
    service = UserSupportService(session)
    return await service.get_stats(current_user.id)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
async def get_ticket_detail(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed ticket information with messages.
    
    Returns full ticket details including conversation history.
    """
    service = UserSupportService(session)
    
    try:
        return await service.get_ticket_detail(current_user.id, ticket_id)
    except TicketNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TicketAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/tickets/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    ticket_id: uuid.UUID,
    data: TicketMessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a message to a ticket.
    
    Users can reply to their tickets to provide more information.
    """
    service = UserSupportService(session)
    
    try:
        return await service.add_message(current_user.id, ticket_id, data)
    except TicketNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TicketAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))



# ============ WebSocket Endpoints ============

from fastapi import WebSocket, WebSocketDisconnect
from app.modules.support.websocket import support_ws_manager, get_debug_state


@router.get("/ws/debug")
async def websocket_debug():
    """Debug endpoint to check WebSocket state."""
    return get_debug_state()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
):
    """WebSocket endpoint for real-time support updates.
    
    Users connect to receive real-time notifications about:
    - New messages on their tickets
    - Status changes on their tickets
    
    Message format:
    {
        "type": "new_message" | "status_change",
        "ticket_id": "uuid",
        "payload": {...},
        "timestamp": "ISO datetime"
    }
    """
    await support_ws_manager.connect_user(websocket, user_id)
    
    try:
        while True:
            # Receive messages from client (for subscriptions, ping, etc.)
            data = await websocket.receive_json()
            
            if data.get("type") == "subscribe":
                ticket_id = data.get("ticket_id")
                if ticket_id:
                    support_ws_manager.subscribe_to_ticket(ticket_id, user_id, is_admin=False)
                    await websocket.send_json({
                        "type": "subscribed",
                        "ticket_id": ticket_id,
                    })
            
            elif data.get("type") == "unsubscribe":
                ticket_id = data.get("ticket_id")
                if ticket_id:
                    support_ws_manager.unsubscribe_from_ticket(ticket_id, user_id, is_admin=False)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "ticket_id": ticket_id,
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        # Clean up subscriptions for this user
        for ticket_id in list(support_ws_manager.ticket_subscriptions.keys()):
            support_ws_manager.unsubscribe_from_ticket(ticket_id, user_id, is_admin=False)
        support_ws_manager.disconnect_user(websocket, user_id)
        print(f"[SupportWS] User {user_id} disconnected and cleaned up")
