"""Property-based tests for moderation rule enforcement.

**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
**Validates: Requirements 12.2, 12.5**
"""

import uuid
from datetime import datetime

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.modules.moderation.models import (
    ChatMessage,
    ModerationActionType,
    ModerationRule,
    RuleType,
    SeverityLevel,
)
from app.modules.moderation.service import ChatAnalyzer
from app.modules.moderation.actions import (
    ModerationActionExecutor,
    get_timeout_duration_for_severity,
    get_action_for_severity,
    UserModerationHistory,
)


# ============================================
# Strategies for generating test data
# ============================================

keyword_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=3,
    max_size=15,
)

keywords_list_strategy = st.lists(keyword_strategy, min_size=1, max_size=10)

severity_strategy = st.sampled_from([
    SeverityLevel.LOW,
    SeverityLevel.MEDIUM,
    SeverityLevel.HIGH,
    SeverityLevel.CRITICAL,
])

action_type_strategy = st.sampled_from([
    ModerationActionType.HIDE,
    ModerationActionType.DELETE,
    ModerationActionType.TIMEOUT,
    ModerationActionType.WARN,
])


def create_test_rule(
    rule_type: RuleType,
    keywords: list[str] = None,
    pattern: str = None,
    caps_threshold: int = 70,
    action_type: ModerationActionType = ModerationActionType.HIDE,
    severity: SeverityLevel = SeverityLevel.MEDIUM,
    timeout_duration: int = None,
) -> ModerationRule:
    """Create a test moderation rule."""
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
        timeout_duration_seconds=timeout_duration,
        is_enabled=True,
        priority=0,
    )
    return rule


def create_test_message(
    content: str,
    account_id: uuid.UUID = None,
) -> ChatMessage:
    """Create a test chat message."""
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


class TestRuleEnforcement:
    """Property tests for rule enforcement.
    
    **Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
    **Validates: Requirements 12.2, 12.5**
    """

    @given(
        keyword=keyword_strategy,
        action_type=action_type_strategy,
        severity=severity_strategy,
    )
    @settings(max_examples=100)
    def test_keyword_violation_triggers_action(
        self,
        keyword: str,
        action_type: ModerationActionType,
        severity: SeverityLevel,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        For any message violating a keyword rule, the message SHALL be hidden
        and the action SHALL be logged.
        """
        assume(len(keyword.strip()) >= 3)  # Ensure keyword is meaningful
        
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=[keyword],
            action_type=action_type,
            severity=severity,
        )
        
        # Create message containing the keyword
        content = f"Hello {keyword} world"
        message = create_test_message(content)
        
        # Analyze message
        analyzer = ChatAnalyzer([rule])
        result = analyzer.analyze(message)
        
        # Property: Violation must be detected
        assert result.is_violation, (
            f"Keyword '{keyword}' in message was not detected as violation"
        )
        
        # Property: Correct action type must be recommended
        assert result.recommended_action == action_type, (
            f"Expected action {action_type}, got {result.recommended_action}"
        )
        
        # Property: Correct severity must be set
        assert result.recommended_severity == severity, (
            f"Expected severity {severity}, got {result.recommended_severity}"
        )

    @given(
        keyword=keyword_strategy,
        action_type=action_type_strategy,
    )
    @settings(max_examples=100)
    def test_action_execution_logs_correctly(
        self,
        keyword: str,
        action_type: ModerationActionType,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        For any moderation action, the action SHALL be logged with all required details.
        """
        assume(len(keyword.strip()) >= 3)
        
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=[keyword],
            action_type=action_type,
        )
        
        content = f"Message with {keyword}"
        message = create_test_message(content)
        
        # Execute action
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=action_type,
            message=message,
            rule=rule,
            reason=f"Keyword '{keyword}' detected",
        )
        
        # Property: Action log must contain all required fields (Requirements: 12.5)
        assert action_log.action_type == action_type.value
        assert action_log.user_channel_id == message.author_channel_id
        assert action_log.message_id == message.youtube_message_id
        assert action_log.message_content == message.content
        assert action_log.reason is not None
        assert action_log.processing_started_at is not None
        assert action_log.processing_completed_at is not None

    @given(keywords=keywords_list_strategy)
    @settings(max_examples=100)
    def test_all_matching_keywords_detected(
        self,
        keywords: list[str],
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        For any keyword in the rule, if present in message, it SHALL be detected.
        """
        # Filter to valid keywords
        valid_keywords = [k for k in keywords if len(k.strip()) >= 3]
        assume(len(valid_keywords) >= 1)
        
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=valid_keywords,
        )
        
        # Test each keyword
        for keyword in valid_keywords:
            content = f"Test message with {keyword} inside"
            message = create_test_message(content)
            
            analyzer = ChatAnalyzer([rule])
            result = analyzer.analyze(message)
            
            assert result.is_violation, (
                f"Keyword '{keyword}' was not detected in message"
            )

    @given(severity=severity_strategy)
    @settings(max_examples=100)
    def test_timeout_duration_matches_severity(
        self,
        severity: SeverityLevel,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        For any severity level, timeout duration SHALL be appropriate.
        """
        duration = get_timeout_duration_for_severity(severity)
        
        # Property: Duration must be positive
        assert duration > 0
        
        # Property: Higher severity = longer timeout
        severity_order = [
            SeverityLevel.LOW,
            SeverityLevel.MEDIUM,
            SeverityLevel.HIGH,
            SeverityLevel.CRITICAL,
        ]
        
        for i, sev in enumerate(severity_order[:-1]):
            next_sev = severity_order[i + 1]
            assert get_timeout_duration_for_severity(sev) < get_timeout_duration_for_severity(next_sev), (
                f"Timeout for {sev} should be less than {next_sev}"
            )

    def test_hide_action_marks_message_hidden(self) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Hide action SHALL mark message as hidden.
        """
        message = create_test_message("Test message")
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=ModerationActionType.HIDE,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=ModerationActionType.HIDE,
            message=message,
            rule=rule,
            reason="Test violation",
        )
        
        # Property: Message must be marked as hidden
        assert message.is_hidden is True
        assert message.is_moderated is True
        assert action_log.was_successful is True

    def test_delete_action_marks_message_deleted(self) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Delete action SHALL mark message as deleted.
        """
        message = create_test_message("Test message")
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=ModerationActionType.DELETE,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=ModerationActionType.DELETE,
            message=message,
            rule=rule,
            reason="Test violation",
        )
        
        # Property: Message must be marked as deleted
        assert message.is_deleted is True
        assert message.is_moderated is True
        assert action_log.was_successful is True

    @given(timeout_seconds=st.integers(min_value=1, max_value=3600))
    @settings(max_examples=100)
    def test_timeout_action_records_duration(
        self,
        timeout_seconds: int,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Timeout action SHALL record the timeout duration.
        """
        message = create_test_message("Test message")
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=ModerationActionType.TIMEOUT,
            timeout_duration=timeout_seconds,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=ModerationActionType.TIMEOUT,
            message=message,
            rule=rule,
            reason="Test violation",
            timeout_duration_seconds=timeout_seconds,
        )
        
        # Property: Timeout duration must be recorded
        assert action_log.timeout_duration_seconds == timeout_seconds
        assert action_log.timeout_expires_at is not None
        assert action_log.was_successful is True


class TestActionLogging:
    """Tests for action logging completeness.
    
    **Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
    **Validates: Requirements 12.5**
    """

    @given(
        action_type=action_type_strategy,
        severity=severity_strategy,
    )
    @settings(max_examples=100)
    def test_action_log_contains_user_info(
        self,
        action_type: ModerationActionType,
        severity: SeverityLevel,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Action log SHALL contain user information.
        """
        message = create_test_message("Test content")
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=action_type,
            severity=severity,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=action_type,
            message=message,
            rule=rule,
            reason="Test reason",
        )
        
        # Property: User info must be present
        assert action_log.user_channel_id == message.author_channel_id
        assert action_log.user_display_name == message.author_display_name

    @given(action_type=action_type_strategy)
    @settings(max_examples=100)
    def test_action_log_contains_message_info(
        self,
        action_type: ModerationActionType,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Action log SHALL contain message information.
        """
        content = "This is test content for logging"
        message = create_test_message(content)
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=action_type,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=action_type,
            message=message,
            rule=rule,
            reason="Test reason",
        )
        
        # Property: Message info must be present
        assert action_log.message_id == message.youtube_message_id
        assert action_log.message_content == content

    @given(action_type=action_type_strategy)
    @settings(max_examples=100)
    def test_action_log_contains_timing_info(
        self,
        action_type: ModerationActionType,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Action log SHALL contain processing timing information.
        """
        message = create_test_message("Test content")
        rule = create_test_rule(
            RuleType.KEYWORD,
            keywords=["test"],
            action_type=action_type,
        )
        
        executor = ModerationActionExecutor()
        action_log = executor.execute_action(
            action_type=action_type,
            message=message,
            rule=rule,
            reason="Test reason",
        )
        
        # Property: Timing info must be present and valid
        assert action_log.processing_started_at is not None
        assert action_log.processing_completed_at is not None
        assert action_log.processing_completed_at >= action_log.processing_started_at


class TestUserModerationHistory:
    """Tests for user moderation history tracking."""

    @given(violation_count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_violation_count_tracking(
        self,
        violation_count: int,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        User violation count SHALL be tracked accurately.
        """
        history = UserModerationHistory()
        user_id = f"UC{uuid.uuid4().hex[:22]}"
        
        for _ in range(violation_count):
            history.record_violation(user_id)
        
        # Property: Count must match recorded violations
        assert history.get_recent_violations(user_id) == violation_count

    @given(threshold=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100)
    def test_escalation_threshold(
        self,
        threshold: int,
    ) -> None:
        """**Feature: youtube-automation, Property 19: Moderation Rule Enforcement**
        
        Escalation SHALL trigger when threshold is reached.
        """
        history = UserModerationHistory()
        user_id = f"UC{uuid.uuid4().hex[:22]}"
        
        # Below threshold - should not escalate
        for _ in range(threshold - 1):
            history.record_violation(user_id)
        assert not history.should_escalate(user_id, threshold)
        
        # At threshold - should escalate
        history.record_violation(user_id)
        assert history.should_escalate(user_id, threshold)
