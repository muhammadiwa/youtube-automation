"""Public API Router for announcements.

Requirements: 10.5 - Display banner in user dashboard with dismiss option
"""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.modules.admin.models import Announcement


router = APIRouter(tags=["announcements"])


class PublicAnnouncementResponse(BaseModel):
    """Public announcement response for client display."""
    id: str
    title: str
    content: str
    announcement_type: str
    is_dismissible: bool

    class Config:
        from_attributes = True


class PublicAnnouncementListResponse(BaseModel):
    """List of active announcements for client."""
    items: List[PublicAnnouncementResponse]


@router.get("/announcements/active", response_model=PublicAnnouncementListResponse)
async def get_active_announcements(
    plan: Optional[str] = Query(None, description="User's subscription plan"),
    session: AsyncSession = Depends(get_session),
):
    """Get active announcements for display in user dashboard.
    
    Requirements: 10.5 - Display banner in user dashboard with dismiss option
    
    This endpoint is public and returns only active, visible announcements.
    """
    now = datetime.now(timezone.utc)
    
    # Build query for active announcements
    query = select(Announcement).where(
        and_(
            Announcement.is_active == True,
            # Start date must be in the past or now
            Announcement.start_date <= now,
            # End date must be in the future or null
            (Announcement.end_date == None) | (Announcement.end_date >= now),
        )
    ).order_by(Announcement.created_at.desc())
    
    result = await session.execute(query)
    announcements = result.scalars().all()
    
    # Filter by plan if specified
    items = []
    for ann in announcements:
        # If target_plans is set, check if user's plan is included
        if ann.target_plans and plan:
            if plan not in ann.target_plans:
                continue
        elif ann.target_plans and not plan:
            # If announcement targets specific plans but user has no plan, skip
            continue
        
        items.append(PublicAnnouncementResponse(
            id=str(ann.id),
            title=ann.title,
            content=ann.content,
            announcement_type=ann.announcement_type,
            is_dismissible=ann.is_dismissible,
        ))
    
    return PublicAnnouncementListResponse(items=items)
