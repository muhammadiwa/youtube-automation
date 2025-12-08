"""Repository for strike data access.

Implements data access patterns for Strike, StrikeAlert, and PausedStream models.
Requirements: 20.1, 20.2, 20.3, 20.4, 20.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.strike.models import (
    Strike,
    StrikeAlert,
    PausedStream,
    StrikeStatus,
    AppealStatus,
)


class StrikeRepository:
    """Repository for Strike model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        account_id: uuid.UUID,
        strike_type: str,
        severity: str,
        reason: str,
        issued_at: datetime,
        youtube_strike_id: Optional[str] = None,
        reason_details: Optional[str] = None,
        affected_video_id: Optional[str] = None,
        affected_video_title: Optional[str] = None,
        affected_content_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        extra_data: Optional[dict] = None,
    ) -> Strike:
        """Create a new strike record."""
        strike = Strike(
            account_id=account_id,
            youtube_strike_id=youtube_strike_id,
            strike_type=strike_type,
            severity=severity,
            reason=reason,
            reason_details=reason_details,
            affected_video_id=affected_video_id,
            affected_video_title=affected_video_title,
            affected_content_url=affected_content_url,
            issued_at=issued_at,
            expires_at=expires_at,
            extra_data=extra_data,
        )
        self.session.add(strike)
        await self.session.flush()
        return strike

    async def get_by_id(
        self, strike_id: uuid.UUID, include_alerts: bool = False
    ) -> Optional[Strike]:
        """Get strike by ID."""
        query = select(Strike).where(Strike.id == strike_id)
        if include_alerts:
            query = query.options(selectinload(Strike.alerts))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_youtube_id(self, youtube_strike_id: str) -> Optional[Strike]:
        """Get strike by YouTube strike ID."""
        query = select(Strike).where(Strike.youtube_strike_id == youtube_strike_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        status: Optional[StrikeStatus] = None,
        include_expired: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Strike]:
        """Get all strikes for an account."""
        query = select(Strike).where(Strike.account_id == account_id)
        
        if status:
            query = query.where(Strike.status == status.value)
        
        if not include_expired:
            query = query.where(Strike.status != StrikeStatus.EXPIRED.value)
        
        query = query.order_by(Strike.issued_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_strikes(self, account_id: uuid.UUID) -> list[Strike]:
        """Get all active strikes for an account."""
        query = select(Strike).where(
            and_(
                Strike.account_id == account_id,
                Strike.status == StrikeStatus.ACTIVE.value,
            )
        ).order_by(Strike.issued_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_active_strikes(self, account_id: uuid.UUID) -> int:
        """Count active strikes for an account."""
        query = select(func.count(Strike.id)).where(
            and_(
                Strike.account_id == account_id,
                Strike.status == StrikeStatus.ACTIVE.value,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, strike: Strike, **kwargs) -> Strike:
        """Update strike fields."""
        for key, value in kwargs.items():
            if hasattr(strike, key):
                setattr(strike, key, value)
        await self.session.flush()
        return strike

    async def set_status(
        self, strike: Strike, status: StrikeStatus, resolved_at: Optional[datetime] = None
    ) -> Strike:
        """Update strike status."""
        strike.status = status.value
        if resolved_at:
            strike.resolved_at = resolved_at
        elif status in [StrikeStatus.RESOLVED, StrikeStatus.EXPIRED]:
            strike.resolved_at = datetime.utcnow()
        await self.session.flush()
        return strike

    async def set_appeal_status(
        self,
        strike: Strike,
        appeal_status: AppealStatus,
        appeal_reason: Optional[str] = None,
        appeal_response: Optional[str] = None,
    ) -> Strike:
        """Update strike appeal status."""
        strike.appeal_status = appeal_status.value
        
        if appeal_status == AppealStatus.PENDING:
            strike.appeal_submitted_at = datetime.utcnow()
            if appeal_reason:
                strike.appeal_reason = appeal_reason
        
        if appeal_status in [AppealStatus.APPROVED, AppealStatus.REJECTED]:
            strike.appeal_resolved_at = datetime.utcnow()
            if appeal_response:
                strike.appeal_response = appeal_response
            
            if appeal_status == AppealStatus.APPROVED:
                strike.status = StrikeStatus.RESOLVED.value
                strike.resolved_at = datetime.utcnow()
        
        await self.session.flush()
        return strike

    async def mark_notification_sent(self, strike: Strike) -> Strike:
        """Mark strike notification as sent."""
        strike.notification_sent = True
        strike.notification_sent_at = datetime.utcnow()
        await self.session.flush()
        return strike

    async def mark_streams_paused(self, strike: Strike) -> Strike:
        """Mark that streams have been paused for this strike."""
        strike.streams_paused = True
        strike.streams_paused_at = datetime.utcnow()
        await self.session.flush()
        return strike

    async def mark_streams_resumed(self, strike: Strike) -> Strike:
        """Mark that streams have been resumed for this strike."""
        strike.streams_resumed_at = datetime.utcnow()
        await self.session.flush()
        return strike

    async def delete(self, strike: Strike) -> None:
        """Delete a strike record."""
        await self.session.delete(strike)
        await self.session.flush()


class StrikeAlertRepository:
    """Repository for StrikeAlert model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        strike_id: uuid.UUID,
        account_id: uuid.UUID,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "high",
    ) -> StrikeAlert:
        """Create a new strike alert."""
        alert = StrikeAlert(
            strike_id=strike_id,
            account_id=account_id,
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity,
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Optional[StrikeAlert]:
        """Get alert by ID."""
        query = select(StrikeAlert).where(StrikeAlert.id == alert_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_strike_id(self, strike_id: uuid.UUID) -> list[StrikeAlert]:
        """Get all alerts for a strike."""
        query = select(StrikeAlert).where(
            StrikeAlert.strike_id == strike_id
        ).order_by(StrikeAlert.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> list[StrikeAlert]:
        """Get all alerts for an account."""
        query = select(StrikeAlert).where(StrikeAlert.account_id == account_id)
        
        if acknowledged is not None:
            query = query.where(StrikeAlert.acknowledged == acknowledged)
        
        query = query.order_by(StrikeAlert.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_delivered(
        self,
        alert: StrikeAlert,
        channels: list[str],
        error: Optional[str] = None,
    ) -> StrikeAlert:
        """Mark alert as delivered."""
        alert.channels_sent = channels
        alert.delivered_at = datetime.utcnow()
        alert.delivery_status = "delivered" if not error else "failed"
        if error:
            alert.delivery_error = error
        await self.session.flush()
        return alert

    async def acknowledge(
        self, alert: StrikeAlert, user_id: uuid.UUID
    ) -> StrikeAlert:
        """Acknowledge an alert."""
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        await self.session.flush()
        return alert


class PausedStreamRepository:
    """Repository for PausedStream model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        strike_id: uuid.UUID,
        live_event_id: uuid.UUID,
        account_id: uuid.UUID,
        original_status: str,
        pause_reason: str,
        original_scheduled_start_at: Optional[datetime] = None,
    ) -> PausedStream:
        """Create a new paused stream record."""
        paused_stream = PausedStream(
            strike_id=strike_id,
            live_event_id=live_event_id,
            account_id=account_id,
            original_status=original_status,
            original_scheduled_start_at=original_scheduled_start_at,
            pause_reason=pause_reason,
        )
        self.session.add(paused_stream)
        await self.session.flush()
        return paused_stream

    async def get_by_id(self, paused_stream_id: uuid.UUID) -> Optional[PausedStream]:
        """Get paused stream by ID."""
        query = select(PausedStream).where(PausedStream.id == paused_stream_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_event_id(self, live_event_id: uuid.UUID) -> Optional[PausedStream]:
        """Get paused stream by live event ID."""
        query = select(PausedStream).where(
            and_(
                PausedStream.live_event_id == live_event_id,
                PausedStream.resumed == False,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        resumed: Optional[bool] = None,
    ) -> list[PausedStream]:
        """Get all paused streams for an account."""
        query = select(PausedStream).where(PausedStream.account_id == account_id)
        
        if resumed is not None:
            query = query.where(PausedStream.resumed == resumed)
        
        query = query.order_by(PausedStream.paused_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_strike_id(self, strike_id: uuid.UUID) -> list[PausedStream]:
        """Get all paused streams for a strike."""
        query = select(PausedStream).where(
            PausedStream.strike_id == strike_id
        ).order_by(PausedStream.paused_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def resume(
        self,
        paused_stream: PausedStream,
        user_id: uuid.UUID,
        confirmation: bool = True,
    ) -> PausedStream:
        """Resume a paused stream."""
        paused_stream.resumed = True
        paused_stream.resumed_at = datetime.utcnow()
        paused_stream.resumed_by = user_id
        paused_stream.resume_confirmation = confirmation
        await self.session.flush()
        return paused_stream

    async def count_paused_streams(self, account_id: uuid.UUID) -> int:
        """Count paused streams for an account."""
        query = select(func.count(PausedStream.id)).where(
            and_(
                PausedStream.account_id == account_id,
                PausedStream.resumed == False,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
