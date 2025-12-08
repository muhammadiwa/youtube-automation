"""Usage Metering Service for tracking resource consumption.

Implements comprehensive usage tracking with progressive warnings.
Requirements: 27.1, 27.2, 27.3, 27.4
"""

import uuid
from datetime import datetime, date
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from app.modules.billing.models import (
    UsageResourceType,
    PLAN_LIMITS,
    PlanTier,
)


# Warning thresholds (Requirements: 27.2)
WARNING_THRESHOLDS = [50, 75, 90]


@dataclass
class UsageWarning:
    """Represents a usage warning event.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    """
    user_id: uuid.UUID
    resource_type: str
    threshold_percent: int
    current_usage: float
    limit: float
    current_percent: float
    message: str


@dataclass
class UsageMetrics:
    """Aggregated usage metrics for a resource.
    
    Requirements: 27.1 - Display breakdown of usage
    """
    resource_type: str
    total_used: float
    limit: float
    percent_used: float
    is_unlimited: bool
    warning_threshold_reached: Optional[int]
    remaining: float


@dataclass
class EncodingUsageDetail:
    """Detailed encoding usage by resolution tier.
    
    Requirements: 27.3 - Track encoding minutes per resolution tier
    """
    resolution: str
    minutes_used: float
    video_count: int


@dataclass
class BandwidthUsageDetail:
    """Detailed bandwidth usage by source.
    
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """
    usage_type: str  # stream, upload, download
    resource_id: Optional[str]
    bandwidth_gb: float


class UsageMeteringService:
    """Service for tracking and managing resource usage.
    
    Requirements: 27.1, 27.2, 27.3, 27.4
    
    This service provides:
    - Unified interface for recording all resource types
    - Progressive warning generation at 50%, 75%, 90% thresholds
    - Detailed breakdown by metadata (resolution, stream/upload attribution)
    - Usage limit checking before operations
    """

    def __init__(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        plan_tier: str,
        billing_period_start: date,
        billing_period_end: date,
        custom_limits: Optional[dict] = None,
    ):
        """Initialize the metering service.
        
        Args:
            user_id: User ID
            subscription_id: Subscription ID
            plan_tier: Current plan tier
            billing_period_start: Start of billing period
            billing_period_end: End of billing period
            custom_limits: Optional custom limits override
        """
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.plan_tier = plan_tier
        self.billing_period_start = billing_period_start
        self.billing_period_end = billing_period_end
        self.custom_limits = custom_limits or {}
        
        # Initialize usage tracking
        self._usage: dict[str, float] = {}
        self._warnings_sent: dict[str, set[int]] = {}
        
        # Load limits
        self._limits = self._get_limits()

    def _get_limits(self) -> dict[str, float]:
        """Get resource limits for the current plan.
        
        Returns:
            Dictionary of resource type to limit value
        """
        base_limits = PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS[PlanTier.FREE.value])
        limits = {}
        
        for resource_type in UsageResourceType:
            key = resource_type.value
            if key in self.custom_limits:
                limits[key] = float(self.custom_limits[key])
            elif key in base_limits:
                limits[key] = float(base_limits[key])
            else:
                limits[key] = 0.0
        
        return limits

    def get_limit(self, resource_type: str) -> float:
        """Get the limit for a specific resource type.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Limit value (-1 for unlimited)
        """
        return self._limits.get(resource_type, 0.0)

    def is_unlimited(self, resource_type: str) -> bool:
        """Check if a resource type has unlimited usage.
        
        Args:
            resource_type: The resource type
            
        Returns:
            True if unlimited
        """
        return self.get_limit(resource_type) == -1

    def set_current_usage(self, resource_type: str, amount: float) -> None:
        """Set the current usage for a resource type.
        
        Args:
            resource_type: The resource type
            amount: Current usage amount
        """
        self._usage[resource_type] = amount

    def set_warnings_sent(self, resource_type: str, thresholds: set[int]) -> None:
        """Set which warning thresholds have been sent.
        
        Args:
            resource_type: The resource type
            thresholds: Set of thresholds already sent (50, 75, 90)
        """
        self._warnings_sent[resource_type] = thresholds

    def get_current_usage(self, resource_type: str) -> float:
        """Get current usage for a resource type.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Current usage amount
        """
        return self._usage.get(resource_type, 0.0)

    def calculate_usage_percent(self, resource_type: str) -> float:
        """Calculate usage as percentage of limit.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Usage percentage (0.0 for unlimited)
        """
        limit = self.get_limit(resource_type)
        if limit == -1:
            return 0.0
        if limit <= 0:
            return 100.0
        
        used = self.get_current_usage(resource_type)
        return (used / limit) * 100

    def check_quota(
        self,
        resource_type: str,
        requested_amount: float = 1.0,
    ) -> Tuple[bool, float, float]:
        """Check if there's enough quota for a requested amount.
        
        Args:
            resource_type: The resource type
            requested_amount: Amount to check
            
        Returns:
            Tuple of (has_quota, current_usage, limit)
        """
        limit = self.get_limit(resource_type)
        current = self.get_current_usage(resource_type)
        
        # Unlimited
        if limit == -1:
            return True, current, -1.0
        
        has_quota = (current + requested_amount) <= limit
        return has_quota, current, limit

    def record_usage(
        self,
        resource_type: str,
        amount: float,
    ) -> Tuple[float, Optional[UsageWarning]]:
        """Record usage and check for warnings.
        
        Requirements: 27.1 - Track usage
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        
        Args:
            resource_type: The resource type
            amount: Amount to record
            
        Returns:
            Tuple of (new_total, warning_if_any)
        """
        # Update usage
        current = self.get_current_usage(resource_type)
        new_total = current + amount
        self._usage[resource_type] = new_total
        
        # Check for warnings
        warning = self._check_warning(resource_type)
        
        return new_total, warning

    def _check_warning(self, resource_type: str) -> Optional[UsageWarning]:
        """Check if a warning should be generated.
        
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        
        Args:
            resource_type: The resource type
            
        Returns:
            UsageWarning if threshold reached, None otherwise
        """
        # Skip if unlimited
        if self.is_unlimited(resource_type):
            return None
        
        percent = self.calculate_usage_percent(resource_type)
        sent = self._warnings_sent.get(resource_type, set())
        
        # Check thresholds in order (highest first for proper detection)
        for threshold in sorted(WARNING_THRESHOLDS, reverse=True):
            if percent >= threshold and threshold not in sent:
                # Mark as sent
                if resource_type not in self._warnings_sent:
                    self._warnings_sent[resource_type] = set()
                self._warnings_sent[resource_type].add(threshold)
                
                # Generate warning
                limit = self.get_limit(resource_type)
                current = self.get_current_usage(resource_type)
                
                return UsageWarning(
                    user_id=self.user_id,
                    resource_type=resource_type,
                    threshold_percent=threshold,
                    current_usage=current,
                    limit=limit,
                    current_percent=percent,
                    message=self._format_warning_message(
                        resource_type, threshold, current, limit, percent
                    ),
                )
        
        return None

    def _format_warning_message(
        self,
        resource_type: str,
        threshold: int,
        current: float,
        limit: float,
        percent: float,
    ) -> str:
        """Format a warning message.
        
        Args:
            resource_type: The resource type
            threshold: Warning threshold
            current: Current usage
            limit: Usage limit
            percent: Usage percentage
            
        Returns:
            Formatted warning message
        """
        resource_display = resource_type.replace("_", " ").title()
        
        if threshold == 90:
            return (
                f"CRITICAL: Your {resource_display} usage has reached {percent:.1f}% "
                f"of your plan limit ({current:.2f}/{limit:.2f}). "
                f"Consider upgrading your plan to avoid service interruption."
            )
        elif threshold == 75:
            return (
                f"WARNING: Your {resource_display} usage has reached {percent:.1f}% "
                f"of your plan limit ({current:.2f}/{limit:.2f}). "
                f"Monitor your usage to avoid reaching the limit."
            )
        else:  # 50%
            return (
                f"INFO: Your {resource_display} usage has reached {percent:.1f}% "
                f"of your plan limit ({current:.2f}/{limit:.2f})."
            )

    def get_warning_threshold_reached(self, resource_type: str) -> Optional[int]:
        """Get the highest warning threshold reached.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Highest threshold reached (50, 75, 90) or None
        """
        percent = self.calculate_usage_percent(resource_type)
        
        if percent >= 90:
            return 90
        elif percent >= 75:
            return 75
        elif percent >= 50:
            return 50
        return None

    def get_metrics(self, resource_type: str) -> UsageMetrics:
        """Get usage metrics for a resource type.
        
        Requirements: 27.1 - Display breakdown of usage
        
        Args:
            resource_type: The resource type
            
        Returns:
            UsageMetrics object
        """
        limit = self.get_limit(resource_type)
        used = self.get_current_usage(resource_type)
        is_unlimited = limit == -1
        percent = 0.0 if is_unlimited else self.calculate_usage_percent(resource_type)
        remaining = -1.0 if is_unlimited else max(0, limit - used)
        
        return UsageMetrics(
            resource_type=resource_type,
            total_used=used,
            limit=limit,
            percent_used=percent,
            is_unlimited=is_unlimited,
            warning_threshold_reached=self.get_warning_threshold_reached(resource_type),
            remaining=remaining,
        )

    def get_all_metrics(self) -> List[UsageMetrics]:
        """Get metrics for all resource types.
        
        Returns:
            List of UsageMetrics for all tracked resources
        """
        return [
            self.get_metrics(rt.value)
            for rt in UsageResourceType
        ]


# ==================== Standalone Functions for Usage Calculation ====================

def calculate_usage_percent(used: float, limit: float) -> float:
    """Calculate usage as percentage of limit.
    
    Args:
        used: Amount used
        limit: Limit value (-1 for unlimited)
        
    Returns:
        Usage percentage (0.0 for unlimited)
    """
    if limit == -1:
        return 0.0
    if limit <= 0:
        return 100.0
    return (used / limit) * 100


def get_warning_threshold(usage_percent: float) -> Optional[int]:
    """Get the warning threshold reached for a usage percentage.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    Args:
        usage_percent: Current usage percentage
        
    Returns:
        The highest threshold reached (50, 75, 90) or None
    """
    if usage_percent >= 90:
        return 90
    elif usage_percent >= 75:
        return 75
    elif usage_percent >= 50:
        return 50
    return None


def should_send_warning(
    usage_percent: float,
    warning_50_sent: bool,
    warning_75_sent: bool,
    warning_90_sent: bool,
) -> Optional[int]:
    """Determine if a warning should be sent.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    Args:
        usage_percent: Current usage percentage
        warning_50_sent: Whether 50% warning was sent
        warning_75_sent: Whether 75% warning was sent
        warning_90_sent: Whether 90% warning was sent
        
    Returns:
        The threshold to warn about, or None if no warning needed
    """
    if usage_percent >= 90 and not warning_90_sent:
        return 90
    elif usage_percent >= 75 and not warning_75_sent:
        return 75
    elif usage_percent >= 50 and not warning_50_sent:
        return 50
    return None


def get_all_pending_warnings(
    usage_percent: float,
    warning_50_sent: bool,
    warning_75_sent: bool,
    warning_90_sent: bool,
) -> List[int]:
    """Get all pending warnings that should be sent.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    This returns all thresholds that have been crossed but not yet warned about.
    
    Args:
        usage_percent: Current usage percentage
        warning_50_sent: Whether 50% warning was sent
        warning_75_sent: Whether 75% warning was sent
        warning_90_sent: Whether 90% warning was sent
        
    Returns:
        List of thresholds to warn about (may be empty)
    """
    pending = []
    
    if usage_percent >= 50 and not warning_50_sent:
        pending.append(50)
    if usage_percent >= 75 and not warning_75_sent:
        pending.append(75)
    if usage_percent >= 90 and not warning_90_sent:
        pending.append(90)
    
    return pending


def format_usage_for_display(
    resource_type: str,
    used: float,
    limit: float,
) -> str:
    """Format usage for display.
    
    Args:
        resource_type: The resource type
        used: Amount used
        limit: Limit value
        
    Returns:
        Formatted string for display
    """
    resource_display = resource_type.replace("_", " ").title()
    
    if limit == -1:
        return f"{resource_display}: {used:.2f} (Unlimited)"
    
    percent = calculate_usage_percent(used, limit)
    return f"{resource_display}: {used:.2f}/{limit:.2f} ({percent:.1f}%)"


def get_resource_unit(resource_type: str) -> str:
    """Get the unit for a resource type.
    
    Args:
        resource_type: The resource type
        
    Returns:
        Unit string
    """
    units = {
        UsageResourceType.API_CALLS.value: "calls",
        UsageResourceType.ENCODING_MINUTES.value: "minutes",
        UsageResourceType.STORAGE_GB.value: "GB",
        UsageResourceType.BANDWIDTH_GB.value: "GB",
        UsageResourceType.CONNECTED_ACCOUNTS.value: "accounts",
        UsageResourceType.CONCURRENT_STREAMS.value: "streams",
    }
    return units.get(resource_type, "units")
