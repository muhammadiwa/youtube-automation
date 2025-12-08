"""Service for AI Chatbot.

Implements chatbot response generation and management.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import re
import time
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.chatbot.models import (
    ChatbotConfig,
    ChatbotInteractionLog,
    ChatbotTrigger,
    PersonalityType,
    ResponseStyle,
    TriggerType,
)
from app.modules.ai.chatbot.prompts import (
    build_content_filter_prompt,
    build_system_prompt,
    build_user_prompt,
)
from app.modules.ai.chatbot.repository import (
    ChatbotConfigRepository,
    ChatbotInteractionLogRepository,
    ChatbotTriggerRepository,
)
from app.modules.ai.chatbot.schemas import (
    ChatbotConfigCreate,
    ChatbotConfigResponse,
    ChatbotConfigUpdate,
    ChatResponseRequest,
    ChatResponseResult,
    TakeoverResponse,
    TriggerCreate,
    TriggerResponse,
)
from app.modules.ai.openai_client import OpenAIClient, OpenAIClientError, get_openai_client


class ChatbotServiceError(Exception):
    """Base exception for chatbot service errors."""
    pass


class TriggerMatcher:
    """Matches chat messages against configured triggers.
    
    Requirements: 11.1 - Matching configured triggers
    """

    def __init__(self, triggers: list[ChatbotTrigger]):
        """Initialize trigger matcher.
        
        Args:
            triggers: List of triggers to match against
        """
        self.triggers = triggers
        self._compiled_patterns: dict[uuid.UUID, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for trigger in self.triggers:
            if trigger.trigger_type == TriggerType.REGEX.value and trigger.pattern:
                try:
                    self._compiled_patterns[trigger.id] = re.compile(
                        trigger.pattern, re.IGNORECASE
                    )
                except re.error:
                    pass


    def match(self, message: str) -> Optional[tuple[ChatbotTrigger, str]]:
        """Match message against triggers.
        
        Args:
            message: Message content to match
            
        Returns:
            Tuple of (matched trigger, matched pattern) or None
        """
        message_lower = message.lower()

        for trigger in self.triggers:
            if not trigger.is_enabled:
                continue

            matched = self._check_trigger(trigger, message, message_lower)
            if matched:
                return trigger, matched

        return None

    def _check_trigger(
        self,
        trigger: ChatbotTrigger,
        message: str,
        message_lower: str,
    ) -> Optional[str]:
        """Check a single trigger against message.
        
        Args:
            trigger: Trigger to check
            message: Original message
            message_lower: Lowercase message
            
        Returns:
            Matched pattern string or None
        """
        if trigger.trigger_type == TriggerType.KEYWORD.value:
            return self._check_keywords(trigger, message_lower)
        elif trigger.trigger_type == TriggerType.REGEX.value:
            return self._check_regex(trigger, message)
        elif trigger.trigger_type == TriggerType.QUESTION.value:
            return self._check_question(message_lower)
        elif trigger.trigger_type == TriggerType.GREETING.value:
            return self._check_greeting(message_lower)
        elif trigger.trigger_type == TriggerType.COMMAND.value:
            return self._check_command(trigger, message_lower)
        elif trigger.trigger_type == TriggerType.MENTION.value:
            return self._check_mention(trigger, message_lower)
        return None

    def _check_keywords(self, trigger: ChatbotTrigger, message_lower: str) -> Optional[str]:
        """Check for keyword matches."""
        if not trigger.keywords:
            return None
        for keyword in trigger.keywords:
            if keyword.lower() in message_lower:
                return keyword
        return None

    def _check_regex(self, trigger: ChatbotTrigger, message: str) -> Optional[str]:
        """Check for regex pattern matches."""
        pattern = self._compiled_patterns.get(trigger.id)
        if pattern:
            match = pattern.search(message)
            if match:
                return match.group()
        return None

    def _check_question(self, message_lower: str) -> Optional[str]:
        """Check if message is a question."""
        question_indicators = ["?", "what", "how", "why", "when", "where", "who", "which", "can you", "could you", "do you"]
        for indicator in question_indicators:
            if indicator in message_lower:
                return "question"
        return None

    def _check_greeting(self, message_lower: str) -> Optional[str]:
        """Check if message is a greeting."""
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "sup", "yo", "greetings"]
        for greeting in greetings:
            if greeting in message_lower:
                return greeting
        return None

    def _check_command(self, trigger: ChatbotTrigger, message_lower: str) -> Optional[str]:
        """Check if message is a command."""
        if trigger.pattern and message_lower.startswith(trigger.pattern.lower()):
            return trigger.pattern
        return None

    def _check_mention(self, trigger: ChatbotTrigger, message_lower: str) -> Optional[str]:
        """Check if bot is mentioned."""
        if trigger.pattern and trigger.pattern.lower() in message_lower:
            return trigger.pattern
        return None



class ChatbotService:
    """Service for AI chatbot operations.
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
    """

    # Response time limit in seconds (Requirements: 11.1)
    RESPONSE_TIME_LIMIT_SECONDS = 3.0

    def __init__(
        self,
        session: AsyncSession,
        openai_client: Optional[OpenAIClient] = None,
    ):
        """Initialize chatbot service.
        
        Args:
            session: Database session
            openai_client: Optional OpenAI client
        """
        self.session = session
        self._openai_client = openai_client
        self.config_repo = ChatbotConfigRepository(session)
        self.trigger_repo = ChatbotTriggerRepository(session)
        self.interaction_repo = ChatbotInteractionLogRepository(session)

    @property
    def openai_client(self) -> OpenAIClient:
        """Get OpenAI client."""
        if self._openai_client is None:
            self._openai_client = get_openai_client()
        return self._openai_client

    # ============================================
    # Configuration Management (Requirements: 11.2)
    # ============================================

    async def create_config(
        self,
        account_id: uuid.UUID,
        data: ChatbotConfigCreate,
    ) -> ChatbotConfig:
        """Create chatbot configuration.
        
        Requirements: 11.2 - Personality customization, Response style settings
        
        Args:
            account_id: YouTube account ID
            data: Configuration data
            
        Returns:
            Created ChatbotConfig
        """
        config = ChatbotConfig(
            account_id=account_id,
            bot_name=data.bot_name,
            bot_prefix=data.bot_prefix,
            personality=data.personality.value,
            response_style=data.response_style.value,
            custom_personality_prompt=data.custom_personality_prompt,
            max_response_length=data.max_response_length,
            response_language=data.response_language,
            use_emojis=data.use_emojis,
            response_delay_ms=data.response_delay_ms,
            cooldown_seconds=data.cooldown_seconds,
            content_filter_enabled=data.content_filter_enabled,
            blocked_topics=data.blocked_topics,
            blocked_keywords=data.blocked_keywords,
            takeover_command=data.takeover_command,
            resume_command=data.resume_command,
        )
        return await self.config_repo.create(config)

    async def get_config(self, account_id: uuid.UUID) -> Optional[ChatbotConfig]:
        """Get chatbot configuration for an account."""
        return await self.config_repo.get_by_account(account_id)

    async def get_or_create_config(self, account_id: uuid.UUID) -> ChatbotConfig:
        """Get existing config or create default one."""
        return await self.config_repo.get_or_create(account_id)

    async def update_config(
        self,
        account_id: uuid.UUID,
        data: ChatbotConfigUpdate,
    ) -> Optional[ChatbotConfig]:
        """Update chatbot configuration."""
        config = await self.config_repo.get_by_account(account_id)
        if config is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "personality" in update_data and update_data["personality"]:
            update_data["personality"] = update_data["personality"].value
        if "response_style" in update_data and update_data["response_style"]:
            update_data["response_style"] = update_data["response_style"].value

        return await self.config_repo.update(config.id, **update_data)

    # ============================================
    # Trigger Management (Requirements: 11.1)
    # ============================================

    async def create_trigger(
        self,
        config_id: uuid.UUID,
        data: TriggerCreate,
    ) -> ChatbotTrigger:
        """Create a chatbot trigger."""
        trigger = ChatbotTrigger(
            config_id=config_id,
            name=data.name,
            trigger_type=data.trigger_type.value,
            pattern=data.pattern,
            keywords=data.keywords,
            custom_response_prompt=data.custom_response_prompt,
            priority=data.priority,
            is_enabled=data.is_enabled,
        )
        return await self.trigger_repo.create(trigger)

    async def get_triggers(
        self,
        config_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[ChatbotTrigger]:
        """Get triggers for a config."""
        return await self.trigger_repo.get_by_config(config_id, enabled_only)

    async def delete_trigger(self, trigger_id: uuid.UUID) -> bool:
        """Delete a trigger."""
        return await self.trigger_repo.delete(trigger_id)


    # ============================================
    # Chat Response Generation (Requirements: 11.1, 11.3)
    # ============================================

    async def generate_response(
        self,
        account_id: uuid.UUID,
        request: ChatResponseRequest,
    ) -> ChatResponseResult:
        """Generate a chat response.
        
        Requirements: 11.1 - Generate responses within 3 seconds
        Requirements: 11.3 - Add bot identifier prefix
        
        Args:
            account_id: YouTube account ID
            request: Chat response request
            
        Returns:
            ChatResponseResult with response or decline info
        """
        start_time = time.time()

        # Get config
        config = await self.get_or_create_config(account_id)

        # Check if bot is active
        if not config.is_active():
            return ChatResponseResult(
                should_respond=False,
                was_declined=True,
                decline_reason="Bot is paused or disabled",
                response_time_ms=(time.time() - start_time) * 1000,
            )

        # Check user cooldown
        recent = await self.interaction_repo.get_recent_by_user(
            config.id,
            request.user_channel_id,
            config.cooldown_seconds,
        )
        if recent:
            return ChatResponseResult(
                should_respond=False,
                was_declined=True,
                decline_reason="User on cooldown",
                response_time_ms=(time.time() - start_time) * 1000,
            )

        # Check for takeover commands (Requirements: 11.5)
        if request.is_owner or request.is_moderator:
            if request.message_content.strip().lower() == config.takeover_command.lower():
                await self._handle_takeover(config, request.user_channel_id)
                return ChatResponseResult(
                    should_respond=False,
                    was_declined=True,
                    decline_reason="Takeover command received",
                    response_time_ms=(time.time() - start_time) * 1000,
                )
            if request.message_content.strip().lower() == config.resume_command.lower():
                await self._handle_resume(config)
                return ChatResponseResult(
                    should_respond=False,
                    was_declined=True,
                    decline_reason="Resume command received",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

        # Get triggers and check for match
        triggers = await self.get_triggers(config.id, enabled_only=True)
        matcher = TriggerMatcher(triggers)
        match_result = matcher.match(request.message_content)

        if match_result is None:
            return ChatResponseResult(
                should_respond=False,
                response_time_ms=(time.time() - start_time) * 1000,
            )

        matched_trigger, matched_pattern = match_result

        # Create interaction log
        interaction = ChatbotInteractionLog(
            config_id=config.id,
            session_id=request.session_id,
            trigger_id=matched_trigger.id,
            user_channel_id=request.user_channel_id,
            user_display_name=request.user_display_name,
            input_message_id=request.message_id,
            input_content=request.message_content,
            processing_started_at=datetime.utcnow(),
            matched_trigger_type=matched_trigger.trigger_type,
            matched_pattern=matched_pattern,
        )
        interaction = await self.interaction_repo.create(interaction)

        # Content filtering (Requirements: 11.4)
        if config.content_filter_enabled:
            filter_result = await self._check_content_filter(
                config,
                request.message_content,
            )
            if filter_result.get("is_inappropriate", False):
                interaction.mark_declined(filter_result.get("reason", "Inappropriate content"))
                config.increment_declined_count()
                await self.session.flush()

                return ChatResponseResult(
                    should_respond=False,
                    was_declined=True,
                    decline_reason=filter_result.get("reason", "Inappropriate content"),
                    response_time_ms=(time.time() - start_time) * 1000,
                    interaction_id=interaction.id,
                )

        # Generate AI response
        try:
            response = await self._generate_ai_response(
                config,
                matched_trigger,
                request.user_display_name,
                request.message_content,
            )
        except OpenAIClientError as e:
            interaction.mark_declined(f"AI error: {str(e)}")
            await self.session.flush()
            return ChatResponseResult(
                should_respond=False,
                was_declined=True,
                decline_reason=f"AI error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                interaction_id=interaction.id,
            )

        # Check if AI declined to respond (Requirements: 11.4)
        if not response.get("should_respond", False):
            reason = response.get("decline_reason", "AI declined to respond")
            interaction.mark_declined(reason)
            config.increment_declined_count()
            await self.session.flush()

            return ChatResponseResult(
                should_respond=False,
                was_declined=True,
                decline_reason=reason,
                response_time_ms=(time.time() - start_time) * 1000,
                interaction_id=interaction.id,
            )

        # Build response with prefix (Requirements: 11.3)
        response_text = response.get("response", "")[:config.max_response_length]
        prefixed_response = f"{config.bot_prefix} {response_text}"

        # Update interaction and config
        response_time_ms = (time.time() - start_time) * 1000
        interaction.complete_response(response_text, "")  # Message ID set later
        config.increment_response_count(response_time_ms)
        await self.trigger_repo.increment_trigger_count(matched_trigger.id)
        await self.session.flush()

        return ChatResponseResult(
            should_respond=True,
            response_content=response_text,
            prefixed_response=prefixed_response,
            matched_trigger=matched_trigger.name,
            matched_trigger_type=matched_trigger.trigger_type,
            response_time_ms=response_time_ms,
            interaction_id=interaction.id,
        )


    async def _generate_ai_response(
        self,
        config: ChatbotConfig,
        trigger: ChatbotTrigger,
        user_name: str,
        message: str,
    ) -> dict:
        """Generate AI response using OpenAI.
        
        Args:
            config: Chatbot configuration
            trigger: Matched trigger
            user_name: User's display name
            message: User's message
            
        Returns:
            dict: AI response with should_respond, response, etc.
        """
        # Build system prompt
        custom_prompt = trigger.custom_response_prompt or config.custom_personality_prompt
        system_prompt = build_system_prompt(
            bot_name=config.bot_name,
            personality=config.personality,
            response_style=config.response_style,
            max_length=config.max_response_length,
            use_emojis=config.use_emojis,
            response_language=config.response_language,
            custom_prompt=custom_prompt,
            blocked_topics=config.blocked_topics,
        )

        # Build user prompt
        user_prompt = build_user_prompt(user_name, message)

        # Generate response
        response = await self.openai_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=config.max_response_length + 100,
        )

        return response

    async def _check_content_filter(
        self,
        config: ChatbotConfig,
        message: str,
    ) -> dict:
        """Check message against content filter.
        
        Requirements: 11.4 - Decline inappropriate requests
        
        Args:
            config: Chatbot configuration
            message: Message to check
            
        Returns:
            dict: Filter result with is_inappropriate, reason, severity
        """
        # Quick keyword check first
        if config.blocked_keywords:
            message_lower = message.lower()
            for keyword in config.blocked_keywords:
                if keyword.lower() in message_lower:
                    return {
                        "is_inappropriate": True,
                        "reason": f"Blocked keyword: {keyword}",
                        "severity": "medium",
                    }

        # AI-based content filter for more nuanced detection
        filter_prompt = build_content_filter_prompt(
            config.blocked_keywords,
            config.blocked_topics,
        )

        try:
            result = await self.openai_client.generate_json(
                system_prompt=filter_prompt,
                user_prompt=f"Message to analyze: {message}",
                temperature=0.1,
                max_tokens=100,
            )
            return result
        except OpenAIClientError:
            # If filter fails, allow the message through
            return {"is_inappropriate": False}

    # ============================================
    # Streamer Takeover (Requirements: 11.5)
    # ============================================

    async def _handle_takeover(
        self,
        config: ChatbotConfig,
        paused_by: str,
    ) -> None:
        """Handle streamer takeover command.
        
        Requirements: 11.5 - Pause bot on command
        """
        await self.config_repo.pause(config.id, paused_by)

    async def _handle_resume(self, config: ChatbotConfig) -> None:
        """Handle resume command after takeover.
        
        Requirements: 11.5
        """
        await self.config_repo.resume(config.id)

    async def pause_bot(
        self,
        account_id: uuid.UUID,
        paused_by: str,
    ) -> TakeoverResponse:
        """Pause the chatbot (streamer takeover).
        
        Requirements: 11.5 - Pause bot on command
        
        Args:
            account_id: YouTube account ID
            paused_by: Channel ID of who paused
            
        Returns:
            TakeoverResponse with pause status
        """
        config = await self.get_or_create_config(account_id)
        config = await self.config_repo.pause(config.id, paused_by)

        return TakeoverResponse(
            is_paused=config.is_paused,
            paused_at=config.paused_at,
            paused_by=config.paused_by,
            pending_messages_count=0,
        )

    async def resume_bot(self, account_id: uuid.UUID) -> TakeoverResponse:
        """Resume the chatbot after takeover.
        
        Requirements: 11.5 - Notify pending messages
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            TakeoverResponse with pending message count
        """
        config = await self.get_or_create_config(account_id)

        # Get pending messages count before resuming
        pending_count = 0
        if config.paused_at:
            pending = await self.interaction_repo.get_pending_during_pause(
                config.id,
                config.paused_at,
            )
            pending_count = len(pending)

        config = await self.config_repo.resume(config.id)

        return TakeoverResponse(
            is_paused=config.is_paused,
            paused_at=config.paused_at,
            paused_by=config.paused_by,
            pending_messages_count=pending_count,
        )

    # ============================================
    # Interaction Logs (Requirements: 11.4)
    # ============================================

    async def get_interaction_logs(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[ChatbotInteractionLog]:
        """Get interaction logs for an account.
        
        Requirements: 11.4 - Log interactions
        
        Args:
            account_id: YouTube account ID
            limit: Maximum logs to return
            
        Returns:
            List of interaction logs
        """
        config = await self.get_config(account_id)
        if config is None:
            return []
        return await self.interaction_repo.get_by_config(config.id, limit)
