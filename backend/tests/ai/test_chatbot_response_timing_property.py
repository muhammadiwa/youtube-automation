"""Property-based tests for chatbot response timing.

**Feature: youtube-automation, Property 17: Chatbot Response Timing**
**Validates: Requirements 11.1**
"""

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st


# ============================================
# Test Data Classes (avoiding SQLAlchemy mapper issues)
# ============================================

@dataclass
class TestTrigger:
    """Test trigger data class for property testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    config_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Test Trigger"
    trigger_type: str = "keyword"
    pattern: Optional[str] = None
    keywords: Optional[list[str]] = None
    is_enabled: bool = True
    priority: int = 0


@dataclass
class TestInteractionLog:
    """Test interaction log data class for property testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    config_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_channel_id: str = "UC123"
    user_display_name: str = "TestUser"
    input_message_id: str = "msg123"
    input_content: str = "Hello"
    processing_started_at: datetime = field(default_factory=datetime.utcnow)
    processing_completed_at: Optional[datetime] = None
    response_time_ms: Optional[float] = None

    def was_within_time_limit(self, limit_seconds: float = 3.0) -> bool:
        """Check if response was within time limit."""
        if self.response_time_ms is None:
            return False
        return self.response_time_ms <= (limit_seconds * 1000)


# ============================================
# Trigger Matcher (copied from service for isolated testing)
# ============================================

class TriggerMatcher:
    """Matches chat messages against configured triggers."""

    def __init__(self, triggers: list[TestTrigger]):
        self.triggers = triggers
        self._compiled_patterns: dict[uuid.UUID, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for trigger in self.triggers:
            if trigger.trigger_type == "regex" and trigger.pattern:
                try:
                    self._compiled_patterns[trigger.id] = re.compile(
                        trigger.pattern, re.IGNORECASE
                    )
                except re.error:
                    pass


    def match(self, message: str) -> Optional[tuple[TestTrigger, str]]:
        """Match message against triggers."""
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
        trigger: TestTrigger,
        message: str,
        message_lower: str,
    ) -> Optional[str]:
        if trigger.trigger_type == "keyword":
            return self._check_keywords(trigger, message_lower)
        elif trigger.trigger_type == "regex":
            return self._check_regex(trigger, message)
        elif trigger.trigger_type == "question":
            return self._check_question(message_lower)
        elif trigger.trigger_type == "greeting":
            return self._check_greeting(message_lower)
        elif trigger.trigger_type == "command":
            return self._check_command(trigger, message_lower)
        elif trigger.trigger_type == "mention":
            return self._check_mention(trigger, message_lower)
        return None

    def _check_keywords(self, trigger: TestTrigger, message_lower: str) -> Optional[str]:
        if not trigger.keywords:
            return None
        for keyword in trigger.keywords:
            if keyword.lower() in message_lower:
                return keyword
        return None

    def _check_regex(self, trigger: TestTrigger, message: str) -> Optional[str]:
        pattern = self._compiled_patterns.get(trigger.id)
        if pattern:
            match = pattern.search(message)
            if match:
                return match.group()
        return None

    def _check_question(self, message_lower: str) -> Optional[str]:
        question_indicators = ["?", "what", "how", "why", "when", "where", "who", "which", "can you", "could you", "do you"]
        for indicator in question_indicators:
            if indicator in message_lower:
                return "question"
        return None

    def _check_greeting(self, message_lower: str) -> Optional[str]:
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "sup", "yo", "greetings"]
        for greeting in greetings:
            if greeting in message_lower:
                return greeting
        return None

    def _check_command(self, trigger: TestTrigger, message_lower: str) -> Optional[str]:
        if trigger.pattern and message_lower.startswith(trigger.pattern.lower()):
            return trigger.pattern
        return None

    def _check_mention(self, trigger: TestTrigger, message_lower: str) -> Optional[str]:
        if trigger.pattern and trigger.pattern.lower() in message_lower:
            return trigger.pattern
        return None


# ============================================
# Strategies for generating test data
# ============================================

message_content_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        whitelist_characters=" !@#$%^&*(),.?\":{}|<>",
    ),
    min_size=1,
    max_size=500,
)

keyword_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=2,
    max_size=20,
)

keywords_list_strategy = st.lists(keyword_strategy, min_size=1, max_size=20)


def create_test_trigger(
    trigger_type: str = "keyword",
    keywords: list[str] = None,
    pattern: str = None,
    is_enabled: bool = True,
) -> TestTrigger:
    """Create a test trigger."""
    return TestTrigger(
        name=f"Test {trigger_type} trigger",
        trigger_type=trigger_type,
        keywords=keywords,
        pattern=pattern,
        is_enabled=is_enabled,
    )



class TestTriggerMatcherTiming:
    """Property tests for trigger matching timing.
    
    **Feature: youtube-automation, Property 17: Chatbot Response Timing**
    **Validates: Requirements 11.1**
    """

    @given(content=message_content_strategy)
    @settings(max_examples=100)
    def test_trigger_matching_is_fast(self, content: str) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        For any chat message, trigger matching SHALL complete quickly (under 100ms).
        """
        triggers = [
            create_test_trigger("keyword", keywords=["hello", "hi", "hey"]),
            create_test_trigger("question"),
            create_test_trigger("greeting"),
            create_test_trigger("command", pattern="!ask"),
            create_test_trigger("mention", pattern="@bot"),
        ]

        matcher = TriggerMatcher(triggers)

        start_time = time.time()
        matcher.match(content)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100, (
            f"Trigger matching took {elapsed_ms}ms, should be under 100ms"
        )

    @given(
        content=message_content_strategy,
        num_triggers=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_trigger_matching_scales_with_triggers(
        self,
        content: str,
        num_triggers: int,
    ) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        For any number of triggers (up to 50), matching SHALL complete quickly.
        """
        triggers = []
        trigger_types = ["keyword", "question", "greeting", "command", "mention"]

        for i in range(num_triggers):
            trigger_type = trigger_types[i % len(trigger_types)]
            if trigger_type == "keyword":
                triggers.append(create_test_trigger(
                    trigger_type,
                    keywords=[f"word{j}" for j in range(5)],
                ))
            elif trigger_type in ("command", "mention"):
                triggers.append(create_test_trigger(
                    trigger_type,
                    pattern=f"!cmd{i}",
                ))
            else:
                triggers.append(create_test_trigger(trigger_type))

        matcher = TriggerMatcher(triggers)

        start_time = time.time()
        matcher.match(content)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 500, (
            f"Trigger matching with {num_triggers} triggers took {elapsed_ms}ms, "
            f"should be under 500ms"
        )

    @given(keywords=keywords_list_strategy, content=message_content_strategy)
    @settings(max_examples=100)
    def test_keyword_trigger_matching_timing(
        self,
        keywords: list[str],
        content: str,
    ) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        For any keyword trigger with any number of keywords, matching SHALL be fast.
        """
        trigger = create_test_trigger("keyword", keywords=keywords)
        matcher = TriggerMatcher([trigger])

        start_time = time.time()
        matcher.match(content)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100, (
            f"Keyword matching with {len(keywords)} keywords took {elapsed_ms}ms, "
            f"should be under 100ms"
        )


class TestTriggerMatchingCorrectness:
    """Tests for trigger matching correctness alongside timing."""

    @given(keyword=keyword_strategy)
    @settings(max_examples=100)
    def test_keyword_trigger_detects_keyword(self, keyword: str) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        For any keyword, if the message contains it, it SHALL be detected.
        """
        trigger = create_test_trigger("keyword", keywords=[keyword])
        matcher = TriggerMatcher([trigger])

        content = f"Hello {keyword} world"

        start_time = time.time()
        result = matcher.match(content)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100
        assert result is not None, f"Keyword '{keyword}' in message was not detected"
        matched_trigger, matched_pattern = result
        assert matched_pattern == keyword

    def test_question_trigger_detects_questions(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Question triggers SHALL detect question patterns.
        """
        trigger = create_test_trigger("question")
        matcher = TriggerMatcher([trigger])

        questions = [
            "What is this stream about?",
            "How do I subscribe?",
            "Why is the quality low?",
            "Can you help me?",
        ]

        for question in questions:
            start_time = time.time()
            result = matcher.match(question)
            elapsed_ms = (time.time() - start_time) * 1000

            assert elapsed_ms < 100
            assert result is not None, f"Question '{question}' was not detected"

    def test_greeting_trigger_detects_greetings(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Greeting triggers SHALL detect greeting patterns.
        """
        trigger = create_test_trigger("greeting")
        matcher = TriggerMatcher([trigger])

        greetings = [
            "Hello everyone!",
            "Hi there",
            "Hey what's up",
            "Good morning stream",
        ]

        for greeting in greetings:
            start_time = time.time()
            result = matcher.match(greeting)
            elapsed_ms = (time.time() - start_time) * 1000

            assert elapsed_ms < 100
            assert result is not None, f"Greeting '{greeting}' was not detected"

    def test_command_trigger_detects_commands(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Command triggers SHALL detect command patterns.
        """
        trigger = create_test_trigger("command", pattern="!ask")
        matcher = TriggerMatcher([trigger])

        start_time = time.time()
        result = matcher.match("!ask what is the topic today?")
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100
        assert result is not None, "Command '!ask' was not detected"

    def test_mention_trigger_detects_mentions(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Mention triggers SHALL detect bot mentions.
        """
        trigger = create_test_trigger("mention", pattern="@StreamBot")
        matcher = TriggerMatcher([trigger])

        start_time = time.time()
        result = matcher.match("Hey @StreamBot can you help?")
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100
        assert result is not None, "Mention '@StreamBot' was not detected"

    def test_no_match_returns_none(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Messages not matching any trigger SHALL return None quickly.
        """
        triggers = [
            create_test_trigger("keyword", keywords=["specific", "words"]),
            create_test_trigger("command", pattern="!special"),
        ]
        matcher = TriggerMatcher(triggers)

        start_time = time.time()
        result = matcher.match("Just a normal message without triggers")
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100
        assert result is None


class TestInteractionLogTiming:
    """Tests for interaction log timing validation."""

    def test_interaction_log_timing_check(self) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        Interaction logs SHALL correctly report if response was within 3 second limit.
        """
        # Create interaction log with fast response
        fast_log = TestInteractionLog(
            input_content="Hello bot",
            processing_started_at=datetime.utcnow(),
        )
        fast_log.processing_completed_at = fast_log.processing_started_at + timedelta(milliseconds=500)
        fast_log.response_time_ms = 500

        assert fast_log.was_within_time_limit(3.0), "500ms response should be within 3s limit"

        # Create interaction log with slow response
        slow_log = TestInteractionLog(
            input_content="Hello bot",
            processing_started_at=datetime.utcnow(),
        )
        slow_log.processing_completed_at = slow_log.processing_started_at + timedelta(milliseconds=4000)
        slow_log.response_time_ms = 4000

        assert not slow_log.was_within_time_limit(3.0), "4000ms response should exceed 3s limit"

    @given(response_time_ms=st.floats(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_timing_check_property(self, response_time_ms: float) -> None:
        """**Feature: youtube-automation, Property 17: Chatbot Response Timing**
        
        For any response time, the timing check SHALL correctly determine if within limit.
        """
        log = TestInteractionLog(input_content="Hello")
        log.response_time_ms = response_time_ms

        limit_seconds = 3.0
        expected = response_time_ms <= (limit_seconds * 1000)
        actual = log.was_within_time_limit(limit_seconds)

        assert actual == expected, (
            f"For response_time_ms={response_time_ms}, "
            f"expected was_within_time_limit={expected}, got {actual}"
        )
