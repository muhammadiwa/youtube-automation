"""Spam detection and slow mode management.

Implements spam pattern detection and auto slow mode.
Requirements: 12.3
"""

import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from app.modules.moderation.models import ChatMessage, SlowModeConfig


class SpamPattern:
    """Represents a spam detection pattern."""

    def __init__(
        self,
        name: str,
        pattern: re.Pattern,
        weight: float = 1.0,
    ):
        """Initialize spam pattern.
        
        Args:
            name: Pattern name
            pattern: Compiled regex pattern
            weight: Weight for spam score calculation
        """
        self.name = name
        self.pattern = pattern
        self.weight = weight

    def matches(self, content: str) -> bool:
        """Check if content matches this pattern.
        
        Args:
            content: Message content to check
            
        Returns:
            True if pattern matches
        """
        return bool(self.pattern.search(content))


# Default spam patterns
DEFAULT_SPAM_PATTERNS = [
    SpamPattern(
        "repeated_chars",
        re.compile(r"(.)\1{4,}"),  # 5+ repeated characters
        weight=1.0,
    ),
    SpamPattern(
        "repeated_words",
        re.compile(r"\b(\w+)\s+\1\s+\1\b", re.IGNORECASE),  # 3+ repeated words
        weight=1.5,
    ),
    SpamPattern(
        "all_caps",
        re.compile(r"^[A-Z\s!?.,]{20,}$"),  # Long all-caps message
        weight=0.8,
    ),
    SpamPattern(
        "excessive_punctuation",
        re.compile(r"[!?]{3,}"),  # 3+ exclamation/question marks
        weight=0.5,
    ),
    SpamPattern(
        "url_spam",
        re.compile(r"(https?://[^\s]+\s*){3,}"),  # 3+ URLs
        weight=2.0,
    ),
    SpamPattern(
        "ascii_art",
        re.compile(r"[^\w\s]{10,}"),  # Long sequences of special chars
        weight=1.0,
    ),
]


class SpamDetector:
    """Detects spam patterns in chat messages.
    
    Requirements: 12.3
    """

    def __init__(
        self,
        patterns: list[SpamPattern] = None,
        spam_threshold: float = 1.0,
    ):
        """Initialize spam detector.
        
        Args:
            patterns: List of spam patterns to check
            spam_threshold: Minimum score to consider as spam
        """
        self.patterns = patterns or DEFAULT_SPAM_PATTERNS
        self.spam_threshold = spam_threshold

    def calculate_spam_score(self, content: str) -> tuple[float, list[str]]:
        """Calculate spam score for message content.
        
        Args:
            content: Message content to analyze
            
        Returns:
            Tuple of (spam_score, matched_patterns)
        """
        score = 0.0
        matched = []

        for pattern in self.patterns:
            if pattern.matches(content):
                score += pattern.weight
                matched.append(pattern.name)

        return score, matched

    def is_spam(self, content: str) -> tuple[bool, float, list[str]]:
        """Check if content is spam.
        
        Args:
            content: Message content to check
            
        Returns:
            Tuple of (is_spam, score, matched_patterns)
        """
        score, matched = self.calculate_spam_score(content)
        return score >= self.spam_threshold, score, matched


class MessageRateTracker:
    """Tracks message rates per user for spam detection.
    
    Requirements: 12.3
    """

    def __init__(self, window_seconds: int = 60):
        """Initialize rate tracker.
        
        Args:
            window_seconds: Time window for rate calculation
        """
        self.window_seconds = window_seconds
        self._messages: dict[str, list[datetime]] = defaultdict(list)

    def record_message(self, user_id: str) -> None:
        """Record a message from a user.
        
        Args:
            user_id: User's channel ID
        """
        self._messages[user_id].append(datetime.utcnow())
        self._cleanup(user_id)

    def get_rate(self, user_id: str) -> int:
        """Get message rate for a user.
        
        Args:
            user_id: User's channel ID
            
        Returns:
            Number of messages in the time window
        """
        self._cleanup(user_id)
        return len(self._messages[user_id])

    def _cleanup(self, user_id: str) -> None:
        """Remove old messages outside the time window.
        
        Args:
            user_id: User's channel ID
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        self._messages[user_id] = [
            ts for ts in self._messages[user_id]
            if ts >= cutoff
        ]

    def is_rate_exceeded(self, user_id: str, threshold: int) -> bool:
        """Check if user's message rate exceeds threshold.
        
        Args:
            user_id: User's channel ID
            threshold: Maximum messages allowed in window
            
        Returns:
            True if rate exceeded
        """
        return self.get_rate(user_id) >= threshold


class DuplicateMessageDetector:
    """Detects duplicate/similar messages from users.
    
    Requirements: 12.3
    """

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        window_seconds: int = 300,
    ):
        """Initialize duplicate detector.
        
        Args:
            similarity_threshold: Minimum similarity to consider duplicate
            window_seconds: Time window to check for duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.window_seconds = window_seconds
        self._recent_messages: dict[str, list[tuple[str, datetime]]] = defaultdict(list)

    def record_message(self, user_id: str, content: str) -> None:
        """Record a message from a user.
        
        Args:
            user_id: User's channel ID
            content: Message content
        """
        self._recent_messages[user_id].append((content, datetime.utcnow()))
        self._cleanup(user_id)

    def is_duplicate(self, user_id: str, content: str) -> bool:
        """Check if message is a duplicate.
        
        Args:
            user_id: User's channel ID
            content: Message content to check
            
        Returns:
            True if message is similar to recent messages
        """
        self._cleanup(user_id)
        
        for prev_content, _ in self._recent_messages[user_id]:
            if self._calculate_similarity(content, prev_content) >= self.similarity_threshold:
                return True
        
        return False

    def _cleanup(self, user_id: str) -> None:
        """Remove old messages outside the time window.
        
        Args:
            user_id: User's channel ID
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        self._recent_messages[user_id] = [
            (content, ts) for content, ts in self._recent_messages[user_id]
            if ts >= cutoff
        ]

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings.
        
        Uses simple character-based similarity.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not s1 or not s2:
            return 0.0
        
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        
        if s1_lower == s2_lower:
            return 1.0
        
        # Simple Jaccard similarity on character sets
        set1 = set(s1_lower)
        set2 = set(s2_lower)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


class SlowModeManager:
    """Manages slow mode activation and deactivation.
    
    Requirements: 12.3
    """

    def __init__(self):
        """Initialize slow mode manager."""
        self._rate_trackers: dict[uuid.UUID, MessageRateTracker] = {}
        self._spam_detectors: dict[uuid.UUID, SpamDetector] = {}

    def get_rate_tracker(self, account_id: uuid.UUID) -> MessageRateTracker:
        """Get or create rate tracker for an account.
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            MessageRateTracker for the account
        """
        if account_id not in self._rate_trackers:
            self._rate_trackers[account_id] = MessageRateTracker()
        return self._rate_trackers[account_id]

    def get_spam_detector(self, account_id: uuid.UUID) -> SpamDetector:
        """Get or create spam detector for an account.
        
        Args:
            account_id: YouTube account ID
            
        Returns:
            SpamDetector for the account
        """
        if account_id not in self._spam_detectors:
            self._spam_detectors[account_id] = SpamDetector()
        return self._spam_detectors[account_id]

    def should_enable_slow_mode(
        self,
        account_id: uuid.UUID,
        config: SlowModeConfig,
        recent_spam_count: int,
    ) -> bool:
        """Check if slow mode should be enabled.
        
        Requirements: 12.3
        
        Args:
            account_id: YouTube account ID
            config: Slow mode configuration
            recent_spam_count: Number of recent spam messages
            
        Returns:
            True if slow mode should be enabled
        """
        if not config.auto_enable:
            return False
        
        if config.is_currently_active:
            return False
        
        return recent_spam_count >= config.spam_threshold_per_minute

    def should_disable_slow_mode(self, config: SlowModeConfig) -> bool:
        """Check if slow mode should be disabled.
        
        Args:
            config: Slow mode configuration
            
        Returns:
            True if slow mode should be disabled
        """
        if not config.is_currently_active:
            return False
        
        return config.should_auto_disable()

    def process_message(
        self,
        account_id: uuid.UUID,
        message: ChatMessage,
        config: SlowModeConfig,
    ) -> tuple[bool, bool, Optional[str]]:
        """Process a message for spam detection.
        
        Args:
            account_id: YouTube account ID
            message: Chat message to process
            config: Slow mode configuration
            
        Returns:
            Tuple of (is_spam, should_enable_slow_mode, spam_reason)
        """
        # Track message rate
        rate_tracker = self.get_rate_tracker(account_id)
        rate_tracker.record_message(message.author_channel_id)
        
        # Check for spam
        spam_detector = self.get_spam_detector(account_id)
        is_spam, score, patterns = spam_detector.is_spam(message.content)
        
        spam_reason = None
        if is_spam:
            spam_reason = f"Spam detected (score: {score:.1f}, patterns: {', '.join(patterns)})"
        
        # Check if slow mode should be enabled
        # Count spam messages in the last minute
        spam_count = rate_tracker.get_rate(message.author_channel_id) if is_spam else 0
        should_enable = self.should_enable_slow_mode(account_id, config, spam_count)
        
        return is_spam, should_enable, spam_reason
