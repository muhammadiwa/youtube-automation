"""Monitoring API router - Live Control Center.

REST endpoints for real-time monitoring of YouTube channels and streams.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.jwt import get_current_user
from app.modules.auth.models import User
from app.modules.monitoring.service import MonitoringService
from app.modules.monitoring.schemas import (
    MonitoringDashboardResponse,
    LiveStreamsResponse,
    ScheduledStreamsResponse,
    ChannelStatusInfo,
    Alert,
    MonitoringOverview,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard", response_model=MonitoringDashboardResponse)
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete monitoring dashboard data.
    
    Returns overview stats, live streams, scheduled streams, channel statuses, and alerts.
    All data is real-time from the database.
    """
    service = MonitoringService(db)
    return await service.get_dashboard(current_user.id)


@router.get("/overview", response_model=MonitoringOverview)
async def get_monitoring_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get monitoring overview statistics only.
    
    Lightweight endpoint for quick stats refresh.
    """
    service = MonitoringService(db)
    dashboard = await service.get_dashboard(current_user.id)
    return dashboard.overview


@router.get("/live", response_model=LiveStreamsResponse)
async def get_live_streams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all currently live streams.
    
    Returns list of live streams with viewer counts and metrics.
    """
    service = MonitoringService(db)
    return await service.get_live_streams(current_user.id)


@router.get("/scheduled", response_model=ScheduledStreamsResponse)
async def get_scheduled_streams(
    days_ahead: int = Query(7, ge=1, le=30, description="Days ahead to look"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scheduled streams.
    
    Returns list of upcoming scheduled streams with countdown timers.
    """
    service = MonitoringService(db)
    return await service.get_scheduled_streams(current_user.id, days_ahead)


@router.get("/channels/{account_id}", response_model=ChannelStatusInfo)
async def get_channel_status(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get status for a specific channel.
    
    Returns detailed status including current stream, next scheduled, and alerts.
    """
    service = MonitoringService(db)
    channel_status = await service.get_channel_status(account_id, current_user.id)
    
    if not channel_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
    
    return channel_status


@router.get("/alerts", response_model=list[Alert])
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active alerts.
    
    Returns alerts sorted by severity (critical first).
    """
    service = MonitoringService(db)
    return await service.get_alerts(current_user.id)
