"""Property-based tests for chat moderation timing.

**Feature: youtube-automation, Property 18: Chat Moderation Timing**
**Validates: Requirements 12.1**
"""

import uuid
from datetime import datetime

import pytest
from hypothesis import given, settings, strategies as st

from app.modules.moderation.models import (
    ChatMessage,
    ModerationActionType,
    ModerationRule,
    RuleType,
    SeverityLevel,
)
from app.modules.moderation.service import ChatAnalyzer


# ============================================
# Strategies for generating test data
# ============================================

# Strategy for generating message content
message_content_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        whitelist_characters=" !@#$%^&*(),.?\":{}|<>",
    ),
    min_size=1,
    max_size=500,
)

# Strategy for generating keywords
keyword_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=2,
    max_size=20,
)

# Strategy for generating keyword lists
keywords_list_strategy = st.lists(keyword_strategy, min_size=1, max_size=20)

# Strategy for generating rule types
rule_type_strategy = st.sampled_from([
    RuleType.KEYWORD,
    RuleType.REGEX,
    RuleType.SPAM,
    RuleType.CAPS,
    RuleType.LINKS,
])

# Strategy for generating action types
action_type_strategy = st.sampled_from([
    ModerationActionType.HIDE,
    ModerationActionType.DELETE,
    ModerationActionType.TIMEOUT,
    ModerationActionType.WARN,
])

# Strategy for generating severity levels
severity_strategy = st.sampled_from([
    SeverityLevel.LOW,
    SeverityLevel.MEDIUM,
    SeverityLevel.HIGH,
    SeverityLevel.CRITICAL,
])


def create_test_rule(
    rule_type: RuleType,
    keywords: list[str] = None,
    pattern: str = None,
    caps_threshold: int = 70,
    action_type: ModerationActionType = ModerationActionType.HIDE,
    severity: SeverityLevel = SeverityLevel.MEDIUM,
) -> ModerationRule:
    """Create a test moderation rule without database."""
    rule = ModerationRule(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        name=f"Test {rule_type.value} rule",
        rule_type=rule_type.value,
        keywords=keywords,
        pattern=pattern,
        caps_threshold_percent=caps_threshold,
        min_message_length=5,
        action_type=action_type.value,
        severity=severity.value,
        is_enabled=True,
        priority=0,
    )
    return rule


def create_test_message(
    content: str,
    account_id: uuid.UUID = None,
) -> ChatMessage:
    """Create a test chat message without database."""
    message = ChatMessage(
        id=uuid.uuid4(),
        account_id=account_id or uuid.uuid4(),
        youtube_message_id=f"msg_{uuid.uuid4().hex[:12]}",
        youtube_live_chat_id=f"chat_{uuid.uuid4().hex[:12]}",
        author_channel_id=f"UC{uuid.uuid4().hex[:22]}",
        author_display_name="TestUser",
        content=content,
        message_type="text",
        published_at=datetime.utcnow(),
    )
    return message


class TestModerationTiming:
    """Property tests for moderation timing.
    
    **Feature: youtube-automation, Property 18: Chat Moderation Timing**
    **Validates: Requirements 12.1**
    """

    @given(content=message_content_strategy)
    @settings(max_examples=100)
    def test_analysis_completes_within_2_seconds(self, content: str) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        For any chat message, moderation analysis SHALL complete within 2 seconds.
        """
        # Create rules of various types
        rules = [
            create_test_rule(RuleType.KEYWORD, keywords=["spam", "bad", "test"]),
            create_test_rule(RuleType.REGEX, pattern=r"\b(buy|sell|discount)\b"),
            create_test_rule(RuleType.SPAM),
            create_test_rule(RuleType.CAPS, caps_threshold=70),
            create_test_rule(RuleType.LINKS),
        ]

        message = create_test_message(content)
        analyzer = ChatAnalyzer(rules)

        # Analyze and check timing
        result = analyzer.analyze(message)

        # Property: Analysis must complete within 2000ms (2 seconds)
        assert result.processing_time_ms <= 2000, (
            f"Analysis took {result.processing_time_ms}ms, "
            f"exceeding 2000ms limit (Requirements 12.1)"
        )

    @given(
        content=message_content_strategy,
        num_rules=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_analysis_scales_with_rules(
        self,
        content: str,
        num_rules: int,
    ) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        For any number of rules (up to 50), analysis SHALL complete within 2 seconds.
        """
        # Create multiple rules
        rules = []
        for i in range(num_rules):
            rule_type = [
                RuleType.KEYWORD,
                RuleType.REGEX,
                RuleType.SPAM,
                RuleType.CAPS,
                RuleType.LINKS,
            ][i % 5]
            
            if rule_type == RuleType.KEYWORD:
                rules.append(create_test_rule(
                    rule_type,
                    keywords=[f"word{j}" for j in range(5)],
                ))
            elif rule_type == RuleType.REGEX:
                rules.append(create_test_rule(
                    rule_type,
                    pattern=rf"\b(pattern{i}|test{i})\b",
                ))
            else:
                rules.append(create_test_rule(rule_type))

        message = create_test_message(content)
        analyzer = ChatAnalyzer(rules)

        result = analyzer.analyze(message)

        # Property: Even with many rules, must complete within 2 seconds
        assert result.processing_time_ms <= 2000, (
            f"Analysis with {num_rules} rules took {result.processing_time_ms}ms, "
            f"exceeding 2000ms limit"
        )

    @given(
        keywords=keywords_list_strategy,
        content=message_content_strategy,
    )
    @settings(max_examples=100)
    def test_keyword_analysis_timing(
        self,
        keywords: list[str],
        content: str,
    ) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        For any keyword rule with any number of keywords, analysis SHALL complete within 2 seconds.
        """
        rule = create_test_rule(RuleType.KEYWORD, keywords=keywords)
        message = create_test_message(content)
        analyzer = ChatAnalyzer([rule])

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000, (
            f"Keyword analysis with {len(keywords)} keywords took "
            f"{result.processing_time_ms}ms, exceeding 2000ms limit"
        )

    @given(content=st.text(min_size=1, max_size=2000))
    @settings(max_examples=100)
    def test_long_message_analysis_timing(self, content: str) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        For any message length (up to 2000 chars), analysis SHALL complete within 2 seconds.
        """
        rules = [
            create_test_rule(RuleType.KEYWORD, keywords=["spam", "bad"]),
            create_test_rule(RuleType.REGEX, pattern=r"https?://[^\s]+"),
            create_test_rule(RuleType.SPAM),
            create_test_rule(RuleType.CAPS),
            create_test_rule(RuleType.LINKS),
        ]

        message = create_test_message(content)
        analyzer = ChatAnalyzer(rules)

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000, (
            f"Analysis of {len(content)}-char message took "
            f"{result.processing_time_ms}ms, exceeding 2000ms limit"
        )


class TestAnalysisCorrectness:
    """Tests for analysis correctness alongside timing."""

    @given(keyword=keyword_strategy)
    @settings(max_examples=100)
    def test_keyword_detection_is_correct(self, keyword: str) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        For any keyword, if the message contains it, it SHALL be detected within 2 seconds.
        """
        rule = create_test_rule(RuleType.KEYWORD, keywords=[keyword])
        
        # Message that contains the keyword
        content = f"Hello {keyword} world"
        message = create_test_message(content)
        analyzer = ChatAnalyzer([rule])

        result = analyzer.analyze(message)

        # Must complete within time limit
        assert result.processing_time_ms <= 2000

        # Must detect the violation
        assert result.is_violation, (
            f"Keyword '{keyword}' in message '{content}' was not detected"
        )
        assert len(result.violations) == 1
        assert result.violations[0].matched_pattern == keyword

    def test_caps_detection_timing(self) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        Caps detection SHALL complete within 2 seconds.
        """
        rule = create_test_rule(RuleType.CAPS, caps_threshold=70)
        
        # Message with excessive caps
        content = "THIS IS ALL CAPS MESSAGE"
        message = create_test_message(content)
        analyzer = ChatAnalyzer([rule])

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000
        assert result.is_violation

    def test_link_detection_timing(self) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        Link detection SHALL complete within 2 seconds.
        """
        rule = create_test_rule(RuleType.LINKS)
        
        content = "Check out https://example.com for more info"
        message = create_test_message(content)
        analyzer = ChatAnalyzer([rule])

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000
        assert result.is_violation

    def test_spam_detection_timing(self) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        Spam detection SHALL complete within 2 seconds.
        """
        rule = create_test_rule(RuleType.SPAM)
        
        # Message with repeated characters
        content = "Hellooooooo everyone"
        message = create_test_message(content)
        analyzer = ChatAnalyzer([rule])

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000
        assert result.is_violation

    def test_no_violation_timing(self) -> None:
        """**Feature: youtube-automation, Property 18: Chat Moderation Timing**
        
        Clean messages SHALL be analyzed within 2 seconds with no violations.
        """
        rules = [
            create_test_rule(RuleType.KEYWORD, keywords=["spam", "bad"]),
            create_test_rule(RuleType.CAPS, caps_threshold=70),
            create_test_rule(RuleType.LINKS),
        ]
        
        content = "Hello everyone, how are you today?"
        message = create_test_message(content)
        analyzer = ChatAnalyzer(rules)

        result = analyzer.analyze(message)

        assert result.processing_time_ms <= 2000
        assert not result.is_violation
        assert len(result.violations) == 0
