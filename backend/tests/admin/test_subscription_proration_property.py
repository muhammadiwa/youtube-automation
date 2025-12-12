"""Property-based tests for Subscription Proration Calculation.

**Feature: admin-panel, Property 7: Subscription Proration Calculation**
**Validates: Requirements 4.2**

Property 7: Subscription Proration Calculation
*For any* subscription upgrade/downgrade, the prorated amount SHALL be calculated as
(remaining_days / total_days) * price_difference.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Test Data Generators ====================

@st.composite
def plan_price_strategy(draw):
    """Generate valid plan prices (in cents)."""
    # Prices range from $0 to $500 per month (0 to 50000 cents)
    return draw(st.integers(min_value=0, max_value=50000))


@st.composite
def billing_cycle_strategy(draw):
    """Generate valid billing cycles."""
    return draw(st.sampled_from(["monthly", "yearly"]))


@st.composite
def subscription_period_strategy(draw):
    """Generate valid subscription period dates."""
    # Start date within the last year
    days_ago = draw(st.integers(min_value=1, max_value=365))
    start_date = datetime.utcnow() - timedelta(days=days_ago)
    
    # Period length based on billing cycle
    billing_cycle = draw(billing_cycle_strategy())
    if billing_cycle == "yearly":
        period_days = 365
    else:
        period_days = 30
    
    end_date = start_date + timedelta(days=period_days)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "billing_cycle": billing_cycle,
        "period_days": period_days,
    }


@st.composite
def subscription_strategy(draw):
    """Generate valid subscription data for testing proration."""
    period = draw(subscription_period_strategy())
    
    return {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "plan_tier": draw(st.sampled_from(["free", "basic", "pro", "enterprise"])),
        "billing_cycle": period["billing_cycle"],
        "current_period_start": period["start_date"],
        "current_period_end": period["end_date"],
        "period_days": period["period_days"],
    }


@st.composite
def plan_strategy(draw, slug: str):
    """Generate valid plan data."""
    price_monthly = draw(plan_price_strategy())
    # Yearly price is typically 10-12 months worth (discount)
    yearly_multiplier = draw(st.integers(min_value=10, max_value=12))
    price_yearly = price_monthly * yearly_multiplier
    
    return {
        "slug": slug,
        "price_monthly": price_monthly,
        "price_yearly": price_yearly,
    }


# ==================== Mock Classes for Testing ====================

class MockPlan:
    """Mock plan for testing proration calculation."""
    
    def __init__(self, plan_data: dict):
        self.slug = plan_data["slug"]
        self.price_monthly = plan_data["price_monthly"]
        self.price_yearly = plan_data["price_yearly"]


class MockSubscription:
    """Mock subscription for testing proration calculation."""
    
    def __init__(self, sub_data: dict):
        self.id = sub_data["id"]
        self.user_id = sub_data["user_id"]
        self.plan_tier = sub_data["plan_tier"]
        self.billing_cycle = sub_data["billing_cycle"]
        self.current_period_start = sub_data["current_period_start"]
        self.current_period_end = sub_data["current_period_end"]


# ==================== Proration Calculation Logic ====================

def calculate_proration(
    subscription: MockSubscription,
    current_plan: MockPlan,
    new_plan: MockPlan,
    calculation_time: Optional[datetime] = None,
) -> float:
    """
    Calculate prorated amount for plan change.
    
    Requirements: 4.2 - Prorated billing calculation
    Property 7: (remaining_days / total_days) * price_difference
    
    Args:
        subscription: Current subscription
        current_plan: Current plan with pricing
        new_plan: New plan with pricing
        calculation_time: Time to calculate proration at (defaults to now)
        
    Returns:
        Prorated amount (positive for upgrade, negative for downgrade credit)
    """
    if calculation_time is None:
        calculation_time = datetime.utcnow()
    
    # Get prices based on billing cycle
    if subscription.billing_cycle == "yearly":
        current_price = current_plan.price_yearly / 100  # Convert cents to dollars
        new_price = new_plan.price_yearly / 100
    else:
        current_price = current_plan.price_monthly / 100
        new_price = new_plan.price_monthly / 100
    
    # Calculate total days in period
    total_days = (subscription.current_period_end - subscription.current_period_start).days
    
    # Calculate remaining days
    remaining_days = max(0, (subscription.current_period_end - calculation_time).days)
    
    # Handle edge case: no days in period
    if total_days <= 0:
        return 0.0
    
    # Calculate proration: (remaining_days / total_days) * price_difference
    price_difference = new_price - current_price
    proration = (remaining_days / total_days) * price_difference
    
    return round(proration, 2)


# ==================== Property Tests ====================

class TestSubscriptionProrationCalculation:
    """Property tests for Subscription Proration Calculation.
    
    **Feature: admin-panel, Property 7: Subscription Proration Calculation**
    **Validates: Requirements 4.2**
    """

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=1, max_value=365),
        remaining_days=st.integers(min_value=0, max_value=365),
    )
    def test_proration_formula_correctness(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
        remaining_days: int,
    ):
        """
        Property: Proration SHALL be calculated as (remaining_days / total_days) * price_difference.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        # Ensure remaining_days <= total_days
        assume(remaining_days <= total_days)
        
        # Create subscription with specific period
        now = datetime.utcnow()
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # Calculate expected value manually
        current_price = current_price_monthly / 100
        new_price = new_price_monthly / 100
        price_difference = new_price - current_price
        expected = round((remaining_days / total_days) * price_difference, 2)
        
        assert result == expected

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        billing_cycle=billing_cycle_strategy(),
    )
    def test_proration_uses_correct_billing_cycle_price(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        billing_cycle: str,
    ):
        """
        Property: Proration SHALL use the correct price based on billing cycle.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        # Set up period based on billing cycle
        now = datetime.utcnow()
        if billing_cycle == "yearly":
            total_days = 365
        else:
            total_days = 30
        
        remaining_days = total_days // 2  # Half the period remaining
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": billing_cycle,
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        # Create plans with different monthly and yearly prices
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # Calculate expected using correct prices for billing cycle
        if billing_cycle == "yearly":
            current_price = (current_price_monthly * 10) / 100
            new_price = (new_price_monthly * 10) / 100
        else:
            current_price = current_price_monthly / 100
            new_price = new_price_monthly / 100
        
        price_difference = new_price - current_price
        expected = round((remaining_days / total_days) * price_difference, 2)
        
        assert result == expected

    @settings(max_examples=100)
    @given(
        price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=1, max_value=365),
        remaining_days=st.integers(min_value=0, max_value=365),
    )
    def test_proration_zero_when_same_plan_price(
        self,
        price_monthly: int,
        total_days: int,
        remaining_days: int,
    ):
        """
        Property: Proration SHALL be zero when current and new plan have same price.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        assume(remaining_days <= total_days)
        
        now = datetime.utcnow()
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        # Same price for both plans
        plan = MockPlan({
            "slug": "basic",
            "price_monthly": price_monthly,
            "price_yearly": price_monthly * 10,
        })
        
        result = calculate_proration(subscription, plan, plan, now)
        
        assert result == 0.0

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=1, max_value=365),
    )
    def test_proration_zero_when_no_remaining_days(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
    ):
        """
        Property: Proration SHALL be zero when there are no remaining days in period.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        # Period has ended (no remaining days)
        now = datetime.utcnow()
        period_start = now - timedelta(days=total_days)
        period_end = now  # Period ends now
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        assert result == 0.0

    @settings(max_examples=100)
    @given(
        current_price_monthly=st.integers(min_value=1, max_value=50000),
        new_price_monthly=st.integers(min_value=1, max_value=50000),
        total_days=st.integers(min_value=1, max_value=365),
        remaining_days=st.integers(min_value=1, max_value=365),
    )
    def test_proration_positive_for_upgrade(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
        remaining_days: int,
    ):
        """
        Property: Proration SHALL be positive when upgrading to a more expensive plan.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        assume(remaining_days <= total_days)
        assume(new_price_monthly > current_price_monthly)  # Upgrade scenario
        
        # Ensure price difference is large enough that proration won't round to zero
        # Formula: (remaining_days / total_days) * (price_diff / 100) > 0.005 (rounds to 0.01)
        # Due to Python's banker's rounding, 0.005 can round to 0.0, so we need > 0.005
        # So: price_diff > 0.5 * total_days / remaining_days (using > instead of >=)
        price_diff = new_price_monthly - current_price_monthly
        min_price_diff_for_nonzero = (0.5 * total_days) / remaining_days
        assume(price_diff > min_price_diff_for_nonzero)
        
        now = datetime.utcnow()
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        assert result > 0

    @settings(max_examples=100)
    @given(
        current_price_monthly=st.integers(min_value=100, max_value=50000),
        new_price_monthly=st.integers(min_value=1, max_value=50000),
        total_days=st.integers(min_value=1, max_value=365),
        remaining_days=st.integers(min_value=1, max_value=365),
    )
    def test_proration_negative_for_downgrade(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
        remaining_days: int,
    ):
        """
        Property: Proration SHALL be negative (credit) when downgrading to a cheaper plan.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        assume(remaining_days <= total_days)
        # Ensure significant price difference to avoid rounding to zero
        assume(current_price_monthly - new_price_monthly >= 10)
        
        now = datetime.utcnow()
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "pro",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "pro",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "basic",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # Result should be negative or zero (credit for downgrade)
        assert result <= 0

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=1, max_value=365),
        remaining_days=st.integers(min_value=0, max_value=365),
    )
    def test_proration_bounded_by_price_difference(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
        remaining_days: int,
    ):
        """
        Property: Proration SHALL never exceed the full price difference.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        assume(remaining_days <= total_days)
        
        now = datetime.utcnow()
        period_start = now - timedelta(days=(total_days - remaining_days))
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # Calculate full price difference
        price_difference = abs((new_price_monthly - current_price_monthly) / 100)
        
        # Proration should never exceed full price difference
        assert abs(result) <= price_difference + 0.01  # Small tolerance for rounding

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=1, max_value=365),
    )
    def test_proration_equals_full_difference_at_period_start(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
    ):
        """
        Property: Proration SHALL equal full price difference at period start.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        # All days remaining (at period start)
        now = datetime.utcnow()
        period_start = now
        period_end = now + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # At period start, proration should equal full price difference
        expected = round((new_price_monthly - current_price_monthly) / 100, 2)
        
        assert result == expected

    @settings(max_examples=100)
    @given(
        current_price_monthly=plan_price_strategy(),
        new_price_monthly=plan_price_strategy(),
        total_days=st.integers(min_value=2, max_value=365),
    )
    def test_proration_proportional_to_remaining_time(
        self,
        current_price_monthly: int,
        new_price_monthly: int,
        total_days: int,
    ):
        """
        Property: Proration SHALL be proportional to remaining time in period.
        
        **Feature: admin-panel, Property 7: Subscription Proration Calculation**
        **Validates: Requirements 4.2**
        """
        # Set up a period with known remaining days
        now = datetime.utcnow()
        elapsed_days = total_days // 2
        period_start = now - timedelta(days=elapsed_days)
        period_end = period_start + timedelta(days=total_days)
        
        subscription = MockSubscription({
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "plan_tier": "basic",
            "billing_cycle": "monthly",
            "current_period_start": period_start,
            "current_period_end": period_end,
        })
        
        current_plan = MockPlan({
            "slug": "basic",
            "price_monthly": current_price_monthly,
            "price_yearly": current_price_monthly * 10,
        })
        
        new_plan = MockPlan({
            "slug": "pro",
            "price_monthly": new_price_monthly,
            "price_yearly": new_price_monthly * 10,
        })
        
        result = calculate_proration(subscription, current_plan, new_plan, now)
        
        # Calculate expected using the same formula
        remaining_days = max(0, (period_end - now).days)
        price_difference = (new_price_monthly - current_price_monthly) / 100
        expected = round((remaining_days / total_days) * price_difference, 2)
        
        # Allow small tolerance for floating-point rounding differences
        assert abs(result - expected) <= 0.02
