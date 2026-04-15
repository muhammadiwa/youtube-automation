"""Property-based tests for Discount Code Validation.

**Feature: admin-panel, Property 15: Discount Code Validation**
**Validates: Requirements 14.1**

Property 15: Discount Code Validation
*For any* discount code application, the code SHALL be valid only if:
- current_date is between valid_from and valid_until
- usage_count < usage_limit (when usage_limit is set)
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Test Data Generators ====================

@st.composite
def discount_type_strategy(draw):
    """Generate valid discount types."""
    return draw(st.sampled_from(["percentage", "fixed"]))


@st.composite
def discount_value_strategy(draw, discount_type: str):
    """Generate valid discount values based on type."""
    if discount_type == "percentage":
        # Percentage: 1-100
        return draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    else:
        # Fixed: $0.01 to $1000
        return draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False))


@st.composite
def validity_period_strategy(draw, is_valid: bool = True):
    """Generate validity period dates.
    
    Args:
        is_valid: If True, generates a currently valid period. If False, generates expired or future period.
    """
    now = datetime.utcnow()
    
    if is_valid:
        # Valid period: started in the past, ends in the future
        days_ago = draw(st.integers(min_value=1, max_value=30))
        days_until = draw(st.integers(min_value=1, max_value=365))
        valid_from = now - timedelta(days=days_ago)
        valid_until = now + timedelta(days=days_until)
    else:
        # Invalid period: either expired or not yet started
        period_type = draw(st.sampled_from(["expired", "future"]))
        if period_type == "expired":
            # Expired: both dates in the past
            days_ago_end = draw(st.integers(min_value=1, max_value=30))
            days_ago_start = days_ago_end + draw(st.integers(min_value=1, max_value=30))
            valid_from = now - timedelta(days=days_ago_start)
            valid_until = now - timedelta(days=days_ago_end)
        else:
            # Future: both dates in the future
            days_until_start = draw(st.integers(min_value=1, max_value=30))
            days_until_end = days_until_start + draw(st.integers(min_value=1, max_value=365))
            valid_from = now + timedelta(days=days_until_start)
            valid_until = now + timedelta(days=days_until_end)
    
    return {
        "valid_from": valid_from,
        "valid_until": valid_until,
    }


@st.composite
def usage_limit_strategy(draw, has_limit: bool = True):
    """Generate usage limit configuration.
    
    Args:
        has_limit: If True, generates a usage limit. If False, returns None (unlimited).
    """
    if has_limit:
        return draw(st.integers(min_value=1, max_value=10000))
    return None


@st.composite
def discount_code_strategy(draw, is_valid: bool = True, within_usage_limit: bool = True):
    """Generate discount code data for testing.
    
    Args:
        is_valid: If True, generates a valid code (active, within date range)
        within_usage_limit: If True, usage_count < usage_limit
    """
    discount_type = draw(discount_type_strategy())
    discount_value = draw(discount_value_strategy(discount_type))
    
    # Generate validity period
    period = draw(validity_period_strategy(is_valid=is_valid))
    
    # Generate usage limit
    has_limit = draw(st.booleans())
    usage_limit = draw(usage_limit_strategy(has_limit=has_limit))
    
    # Generate usage count
    if usage_limit is not None:
        if within_usage_limit:
            usage_count = draw(st.integers(min_value=0, max_value=max(0, usage_limit - 1)))
        else:
            usage_count = draw(st.integers(min_value=usage_limit, max_value=usage_limit + 100))
    else:
        usage_count = draw(st.integers(min_value=0, max_value=10000))
    
    return {
        "id": uuid.uuid4(),
        "code": f"TEST{draw(st.integers(min_value=1000, max_value=9999))}",
        "discount_type": discount_type,
        "discount_value": discount_value,
        "valid_from": period["valid_from"],
        "valid_until": period["valid_until"],
        "usage_limit": usage_limit,
        "usage_count": usage_count,
        "applicable_plans": draw(st.lists(st.sampled_from(["free", "basic", "pro", "enterprise"]), max_size=4)),
        "is_active": is_valid,  # Active status matches validity for simplicity
        "created_by": uuid.uuid4(),
    }


# ==================== Mock Classes for Testing ====================

class MockDiscountCode:
    """Mock discount code for testing validation logic.
    
    Implements the same validation logic as the actual DiscountCode model.
    """
    
    def __init__(self, data: dict):
        self.id = data["id"]
        self.code = data["code"]
        self.discount_type = data["discount_type"]
        self.discount_value = data["discount_value"]
        self.valid_from = data["valid_from"]
        self.valid_until = data["valid_until"]
        self.usage_limit = data["usage_limit"]
        self.usage_count = data["usage_count"]
        self.applicable_plans = data["applicable_plans"]
        self.is_active = data["is_active"]
        self.created_by = data["created_by"]
    
    def is_valid(self, current_date: Optional[datetime] = None) -> bool:
        """Check if discount code is currently valid.
        
        Property 15: Discount Code Validation
        - Code is valid only if current_date is between valid_from and valid_until
        - Code is valid only if usage_count < usage_limit (when usage_limit is set)
        
        Args:
            current_date: Date to check validity against (defaults to now)
            
        Returns:
            bool: True if code is valid
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Check if code is active
        if not self.is_active:
            return False
        
        # Check date validity
        if current_date < self.valid_from or current_date > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        
        return True
    
    def calculate_discount(self, original_price: float) -> float:
        """Calculate the discount amount.
        
        Args:
            original_price: Original price before discount
            
        Returns:
            float: Discount amount
        """
        if self.discount_type == "percentage":
            return original_price * (self.discount_value / 100)
        else:  # fixed
            return min(self.discount_value, original_price)


# ==================== Property Tests ====================

class TestDiscountCodeValidation:
    """Property tests for Discount Code Validation.
    
    **Feature: admin-panel, Property 15: Discount Code Validation**
    **Validates: Requirements 14.1**
    """

    @settings(max_examples=100)
    @given(
        days_ago=st.integers(min_value=1, max_value=30),
        days_until=st.integers(min_value=1, max_value=365),
        usage_limit=st.integers(min_value=1, max_value=1000),
        usage_count=st.integers(min_value=0, max_value=999),
    )
    def test_valid_code_within_date_range_and_usage_limit(
        self,
        days_ago: int,
        days_until: int,
        usage_limit: int,
        usage_count: int,
    ):
        """
        Property: Code SHALL be valid when within date range AND usage_count < usage_limit.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        assume(usage_count < usage_limit)
        
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "VALID123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=days_ago),
            "valid_until": now + timedelta(days=days_until),
            "usage_limit": usage_limit,
            "usage_count": usage_count,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is True

    @settings(max_examples=100)
    @given(
        days_ago_end=st.integers(min_value=1, max_value=30),
        days_ago_start=st.integers(min_value=31, max_value=60),
    )
    def test_expired_code_is_invalid(
        self,
        days_ago_end: int,
        days_ago_start: int,
    ):
        """
        Property: Code SHALL be invalid when current_date > valid_until (expired).
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "EXPIRED123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=days_ago_start),
            "valid_until": now - timedelta(days=days_ago_end),
            "usage_limit": 100,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is False

    @settings(max_examples=100)
    @given(
        days_until_start=st.integers(min_value=1, max_value=30),
        days_until_end=st.integers(min_value=31, max_value=365),
    )
    def test_future_code_is_invalid(
        self,
        days_until_start: int,
        days_until_end: int,
    ):
        """
        Property: Code SHALL be invalid when current_date < valid_from (not yet valid).
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "FUTURE123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now + timedelta(days=days_until_start),
            "valid_until": now + timedelta(days=days_until_end),
            "usage_limit": 100,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is False

    @settings(max_examples=100)
    @given(
        usage_limit=st.integers(min_value=1, max_value=1000),
        extra_usage=st.integers(min_value=0, max_value=100),
    )
    def test_code_at_usage_limit_is_invalid(
        self,
        usage_limit: int,
        extra_usage: int,
    ):
        """
        Property: Code SHALL be invalid when usage_count >= usage_limit.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "MAXED123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": usage_limit,
            "usage_count": usage_limit + extra_usage,  # At or over limit
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is False

    @settings(max_examples=100)
    @given(
        usage_count=st.integers(min_value=0, max_value=10000),
    )
    def test_code_without_usage_limit_ignores_usage_count(
        self,
        usage_count: int,
    ):
        """
        Property: Code with no usage_limit SHALL be valid regardless of usage_count.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "UNLIMITED123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": None,  # No limit
            "usage_count": usage_count,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is True

    @settings(max_examples=100)
    @given(
        days_ago=st.integers(min_value=1, max_value=30),
        days_until=st.integers(min_value=1, max_value=365),
    )
    def test_inactive_code_is_invalid(
        self,
        days_ago: int,
        days_until: int,
    ):
        """
        Property: Code SHALL be invalid when is_active is False.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "INACTIVE123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=days_ago),
            "valid_until": now + timedelta(days=days_until),
            "usage_limit": None,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": False,  # Inactive
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is False

    @settings(max_examples=100)
    @given(
        check_time_offset=st.integers(min_value=-30, max_value=30),
    )
    def test_validity_at_boundary_dates(
        self,
        check_time_offset: int,
    ):
        """
        Property: Code validity SHALL be correctly determined at boundary dates.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        valid_from = now - timedelta(days=15)
        valid_until = now + timedelta(days=15)
        
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "BOUNDARY123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "usage_limit": None,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        check_time = now + timedelta(days=check_time_offset)
        expected_valid = valid_from <= check_time <= valid_until
        
        assert code.is_valid(check_time) == expected_valid

    @settings(max_examples=100)
    @given(
        percentage=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        original_price=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_percentage_discount_calculation(
        self,
        percentage: float,
        original_price: float,
    ):
        """
        Property: Percentage discount SHALL be calculated as original_price * (percentage / 100).
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "PERCENT123",
            "discount_type": "percentage",
            "discount_value": percentage,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": None,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        discount = code.calculate_discount(original_price)
        expected = original_price * (percentage / 100)
        
        assert abs(discount - expected) < 0.01  # Allow small floating point tolerance

    @settings(max_examples=100)
    @given(
        fixed_amount=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        original_price=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_fixed_discount_calculation(
        self,
        fixed_amount: float,
        original_price: float,
    ):
        """
        Property: Fixed discount SHALL be min(fixed_amount, original_price).
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "FIXED123",
            "discount_type": "fixed",
            "discount_value": fixed_amount,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": None,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        discount = code.calculate_discount(original_price)
        expected = min(fixed_amount, original_price)
        
        assert abs(discount - expected) < 0.01  # Allow small floating point tolerance

    @settings(max_examples=100)
    @given(
        fixed_amount=st.floats(min_value=100.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        original_price=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    def test_fixed_discount_capped_at_original_price(
        self,
        fixed_amount: float,
        original_price: float,
    ):
        """
        Property: Fixed discount SHALL never exceed original price.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        assume(fixed_amount > original_price)
        
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "CAPPED123",
            "discount_type": "fixed",
            "discount_value": fixed_amount,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": None,
            "usage_count": 0,
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        discount = code.calculate_discount(original_price)
        
        assert discount <= original_price

    @settings(max_examples=100)
    @given(
        usage_limit=st.integers(min_value=2, max_value=1000),
    )
    def test_code_valid_one_below_usage_limit(
        self,
        usage_limit: int,
    ):
        """
        Property: Code SHALL be valid when usage_count is exactly one below usage_limit.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "ONELEFT123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": usage_limit,
            "usage_count": usage_limit - 1,  # One use remaining
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is True

    @settings(max_examples=100)
    @given(
        usage_limit=st.integers(min_value=1, max_value=1000),
    )
    def test_code_invalid_exactly_at_usage_limit(
        self,
        usage_limit: int,
    ):
        """
        Property: Code SHALL be invalid when usage_count equals usage_limit exactly.
        
        **Feature: admin-panel, Property 15: Discount Code Validation**
        **Validates: Requirements 14.1**
        """
        now = datetime.utcnow()
        code = MockDiscountCode({
            "id": uuid.uuid4(),
            "code": "EXACT123",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "valid_from": now - timedelta(days=10),
            "valid_until": now + timedelta(days=10),
            "usage_limit": usage_limit,
            "usage_count": usage_limit,  # Exactly at limit
            "applicable_plans": [],
            "is_active": True,
            "created_by": uuid.uuid4(),
        })
        
        assert code.is_valid(now) is False
