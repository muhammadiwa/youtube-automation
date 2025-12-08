"""Monitoring API router.

Implements REST endpoints for multi-channel monitoring dashboard.
Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.monitoring.service import MonitoringService
from app.modules.monitoring.schemas import (
    ChannelStatusFilter,
    ChannelGridResponse,
    ChannelDetailMetrics,
    LayoutPreferencesUpdate,
    LayoutPreferencesResponse,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/channels", response_model=ChannelGridResponse)
async def get_channel_grid(
    status_filter: ChannelStatusFilter = Query(
        ChannelStatusFilter.ALL,
        description="Filter channels by status"
    ),
    search: Optional[str] = Query(
        None,
        description="Search term for channel title"
    ),
    sort_by: str = Query(
        "status",
        description="Sort field (status, subscribers, views, title, quota)"
    ),
    sort_order: str = Query(
        "asc",
        pattern="^(asc|desc)$",
        description="Sort order"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get channel grid with filtering and status indicators.
    
    Returns all channels for the current user with live status indicators.
    Supports filtering by status (live, scheduled, offline, error, token_expired).
    
    Requirements: 16.1, 16.2
    """
    service = MonitoringService(db)
    
    # In production, user_id would come from auth dependency
    user_id = uuid.uuid4()  # Placeholder
    
    return await service.get_channel_grid(
        user_id=user_id,
        status_filter=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/channels/{account_id}", response_model=ChannelDetailMetrics)
async def get_channel_details(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed metrics for a specific channel.
    
    Shows detailed metrics without leaving the monitoring view.
    Includes current stream info, recent streams, scheduled streams, and issues.
    
    Requirements: 16.4
    """
    service = MonitoringService(db)
    
    details = await service.get_channel_details(account_id)
    
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    return details


@router.get("/preferences", response_model=LayoutPreferencesResponse)
async def get_layout_preferences(
    db: AsyncSession = Depends(get_db),
):
    """Get user's monitoring layout preferences.
    
    Returns saved preferences for grid size and displayed metrics.
    
    Requirements: 16.5
    """
    service = MonitoringService(db)
    
    # In production, user_id would come from auth dependency
    user_id = uuid.uuid4()  # Placeholder
    
    return await service.get_layout_preferences(user_id)


@router.put("/preferences", response_model=LayoutPreferencesResponse)
async def update_layout_preferences(
    request: LayoutPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update user's monitoring layout preferences.
    
    Saves preferences for grid size and displayed metrics.
    
    Requirements: 16.5
    """
    service = MonitoringService(db)
    
    # In production, user_id would come from auth dependency
    user_id = uuid.uuid4()  # Placeholder
    
    updates = request.model_dump(exclude_unset=True)
    
    return await service.update_layout_preferences(user_id, updates)
