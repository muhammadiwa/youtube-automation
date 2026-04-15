"""Public API Router for announcements and terms of service.

Requirements: 10.5 - Display banner in user dashboard with dismiss option
Requirements: 15.4 - Terms of Service versioning and display
"""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.modules.admin.models import Announcement, TermsOfService, TermsOfServiceStatus


router = APIRouter(tags=["public"])


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


# ==================== Terms of Service Public Endpoints ====================


class PublicTermsOfServiceResponse(BaseModel):
    """Public terms of service response for client display."""
    id: str
    version: str
    title: str
    content: str
    content_html: Optional[str] = None
    summary: Optional[str] = None
    effective_date: Optional[datetime] = None
    activated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/terms-of-service", response_model=PublicTermsOfServiceResponse)
async def get_active_terms_of_service(
    session: AsyncSession = Depends(get_session),
):
    """Get the currently active terms of service.
    
    Requirements: 15.4 - Display active terms of service to users
    
    This endpoint is public and returns the currently active ToS version.
    """
    # Get the active terms of service
    query = select(TermsOfService).where(
        TermsOfService.status == TermsOfServiceStatus.ACTIVE.value
    )
    
    result = await session.execute(query)
    terms = result.scalar_one_or_none()
    
    if not terms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active terms of service found",
        )
    
    return PublicTermsOfServiceResponse(
        id=str(terms.id),
        version=terms.version,
        title=terms.title,
        content=terms.content,
        content_html=terms.content_html,
        summary=terms.summary,
        effective_date=terms.effective_date,
        activated_at=terms.activated_at,
    )


@router.get("/terms-of-service/{version}", response_model=PublicTermsOfServiceResponse)
async def get_terms_of_service_by_version(
    version: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific version of terms of service.
    
    Requirements: 15.4 - Allow users to view specific ToS versions
    
    Only active or archived versions can be viewed publicly.
    """
    # Get the terms of service by version (only active or archived)
    query = select(TermsOfService).where(
        and_(
            TermsOfService.version == version,
            TermsOfService.status.in_([
                TermsOfServiceStatus.ACTIVE.value,
                TermsOfServiceStatus.ARCHIVED.value,
            ])
        )
    )
    
    result = await session.execute(query)
    terms = result.scalar_one_or_none()
    
    if not terms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terms of service version '{version}' not found",
        )
    
    return PublicTermsOfServiceResponse(
        id=str(terms.id),
        version=terms.version,
        title=terms.title,
        content=terms.content,
        content_html=terms.content_html,
        summary=terms.summary,
        effective_date=terms.effective_date,
        activated_at=terms.activated_at,
    )
