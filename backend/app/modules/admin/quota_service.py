"""Admin Quota Management Service.

Service for admin quota monitoring and alerting.
Requirements: 11.1, 11.2

Property 13: Quota Alert Threshold
- For any YouTube API quota check, when usage exceeds 80% of daily limit,
  an alert SHALL be generated for admin.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.alerting import alert_manager, AlertSeverity, AlertThreshold
from app.modules.admin.quota_schemas import (
    QuotaDashboardResponse,
    UserQuotaUsage,
    AccountQuotaInfo,
    QuotaAlertInfo,
    QuotaAlertsResponse,
)

logger = logging.getLogger(__name__)

# Default quota limit per YouTube account
DEFAULT_DAILY_QUOTA_LIMIT = 10000

# Alert thresholds
QUOTA_WARNING_THRESHOLD = 80  # 80%
QUOTA_CRITICAL_THRESHOLD = 90  # 90%


class AdminQuotaService:
    """Service for admin quota monitoring and management.
    
    Requirements: 11.1, 11.2
    
    Property 13: Quota Alert Threshold
    - When usage exceeds 80% of daily limit, an alert is generated for admin.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_quota_dashboard(self) -> QuotaDashboardResponse:
        """Get comprehensive quota dashboard for admin.
        
        Requirements: 11.1
        
        Returns:
            QuotaDashboardResponse with daily usage, remaining, by user
        """
        from app.modules.account.models import YouTubeAccount, AccountStatus
        from app.modules.auth.models import User
        
        # Get all active YouTube accounts with their users
        result = await self.session.execute(
            select(YouTubeAccount)
            .options(selectinload(YouTubeAccount.user))
            .where(YouTubeAccount.status == AccountStatus.ACTIVE.value)
        )
        accounts = list(result.scalars().all())
        
        # Calculate platform-wide totals
        total_quota_used = sum(acc.daily_quota_used for acc in accounts)
        total_quota_limit = len(accounts) * DEFAULT_DAILY_QUOTA_LIMIT
        platform_usage_percent = (
            (total_quota_used / total_quota_limit * 100) 
            if total_quota_limit > 0 else 0.0
        )
        
        # Count accounts by usage threshold
        accounts_over_80 = sum(
            1 for acc in accounts 
            if acc.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT) >= QUOTA_WARNING_THRESHOLD
        )
        accounts_over_90 = sum(
            1 for acc in accounts 
            if acc.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT) >= QUOTA_CRITICAL_THRESHOLD
        )
        
        # Group accounts by user
        user_accounts: dict[uuid.UUID, List] = {}
        for acc in accounts:
            if acc.user_id not in user_accounts:
                user_accounts[acc.user_id] = []
            user_accounts[acc.user_id].append(acc)
        
        # Build high usage users list (users with any account over 80%)
        high_usage_users: List[UserQuotaUsage] = []
        alerts_triggered = 0
        
        for user_id, user_accs in user_accounts.items():
            # Check if any account is over threshold
            max_usage = max(
                acc.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT) 
                for acc in user_accs
            )
            
            if max_usage >= QUOTA_WARNING_THRESHOLD:
                # Get user info
                user = user_accs[0].user if user_accs else None
                
                # Build account info list
                account_infos = [
                    AccountQuotaInfo(
                        account_id=acc.id,
                        channel_title=acc.channel_title or "Unknown",
                        daily_quota_used=acc.daily_quota_used,
                        daily_quota_limit=DEFAULT_DAILY_QUOTA_LIMIT,
                        usage_percent=acc.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT),
                        quota_reset_at=acc.quota_reset_at,
                    )
                    for acc in user_accs
                ]
                
                total_user_quota = sum(acc.daily_quota_used for acc in user_accs)
                
                high_usage_users.append(UserQuotaUsage(
                    user_id=user_id,
                    user_email=user.email if user else "unknown",
                    user_name=user.name if user else None,
                    total_quota_used=total_user_quota,
                    account_count=len(user_accs),
                    highest_usage_percent=max_usage,
                    accounts=account_infos,
                ))
                
                # Count alerts for accounts over threshold
                alerts_triggered += sum(
                    1 for acc in user_accs 
                    if acc.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT) >= QUOTA_WARNING_THRESHOLD
                )
        
        # Sort by highest usage
        high_usage_users.sort(key=lambda u: u.highest_usage_percent, reverse=True)
        
        return QuotaDashboardResponse(
            timestamp=datetime.utcnow(),
            total_daily_quota_used=total_quota_used,
            total_daily_quota_limit=total_quota_limit,
            platform_usage_percent=round(platform_usage_percent, 2),
            total_accounts=len(accounts),
            accounts_over_80_percent=accounts_over_80,
            accounts_over_90_percent=accounts_over_90,
            total_users_with_accounts=len(user_accounts),
            high_usage_users=high_usage_users[:50],  # Limit to top 50
            alert_threshold_percent=QUOTA_WARNING_THRESHOLD,
            alerts_triggered=alerts_triggered,
        )
    
    async def check_and_alert_quota(
        self,
        account_id: uuid.UUID,
        quota_used: int,
        quota_limit: int = DEFAULT_DAILY_QUOTA_LIMIT,
    ) -> Optional[QuotaAlertInfo]:
        """Check quota usage and generate alert if threshold exceeded.
        
        Requirements: 11.2
        
        Property 13: Quota Alert Threshold
        - For any YouTube API quota check, when usage exceeds 80% of daily limit,
          an alert SHALL be generated for admin.
        
        Args:
            account_id: YouTube account ID
            quota_used: Current quota used
            quota_limit: Daily quota limit
            
        Returns:
            QuotaAlertInfo if alert triggered, None otherwise
        """
        usage_percent = (quota_used / quota_limit * 100) if quota_limit > 0 else 100.0
        
        # Property 13: Alert when usage exceeds 80%
        if usage_percent < QUOTA_WARNING_THRESHOLD:
            return None
        
        from app.modules.account.models import YouTubeAccount
        from app.modules.auth.models import User
        
        # Get account and user info
        result = await self.session.execute(
            select(YouTubeAccount)
            .options(selectinload(YouTubeAccount.user))
            .where(YouTubeAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            logger.warning(f"Account {account_id} not found for quota alert")
            return None
        
        user = account.user
        
        # Determine severity
        severity = (
            AlertSeverity.CRITICAL 
            if usage_percent >= QUOTA_CRITICAL_THRESHOLD 
            else AlertSeverity.WARNING
        )
        
        # Trigger alert via alert manager
        alert_manager.check_metric(
            metric_name="youtube_api_quota_percent",
            value=usage_percent,
            labels={
                "account_id": str(account_id),
                "user_id": str(account.user_id),
            },
        )
        
        alert_info = QuotaAlertInfo(
            id=f"quota_{account_id}_{datetime.utcnow().timestamp()}",
            user_id=account.user_id,
            user_email=user.email if user else "unknown",
            account_id=account_id,
            channel_title=account.channel_title or "Unknown",
            usage_percent=round(usage_percent, 2),
            quota_used=quota_used,
            quota_limit=quota_limit,
            triggered_at=datetime.utcnow(),
            notified=True,
        )
        
        logger.warning(
            f"Quota alert triggered for account {account_id}: {usage_percent:.1f}% used",
            extra={
                "account_id": str(account_id),
                "user_id": str(account.user_id),
                "usage_percent": usage_percent,
                "severity": severity.value,
            }
        )
        
        return alert_info
    
    async def get_quota_alerts(self) -> QuotaAlertsResponse:
        """Get all active quota alerts.
        
        Requirements: 11.2
        
        Returns:
            QuotaAlertsResponse with all accounts exceeding threshold
        """
        from app.modules.account.models import YouTubeAccount, AccountStatus
        
        # Get all accounts over warning threshold
        result = await self.session.execute(
            select(YouTubeAccount)
            .options(selectinload(YouTubeAccount.user))
            .where(YouTubeAccount.status == AccountStatus.ACTIVE.value)
        )
        accounts = list(result.scalars().all())
        
        alerts: List[QuotaAlertInfo] = []
        critical_count = 0
        warning_count = 0
        
        for account in accounts:
            usage_percent = account.get_quota_usage_percent(DEFAULT_DAILY_QUOTA_LIMIT)
            
            if usage_percent >= QUOTA_WARNING_THRESHOLD:
                user = account.user
                
                alert = QuotaAlertInfo(
                    id=f"quota_{account.id}",
                    user_id=account.user_id,
                    user_email=user.email if user else "unknown",
                    account_id=account.id,
                    channel_title=account.channel_title or "Unknown",
                    usage_percent=round(usage_percent, 2),
                    quota_used=account.daily_quota_used,
                    quota_limit=DEFAULT_DAILY_QUOTA_LIMIT,
                    triggered_at=datetime.utcnow(),
                    notified=True,
                )
                alerts.append(alert)
                
                if usage_percent >= QUOTA_CRITICAL_THRESHOLD:
                    critical_count += 1
                else:
                    warning_count += 1
        
        # Sort by usage percent descending
        alerts.sort(key=lambda a: a.usage_percent, reverse=True)
        
        return QuotaAlertsResponse(
            timestamp=datetime.utcnow(),
            alerts=alerts,
            total_alerts=len(alerts),
            critical_count=critical_count,
            warning_count=warning_count,
        )


def setup_quota_alerting() -> None:
    """Set up quota alerting thresholds.
    
    Requirements: 11.2
    
    Property 13: Quota Alert Threshold
    - Alert admin when usage exceeds 80%
    """
    # Register warning threshold (80%)
    alert_manager.register_threshold(AlertThreshold(
        name="youtube_quota_warning",
        metric_name="youtube_api_quota_percent",
        threshold_value=float(QUOTA_WARNING_THRESHOLD),
        comparison="gte",
        severity=AlertSeverity.WARNING,
        description=f"YouTube API quota usage exceeds {QUOTA_WARNING_THRESHOLD}%",
        duration_seconds=0,  # Immediate alert
        cooldown_seconds=3600,  # Alert at most once per hour per account
    ))
    
    # Register critical threshold (90%)
    alert_manager.register_threshold(AlertThreshold(
        name="youtube_quota_critical",
        metric_name="youtube_api_quota_percent",
        threshold_value=float(QUOTA_CRITICAL_THRESHOLD),
        comparison="gte",
        severity=AlertSeverity.CRITICAL,
        description=f"YouTube API quota usage exceeds {QUOTA_CRITICAL_THRESHOLD}%",
        duration_seconds=0,  # Immediate alert
        cooldown_seconds=1800,  # Alert at most once per 30 minutes per account
    ))
    
    logger.info("Quota alerting thresholds configured")
