"""Repository for AI Chatbot module.

Provides database operations for chatbot configuration and interactions.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.chatbot.models import (
    ChatbotConfig,
    ChatbotInteractionLog,
    ChatbotTrigger,
)


class ChatbotConfigRepository:
    """Repository for ChatbotConfig operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, config: ChatbotConfig) -> ChatbotConfig:
        """Create a new chatbot configuration."""
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def get_by_id(self, config_id: uuid.UUID) -> Optional[ChatbotConfig]:
        """Get chatbot configuration by ID."""
        result = await self.session.execute(
            select(ChatbotConfig).where(ChatbotConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(self, account_id: uuid.UUID) -> Optional[ChatbotConfig]:
        """Get chatbot configuration by account ID."""
        result = await self.session.execute(
            select(ChatbotConfig).where(ChatbotConfig.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, account_id: uuid.UUID) -> ChatbotConfig:
        """Get existing config or create default one."""
        config = await self.get_by_account(account_id)
        if config is None:
            config = ChatbotConfig(account_id=account_id)
            config = await self.create(config)
        return config

    async def update(
        self,
        config_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ChatbotConfig]:
        """Update chatbot configuration."""
        config = await self.get_by_id(config_id)
        if config is None:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        await self.session.flush()
        await self.session.refresh(config)
        return config


    async def pause(self, config_id: uuid.UUID, paused_by: str) -> Optional[ChatbotConfig]:
        """Pause chatbot (streamer takeover).
        
        Requirements: 11.5
        """
        config = await self.get_by_id(config_id)
        if config is None:
            return None

        config.pause(paused_by)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def resume(self, config_id: uuid.UUID) -> Optional[ChatbotConfig]:
        """Resume chatbot after takeover.
        
        Requirements: 11.5
        """
        config = await self.get_by_id(config_id)
        if config is None:
            return None

        config.resume()
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def delete(self, config_id: uuid.UUID) -> bool:
        """Delete chatbot configuration."""
        result = await self.session.execute(
            delete(ChatbotConfig).where(ChatbotConfig.id == config_id)
        )
        return result.rowcount > 0


class ChatbotTriggerRepository:
    """Repository for ChatbotTrigger operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, trigger: ChatbotTrigger) -> ChatbotTrigger:
        """Create a new chatbot trigger."""
        self.session.add(trigger)
        await self.session.flush()
        await self.session.refresh(trigger)
        return trigger

    async def get_by_id(self, trigger_id: uuid.UUID) -> Optional[ChatbotTrigger]:
        """Get trigger by ID."""
        result = await self.session.execute(
            select(ChatbotTrigger).where(ChatbotTrigger.id == trigger_id)
        )
        return result.scalar_one_or_none()

    async def get_by_config(
        self,
        config_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[ChatbotTrigger]:
        """Get all triggers for a config."""
        query = select(ChatbotTrigger).where(
            ChatbotTrigger.config_id == config_id
        )
        if enabled_only:
            query = query.where(ChatbotTrigger.is_enabled == True)
        query = query.order_by(ChatbotTrigger.priority.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        trigger_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ChatbotTrigger]:
        """Update a trigger."""
        trigger = await self.get_by_id(trigger_id)
        if trigger is None:
            return None

        for key, value in kwargs.items():
            if hasattr(trigger, key) and value is not None:
                setattr(trigger, key, value)

        await self.session.flush()
        await self.session.refresh(trigger)
        return trigger

    async def increment_trigger_count(self, trigger_id: uuid.UUID) -> None:
        """Increment trigger count."""
        trigger = await self.get_by_id(trigger_id)
        if trigger:
            trigger.increment_trigger_count()
            await self.session.flush()

    async def delete(self, trigger_id: uuid.UUID) -> bool:
        """Delete a trigger."""
        result = await self.session.execute(
            delete(ChatbotTrigger).where(ChatbotTrigger.id == trigger_id)
        )
        return result.rowcount > 0


class ChatbotInteractionLogRepository:
    """Repository for ChatbotInteractionLog operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: ChatbotInteractionLog) -> ChatbotInteractionLog:
        """Create a new interaction log."""
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> Optional[ChatbotInteractionLog]:
        """Get interaction log by ID."""
        result = await self.session.execute(
            select(ChatbotInteractionLog).where(ChatbotInteractionLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_config(
        self,
        config_id: uuid.UUID,
        limit: int = 100,
    ) -> list[ChatbotInteractionLog]:
        """Get interaction logs for a config."""
        result = await self.session.execute(
            select(ChatbotInteractionLog)
            .where(ChatbotInteractionLog.config_id == config_id)
            .order_by(ChatbotInteractionLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_during_pause(
        self,
        config_id: uuid.UUID,
        paused_at: datetime,
    ) -> list[ChatbotInteractionLog]:
        """Get messages received during pause (pending messages).
        
        Requirements: 11.5 - Notify pending messages
        """
        result = await self.session.execute(
            select(ChatbotInteractionLog)
            .where(
                ChatbotInteractionLog.config_id == config_id,
                ChatbotInteractionLog.created_at >= paused_at,
                ChatbotInteractionLog.was_responded == False,
                ChatbotInteractionLog.was_declined == False,
            )
            .order_by(ChatbotInteractionLog.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_recent_by_user(
        self,
        config_id: uuid.UUID,
        user_channel_id: str,
        seconds: int = 60,
    ) -> list[ChatbotInteractionLog]:
        """Get recent interactions from a user (for cooldown check)."""
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        result = await self.session.execute(
            select(ChatbotInteractionLog)
            .where(
                ChatbotInteractionLog.config_id == config_id,
                ChatbotInteractionLog.user_channel_id == user_channel_id,
                ChatbotInteractionLog.created_at >= cutoff,
            )
            .order_by(ChatbotInteractionLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        log_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ChatbotInteractionLog]:
        """Update an interaction log."""
        log = await self.get_by_id(log_id)
        if log is None:
            return None

        for key, value in kwargs.items():
            if hasattr(log, key) and value is not None:
                setattr(log, key, value)

        await self.session.flush()
        await self.session.refresh(log)
        return log
