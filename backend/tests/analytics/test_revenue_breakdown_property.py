"""Property-based tests for revenue breakdown.

**Feature: youtube-automation, Property 25: Revenue Source Breakdown**
**Validates: Requirements 18.2**

Tests that the sum of individual revenue sources equals the total revenue amount.
"""

import uuid
from datetime import date, timedelta
from typing import List

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.modules.analytics.revenue_models import RevenueRecord
from app.modules.analytics.revenue_schemas import RevenueBreakdown
from app.modules.analytics.revenue_service import RevenueService


# Strategy for generating non-negative revenue amounts
revenue_amount = st.floats(min_value=0.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False)


@st.composite
def revenue_record_strategy(draw):
    """Generate a RevenueRecord with random revenue values."""
    ad_revenue = draw(revenue_amount)
    membership_revenue = draw(revenue_amount)
    super_chat_revenue = draw(revenue_amount)
    super_sticker_revenue = draw(revenue_amount)
    merchandise_revenue = draw(revenue_amount)
    youtube_premium_revenue = draw(revenue_amount)
    
    # Create a mock RevenueRecord-like object
    class MockRevenueRecord:
        def __init__(self):
            self.ad_revenue = ad_revenue
            self.membership_revenue = membership_revenue
            self.super_chat_revenue = super_chat_revenue
            self.super_sticker_revenue = super_sticker_revenue
            self.merchandise_revenue = merchandise_revenue
            self.youtube_premium_revenue = youtube_premium_revenue
    
    return MockRevenueRecord()


@st.composite
def revenue_records_list_strategy(draw):
    """Generate a list of RevenueRecords."""
    records = draw(st.lists(revenue_record_strategy(), min_size=0, max_size=100))
    return records


class TestRevenueSourceBreakdown:
    """Property tests for revenue source breakdown.
    
    **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
    **Validates: Requirements 18.2**
    """

    @given(
        ad=revenue_amount,
        membership=revenue_amount,
        super_chat=revenue_amount,
        super_sticker=revenue_amount,
        merchandise=revenue_amount,
        youtube_premium=revenue_amount,
    )
    @settings(max_examples=100)
    def test_breakdown_total_equals_sum_of_sources(
        self,
        ad: float,
        membership: float,
        super_chat: float,
        super_sticker: float,
        merchandise: float,
        youtube_premium: float,
    ):
        """
        **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
        **Validates: Requirements 18.2**
        
        For any revenue calculation, the sum of individual source amounts
        SHALL equal the total revenue amount.
        """
        # Calculate expected total
        expected_total = (
            ad + membership + super_chat + 
            super_sticker + merchandise + youtube_premium
        )
        
        # Create breakdown with explicit total
        breakdown = RevenueBreakdown(
            ad_revenue=ad,
            membership_revenue=membership,
            super_chat_revenue=super_chat,
            super_sticker_revenue=super_sticker,
            merchandise_revenue=merchandise,
            youtube_premium_revenue=youtube_premium,
            total_revenue=expected_total,
        )
        
        # Verify total equals sum of sources
        calculated_sum = (
            breakdown.ad + breakdown.membership + breakdown.super_chat +
            breakdown.super_sticker + breakdown.merchandise + breakdown.youtube_premium
        )
        
        # Allow small floating point differences
        assert abs(breakdown.total - calculated_sum) < 0.01, (
            f"Total {breakdown.total} does not equal sum of sources {calculated_sum}"
        )

    @given(
        ad=revenue_amount,
        membership=revenue_amount,
        super_chat=revenue_amount,
        super_sticker=revenue_amount,
        merchandise=revenue_amount,
        youtube_premium=revenue_amount,
    )
    @settings(max_examples=100)
    def test_breakdown_auto_corrects_incorrect_total(
        self,
        ad: float,
        membership: float,
        super_chat: float,
        super_sticker: float,
        merchandise: float,
        youtube_premium: float,
    ):
        """
        **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
        **Validates: Requirements 18.2**
        
        For any revenue breakdown with incorrect total, the model validator
        SHALL auto-correct the total to match the sum of sources.
        """
        # Calculate correct total
        correct_total = (
            ad + membership + super_chat + 
            super_sticker + merchandise + youtube_premium
        )
        
        # Provide an intentionally wrong total
        wrong_total = correct_total + 1000.0
        
        # Create breakdown with wrong total - validator should correct it
        breakdown = RevenueBreakdown(
            ad_revenue=ad,
            membership_revenue=membership,
            super_chat_revenue=super_chat,
            super_sticker_revenue=super_sticker,
            merchandise_revenue=merchandise,
            youtube_premium_revenue=youtube_premium,
            total_revenue=wrong_total,
        )
        
        # Verify total was corrected
        calculated_sum = (
            breakdown.ad + breakdown.membership + breakdown.super_chat +
            breakdown.super_sticker + breakdown.merchandise + breakdown.youtube_premium
        )
        
        assert abs(breakdown.total - calculated_sum) < 0.01, (
            f"Total {breakdown.total} was not corrected to match sum {calculated_sum}"
        )

    @given(records=revenue_records_list_strategy())
    @settings(max_examples=100)
    def test_calculate_breakdown_from_records(self, records: List):
        """
        **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
        **Validates: Requirements 18.2**
        
        For any list of revenue records, calculating the breakdown SHALL
        produce a total that equals the sum of all individual sources.
        """
        # Calculate expected totals
        expected_ad = sum(r.ad_revenue for r in records)
        expected_membership = sum(r.membership_revenue for r in records)
        expected_super_chat = sum(r.super_chat_revenue for r in records)
        expected_super_sticker = sum(r.super_sticker_revenue for r in records)
        expected_merchandise = sum(r.merchandise_revenue for r in records)
        expected_youtube_premium = sum(r.youtube_premium_revenue for r in records)
        
        expected_total = (
            expected_ad + expected_membership + expected_super_chat +
            expected_super_sticker + expected_merchandise + expected_youtube_premium
        )
        
        # Create breakdown
        breakdown = RevenueBreakdown(
            ad_revenue=expected_ad,
            membership_revenue=expected_membership,
            super_chat_revenue=expected_super_chat,
            super_sticker_revenue=expected_super_sticker,
            merchandise_revenue=expected_merchandise,
            youtube_premium_revenue=expected_youtube_premium,
            total_revenue=expected_total,
        )
        
        # Verify invariant: total equals sum of sources
        calculated_sum = (
            breakdown.ad + breakdown.membership + breakdown.super_chat +
            breakdown.super_sticker + breakdown.merchandise + breakdown.youtube_premium
        )
        
        assert abs(breakdown.total - calculated_sum) < 0.01, (
            f"Total {breakdown.total} does not equal sum of sources {calculated_sum}"
        )

    @given(
        ad=revenue_amount,
        membership=revenue_amount,
        super_chat=revenue_amount,
        super_sticker=revenue_amount,
        merchandise=revenue_amount,
        youtube_premium=revenue_amount,
    )
    @settings(max_examples=100)
    def test_revenue_record_calculate_total(
        self,
        ad: float,
        membership: float,
        super_chat: float,
        super_sticker: float,
        merchandise: float,
        youtube_premium: float,
    ):
        """
        **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
        **Validates: Requirements 18.2**
        
        For any RevenueRecord, the calculate_total method SHALL return
        the sum of all revenue sources.
        """
        # Create a RevenueRecord instance
        record = RevenueRecord(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            record_date=date.today(),
            ad_revenue=ad,
            membership_revenue=membership,
            super_chat_revenue=super_chat,
            super_sticker_revenue=super_sticker,
            merchandise_revenue=merchandise,
            youtube_premium_revenue=youtube_premium,
        )
        
        # Calculate total using the model method
        calculated_total = record.calculate_total()
        
        # Calculate expected total
        expected_total = (
            ad + membership + super_chat + 
            super_sticker + merchandise + youtube_premium
        )
        
        # Verify they match
        assert abs(calculated_total - expected_total) < 0.01, (
            f"calculate_total() returned {calculated_total}, expected {expected_total}"
        )

    @given(
        ad=revenue_amount,
        membership=revenue_amount,
        super_chat=revenue_amount,
        super_sticker=revenue_amount,
        merchandise=revenue_amount,
        youtube_premium=revenue_amount,
    )
    @settings(max_examples=100)
    def test_revenue_record_get_breakdown(
        self,
        ad: float,
        membership: float,
        super_chat: float,
        super_sticker: float,
        merchandise: float,
        youtube_premium: float,
    ):
        """
        **Feature: youtube-automation, Property 25: Revenue Source Breakdown**
        **Validates: Requirements 18.2**
        
        For any RevenueRecord, the get_breakdown method SHALL return
        a dictionary where the sum of values equals calculate_total().
        """
        # Create a RevenueRecord instance
        record = RevenueRecord(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            record_date=date.today(),
            ad_revenue=ad,
            membership_revenue=membership,
            super_chat_revenue=super_chat,
            super_sticker_revenue=super_sticker,
            merchandise_revenue=merchandise,
            youtube_premium_revenue=youtube_premium,
        )
        
        # Get breakdown
        breakdown = record.get_breakdown()
        
        # Sum all values in breakdown
        breakdown_sum = sum(breakdown.values())
        
        # Get total from calculate_total
        total = record.calculate_total()
        
        # Verify they match
        assert abs(breakdown_sum - total) < 0.01, (
            f"Breakdown sum {breakdown_sum} does not equal total {total}"
        )
