"""Pydantic schemas for Admin Promotional operations.

Requirements: 14.3, 14.4, 14.5 - Extended Promotional & Marketing Tools
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ==================== Referral Program Config (Requirements 14.3) ====================


class ReferralRewards(BaseModel):
    """Referral reward configuration."""
    referrer_reward_type: Literal["credit", "discount", "free_days"] = Field(
        default="credit",
        description="Type of reward for referrer"
    )
    referrer_reward_value: float = Field(
        default=10.0,
        ge=0,
        description="Value of reward for referrer (amount, percentage, or days)"
    )
    referee_reward_type: Literal["credit", "discount", "free_days", "extended_trial"] = Field(
        default="extended_trial",
        description="Type of reward for referee"
    )
    referee_reward_value: float = Field(
        default=7.0,
        ge=0,
        description="Value of reward for referee (amount, percentage, or days)"
    )


class ReferralProgramConfig(BaseModel):
    """Referral program configuration.
    
    Requirements: 14.3 - Configure referral program rewards
    """
    is_enabled: bool = Field(default=True, description="Whether referral program is enabled")
    rewards: ReferralRewards = Field(default_factory=ReferralRewards)
    max_referrals_per_user: int = Field(
        default=50,
        ge=0,
        description="Maximum referrals per user (0 for unlimited)"
    )
    referral_code_prefix: str = Field(
        default="REF",
        max_length=10,
        description="Prefix for generated referral codes"
    )
    minimum_subscription_days: int = Field(
        default=30,
        ge=0,
        description="Minimum days referee must be subscribed for referrer to get reward"
    )
    eligible_plans: list[str] = Field(
        default_factory=lambda: ["starter", "professional", "enterprise"],
        description="Plans eligible for referral rewards"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReferralProgramConfigUpdate(BaseModel):
    """Schema for updating referral program configuration."""
    is_enabled: Optional[bool] = None
    rewards: Optional[ReferralRewards] = None
    max_referrals_per_user: Optional[int] = Field(None, ge=0)
    referral_code_prefix: Optional[str] = Field(None, max_length=10)
    minimum_subscription_days: Optional[int] = Field(None, ge=0)
    eligible_plans: Optional[list[str]] = None


class ReferralProgramConfigResponse(BaseModel):
    """Response for referral program configuration."""
    config: ReferralProgramConfig
    updated_by: Optional[uuid.UUID] = None
    message: str = "Referral program configuration retrieved successfully"


# ==================== Trial Extension (Requirements 14.4) ====================


class TrialExtensionRequest(BaseModel):
    """Request to extend a user's trial period.
    
    Requirements: 14.4 - Extend trial for specific user
    """
    days: int = Field(
        ...,
        ge=1,
        le=365,
        description="Number of days to extend trial"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for trial extension"
    )


class TrialExtensionResponse(BaseModel):
    """Response after extending a user's trial."""
    user_id: uuid.UUID
    previous_trial_end: Optional[datetime]
    new_trial_end: datetime
    days_extended: int
    reason: Optional[str]
    extended_at: datetime
    extended_by: uuid.UUID
    message: str


class TrialCodeCreate(BaseModel):
    """Request to create an extended trial code.
    
    Requirements: 14.4 - Create extended trial codes
    """
    code: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique trial code"
    )
    trial_days: int = Field(
        ...,
        ge=1,
        le=365,
        description="Number of trial days this code provides"
    )
    valid_from: datetime = Field(..., description="Start date of validity")
    valid_until: datetime = Field(..., description="End date of validity")
    usage_limit: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum number of uses (None for unlimited)"
    )
    applicable_plans: list[str] = Field(
        default_factory=list,
        description="Plans this code applies to (empty for all)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the trial code"
    )


class TrialCodeResponse(BaseModel):
    """Response for a trial code."""
    id: uuid.UUID
    code: str
    trial_days: int
    valid_from: datetime
    valid_until: datetime
    usage_limit: Optional[int]
    usage_count: int
    applicable_plans: list[str]
    description: Optional[str]
    is_active: bool
    is_valid: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrialCodeListResponse(BaseModel):
    """Paginated list of trial codes."""
    items: list[TrialCodeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Promotion Analytics (Requirements 14.5) ====================


class DiscountCodeAnalytics(BaseModel):
    """Analytics for a single discount code."""
    code: str
    usage_count: int
    total_discount_given: float
    revenue_generated: float
    conversion_rate: float
    average_order_value: float


class ReferralAnalytics(BaseModel):
    """Analytics for referral program."""
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    total_rewards_given: float
    conversion_rate: float


class TopReferrer(BaseModel):
    """Top referrer information."""
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    referral_count: int
    successful_referrals: int
    total_rewards_earned: float


class PromotionAnalyticsResponse(BaseModel):
    """Response for promotion analytics.
    
    Requirements: 14.5 - Show conversion rate, revenue generated, top referrers
    """
    # Overall metrics
    total_discount_codes: int
    active_discount_codes: int
    total_trial_codes: int
    active_trial_codes: int
    
    # Discount code metrics
    total_discount_usage: int
    total_discount_amount: float
    discount_revenue_impact: float
    
    # Referral metrics
    referral_analytics: ReferralAnalytics
    
    # Top performers
    top_discount_codes: list[DiscountCodeAnalytics]
    top_referrers: list[TopReferrer]
    
    # Time period
    period_start: datetime
    period_end: datetime
    
    # Conversion metrics
    overall_conversion_rate: float
    discount_conversion_rate: float
    referral_conversion_rate: float
