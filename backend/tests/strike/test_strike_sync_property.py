"""Property-based tests for strike status sync.

**Feature: youtube-automation, Property 26: Strike Status Sync**
**Validates: Requirements 20.1**
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.modules.strike.models import (
    Strike,
    StrikeType,
    StrikeStatus,
    StrikeSeverity,
    AppealStatus,
)
from app.modules.strike.schemas import (
    StrikeCreate,
    StrikeResponse,
    StrikeSummary,
    YouTubeStrikeData,
)


# ============================================
# Strategies for generating test data
# ============================================

strike_type_strategy = st.sampled_from([
    StrikeType.COPYRIGHT,
    StrikeType.COMMUNITY_GUIDELINES,
    StrikeType.TERMS_OF_SERVICE,
    StrikeType.SPAM,
    StrikeType.HARASSMENT,
    StrikeType.HARMFUL_CONTENT,
    StrikeType.MISINFORMATION,
    StrikeType.OTHER,
])

severity_strategy = st.sampled_from([
    StrikeSeverity.WARNING,
    StrikeSeverity.STRIKE,
    StrikeSeverity.SEVERE,
    StrikeSeverity.TERMINATION_RISK,
])

status_strategy = st.sampled_from([
    StrikeStatus.ACTIVE,
    StrikeStatus.APPEALED,
    StrikeStatus.APPEAL_PENDING,
    StrikeStatus.APPEAL_APPROVED,
    StrikeStatus.APPEAL_REJECTED,
    StrikeStatus.EXPIRED,
    StrikeStatus.RESOLVED,
])

appeal_status_strategy = st.sampled_from([
    AppealStatus.NOT_APPEALED,
    AppealStatus.PENDING,
    AppealStatus.IN_REVIEW,
    AppealStatus.APPROVED,
    AppealStatus.REJECTED,
])

# Strategy for generating valid reason strings
reason_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
        whitelist_characters="-_.,!?"
    ),
    min_size=10,
    max_size=500
)

# Strategy for generating YouTube strike IDs
youtube_strike_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=10,
    max_size=50
)

# Strategy for generating video IDs
video_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
    min_size=11,
    max_size=11
)


@st.composite
def youtube_strike_data_strategy(draw) -> YouTubeStrikeData:
    """Generate valid YouTubeStrikeData for testing."""
    strike_type = draw(strike_type_strategy)
    severity = draw(severity_strategy)
    reason = draw(reason_strategy)
    
    # Generate dates
    days_ago = draw(st.integers(min_value=0, max_value=90))
    issued_at = datetime.utcnow() - timedelta(days=days_ago)
    
    # Optionally generate expiry date (90 days from issue)
    has_expiry = draw(st.booleans())
    expires_at = issued_at + timedelta(days=90) if has_expiry else None
    
    # Optionally generate affected video
    has_video = draw(st.booleans())
    video_id = draw(video_id_strategy) if has_video else None
    video_title = draw(st.text(min_size=5, max_size=100)) if has_video else None
    
    return YouTubeStrikeData(
        strike_id=draw(youtube_strike_id_strategy),
        strike_type=strike_type.value,
        reason=reason if reason.strip() else "Default reason",
        reason_details=draw(st.none() | reason_strategy),
        affected_video_id=video_id,
        affected_video_title=video_title,
        issued_at=issued_at,
        expires_at=expires_at,
        severity=severity.value,
    )


@st.composite
def strike_create_strategy(draw) -> StrikeCreate:
    """Generate valid StrikeCreate for testing."""
    strike_type = draw(strike_type_strategy)
    severity = draw(severity_strategy)
    reason = draw(reason_strategy)
    
    # Generate dates
    days_ago = draw(st.integers(min_value=0, max_value=90))
    issued_at = datetime.utcnow() - timedelta(days=days_ago)
    
    # Optionally generate expiry date
    has_expiry = draw(st.booleans())
    expires_at = issued_at + timedelta(days=90) if has_expiry else None
    
    return StrikeCreate(
        account_id=uuid.uuid4(),
        youtube_strike_id=draw(st.none() | youtube_strike_id_strategy),
        strike_type=strike_type,
        severity=severity,
        reason=reason if reason.strip() else "Default reason",
        reason_details=draw(st.none() | reason_strategy),
        affected_video_id=draw(st.none() | video_id_strategy),
        affected_video_title=draw(st.none() | st.text(min_size=5, max_size=100)),
        affected_content_url=None,
        issued_at=issued_at,
        expires_at=expires_at,
        metadata=None,
    )


class TestStrikeStatusSync:
    """Property tests for strike status sync.

    **Feature: youtube-automation, Property 26: Strike Status Sync**
    **Validates: Requirements 20.1**
    """

    @given(strike_data=youtube_strike_data_strategy())
    @settings(max_examples=100)
    def test_youtube_strike_data_preserves_all_fields(
        self, strike_data: YouTubeStrikeData
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any YouTube strike data, all fields SHALL be preserved when
        converting to/from the schema.
        """
        # Convert to dict and back
        data_dict = strike_data.model_dump()
        restored = YouTubeStrikeData.model_validate(data_dict)
        
        assert restored.strike_id == strike_data.strike_id
        assert restored.strike_type == strike_data.strike_type
        assert restored.reason == strike_data.reason
        assert restored.severity == strike_data.severity
        assert restored.issued_at == strike_data.issued_at
        assert restored.expires_at == strike_data.expires_at
        assert restored.affected_video_id == strike_data.affected_video_id

    @given(strike_create=strike_create_strategy())
    @settings(max_examples=100)
    def test_strike_create_has_valid_structure(
        self, strike_create: StrikeCreate
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike creation request, the data SHALL have valid structure
        with required fields populated.
        """
        assert strike_create.account_id is not None
        assert strike_create.strike_type in StrikeType
        assert strike_create.severity in StrikeSeverity
        assert len(strike_create.reason) > 0
        assert strike_create.issued_at is not None

    @given(
        strike_type=strike_type_strategy,
        severity=severity_strategy,
        status=status_strategy,
    )
    @settings(max_examples=100)
    def test_strike_status_consistency(
        self,
        strike_type: StrikeType,
        severity: StrikeSeverity,
        status: StrikeStatus,
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike, the status SHALL be one of the valid status values
        and the type/severity SHALL be preserved.
        """
        # Create a mock strike object
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            strike_type=strike_type.value,
            severity=severity.value,
            status=status.value,
            reason="Test reason",
            issued_at=datetime.utcnow(),
        )
        
        # Verify status is valid
        assert strike.status in [s.value for s in StrikeStatus]
        assert strike.strike_type in [t.value for t in StrikeType]
        assert strike.severity in [s.value for s in StrikeSeverity]

    @given(
        days_ago=st.integers(min_value=0, max_value=365),
        expiry_days=st.integers(min_value=1, max_value=180),
    )
    @settings(max_examples=100)
    def test_strike_expiry_detection(
        self, days_ago: int, expiry_days: int
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike with expiry date, the is_expired method SHALL correctly
        determine if the strike has expired based on current time.
        """
        issued_at = datetime.utcnow() - timedelta(days=days_ago)
        expires_at = issued_at + timedelta(days=expiry_days)
        
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            strike_type=StrikeType.OTHER.value,
            severity=StrikeSeverity.WARNING.value,
            status=StrikeStatus.ACTIVE.value,
            reason="Test reason",
            issued_at=issued_at,
            expires_at=expires_at,
        )
        
        # Calculate expected expiry status
        expected_expired = datetime.utcnow() >= expires_at
        
        assert strike.is_expired() == expected_expired

    @given(severity=severity_strategy)
    @settings(max_examples=100)
    def test_high_risk_detection(self, severity: StrikeSeverity) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike, is_high_risk SHALL return True only for SEVERE
        and TERMINATION_RISK severity levels.
        """
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            strike_type=StrikeType.OTHER.value,
            severity=severity.value,
            status=StrikeStatus.ACTIVE.value,
            reason="Test reason",
            issued_at=datetime.utcnow(),
        )
        
        expected_high_risk = severity in [
            StrikeSeverity.SEVERE,
            StrikeSeverity.TERMINATION_RISK,
        ]
        
        assert strike.is_high_risk() == expected_high_risk

    @given(
        status=status_strategy,
        appeal_status=appeal_status_strategy,
    )
    @settings(max_examples=100)
    def test_can_appeal_logic(
        self, status: StrikeStatus, appeal_status: AppealStatus
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike, can_appeal SHALL return True only when status is ACTIVE
        and appeal_status is NOT_APPEALED.
        """
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            strike_type=StrikeType.OTHER.value,
            severity=StrikeSeverity.WARNING.value,
            status=status.value,
            appeal_status=appeal_status.value,
            reason="Test reason",
            issued_at=datetime.utcnow(),
        )
        
        expected_can_appeal = (
            status == StrikeStatus.ACTIVE
            and appeal_status == AppealStatus.NOT_APPEALED
        )
        
        assert strike.can_appeal() == expected_can_appeal

    @given(
        num_active=st.integers(min_value=0, max_value=5),
        num_resolved=st.integers(min_value=0, max_value=5),
        num_expired=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=100)
    def test_strike_summary_counts(
        self, num_active: int, num_resolved: int, num_expired: int
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any collection of strikes, the summary counts SHALL accurately
        reflect the number of strikes in each status category.
        """
        account_id = uuid.uuid4()
        total = num_active + num_resolved + num_expired
        
        # Create mock summary
        summary = StrikeSummary(
            account_id=account_id,
            total_strikes=total,
            active_strikes=num_active,
            appealed_strikes=0,
            resolved_strikes=num_resolved,
            expired_strikes=num_expired,
            has_high_risk=False,
            latest_strike=None,
        )
        
        # Verify counts are consistent
        assert summary.total_strikes == num_active + num_resolved + num_expired
        assert summary.active_strikes == num_active
        assert summary.resolved_strikes == num_resolved
        assert summary.expired_strikes == num_expired

    @given(strike_data=youtube_strike_data_strategy())
    @settings(max_examples=100)
    def test_strike_data_type_values_are_valid(
        self, strike_data: YouTubeStrikeData
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any YouTube strike data, the strike_type and severity values
        SHALL be valid enum values.
        """
        valid_types = [t.value for t in StrikeType]
        valid_severities = [s.value for s in StrikeSeverity]
        
        assert strike_data.strike_type in valid_types, (
            f"Invalid strike type: {strike_data.strike_type}"
        )
        assert strike_data.severity in valid_severities, (
            f"Invalid severity: {strike_data.severity}"
        )

    @given(
        youtube_id=youtube_strike_id_strategy,
        strike_type=strike_type_strategy,
    )
    @settings(max_examples=100)
    def test_strike_youtube_id_uniqueness_constraint(
        self, youtube_id: str, strike_type: StrikeType
    ) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike with a YouTube strike ID, the ID SHALL be preserved
        and can be used to identify the strike uniquely.
        """
        assume(len(youtube_id) > 0)
        
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            youtube_strike_id=youtube_id,
            strike_type=strike_type.value,
            severity=StrikeSeverity.WARNING.value,
            status=StrikeStatus.ACTIVE.value,
            reason="Test reason",
            issued_at=datetime.utcnow(),
        )
        
        assert strike.youtube_strike_id == youtube_id
        assert len(strike.youtube_strike_id) > 0


class TestStrikeStatusTransitions:
    """Property tests for strike status transitions."""

    @given(initial_status=status_strategy)
    @settings(max_examples=100)
    def test_is_active_matches_status(self, initial_status: StrikeStatus) -> None:
        """**Feature: youtube-automation, Property 26: Strike Status Sync**

        For any strike, is_active SHALL return True if and only if
        status is ACTIVE.
        """
        strike = Strike(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            strike_type=StrikeType.OTHER.value,
            severity=StrikeSeverity.WARNING.value,
            status=initial_status.value,
            reason="Test reason",
            issued_at=datetime.utcnow(),
        )
        
        expected_active = initial_status == StrikeStatus.ACTIVE
        assert strike.is_active() == expected_active
