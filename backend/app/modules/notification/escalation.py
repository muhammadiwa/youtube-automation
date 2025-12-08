"""Escalation logic for critical notifications.

Implements multi-channel escalation for critical issues.
Requirements: 23.4
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class EscalationConfig:
    """Configuration for an escalation level."""
    level: int
    channels: list[str]
    wait_minutes: int


@dataclass
class EscalationState:
    """Current state of notification escalation."""
    notification_id: uuid.UUID
    current_level: int
    max_level: int
    last_escalated_at: Optional[datetime]
    acknowledged: bool
    
    def should_escalate(self, wait_minutes: int) -> bool:
        """Check if notification should escalate to next level.
        
        Requirements: 23.4 - Multi-channel escalation
        
        Args:
            wait_minutes: Minutes to wait before escalating
            
        Returns:
            True if should escalate
        """
        if self.acknowledged:
            return False
        
        if self.current_level >= self.max_level:
            return False
        
        if self.last_escalated_at is None:
            return True
        
        time_since_escalation = datetime.utcnow() - self.last_escalated_at
        return time_since_escalation >= timedelta(minutes=wait_minutes)


def get_escalation_channels(
    rule_levels: list[dict],
    target_level: int,
) -> list[str]:
    """Get channels for a specific escalation level.
    
    Requirements: 23.4 - Multi-channel escalation
    
    Args:
        rule_levels: List of escalation level configurations
        target_level: Target escalation level
        
    Returns:
        List of channel names for the level
    """
    for level in rule_levels:
        if level.get("level") == target_level:
            return level.get("channels", [])
    return []


def get_escalation_wait_time(
    rule_levels: list[dict],
    current_level: int,
) -> int:
    """Get wait time before escalating to next level.
    
    Requirements: 23.4 - Multi-channel escalation
    
    Args:
        rule_levels: List of escalation level configurations
        current_level: Current escalation level
        
    Returns:
        Wait time in minutes
    """
    for level in rule_levels:
        if level.get("level") == current_level:
            return level.get("wait_minutes", 5)
    return 5  # Default 5 minutes


def should_escalate_notification(
    notification_status: str,
    notification_priority: str,
    acknowledged: bool,
    current_level: int,
    max_level: int,
    last_escalated_at: Optional[datetime],
    wait_minutes: int,
) -> bool:
    """Determine if a notification should be escalated.
    
    Requirements: 23.4 - Multi-channel escalation for critical issues
    
    Args:
        notification_status: Current notification status
        notification_priority: Notification priority
        acknowledged: Whether notification is acknowledged
        current_level: Current escalation level
        max_level: Maximum escalation level
        last_escalated_at: When last escalation occurred
        wait_minutes: Minutes to wait before escalating
        
    Returns:
        True if notification should be escalated
    """
    # Only escalate delivered but unacknowledged notifications
    if notification_status != "delivered":
        return False
    
    # Only escalate critical or high priority
    if notification_priority not in ("critical", "high"):
        return False
    
    # Don't escalate acknowledged notifications
    if acknowledged:
        return False
    
    # Check if at max level
    if current_level >= max_level:
        return False
    
    # Check wait time
    if last_escalated_at is None:
        return True
    
    time_since_escalation = datetime.utcnow() - last_escalated_at
    return time_since_escalation >= timedelta(minutes=wait_minutes)


def calculate_next_escalation_time(
    last_escalated_at: datetime,
    wait_minutes: int,
) -> datetime:
    """Calculate when next escalation should occur.
    
    Args:
        last_escalated_at: When last escalation occurred
        wait_minutes: Minutes to wait before escalating
        
    Returns:
        Datetime of next escalation
    """
    return last_escalated_at + timedelta(minutes=wait_minutes)


def get_max_escalation_level(rule_levels: list[dict]) -> int:
    """Get the maximum escalation level from rule configuration.
    
    Args:
        rule_levels: List of escalation level configurations
        
    Returns:
        Maximum level number
    """
    if not rule_levels:
        return 0
    
    return max(level.get("level", 0) for level in rule_levels)


def build_escalation_message(
    original_title: str,
    original_message: str,
    escalation_level: int,
) -> tuple[str, str]:
    """Build escalation message with level indicator.
    
    Requirements: 23.4 - Multi-channel escalation
    
    Args:
        original_title: Original notification title
        original_message: Original notification message
        escalation_level: Current escalation level
        
    Returns:
        Tuple of (escalated_title, escalated_message)
    """
    level_prefix = f"[ESCALATION LEVEL {escalation_level}]"
    
    escalated_title = f"{level_prefix} {original_title}"
    escalated_message = (
        f"{level_prefix}\n\n"
        f"This notification has been escalated due to no acknowledgment.\n\n"
        f"Original Message:\n{original_message}"
    )
    
    return escalated_title, escalated_message


def validate_escalation_rule(rule_levels: list[dict]) -> tuple[bool, Optional[str]]:
    """Validate escalation rule configuration.
    
    Args:
        rule_levels: List of escalation level configurations
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not rule_levels:
        return False, "Escalation rule must have at least one level"
    
    seen_levels = set()
    for level in rule_levels:
        level_num = level.get("level")
        
        if level_num is None:
            return False, "Each level must have a 'level' number"
        
        if level_num in seen_levels:
            return False, f"Duplicate level number: {level_num}"
        
        seen_levels.add(level_num)
        
        channels = level.get("channels", [])
        if not channels:
            return False, f"Level {level_num} must have at least one channel"
        
        wait_minutes = level.get("wait_minutes")
        if wait_minutes is None or wait_minutes < 1:
            return False, f"Level {level_num} must have wait_minutes >= 1"
    
    return True, None


def get_escalation_summary(
    notification_id: uuid.UUID,
    current_level: int,
    max_level: int,
    channels_notified: list[str],
    acknowledged: bool,
) -> dict:
    """Get summary of escalation state for a notification.
    
    Args:
        notification_id: Notification UUID
        current_level: Current escalation level
        max_level: Maximum escalation level
        channels_notified: List of channels that have been notified
        acknowledged: Whether notification is acknowledged
        
    Returns:
        Escalation summary dict
    """
    return {
        "notification_id": str(notification_id),
        "current_level": current_level,
        "max_level": max_level,
        "channels_notified": channels_notified,
        "acknowledged": acknowledged,
        "fully_escalated": current_level >= max_level,
        "can_escalate": not acknowledged and current_level < max_level,
    }
