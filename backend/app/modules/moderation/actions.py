"""Moderation actions for chat moderation.

Implements hide/delete messages, timeout users, and logging.
Requirements: 12.2, 12.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.modules.moderation.models import (
    ChatMessage,
    ModerationActionLog,
    ModerationActionType,
    ModerationRule,
    SeverityLevel,
)


class ModerationActionExecutor:
    """Executes moderation actions on chat messages.
    
    Requirements: 12.2, 12.5
    """

    def __init__(self):
        """Initialize the action executor."""
        self._action_handlers = {
            ModerationActionType.HIDE: self._execute_hide,
            ModerationActionType.DELETE: self._execute_delete,
            ModerationActionType.TIMEOUT: self._execute_timeout,
            ModerationActionType.WARN: self._execute_warn,
            ModerationActionType.BAN: self._execute_ban,
        }

    def execute_action(
        self,
        action_type: ModerationActionType,
        message: ChatMessage,
        rule: Optional[ModerationRule],
        reason: str,
        timeout_duration_seconds: Optional[int] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> ModerationActionLog:
        """Execute a moderation action on a message.
        
        Requirements: 12.2, 12.5
        
        Args:
            action_type: Type of action to execute
            message: Chat message to act on
            rule: Rule that triggered the action (optional)
            reason: Reason for the action
            timeout_duration_seconds: Duration for timeout action
            session_id: Stream session ID
            
        Returns:
            ModerationActionLog recording the action
        """
        processing_started = datetime.utcnow()
        
        # Execute the action
        handler = self._action_handlers.get(action_type)
        if handler:
            was_successful, error_message = handler(
                message,
                timeout_duration_seconds,
            )
        else:
            was_successful = False
            error_message = f"Unknown action type: {action_type}"

        processing_completed = datetime.utcnow()

        # Create action log (Requirements: 12.5)
        action_log = ModerationActionLog(
            id=uuid.uuid4(),
            rule_id=rule.id if rule else None,
            account_id=message.account_id,
            session_id=session_id,
            action_type=action_type.value,
            severity=rule.severity if rule else SeverityLevel.MEDIUM.value,
            user_channel_id=message.author_channel_id,
            user_display_name=message.author_display_name,
            message_id=message.youtube_message_id,
            message_content=message.content,
            reason=reason,
            was_successful=was_successful,
            error_message=error_message,
            timeout_duration_seconds=timeout_duration_seconds,
            processing_started_at=processing_started,
            processing_completed_at=processing_completed,
        )

        if timeout_duration_seconds and action_type == ModerationActionType.TIMEOUT:
            action_log.timeout_expires_at = datetime.utcnow() + timedelta(
                seconds=timeout_duration_seconds
            )

        return action_log

    def _execute_hide(
        self,
        message: ChatMessage,
        timeout_duration_seconds: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Execute hide action on a message.
        
        Requirements: 12.2
        
        Args:
            message: Message to hide
            timeout_duration_seconds: Not used for hide
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            message.is_hidden = True
            message.is_moderated = True
            message.moderated_at = datetime.utcnow()
            return True, None
        except Exception as e:
            return False, str(e)

    def _execute_delete(
        self,
        message: ChatMessage,
        timeout_duration_seconds: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Execute delete action on a message.
        
        Requirements: 12.2
        
        Args:
            message: Message to delete
            timeout_duration_seconds: Not used for delete
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            message.is_deleted = True
            message.is_moderated = True
            message.moderated_at = datetime.utcnow()
            return True, None
        except Exception as e:
            return False, str(e)

    def _execute_timeout(
        self,
        message: ChatMessage,
        timeout_duration_seconds: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Execute timeout action on a user.
        
        Requirements: 12.2
        
        Args:
            message: Message from user to timeout
            timeout_duration_seconds: Duration of timeout
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not timeout_duration_seconds:
                timeout_duration_seconds = 300  # Default 5 minutes
            
            # Mark message as moderated
            message.is_hidden = True
            message.is_moderated = True
            message.moderated_at = datetime.utcnow()
            
            # Note: Actual YouTube API timeout would be called here
            # This is a placeholder for the timeout logic
            return True, None
        except Exception as e:
            return False, str(e)

    def _execute_warn(
        self,
        message: ChatMessage,
        timeout_duration_seconds: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Execute warn action on a user.
        
        Args:
            message: Message from user to warn
            timeout_duration_seconds: Not used for warn
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Mark message as moderated but not hidden
            message.is_moderated = True
            message.moderated_at = datetime.utcnow()
            return True, None
        except Exception as e:
            return False, str(e)

    def _execute_ban(
        self,
        message: ChatMessage,
        timeout_duration_seconds: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """Execute ban action on a user.
        
        Args:
            message: Message from user to ban
            timeout_duration_seconds: Not used for ban
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Mark message as deleted
            message.is_deleted = True
            message.is_moderated = True
            message.moderated_at = datetime.utcnow()
            
            # Note: Actual YouTube API ban would be called here
            return True, None
        except Exception as e:
            return False, str(e)


def get_timeout_duration_for_severity(severity: SeverityLevel) -> int:
    """Get recommended timeout duration based on severity.
    
    Requirements: 12.2
    
    Args:
        severity: Severity level of violation
        
    Returns:
        Timeout duration in seconds
    """
    durations = {
        SeverityLevel.LOW: 60,       # 1 minute
        SeverityLevel.MEDIUM: 300,   # 5 minutes
        SeverityLevel.HIGH: 600,     # 10 minutes
        SeverityLevel.CRITICAL: 3600,  # 1 hour
    }
    return durations.get(severity, 300)


def get_action_for_severity(severity: SeverityLevel) -> ModerationActionType:
    """Get recommended action based on severity.
    
    Requirements: 12.2
    
    Args:
        severity: Severity level of violation
        
    Returns:
        Recommended action type
    """
    actions = {
        SeverityLevel.LOW: ModerationActionType.WARN,
        SeverityLevel.MEDIUM: ModerationActionType.HIDE,
        SeverityLevel.HIGH: ModerationActionType.TIMEOUT,
        SeverityLevel.CRITICAL: ModerationActionType.BAN,
    }
    return actions.get(severity, ModerationActionType.HIDE)


class UserModerationHistory:
    """Tracks user moderation history for escalation.
    
    Requirements: 12.2
    """

    def __init__(self):
        """Initialize history tracker."""
        self._violations: dict[str, list[datetime]] = {}
        self._timeouts: dict[str, list[datetime]] = {}

    def record_violation(self, user_channel_id: str) -> None:
        """Record a violation for a user.
        
        Args:
            user_channel_id: User's channel ID
        """
        if user_channel_id not in self._violations:
            self._violations[user_channel_id] = []
        self._violations[user_channel_id].append(datetime.utcnow())

    def record_timeout(self, user_channel_id: str) -> None:
        """Record a timeout for a user.
        
        Args:
            user_channel_id: User's channel ID
        """
        if user_channel_id not in self._timeouts:
            self._timeouts[user_channel_id] = []
        self._timeouts[user_channel_id].append(datetime.utcnow())

    def get_recent_violations(
        self,
        user_channel_id: str,
        minutes: int = 60,
    ) -> int:
        """Get count of recent violations for a user.
        
        Args:
            user_channel_id: User's channel ID
            minutes: Time window in minutes
            
        Returns:
            Number of violations in time window
        """
        if user_channel_id not in self._violations:
            return 0
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return sum(
            1 for v in self._violations[user_channel_id]
            if v >= cutoff
        )

    def should_escalate(
        self,
        user_channel_id: str,
        threshold: int = 3,
    ) -> bool:
        """Check if action should be escalated for a user.
        
        Args:
            user_channel_id: User's channel ID
            threshold: Number of violations before escalation
            
        Returns:
            True if should escalate
        """
        return self.get_recent_violations(user_channel_id) >= threshold

    def get_escalated_action(
        self,
        base_action: ModerationActionType,
    ) -> ModerationActionType:
        """Get escalated action type.
        
        Args:
            base_action: Original action type
            
        Returns:
            Escalated action type
        """
        escalation = {
            ModerationActionType.WARN: ModerationActionType.HIDE,
            ModerationActionType.HIDE: ModerationActionType.TIMEOUT,
            ModerationActionType.TIMEOUT: ModerationActionType.BAN,
            ModerationActionType.DELETE: ModerationActionType.TIMEOUT,
            ModerationActionType.BAN: ModerationActionType.BAN,
        }
        return escalation.get(base_action, ModerationActionType.TIMEOUT)
