"""Service for chat moderation.

Implements real-time chat analysis and moderation actions.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.moderation.models import (
    ChatMessage,
    CustomCommand,
    ModerationActionLog,
    ModerationActionType,
    ModerationRule,
    RuleType,
    SeverityLevel,
    SlowModeConfig,
)
from app.modules.moderation.repository import (
    ChatMessageRepository,
    CustomCommandRepository,
    ModerationActionLogRepository,
    ModerationRuleRepository,
    SlowModeConfigRepository,
)
from app.modules.moderation.schemas import (
    ModerationAnalysisResult,
    RuleViolation,
)


class ChatAnalyzer:
    """Analyzes chat messages against moderation rules.
    
    Requirements: 12.1 - Analyze messages within 2 seconds
    """

    def __init__(self, rules: list[ModerationRule]):
        """Initialize analyzer with rules.
        
        Args:
            rules: List of moderation rules to check against
        """
        self.rules = rules
        self._compiled_patterns: dict[uuid.UUID, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for rule in self.rules:
            if rule.is_regex_rule() and rule.pattern:
                try:
                    self._compiled_patterns[rule.id] = re.compile(
                        rule.pattern, re.IGNORECASE
                    )
                except re.error:
                    # Invalid regex, skip
                    pass

    def analyze(self, message: ChatMessage) -> ModerationAnalysisResult:
        """Analyze a chat message against all rules.
        
        Args:
            message: Chat message to analyze
            
        Returns:
            ModerationAnalysisResult with violations found
        """
        start_time = time.time()
        violations: list[RuleViolation] = []
        content = message.content

        for rule in self.rules:
            if not rule.is_enabled:
                continue

            violation = self._check_rule(rule, content)
            if violation:
                violations.append(violation)

        processing_time_ms = (time.time() - start_time) * 1000

        # Determine recommended action based on highest severity violation
        recommended_action = None
        recommended_severity = None
        if violations:
            # Sort by severity (critical > high > medium > low)
            severity_order = {
                SeverityLevel.CRITICAL.value: 4,
                SeverityLevel.HIGH.value: 3,
                SeverityLevel.MEDIUM.value: 2,
                SeverityLevel.LOW.value: 1,
            }
            violations.sort(
                key=lambda v: severity_order.get(v.severity.value, 0),
                reverse=True,
            )
            recommended_action = violations[0].action_type
            recommended_severity = violations[0].severity

        return ModerationAnalysisResult(
            message_id=message.youtube_message_id,
            is_violation=len(violations) > 0,
            violations=violations,
            processing_time_ms=processing_time_ms,
            recommended_action=recommended_action,
            recommended_severity=recommended_severity,
        )

    def _check_rule(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[RuleViolation]:
        """Check a single rule against message content.
        
        Args:
            rule: Rule to check
            content: Message content
            
        Returns:
            RuleViolation if rule is violated, None otherwise
        """
        matched_pattern = None

        if rule.is_keyword_rule():
            matched_pattern = self._check_keywords(rule, content)
        elif rule.is_regex_rule():
            matched_pattern = self._check_regex(rule, content)
        elif rule.is_spam_rule():
            matched_pattern = self._check_spam(rule, content)
        elif rule.is_caps_rule():
            matched_pattern = self._check_caps(rule, content)
        elif rule.is_links_rule():
            matched_pattern = self._check_links(rule, content)

        if matched_pattern is not None:
            return RuleViolation(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=RuleType(rule.rule_type),
                severity=SeverityLevel(rule.severity),
                action_type=ModerationActionType(rule.action_type),
                matched_pattern=matched_pattern,
                timeout_duration_seconds=rule.timeout_duration_seconds,
            )

        return None

    def _check_keywords(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[str]:
        """Check for keyword matches."""
        if not rule.keywords:
            return None

        content_lower = content.lower()
        for keyword in rule.keywords:
            if keyword.lower() in content_lower:
                return keyword
        return None

    def _check_regex(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[str]:
        """Check for regex pattern matches."""
        pattern = self._compiled_patterns.get(rule.id)
        if pattern:
            match = pattern.search(content)
            if match:
                return match.group()
        return None

    def _check_spam(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[str]:
        """Check for spam patterns.
        
        Detects:
        - Repeated characters (e.g., "aaaaaaa")
        - Repeated words (e.g., "buy buy buy buy")
        - Excessive emojis
        """
        # Check for repeated characters (5+ same char in a row)
        if re.search(r"(.)\1{4,}", content):
            return "repeated_characters"

        # Check for repeated words (3+ same word in a row)
        words = content.lower().split()
        if len(words) >= 3:
            for i in range(len(words) - 2):
                if words[i] == words[i + 1] == words[i + 2]:
                    return f"repeated_word:{words[i]}"

        # Check for excessive emojis (configurable via settings)
        settings = rule.settings or {}
        max_emojis = settings.get("max_emojis", 10)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE,
        )
        emojis = emoji_pattern.findall(content)
        total_emojis = sum(len(e) for e in emojis)
        if total_emojis > max_emojis:
            return f"excessive_emojis:{total_emojis}"

        return None

    def _check_caps(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[str]:
        """Check for excessive caps."""
        min_length = rule.min_message_length or 5
        if len(content) < min_length:
            return None

        # Count uppercase letters
        letters = [c for c in content if c.isalpha()]
        if not letters:
            return None

        uppercase_count = sum(1 for c in letters if c.isupper())
        caps_percent = (uppercase_count / len(letters)) * 100

        threshold = rule.caps_threshold_percent or 70
        if caps_percent >= threshold:
            return f"caps:{caps_percent:.0f}%"

        return None

    def _check_links(
        self,
        rule: ModerationRule,
        content: str,
    ) -> Optional[str]:
        """Check for links."""
        # URL pattern
        url_pattern = re.compile(
            r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*",
            re.IGNORECASE,
        )
        
        settings = rule.settings or {}
        allowed_domains = settings.get("allowed_domains", [])
        
        matches = url_pattern.findall(content)
        for match in matches:
            # Check if domain is allowed
            is_allowed = False
            for domain in allowed_domains:
                if domain.lower() in match.lower():
                    is_allowed = True
                    break
            
            if not is_allowed:
                return match

        return None



class ModerationService:
    """Service for chat moderation operations.
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize moderation service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.rule_repo = ModerationRuleRepository(session)
        self.action_log_repo = ModerationActionLogRepository(session)
        self.message_repo = ChatMessageRepository(session)
        self.slow_mode_repo = SlowModeConfigRepository(session)
        self.command_repo = CustomCommandRepository(session)

    # ============================================
    # Rule Management
    # ============================================

    async def create_rule(
        self,
        account_id: uuid.UUID,
        name: str,
        rule_type: RuleType,
        action_type: ModerationActionType = ModerationActionType.HIDE,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        pattern: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        settings: Optional[dict] = None,
        caps_threshold_percent: Optional[int] = None,
        min_message_length: Optional[int] = None,
        timeout_duration_seconds: Optional[int] = None,
        description: Optional[str] = None,
        priority: int = 0,
    ) -> ModerationRule:
        """Create a new moderation rule.
        
        Args:
            account_id: YouTube account ID
            name: Rule name
            rule_type: Type of rule
            action_type: Action to take on violation
            severity: Severity level
            pattern: Regex pattern (for REGEX type)
            keywords: Keywords to match (for KEYWORD type)
            settings: Additional settings
            caps_threshold_percent: Caps threshold (for CAPS type)
            min_message_length: Minimum message length to check
            timeout_duration_seconds: Timeout duration (for TIMEOUT action)
            description: Rule description
            priority: Rule priority (higher = checked first)
            
        Returns:
            Created ModerationRule
        """
        rule = ModerationRule(
            account_id=account_id,
            name=name,
            rule_type=rule_type.value,
            action_type=action_type.value,
            severity=severity.value,
            pattern=pattern,
            keywords=keywords,
            settings=settings,
            caps_threshold_percent=caps_threshold_percent,
            min_message_length=min_message_length,
            timeout_duration_seconds=timeout_duration_seconds,
            description=description,
            priority=priority,
        )
        return await self.rule_repo.create(rule)

    async def get_rules(
        self,
        account_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[ModerationRule]:
        """Get moderation rules for an account.
        
        Args:
            account_id: YouTube account ID
            enabled_only: Only return enabled rules
            
        Returns:
            List of moderation rules
        """
        return await self.rule_repo.get_by_account(account_id, enabled_only)

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ModerationRule]:
        """Update a moderation rule.
        
        Args:
            rule_id: Rule ID
            **kwargs: Fields to update
            
        Returns:
            Updated rule or None if not found
        """
        return await self.rule_repo.update(rule_id, **kwargs)

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        """Delete a moderation rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if deleted, False if not found
        """
        return await self.rule_repo.delete(rule_id)

    # ============================================
    # Real-time Chat Analysis (Requirements: 12.1)
    # ============================================

    async def analyze_message(
        self,
        message: ChatMessage,
        rules: Optional[list[ModerationRule]] = None,
    ) -> ModerationAnalysisResult:
        """Analyze a chat message against moderation rules.
        
        Requirements: 12.1 - Analyze messages within 2 seconds
        
        Args:
            message: Chat message to analyze
            rules: Optional list of rules (fetches from DB if not provided)
            
        Returns:
            ModerationAnalysisResult with violations found
        """
        if rules is None:
            rules = await self.get_rules(message.account_id, enabled_only=True)

        analyzer = ChatAnalyzer(rules)
        return analyzer.analyze(message)

    async def process_message(
        self,
        message: ChatMessage,
        session_id: Optional[uuid.UUID] = None,
        auto_moderate: bool = True,
    ) -> tuple[ChatMessage, ModerationAnalysisResult]:
        """Process a chat message: store, analyze, and optionally moderate.
        
        Requirements: 12.1, 12.2
        
        Args:
            message: Chat message to process
            session_id: Stream session ID
            auto_moderate: Whether to automatically apply moderation actions
            
        Returns:
            Tuple of (stored message, analysis result)
        """
        # Store the message
        message.session_id = session_id
        stored_message = await self.message_repo.create(message)

        # Get rules and analyze
        rules = await self.get_rules(message.account_id, enabled_only=True)
        result = await self.analyze_message(stored_message, rules)

        # Update message with analysis results
        violated_rule_ids = [str(v.rule_id) for v in result.violations]
        await self.message_repo.update_moderation_status(
            stored_message.id,
            is_moderated=result.is_violation and auto_moderate,
            is_hidden=result.is_violation and auto_moderate,
            reason=f"Violated rules: {', '.join(v.rule_name for v in result.violations)}" if result.violations else None,
            violated_rules=violated_rule_ids if violated_rule_ids else None,
        )

        # Apply moderation action if violations found
        if result.is_violation and auto_moderate:
            await self._apply_moderation_action(
                stored_message,
                result,
                session_id,
            )

        # Check for spam and potentially enable slow mode
        await self._check_spam_rate(message.account_id, message.author_channel_id)

        return stored_message, result

    async def _apply_moderation_action(
        self,
        message: ChatMessage,
        result: ModerationAnalysisResult,
        session_id: Optional[uuid.UUID],
    ) -> ModerationActionLog:
        """Apply moderation action based on analysis result.
        
        Requirements: 12.2, 12.5
        
        Args:
            message: Chat message
            result: Analysis result
            session_id: Stream session ID
            
        Returns:
            Created action log
        """
        if not result.violations:
            raise ValueError("No violations to act on")

        # Use the highest severity violation
        violation = result.violations[0]
        processing_started = datetime.utcnow()

        # Create action log
        action_log = ModerationActionLog(
            rule_id=violation.rule_id,
            account_id=message.account_id,
            session_id=session_id,
            action_type=violation.action_type.value,
            severity=violation.severity.value,
            user_channel_id=message.author_channel_id,
            user_display_name=message.author_display_name,
            message_id=message.youtube_message_id,
            message_content=message.content,
            reason=f"Rule '{violation.rule_name}' violated: {violation.matched_pattern or 'pattern match'}",
            was_successful=True,
            timeout_duration_seconds=violation.timeout_duration_seconds,
            processing_started_at=processing_started,
            processing_completed_at=datetime.utcnow(),
        )

        if violation.timeout_duration_seconds:
            action_log.timeout_expires_at = datetime.utcnow() + timedelta(
                seconds=violation.timeout_duration_seconds
            )

        # Increment rule trigger count
        await self.rule_repo.increment_trigger_count(violation.rule_id)

        return await self.action_log_repo.create(action_log)

    # ============================================
    # Spam Detection & Slow Mode (Requirements: 12.3)
    # ============================================

    async def _check_spam_rate(
        self,
        account_id: uuid.UUID,
        author_channel_id: str,
    ) -> None:
        """Check spam rate and potentially enable slow mode.
        
        Requirements: 12.3
        
        Args:
            account_id: YouTube account ID
            author_channel_id: Author's channel ID
        """
        config = await self.slow_mode_repo.get_or_create(account_id)
        
        if not config.auto_enable or config.is_currently_active:
            return

        # Get recent messages from this author
        recent_messages = await self.message_repo.get_recent_by_author(
            account_id,
            author_channel_id,
            minutes=1,
        )

        # Check if spam threshold exceeded
        if len(recent_messages) >= config.spam_threshold_per_minute:
            await self.enable_slow_mode(account_id)

    async def enable_slow_mode(self, account_id: uuid.UUID) -> SlowModeConfig:
        """Enable slow mode for an account.
        
        Requirements: 12.3
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            Updated slow mode config
        """
        config = await self.slow_mode_repo.get_or_create(account_id)
        config.activate()
        await self.session.flush()
        return config

    async def disable_slow_mode(self, account_id: uuid.UUID) -> SlowModeConfig:
        """Disable slow mode for an account.
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            Updated slow mode config
        """
        config = await self.slow_mode_repo.get_or_create(account_id)
        config.deactivate()
        await self.session.flush()
        return config

    async def get_slow_mode_config(
        self,
        account_id: uuid.UUID,
    ) -> SlowModeConfig:
        """Get slow mode configuration for an account.
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            Slow mode configuration
        """
        return await self.slow_mode_repo.get_or_create(account_id)

    async def update_slow_mode_config(
        self,
        account_id: uuid.UUID,
        **kwargs,
    ) -> Optional[SlowModeConfig]:
        """Update slow mode configuration.
        
        Args:
            account_id: YouTube account ID
            **kwargs: Fields to update
            
        Returns:
            Updated config or None
        """
        return await self.slow_mode_repo.update(account_id, **kwargs)

    # ============================================
    # Custom Commands (Requirements: 12.4)
    # ============================================

    async def create_command(
        self,
        account_id: uuid.UUID,
        trigger: str,
        response_text: Optional[str] = None,
        response_type: str = "text",
        description: Optional[str] = None,
        action_type: Optional[str] = None,
        webhook_url: Optional[str] = None,
        moderator_only: bool = False,
        member_only: bool = False,
        cooldown_seconds: int = 5,
    ) -> CustomCommand:
        """Create a custom command.
        
        Requirements: 12.4
        
        Args:
            account_id: YouTube account ID
            trigger: Command trigger (e.g., "!help")
            response_text: Response text
            response_type: Type of response
            description: Command description
            action_type: Action type
            webhook_url: Webhook URL for webhook responses
            moderator_only: Only moderators can use
            member_only: Only members can use
            cooldown_seconds: Cooldown between uses
            
        Returns:
            Created CustomCommand
        """
        command = CustomCommand(
            account_id=account_id,
            trigger=trigger,
            response_text=response_text,
            response_type=response_type,
            description=description,
            action_type=action_type,
            webhook_url=webhook_url,
            moderator_only=moderator_only,
            member_only=member_only,
            cooldown_seconds=cooldown_seconds,
        )
        return await self.command_repo.create(command)

    async def get_commands(
        self,
        account_id: uuid.UUID,
        enabled_only: bool = True,
    ) -> list[CustomCommand]:
        """Get custom commands for an account.
        
        Args:
            account_id: YouTube account ID
            enabled_only: Only return enabled commands
            
        Returns:
            List of custom commands
        """
        return await self.command_repo.get_by_account(account_id, enabled_only)

    async def process_command(
        self,
        account_id: uuid.UUID,
        message_content: str,
        is_moderator: bool = False,
        is_member: bool = False,
        is_owner: bool = False,
    ) -> Optional[tuple[CustomCommand, str]]:
        """Process a potential command message.
        
        Requirements: 12.4
        
        Args:
            account_id: YouTube account ID
            message_content: Message content
            is_moderator: Whether sender is moderator
            is_member: Whether sender is member
            is_owner: Whether sender is owner
            
        Returns:
            Tuple of (command, response) if command found, None otherwise
        """
        # Check if message starts with a command trigger
        if not message_content.startswith("!"):
            return None

        # Extract trigger
        parts = message_content.split(maxsplit=1)
        trigger = parts[0]

        # Find matching command
        command = await self.command_repo.get_by_trigger(account_id, trigger)
        if not command:
            return None

        # Check permissions
        if not command.can_be_used_by(is_moderator, is_member, is_owner):
            return None

        # Check cooldown
        if command.is_on_cooldown():
            return None

        # Record usage
        await self.command_repo.record_usage(command.id)

        # Generate response
        response = command.response_text or ""
        return command, response

    async def update_command(
        self,
        command_id: uuid.UUID,
        **kwargs,
    ) -> Optional[CustomCommand]:
        """Update a custom command.
        
        Args:
            command_id: Command ID
            **kwargs: Fields to update
            
        Returns:
            Updated command or None
        """
        return await self.command_repo.update(command_id, **kwargs)

    async def delete_command(self, command_id: uuid.UUID) -> bool:
        """Delete a custom command.
        
        Args:
            command_id: Command ID
            
        Returns:
            True if deleted, False if not found
        """
        return await self.command_repo.delete(command_id)

    # ============================================
    # Action Logs (Requirements: 12.5)
    # ============================================

    async def get_action_logs(
        self,
        account_id: uuid.UUID,
        limit: int = 100,
    ) -> list[ModerationActionLog]:
        """Get moderation action logs for an account.
        
        Requirements: 12.5
        
        Args:
            account_id: YouTube account ID
            limit: Maximum number of logs to return
            
        Returns:
            List of action logs
        """
        return await self.action_log_repo.get_by_account(account_id, limit)

    async def get_user_action_logs(
        self,
        account_id: uuid.UUID,
        user_channel_id: str,
        limit: int = 50,
    ) -> list[ModerationActionLog]:
        """Get moderation action logs for a specific user.
        
        Args:
            account_id: YouTube account ID
            user_channel_id: User's channel ID
            limit: Maximum number of logs to return
            
        Returns:
            List of action logs
        """
        return await self.action_log_repo.get_by_user(
            account_id,
            user_channel_id,
            limit,
        )
