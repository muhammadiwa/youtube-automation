"""Pydantic schemas for Admin Payment Gateway module.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5 - Payment Gateway Administration
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ==================== Gateway List Schemas (5.1) ====================


class GatewayHealthInfo(BaseModel):
    """Gateway health information."""
    status: str = Field(..., description="Health status (healthy, degraded, down)")
    success_rate: float = Field(..., description="Success rate percentage")
    success_rate_24h: float = Field(..., description="Success rate in last 24 hours")
    last_transaction_at: Optional[datetime] = Field(None, description="Last transaction timestamp")
    last_failure_at: Optional[datetime] = Field(None, description="Last failure timestamp")


class GatewayStatsInfo(BaseModel):
    """Gateway statistics summary."""
    total_transactions: int = Field(0, description="Total number of transactions")
    successful_transactions: int = Field(0, description="Number of successful transactions")
    failed_transactions: int = Field(0, description="Number of failed transactions")
    total_volume: float = Field(0.0, description="Total transaction volume")
    average_transaction: float = Field(0.0, description="Average transaction amount")
    transactions_24h: int = Field(0, description="Transactions in last 24 hours")


class GatewayResponse(BaseModel):
    """Response for a single payment gateway.
    
    Requirements: 5.1 - Display all gateways with status, health, and transaction stats
    """
    id: uuid.UUID
    provider: str
    display_name: str
    is_enabled: bool
    is_default: bool
    sandbox_mode: bool
    has_credentials: bool
    supported_currencies: list[str]
    supported_payment_methods: list[str]
    transaction_fee_percent: float
    fixed_fee: float
    min_amount: float
    max_amount: Optional[float]
    health: GatewayHealthInfo
    stats: GatewayStatsInfo
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GatewayListResponse(BaseModel):
    """Response for gateway list.
    
    Requirements: 5.1 - Display all gateways with status, health, and transaction stats
    """
    items: list[GatewayResponse]
    total: int


# ==================== Gateway Enable/Disable Schemas (5.2) ====================


class GatewayStatusUpdateRequest(BaseModel):
    """Request to enable/disable a gateway.
    
    Requirements: 5.2 - Enable/disable gateway dynamically without system restart
    """
    is_enabled: bool = Field(..., description="Whether to enable or disable the gateway")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")


class GatewaySetDefaultRequest(BaseModel):
    """Request to set a gateway as default.
    
    Requirements: 5.2 - Set default payment gateway
    """
    reason: Optional[str] = Field(None, max_length=500, description="Reason for setting as default")


class GatewaySetDefaultResponse(BaseModel):
    """Response after setting gateway as default.
    
    Requirements: 5.2 - Set default payment gateway
    """
    provider: str
    is_default: bool
    updated_at: datetime
    message: str


class GatewayStatusUpdateResponse(BaseModel):
    """Response after updating gateway status.
    
    Requirements: 5.2 - Update availability immediately without system restart
    """
    provider: str
    is_enabled: bool
    updated_at: datetime
    message: str


# ==================== Gateway Credentials Schemas (5.3) ====================


class GatewayCredentialsUpdateRequest(BaseModel):
    """Request to update gateway credentials.
    
    Requirements: 5.3 - Validate credentials before saving and encrypt sensitive data
    """
    api_key: str = Field(..., min_length=1, description="API key")
    api_secret: str = Field(..., min_length=1, description="API secret")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret")
    sandbox_mode: bool = Field(True, description="Whether to use sandbox/test mode")
    validate_before_save: bool = Field(True, description="Validate credentials before saving")


class GatewayCredentialsUpdateResponse(BaseModel):
    """Response after updating gateway credentials.
    
    Requirements: 5.3 - Validate credentials before saving and encrypt sensitive data
    """
    provider: str
    credentials_valid: bool
    sandbox_mode: bool
    updated_at: datetime
    message: str


# ==================== Gateway Statistics Schemas (5.4) ====================


class GatewayDetailedStats(BaseModel):
    """Detailed gateway statistics.
    
    Requirements: 5.4 - Show success rate, failure rate, total volume, average transaction
    """
    provider: str
    display_name: str
    primary_currency: str = Field("USD", description="Primary currency for this gateway")
    
    # Transaction counts
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    
    # Rates
    success_rate: float = Field(..., description="Overall success rate percentage")
    failure_rate: float = Field(..., description="Overall failure rate percentage")
    success_rate_24h: float = Field(..., description="Success rate in last 24 hours")
    
    # Volume in original currency
    total_volume: float = Field(..., description="Total transaction volume in primary currency")
    average_transaction: float = Field(..., description="Average transaction amount in primary currency")
    
    # Volume converted to USD for comparison
    total_volume_usd: float = Field(0.0, description="Total transaction volume converted to USD")
    average_transaction_usd: float = Field(0.0, description="Average transaction amount converted to USD")
    
    # Time-based stats
    transactions_24h: int = Field(..., description="Transactions in last 24 hours")
    volume_24h: float = Field(0.0, description="Volume in last 24 hours in primary currency")
    volume_24h_usd: float = Field(0.0, description="Volume in last 24 hours converted to USD")
    
    # Health
    health_status: str
    last_transaction_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    
    # Period info
    stats_since: Optional[datetime] = Field(None, description="Statistics collection start date")


class GatewayStatsResponse(BaseModel):
    """Response for gateway statistics.
    
    Requirements: 5.4 - Show success rate, failure rate, total volume, average transaction
    """
    stats: GatewayDetailedStats
    period_start: Optional[datetime]
    period_end: Optional[datetime]


# ==================== Gateway Health Alert Schemas (5.5) ====================


class GatewayHealthAlert(BaseModel):
    """Gateway health alert.
    
    Requirements: 5.5 - Alert admin when gateway health degrades
    """
    id: uuid.UUID
    provider: str
    alert_type: str = Field(..., description="Type of alert (degraded, down, recovered)")
    severity: str = Field(..., description="Alert severity (warning, critical)")
    message: str
    health_status: str
    success_rate: float
    suggested_action: Optional[str] = Field(None, description="Suggested failover action")
    alternative_gateways: list[str] = Field(default_factory=list, description="Available alternative gateways")
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[uuid.UUID] = None


class GatewayHealthAlertListResponse(BaseModel):
    """Response for gateway health alerts list."""
    items: list[GatewayHealthAlert]
    total: int
    unacknowledged_count: int


class GatewayHealthAlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge a health alert."""
    notes: Optional[str] = Field(None, max_length=500, description="Acknowledgement notes")


class GatewayHealthAlertAcknowledgeResponse(BaseModel):
    """Response after acknowledging a health alert."""
    alert_id: uuid.UUID
    acknowledged: bool
    acknowledged_at: datetime
    message: str


class GatewayFailoverSuggestion(BaseModel):
    """Failover suggestion when gateway health degrades.
    
    Requirements: 5.5 - Suggest failover to alternative gateway
    """
    current_gateway: str
    current_health_status: str
    current_success_rate: float
    suggested_gateway: str
    suggested_gateway_health: str
    suggested_gateway_success_rate: float
    reason: str
    auto_failover_available: bool = False
