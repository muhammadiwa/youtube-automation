"""Pydantic schemas for AI Service Management.

Requirements: 13.1-13.5 - AI Service Management
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ==================== AI Dashboard Schemas (Requirements 13.1) ====================


class AIFeatureUsage(BaseModel):
    """Usage statistics for a specific AI feature."""
    feature: str = Field(description="Feature name (titles, descriptions, thumbnails, chatbot)")
    api_calls: int = Field(description="Total API calls")
    tokens_used: int = Field(description="Total tokens consumed")
    cost_usd: float = Field(description="Total cost in USD")
    success_rate: float = Field(ge=0, le=100, description="Success rate percentage")
    avg_latency_ms: float = Field(description="Average latency in milliseconds")


class AIDashboardMetrics(BaseModel):
    """AI Dashboard metrics response.
    
    Requirements: 13.1 - Display total API calls, costs, and usage by feature
    """
    total_api_calls: int = Field(description="Total API calls across all features")
    total_tokens_used: int = Field(description="Total tokens consumed")
    total_cost_usd: float = Field(description="Total cost in USD")
    monthly_budget_usd: float = Field(description="Monthly budget limit")
    budget_used_percentage: float = Field(ge=0, le=100, description="Percentage of budget used")
    usage_by_feature: list[AIFeatureUsage] = Field(description="Usage breakdown by feature")
    period_start: datetime = Field(description="Start of the reporting period")
    period_end: datetime = Field(description="End of the reporting period")
    is_throttled: bool = Field(default=False, description="Whether AI is currently throttled")


# ==================== AI Limits Config Schemas (Requirements 13.2) ====================


class AIPlanLimits(BaseModel):
    """AI generation limits for a specific plan."""
    plan_id: str = Field(description="Plan identifier")
    plan_name: str = Field(description="Plan display name")
    max_title_generations: int = Field(ge=0, description="Max title generations per month")
    max_description_generations: int = Field(ge=0, description="Max description generations per month")
    max_thumbnail_generations: int = Field(ge=0, description="Max thumbnail generations per month")
    max_chatbot_messages: int = Field(ge=0, description="Max chatbot messages per month")
    max_total_tokens: int = Field(ge=0, description="Max total tokens per month")


class AILimitsConfig(BaseModel):
    """AI limits configuration for all plans.
    
    Requirements: 13.2 - Configure generation limits per plan
    """
    limits_by_plan: list[AIPlanLimits] = Field(description="Limits for each plan")
    global_daily_limit: int = Field(ge=0, description="Global daily API call limit")
    throttle_at_percentage: int = Field(ge=0, le=100, default=90, description="Throttle when budget reaches this %")


class AILimitsUpdate(BaseModel):
    """Update schema for AI limits configuration."""
    plan_id: str = Field(description="Plan to update")
    max_title_generations: Optional[int] = Field(None, ge=0)
    max_description_generations: Optional[int] = Field(None, ge=0)
    max_thumbnail_generations: Optional[int] = Field(None, ge=0)
    max_chatbot_messages: Optional[int] = Field(None, ge=0)
    max_total_tokens: Optional[int] = Field(None, ge=0)


class AIGlobalLimitsUpdate(BaseModel):
    """Update schema for global AI limits."""
    global_daily_limit: Optional[int] = Field(None, ge=0)
    throttle_at_percentage: Optional[int] = Field(None, ge=0, le=100)


# ==================== AI Logs Schemas (Requirements 13.3) ====================


class AILogEntry(BaseModel):
    """Single AI API log entry.
    
    Requirements: 13.3 - Show request/response with latency and tokens
    """
    id: uuid.UUID = Field(description="Log entry ID")
    user_id: uuid.UUID = Field(description="User who made the request")
    feature: str = Field(description="AI feature used")
    model: str = Field(description="AI model used")
    request_summary: str = Field(description="Summary of the request")
    response_summary: Optional[str] = Field(description="Summary of the response")
    tokens_input: int = Field(description="Input tokens used")
    tokens_output: int = Field(description="Output tokens generated")
    total_tokens: int = Field(description="Total tokens used")
    latency_ms: float = Field(description="Request latency in milliseconds")
    cost_usd: float = Field(description="Cost of this request")
    status: Literal["success", "error", "timeout"] = Field(description="Request status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(description="When the request was made")


class AILogsResponse(BaseModel):
    """Paginated AI logs response."""
    logs: list[AILogEntry] = Field(description="List of log entries")
    total: int = Field(description="Total number of logs")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")


class AILogsFilter(BaseModel):
    """Filter options for AI logs."""
    user_id: Optional[uuid.UUID] = Field(None, description="Filter by user")
    feature: Optional[str] = Field(None, description="Filter by feature")
    status: Optional[Literal["success", "error", "timeout"]] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter from date")
    end_date: Optional[datetime] = Field(None, description="Filter to date")
    min_latency_ms: Optional[float] = Field(None, ge=0, description="Minimum latency filter")
    max_latency_ms: Optional[float] = Field(None, ge=0, description="Maximum latency filter")


# ==================== AI Budget Alerting Schemas (Requirements 13.4) ====================


class AIBudgetStatus(BaseModel):
    """Current AI budget status.
    
    Requirements: 13.4 - Alert when costs exceed budget
    """
    monthly_budget_usd: float = Field(description="Monthly budget limit")
    current_spend_usd: float = Field(description="Current month spend")
    remaining_budget_usd: float = Field(description="Remaining budget")
    budget_used_percentage: float = Field(ge=0, description="Percentage of budget used")
    projected_monthly_spend: float = Field(description="Projected spend by month end")
    is_over_budget: bool = Field(description="Whether budget is exceeded")
    is_throttled: bool = Field(description="Whether AI is currently throttled")
    throttle_threshold_percentage: int = Field(description="Percentage at which throttling kicks in")
    alert_thresholds: list[int] = Field(description="Alert threshold percentages")
    alerts_sent: list[int] = Field(description="Thresholds for which alerts were sent")


class AIBudgetConfig(BaseModel):
    """AI budget configuration."""
    monthly_budget_usd: float = Field(ge=0, description="Monthly budget limit")
    alert_thresholds: list[int] = Field(description="Alert threshold percentages (e.g., [50, 75, 90, 100])")
    enable_throttling: bool = Field(default=True, description="Enable automatic throttling")
    throttle_at_percentage: int = Field(ge=0, le=100, default=90, description="Throttle at this percentage")
    disable_at_percentage: int = Field(ge=0, le=150, default=100, description="Disable AI at this percentage")


class AIBudgetConfigUpdate(BaseModel):
    """Update schema for AI budget configuration."""
    monthly_budget_usd: Optional[float] = Field(None, ge=0)
    alert_thresholds: Optional[list[int]] = None
    enable_throttling: Optional[bool] = None
    throttle_at_percentage: Optional[int] = Field(None, ge=0, le=100)
    disable_at_percentage: Optional[int] = Field(None, ge=0, le=150)


class AIBudgetAlert(BaseModel):
    """AI budget alert notification."""
    alert_type: Literal["warning", "critical", "over_budget"] = Field(description="Alert severity")
    threshold_percentage: int = Field(description="Threshold that triggered the alert")
    current_spend_usd: float = Field(description="Current spend when alert triggered")
    monthly_budget_usd: float = Field(description="Monthly budget")
    message: str = Field(description="Alert message")
    created_at: datetime = Field(description="When alert was created")
    acknowledged: bool = Field(default=False, description="Whether alert was acknowledged")


# ==================== AI Model Config Schemas (Requirements 13.5) ====================


class AIFeatureModelConfig(BaseModel):
    """Model configuration for a specific AI feature."""
    feature: str = Field(description="Feature name")
    model: str = Field(description="Model to use (e.g., gpt-4, gpt-3.5-turbo)")
    max_tokens: int = Field(ge=1, le=8000, description="Max tokens for response")
    temperature: float = Field(ge=0, le=2, default=0.7, description="Model temperature")
    top_p: float = Field(ge=0, le=1, default=1.0, description="Top-p sampling")
    frequency_penalty: float = Field(ge=-2, le=2, default=0, description="Frequency penalty")
    presence_penalty: float = Field(ge=-2, le=2, default=0, description="Presence penalty")
    timeout_seconds: int = Field(ge=1, le=120, default=30, description="Request timeout")


class AIModelConfig(BaseModel):
    """AI model configuration for all features.
    
    Requirements: 13.5 - Configure model version and parameters per feature
    """
    default_model: str = Field(default="gpt-4", description="Default model for all features")
    features: list[AIFeatureModelConfig] = Field(description="Per-feature model configuration")
    available_models: list[str] = Field(
        default=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        description="Available models"
    )


class AIModelConfigUpdate(BaseModel):
    """Update schema for AI model configuration."""
    feature: str = Field(description="Feature to update")
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=8000)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=120)


class AIDefaultModelUpdate(BaseModel):
    """Update schema for default AI model."""
    default_model: str = Field(description="New default model")


# ==================== Response Schemas ====================


class AIConfigUpdateResponse(BaseModel):
    """Response after updating AI configuration."""
    category: str = Field(description="Configuration category updated")
    previous_value: dict = Field(description="Previous configuration")
    new_value: dict = Field(description="New configuration")
    updated_by: uuid.UUID = Field(description="Admin who made the update")
    updated_at: datetime = Field(description="When the update was made")
    message: str = Field(description="Success message")
