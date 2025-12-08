"""Property-based tests for token expiry alerting.

**Feature: youtube-automation, Property 6: Token Expiry Alerting**
**Validates: Requirements 2.3**
"""

import uuid
from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.modules.account.tasks import (
    TokenExpiryAlert,
    TokenExpiryAlertStore,
    check_token_expiry,
)


# Strategy for generating valid UUIDs
uuid_strategy = st.uuids()

# Strategy for generating channel titles
channel_title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=100,
)

# Strategy for hours until expiry (0 to 48 hours)
hours_strategy = st.integers(min_value=0, max_value=48)

# Strategy for alert threshold (1 to 72 hours)
threshold_strategy = st.integers(min_value=1, max_value=72)


class TestTokenExpiryAlerting:
    """Property tests for token expiry alerting.

    **Feature: youtube-automation, Property 6: Token Expiry Alerting**
    **Validates: Requirements 2.3**
    """

    def setup_method(self) -> None:
        """Clear alert store before each test."""
        TokenExpiryAlertStore.clear_alerts()

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
        hours_until_expiry=hours_strategy,
        threshold_hours=threshold_strategy,
    )
    @settings(max_examples=100)
    def test_expiring_token_generates_alert(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
        hours_until_expiry: int,
        threshold_hours: int,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any YouTube account with token expiring within the threshold hours,
        the system SHALL generate an alert notification to the user.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        # Create token expiry time
        token_expires_at = datetime.utcnow() + timedelta(hours=hours_until_expiry)
        
        # Check token expiry
        alert = check_token_expiry(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            token_expires_at=token_expires_at,
            alert_threshold_hours=threshold_hours,
        )
        
        # If hours until expiry is within threshold, alert should be generated
        if hours_until_expiry <= threshold_hours:
            assert alert is not None, (
                f"Alert should be generated when token expires in {hours_until_expiry}h "
                f"(threshold: {threshold_hours}h)"
            )
            assert alert.account_id == account_id
            assert alert.user_id == user_id
            assert alert.channel_title == channel_title
        else:
            assert alert is None, (
                f"No alert should be generated when token expires in {hours_until_expiry}h "
                f"(threshold: {threshold_hours}h)"
            )

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
    )
    @settings(max_examples=100)
    def test_expired_token_generates_alert(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any YouTube account with already expired token,
        the system SHALL generate an alert notification.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        # Create already expired token
        token_expires_at = datetime.utcnow() - timedelta(hours=1)
        
        alert = check_token_expiry(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            token_expires_at=token_expires_at,
            alert_threshold_hours=24,
        )
        
        assert alert is not None, "Alert should be generated for expired token"
        assert alert.hours_until_expiry == 0, "Hours until expiry should be 0 for expired token"

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
    )
    @settings(max_examples=100)
    def test_none_expiry_generates_alert(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any YouTube account with unknown token expiry (None),
        the system SHALL generate an alert notification.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        alert = check_token_expiry(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            token_expires_at=None,
            alert_threshold_hours=24,
        )
        
        assert alert is not None, "Alert should be generated when expiry is unknown"

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
        hours_until_expiry=st.integers(min_value=26, max_value=100),
    )
    @settings(max_examples=100)
    def test_non_expiring_token_no_alert(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
        hours_until_expiry: int,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any YouTube account with token NOT expiring within 24 hours,
        the system SHALL NOT generate an alert notification.
        
        Note: We use min_value=26 to account for timing differences between
        when the test creates the expiry time and when check_token_expiry
        calculates hours_until_expiry (which truncates to int).
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        # Token expires well after threshold (26+ hours to avoid boundary issues)
        token_expires_at = datetime.utcnow() + timedelta(hours=hours_until_expiry)
        
        alert = check_token_expiry(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            token_expires_at=token_expires_at,
            alert_threshold_hours=24,
        )
        
        assert alert is None, (
            f"No alert should be generated when token expires in {hours_until_expiry}h "
            "(threshold: 24h)"
        )


class TestTokenExpiryAlertStore:
    """Tests for TokenExpiryAlertStore functionality."""

    def setup_method(self) -> None:
        """Clear alert store before each test."""
        TokenExpiryAlertStore.clear_alerts()

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
    )
    @settings(max_examples=100)
    def test_alert_stored_correctly(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any generated alert, the alert SHALL be stored and retrievable.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=12),
            hours_until_expiry=12,
        )
        
        TokenExpiryAlertStore.add_alert(alert)
        
        alerts = TokenExpiryAlertStore.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["account_id"] == str(account_id)
        assert alerts[0]["user_id"] == str(user_id)
        assert alerts[0]["channel_title"] == channel_title

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
    )
    @settings(max_examples=100)
    def test_duplicate_alerts_prevented(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        For any account, duplicate alerts within 24 hours SHALL be prevented.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        alert1 = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=12),
            hours_until_expiry=12,
        )
        
        alert2 = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=6),
            hours_until_expiry=6,
        )
        
        TokenExpiryAlertStore.add_alert(alert1)
        TokenExpiryAlertStore.add_alert(alert2)
        
        alerts = TokenExpiryAlertStore.get_alerts()
        assert len(alerts) == 1, "Duplicate alerts should be prevented"

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
    )
    @settings(max_examples=100)
    def test_alert_cleared_after_reset(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        After token refresh, the notification status SHALL be reset
        to allow future alerts.
        """
        assume(len(channel_title.strip()) > 0)
        
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        # Add first alert
        alert1 = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=12),
            hours_until_expiry=12,
        )
        TokenExpiryAlertStore.add_alert(alert1)
        
        # Reset notification status (simulating token refresh)
        TokenExpiryAlertStore.reset_notification_status(account_id)
        
        # Add second alert - should now be allowed
        alert2 = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=6),
            hours_until_expiry=6,
        )
        TokenExpiryAlertStore.add_alert(alert2)
        
        alerts = TokenExpiryAlertStore.get_alerts()
        assert len(alerts) == 2, "Alert should be allowed after reset"

    @given(
        user_id=uuid_strategy,
    )
    @settings(max_examples=100)
    def test_filter_alerts_by_user(
        self,
        user_id: uuid.UUID,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        Alerts SHALL be filterable by user ID.
        """
        # Clear store for this test
        TokenExpiryAlertStore.clear_alerts()
        
        # Add alert for target user
        alert1 = TokenExpiryAlert(
            account_id=uuid.uuid4(),
            channel_title="User Channel",
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=12),
            hours_until_expiry=12,
        )
        TokenExpiryAlertStore.add_alert(alert1)
        
        # Add alert for different user
        other_user_id = uuid.uuid4()
        alert2 = TokenExpiryAlert(
            account_id=uuid.uuid4(),
            channel_title="Other Channel",
            user_id=other_user_id,
            expires_at=datetime.utcnow() + timedelta(hours=12),
            hours_until_expiry=12,
        )
        TokenExpiryAlertStore.add_alert(alert2)
        
        # Filter by user
        user_alerts = TokenExpiryAlertStore.get_alerts(user_id)
        assert len(user_alerts) == 1
        assert user_alerts[0]["user_id"] == str(user_id)


class TestTokenExpiryAlertModel:
    """Tests for TokenExpiryAlert model."""

    @given(
        account_id=uuid_strategy,
        user_id=uuid_strategy,
        channel_title=channel_title_strategy,
        hours_until_expiry=hours_strategy,
    )
    @settings(max_examples=100)
    def test_alert_to_dict_serialization(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        channel_title: str,
        hours_until_expiry: int,
    ) -> None:
        """**Feature: youtube-automation, Property 6: Token Expiry Alerting**

        Alert model SHALL serialize to dictionary correctly.
        """
        assume(len(channel_title.strip()) > 0)
        
        expires_at = datetime.utcnow() + timedelta(hours=hours_until_expiry)
        
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=expires_at,
            hours_until_expiry=hours_until_expiry,
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["account_id"] == str(account_id)
        assert alert_dict["user_id"] == str(user_id)
        assert alert_dict["channel_title"] == channel_title
        assert alert_dict["hours_until_expiry"] == hours_until_expiry
        assert alert_dict["alert_type"] == "token_expiry"
        assert "created_at" in alert_dict
        assert "expires_at" in alert_dict
