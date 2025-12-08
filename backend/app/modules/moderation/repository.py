"""Repository for moderation data access.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.moderation.models import (
    ChatMessage,
    CustomCommand,
    ModerationActionLog,
    ModerationRule,
    SlowModeConfig,
)


class ModerationRuleRepository:
    """Repository for ModerationRule CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, rule: ModerationRule) -> ModerationRule:
        """Create a new moderation rule."""
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> Optional[ModerationRule]:
        """Get a moderation rule by ID."""
        result = await self.session.execute(
            select(ModerationRule).where(ModerationRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[ModerationRule]:
        """Get all moderation rules for an account.
        
        Args:
            account_id: YouTube account ID
            enabled_only: Only return enabled rules
            
        Returns:
            List of moderation rules ordered by priority (descending)
        """
        query = select(ModerationRule).where(
            ModerationRule.account_id == account_id
        )
        if enabled_only:
            query = query.where(ModerationRule.is_enabled == True)
        query = query.order_by(ModerationRule.priority.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        rule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ModerationRule]:
        """Update a moderation rule."""
        rule = await self.get_by_id(rule_id)
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key) and value is not None:
                    setattr(rule, key, value)
            await self.session.flush()
        return rule

    async def delete(self, rule_id: uuid.UUID) -> bool:
        """Delete a moderation rule."""
        rule = await self.get_by_id(rule_id)
        if rule:
            await self.session.delete(rule)
            await self.session.flush()
            return True
        return False

    async def increment_trigger_count(self, rule_id: uuid.UUID) -> None:
        """Increment the trigger count for a rule."""
        await self.session.execute(
            update(ModerationRule)
            .where(ModerationRule.id == rule_id)
            .values(
                trigger_count=ModerationRule.trigger_count + 1,
                last_triggered_at=datetime.utcnow(),
            )
        )


class ModerationActionLogRepository:
    """Repository for ModerationActionLog operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: ModerationActionLog) -> ModerationActionLog:
        """Create a new moderation action log."""
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> Optional[ModerationActionLog]:
        """Get a moderation action log by ID."""
        result = await self.session.execute(
            select(ModerationActionLog).where(ModerationActionLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[ModerationActionLog]:
        """Get moderation action logs for an account."""
        result = await self.session.execute(
            select(ModerationActionLog)
            .where(ModerationActionLog.account_id == account_id)
            .order_by(ModerationActionLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self,
        account_id: uuid.UUID,
        user_channel_id: str,
        limit: int = 50,
    ) -> list[ModerationActionLog]:
        """Get moderation action logs for a specific user."""
        result = await self.session.execute(
            select(ModerationActionLog)
            .where(
                and_(
                    ModerationActionLog.account_id == account_id,
                    ModerationActionLog.user_channel_id == user_channel_id,
                )
            )
            .order_by(ModerationActionLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ChatMessageRepository:
    """Repository for ChatMessage operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new chat message."""
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_by_id(self, message_id: uuid.UUID) -> Optional[ChatMessage]:
        """Get a chat message by ID."""
        result = await self.session.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_by_youtube_id(
        self,
        youtube_message_id: str,
    ) -> Optional[ChatMessage]:
        """Get a chat message by YouTube message ID."""
        result = await self.session.execute(
            select(ChatMessage).where(
                ChatMessage.youtube_message_id == youtube_message_id
            )
        )
        return result.scalar_one_or_none()

    async def update_moderation_status(
        self,
        message_id: uuid.UUID,
        is_moderated: bool,
        is_hidden: bool = False,
        is_deleted: bool = False,
        reason: Optional[str] = None,
        violated_rules: Optional[list[str]] = None,
    ) -> Optional[ChatMessage]:
        """Update moderation status of a message."""
        message = await self.get_by_id(message_id)
        if message:
            message.is_moderated = is_moderated
            message.is_hidden = is_hidden
            message.is_deleted = is_deleted
            message.moderation_reason = reason
            message.moderated_at = datetime.utcnow() if is_moderated else None
            message.analysis_completed = True
            if violated_rules:
                message.violated_rules = violated_rules
            await self.session.flush()
        return message

    async def get_recent_by_author(
        self,
        account_id: uuid.UUID,
        author_channel_id: str,
        minutes: int = 1,
    ) -> list[ChatMessage]:
        """Get recent messages from an author within a time window."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        result = await self.session.execute(
            select(ChatMessage)
            .where(
                and_(
                    ChatMessage.account_id == account_id,
                    ChatMessage.author_channel_id == author_channel_id,
                    ChatMessage.published_at >= cutoff,
                )
            )
            .order_by(ChatMessage.published_at.desc())
        )
        return list(result.scalars().all())


class SlowModeConfigRepository:
    """Repository for SlowModeConfig operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, config: SlowModeConfig) -> SlowModeConfig:
        """Create a new slow mode configuration."""
        self.session.add(config)
        await self.session.flush()
        return config

    async def get_by_account(
        self,
        account_id: uuid.UUID,
    ) -> Optional[SlowModeConfig]:
        """Get slow mode configuration for an account."""
        result = await self.session.execute(
            select(SlowModeConfig).where(SlowModeConfig.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        account_id: uuid.UUID,
    ) -> SlowModeConfig:
        """Get or create slow mode configuration for an account."""
        config = await self.get_by_account(account_id)
        if not config:
            config = SlowModeConfig(account_id=account_id)
            self.session.add(config)
            await self.session.flush()
        return config

    async def update(
        self,
        account_id: uuid.UUID,
        **kwargs,
    ) -> Optional[SlowModeConfig]:
        """Update slow mode configuration."""
        config = await self.get_by_account(account_id)
        if config:
            for key, value in kwargs.items():
                if hasattr(config, key) and value is not None:
                    setattr(config, key, value)
            await self.session.flush()
        return config


class CustomCommandRepository:
    """Repository for CustomCommand operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, command: CustomCommand) -> CustomCommand:
        """Create a new custom command."""
        self.session.add(command)
        await self.session.flush()
        return command

    async def get_by_id(self, command_id: uuid.UUID) -> Optional[CustomCommand]:
        """Get a custom command by ID."""
        result = await self.session.execute(
            select(CustomCommand).where(CustomCommand.id == command_id)
        )
        return result.scalar_one_or_none()

    async def get_by_trigger(
        self,
        account_id: uuid.UUID,
        trigger: str,
    ) -> Optional[CustomCommand]:
        """Get a custom command by trigger."""
        result = await self.session.execute(
            select(CustomCommand).where(
                and_(
                    CustomCommand.account_id == account_id,
                    CustomCommand.trigger == trigger,
                    CustomCommand.is_enabled == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_account(
        self,
        account_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[CustomCommand]:
        """Get all custom commands for an account."""
        query = select(CustomCommand).where(
            CustomCommand.account_id == account_id
        )
        if enabled_only:
            query = query.where(CustomCommand.is_enabled == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        command_id: uuid.UUID,
        **kwargs,
    ) -> Optional[CustomCommand]:
        """Update a custom command."""
        command = await self.get_by_id(command_id)
        if command:
            for key, value in kwargs.items():
                if hasattr(command, key) and value is not None:
                    setattr(command, key, value)
            await self.session.flush()
        return command

    async def delete(self, command_id: uuid.UUID) -> bool:
        """Delete a custom command."""
        command = await self.get_by_id(command_id)
        if command:
            await self.session.delete(command)
            await self.session.flush()
            return True
        return False

    async def record_usage(self, command_id: uuid.UUID) -> None:
        """Record command usage."""
        await self.session.execute(
            update(CustomCommand)
            .where(CustomCommand.id == command_id)
            .values(
                usage_count=CustomCommand.usage_count + 1,
                last_used_at=datetime.utcnow(),
            )
        )
