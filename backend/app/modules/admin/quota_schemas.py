"""Admin Quota Management Schemas.

Pydantic models for admin quota management API responses.
Requirements: 11.1, 11.2
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UserQuotaUsage(BaseModel):
    """Individual user quota usage information.
    
    Requirements: 11.1
    """
    user_id: uuid.UUID = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    user_name: Optional[str] = Field(None, description="User display name")
    total_quota_used: int = Field(..., description="Total quota used across all accounts")
    account_count: int = Field(..., description="Number of YouTube accounts")
    highest_usage_percent: float = Field(..., description="Highest usage percentage among accounts")
    accounts: List["AccountQuotaInfo"] = Field(default_factory=list, description="Per-account quota info")


class AccountQuotaInfo(BaseModel):
    """Individual account quota information.
    
    Requirements: 11.1
    """
    account_id: uuid.UUID = Field(..., description="Account ID")
    channel_title: str = Field(..., description="YouTube channel title")
    daily_quota_used: int = Field(..., description="Daily quota used")
    daily_quota_limit: int = Field(default=10000, description="Daily quota limit")
    usage_percent: float = Field(..., description="Usage percentage")
    quota_reset_at: Optional[datetime] = Field(None, description="When quota resets")


class QuotaDashboardResponse(BaseModel):
    """Admin quota dashboard response.
    
    Requirements: 11.1
    """
    timestamp: datetime = Field(..., description="Dashboard timestamp")
    
    # Platform-wide totals
    total_daily_quota_used: int = Field(..., description="Total quota used across platform")
    total_daily_quota_limit: int = Field(..., description="Total quota limit (sum of all accounts)")
    platform_usage_percent: float = Field(..., description="Platform-wide usage percentage")
    
    # Account statistics
    total_accounts: int = Field(..., description="Total YouTube accounts")
    accounts_over_80_percent: int = Field(..., description="Accounts with >80% usage")
    accounts_over_90_percent: int = Field(..., description="Accounts with >90% usage")
    
    # User breakdown
    total_users_with_accounts: int = Field(..., description="Users with YouTube accounts")
    high_usage_users: List[UserQuotaUsage] = Field(..., description="Users with high quota usage")
    
    # Alert status
    alert_threshold_percent: int = Field(default=80, description="Alert threshold percentage")
    alerts_triggered: int = Field(..., description="Number of quota alerts triggered")


class QuotaAlertInfo(BaseModel):
    """Quota alert information.
    
    Requirements: 11.2
    """
    id: str = Field(..., description="Alert ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    account_id: uuid.UUID = Field(..., description="Account ID")
    channel_title: str = Field(..., description="Channel title")
    usage_percent: float = Field(..., description="Current usage percentage")
    quota_used: int = Field(..., description="Quota used")
    quota_limit: int = Field(..., description="Quota limit")
    triggered_at: datetime = Field(..., description="When alert was triggered")
    notified: bool = Field(default=False, description="Whether admin was notified")


class QuotaAlertsResponse(BaseModel):
    """Admin quota alerts response.
    
    Requirements: 11.2
    """
    timestamp: datetime = Field(..., description="Response timestamp")
    alerts: List[QuotaAlertInfo] = Field(..., description="Active quota alerts")
    total_alerts: int = Field(..., description="Total number of alerts")
    critical_count: int = Field(..., description="Alerts at >90% usage")
    warning_count: int = Field(..., description="Alerts at >80% usage")


# Update forward references
UserQuotaUsage.model_rebuild()
