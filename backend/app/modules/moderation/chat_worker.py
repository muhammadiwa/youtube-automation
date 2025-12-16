"""Live Chat Moderation Worker.

Background worker for polling YouTube live chat and applying moderation rules.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.account.repository import YouTubeAccountRepository
from app.modules.moderation.youtube_chat_api import YouTubeLiveChatClient, YouTubeChatAPIError
from app.modules.moderation.service import ModerationService, ChatAnalyzer
from app.modules.moderation.models import (
    ChatMessage,
    ModerationActionLog,
    ModerationActionType,
    ModerationRule,
)
from app.modules.moderation.repository import (
    ModerationRuleRepository,
    ChatMessageRepository,
    ModerationActionLogRepository,
    CustomCommandRepository,
)

logger = logging.getLogger(__name__)


class LiveChatModerationWorker:
    """Worker for live chat moderation.
    
    Polls YouTube live chat, analyzes messages against rules,
    and executes moderation actions.
    
    Requirements: 12.1 - Analyze messages within 2 seconds
    """

    def __init__(
        self,
        account_id: uuid.UUID,
        broadcast_id: str,
        session_id: Optional[uuid.UUID] = None,
    ):
        """Initialize the worker.

        Args:
            account_id: YouTube account UUID
            broadcast_id: YouTube broadcast/video ID
            session_id: Optional stream session UUID
        """
        self.account_id = account_id
        self.broadcast_id = broadcast_id
        self.session_id = session_id
        self.live_chat_id: Optional[str] = None
        self.page_token: Optional[str] = None
        self.polling_interval_ms: int = 5000  # Default 5 seconds
        self.is_running: bool = False
        self.processed_message_ids: set[str] = set()
        self._rules: list[ModerationRule] = []
        self._analyzer: Optional[ChatAnalyzer] = None
        self._access_token: Optional[str] = None

    async def start(self) -> None:
        """Start the moderation worker."""
        logger.info(f"Starting chat moderation worker for broadcast {self.broadcast_id}")
        self.is_running = True

        try:
            # Initialize
            await self._initialize()

            # Main polling loop
            while self.is_running:
                try:
                    await self._poll_and_moderate()
                except YouTubeChatAPIError as e:
                    logger.error(f"YouTube API error: {e.message}")
                    if e.status_code == 403:
                        # Quota exceeded or forbidden - slow down
                        await asyncio.sleep(60)
                    elif e.status_code == 404:
                        # Chat ended
                        logger.info("Live chat ended")
                        break
                except Exception as e:
                    logger.error(f"Error in moderation loop: {e}")

                # Wait for next poll
                await asyncio.sleep(self.polling_interval_ms / 1000)

        except Exception as e:
            logger.error(f"Fatal error in moderation worker: {e}")
        finally:
            self.is_running = False
            logger.info(f"Chat moderation worker stopped for broadcast {self.broadcast_id}")

    async def stop(self) -> None:
        """Stop the moderation worker."""
        logger.info(f"Stopping chat moderation worker for broadcast {self.broadcast_id}")
        self.is_running = False

    async def _initialize(self) -> None:
        """Initialize the worker with account and rules."""
        async with async_session_maker() as session:
            # Get account and access token
            account_repo = YouTubeAccountRepository(session)
            account = await account_repo.get_by_id(self.account_id)
            if not account:
                raise ValueError(f"Account {self.account_id} not found")

            self._access_token = account.access_token

            # Get live chat ID
            client = YouTubeLiveChatClient(self._access_token)
            self.live_chat_id = await client.get_live_chat_id(self.broadcast_id)
            if not self.live_chat_id:
                raise ValueError(f"No live chat found for broadcast {self.broadcast_id}")

            # Load moderation rules
            rule_repo = ModerationRuleRepository(session)
            self._rules = await rule_repo.get_by_account(self.account_id, enabled_only=True)
            self._analyzer = ChatAnalyzer(self._rules)

            logger.info(f"Initialized with {len(self._rules)} moderation rules")

    async def _poll_and_moderate(self) -> None:
        """Poll for new messages and apply moderation."""
        if not self.live_chat_id or not self._access_token:
            return

        client = YouTubeLiveChatClient(self._access_token)

        # Get new messages
        response = await client.get_live_chat_messages(
            live_chat_id=self.live_chat_id,
            page_token=self.page_token,
        )

        # Update pagination
        self.page_token = response.get("nextPageToken")
        self.polling_interval_ms = response.get("pollingIntervalMillis", 5000)

        # Process messages
        items = response.get("items", [])
        for item in items:
            message_id = item.get("id")
            if message_id in self.processed_message_ids:
                continue

            self.processed_message_ids.add(message_id)

            # Parse message
            parsed = client.parse_chat_message(item)

            # Skip messages from owner/moderators
            if parsed["is_chat_owner"] or parsed["is_chat_moderator"]:
                continue

            # Process the message
            await self._process_message(parsed, client)

        # Limit processed IDs cache size
        if len(self.processed_message_ids) > 10000:
            # Keep only recent 5000
            self.processed_message_ids = set(list(self.processed_message_ids)[-5000:])

    async def _process_message(
        self,
        parsed_message: Dict[str, Any],
        client: YouTubeLiveChatClient,
    ) -> None:
        """Process a single chat message.

        Args:
            parsed_message: Parsed message data
            client: YouTube chat client
        """
        async with async_session_maker() as session:
            try:
                # Create ChatMessage object for analysis
                chat_message = ChatMessage(
                    account_id=self.account_id,
                    session_id=self.session_id,
                    youtube_message_id=parsed_message["youtube_message_id"],
                    content=parsed_message["content"],
                    author_channel_id=parsed_message["author_channel_id"],
                    author_display_name=parsed_message["author_display_name"],
                    author_profile_image=parsed_message.get("author_profile_image"),
                    is_owner=parsed_message["is_chat_owner"],
                    is_moderator=parsed_message["is_chat_moderator"],
                    is_member=parsed_message["is_chat_sponsor"],
                    published_at=datetime.fromisoformat(
                        parsed_message["published_at"].replace("Z", "+00:00")
                    ) if parsed_message.get("published_at") else datetime.utcnow(),
                )

                # Check for custom commands first
                command_response = await self._check_custom_command(
                    session, parsed_message, client
                )
                if command_response:
                    return  # Command was handled

                # Analyze message against rules
                if self._analyzer:
                    result = self._analyzer.analyze(chat_message)

                    if result.is_violation:
                        # Execute moderation action
                        await self._execute_moderation_action(
                            session, chat_message, result, client
                        )

                # Store message in database
                message_repo = ChatMessageRepository(session)
                await message_repo.create(chat_message)
                await session.commit()

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await session.rollback()

    async def _check_custom_command(
        self,
        session: AsyncSession,
        parsed_message: Dict[str, Any],
        client: YouTubeLiveChatClient,
    ) -> bool:
        """Check if message is a custom command and execute it.

        Args:
            session: Database session
            parsed_message: Parsed message data
            client: YouTube chat client

        Returns:
            bool: True if command was executed
        """
        content = parsed_message["content"].strip()
        if not content.startswith("!"):
            return False

        # Extract trigger
        parts = content.split(maxsplit=1)
        trigger = parts[0].lower()

        # Find matching command
        command_repo = CustomCommandRepository(session)
        command = await command_repo.get_by_trigger(self.account_id, trigger)

        if not command:
            return False

        # Check permissions
        is_moderator = parsed_message["is_chat_moderator"]
        is_member = parsed_message["is_chat_sponsor"]
        is_owner = parsed_message["is_chat_owner"]

        if not command.can_be_used_by(is_moderator, is_member, is_owner):
            return False

        # Check cooldown
        if command.is_on_cooldown():
            return False

        # Execute command - send response
        if command.response_text and self.live_chat_id:
            # Replace placeholders
            response = command.response_text
            response = response.replace("{user}", parsed_message["author_display_name"])
            response = response.replace("{channel}", parsed_message["author_display_name"])

            try:
                await client.send_message(self.live_chat_id, response)
            except YouTubeChatAPIError as e:
                logger.error(f"Failed to send command response: {e}")

        # Record usage
        await command_repo.record_usage(command.id)
        await session.commit()

        return True

    async def _execute_moderation_action(
        self,
        session: AsyncSession,
        message: ChatMessage,
        result: Any,  # ModerationAnalysisResult
        client: YouTubeLiveChatClient,
    ) -> None:
        """Execute moderation action based on analysis result.

        Args:
            session: Database session
            message: Chat message
            result: Analysis result
            client: YouTube chat client
        """
        if not result.violations:
            return

        violation = result.violations[0]  # Highest severity
        action_type = violation.action_type
        success = False
        error_message = None

        try:
            if action_type == ModerationActionType.DELETE:
                # Delete the message
                await client.delete_message(message.youtube_message_id)
                success = True
                logger.info(f"Deleted message: {message.youtube_message_id}")

            elif action_type == ModerationActionType.HIDE:
                # YouTube doesn't have "hide" - we delete instead
                await client.delete_message(message.youtube_message_id)
                success = True
                logger.info(f"Hidden (deleted) message: {message.youtube_message_id}")

            elif action_type == ModerationActionType.TIMEOUT:
                # Timeout user (temporary ban)
                duration = violation.timeout_duration_seconds or 300
                if self.live_chat_id:
                    await client.ban_user(
                        live_chat_id=self.live_chat_id,
                        channel_id=message.author_channel_id,
                        ban_duration_seconds=duration,
                    )
                    # Also delete the offending message
                    await client.delete_message(message.youtube_message_id)
                    success = True
                    logger.info(f"Timed out user {message.author_channel_id} for {duration}s")

            elif action_type == ModerationActionType.BAN:
                # Permanent ban
                if self.live_chat_id:
                    await client.ban_user(
                        live_chat_id=self.live_chat_id,
                        channel_id=message.author_channel_id,
                        ban_duration_seconds=None,  # Permanent
                    )
                    await client.delete_message(message.youtube_message_id)
                    success = True
                    logger.info(f"Banned user {message.author_channel_id}")

            elif action_type == ModerationActionType.WARN:
                # Send warning message
                if self.live_chat_id:
                    warning = f"@{message.author_display_name} ⚠️ Warning: Your message violated chat rules."
                    await client.send_message(self.live_chat_id, warning)
                    success = True
                    logger.info(f"Warned user {message.author_display_name}")

        except YouTubeChatAPIError as e:
            error_message = str(e)
            logger.error(f"Failed to execute moderation action: {e}")

        # Log the action
        log_repo = ModerationActionLogRepository(session)
        action_log = ModerationActionLog(
            rule_id=violation.rule_id,
            account_id=self.account_id,
            session_id=self.session_id,
            action_type=action_type.value,
            severity=violation.severity.value,
            user_channel_id=message.author_channel_id,
            user_display_name=message.author_display_name,
            message_id=message.youtube_message_id,
            message_content=message.content,
            reason=f"Rule '{violation.rule_name}' violated: {violation.matched_pattern or 'pattern match'}",
            was_successful=success,
            error_message=error_message,
            timeout_duration_seconds=violation.timeout_duration_seconds,
            processing_started_at=datetime.utcnow(),
            processing_completed_at=datetime.utcnow(),
        )
        await log_repo.create(action_log)

        # Increment rule trigger count
        rule_repo = ModerationRuleRepository(session)
        await rule_repo.increment_trigger_count(violation.rule_id)

        await session.commit()


# Global registry of active workers
_active_workers: Dict[str, LiveChatModerationWorker] = {}


async def start_moderation_for_broadcast(
    account_id: uuid.UUID,
    broadcast_id: str,
    session_id: Optional[uuid.UUID] = None,
) -> LiveChatModerationWorker:
    """Start moderation worker for a broadcast.

    Args:
        account_id: YouTube account UUID
        broadcast_id: YouTube broadcast ID
        session_id: Optional stream session UUID

    Returns:
        LiveChatModerationWorker: Started worker instance
    """
    key = f"{account_id}:{broadcast_id}"

    # Stop existing worker if any
    if key in _active_workers:
        await _active_workers[key].stop()

    # Create and start new worker
    worker = LiveChatModerationWorker(
        account_id=account_id,
        broadcast_id=broadcast_id,
        session_id=session_id,
    )

    _active_workers[key] = worker

    # Start in background
    asyncio.create_task(worker.start())

    return worker


async def stop_moderation_for_broadcast(
    account_id: uuid.UUID,
    broadcast_id: str,
) -> bool:
    """Stop moderation worker for a broadcast.

    Args:
        account_id: YouTube account UUID
        broadcast_id: YouTube broadcast ID

    Returns:
        bool: True if worker was stopped
    """
    key = f"{account_id}:{broadcast_id}"

    if key in _active_workers:
        await _active_workers[key].stop()
        del _active_workers[key]
        return True

    return False


def get_active_workers() -> Dict[str, LiveChatModerationWorker]:
    """Get all active moderation workers.

    Returns:
        Dict mapping broadcast keys to workers
    """
    return _active_workers.copy()
