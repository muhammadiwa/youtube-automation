"""Celery tasks for revenue tracking automation.

Implements background tasks for trend detection and AI analysis.
Requirements: 18.3
"""

import uuid
from datetime import date, timedelta
from typing import Optional

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import get_sync_session
from app.modules.analytics.revenue_models import (
    RevenueRecord,
    RevenueGoal,
    RevenueAlert,
    AlertType,
    AlertSeverity,
    AlertStatus,
    GoalStatus,
)
from app.modules.analytics.revenue_schemas import RevenueAlertCreate


@celery_app.task(bind=True, max_retries=3)
def detect_revenue_trend_changes(
    self,
    user_id: str,
    account_id: str,
    threshold_percent: float = 20.0,
) -> Optional[dict]:
    """Detect significant revenue trend changes for an account.
    
    Requirements: 18.3
    
    Args:
        user_id: User ID
        account_id: YouTube account ID
        threshold_percent: Minimum percentage change to trigger alert
        
    Returns:
        Alert data if trend change detected, None otherwise
    """
    from sqlalchemy import select, func, and_
    
    try:
        with get_sync_session() as session:
            user_uuid = uuid.UUID(user_id)
            account_uuid = uuid.UUID(account_id)
            
            today = date.today()
            
            # Compare last 7 days to previous 7 days
            current_end = today
            current_start = today - timedelta(days=6)
            previous_end = current_start - timedelta(days=1)
            previous_start = previous_end - timedelta(days=6)
            
            # Get current period total
            current_result = session.execute(
                select(func.sum(RevenueRecord.total_revenue)).where(
                    and_(
                        RevenueRecord.account_id == account_uuid,
                        RevenueRecord.record_date >= current_start,
                        RevenueRecord.record_date <= current_end,
                    )
                )
            )
            current_total = current_result.scalar() or 0.0
            
            # Get previous period total
            previous_result = session.execute(
                select(func.sum(RevenueRecord.total_revenue)).where(
                    and_(
                        RevenueRecord.account_id == account_uuid,
                        RevenueRecord.record_date >= previous_start,
                        RevenueRecord.record_date <= previous_end,
                    )
                )
            )
            previous_total = previous_result.scalar() or 0.0
            
            if previous_total == 0:
                return None
            
            change_percent = ((current_total - previous_total) / previous_total) * 100
            
            # Check if change exceeds threshold
            if abs(change_percent) >= threshold_percent:
                severity = AlertSeverity.INFO.value
                if abs(change_percent) >= 50:
                    severity = AlertSeverity.CRITICAL.value
                elif abs(change_percent) >= 30:
                    severity = AlertSeverity.WARNING.value
                
                direction = "increased" if change_percent > 0 else "decreased"
                title = f"Revenue {direction} by {abs(change_percent):.1f}%"
                message = (
                    f"Your revenue has {direction} from ${previous_total:.2f} "
                    f"to ${current_total:.2f} compared to the previous week."
                )
                
                # Create alert
                alert = RevenueAlert(
                    user_id=user_uuid,
                    account_id=account_uuid,
                    alert_type=AlertType.TREND_CHANGE.value,
                    severity=severity,
                    title=title,
                    message=message,
                    metric_name="total_revenue",
                    previous_value=previous_total,
                    current_value=current_total,
                    change_percentage=change_percent,
                )
                
                session.add(alert)
                session.commit()
                
                # Trigger AI analysis
                analyze_revenue_trend.delay(str(alert.id))
                
                return {
                    "alert_id": str(alert.id),
                    "change_percent": change_percent,
                    "severity": severity,
                }
            
            return None
            
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def analyze_revenue_trend(self, alert_id: str) -> Optional[dict]:
    """Analyze revenue trend using AI and update alert.
    
    Requirements: 18.3
    
    Args:
        alert_id: Revenue alert ID
        
    Returns:
        AI analysis result
    """
    from sqlalchemy import select
    
    try:
        with get_sync_session() as session:
            alert_uuid = uuid.UUID(alert_id)
            
            # Get alert
            result = session.execute(
                select(RevenueAlert).where(RevenueAlert.id == alert_uuid)
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                return None
            
            # Generate AI analysis based on the trend
            change = alert.change_percentage or 0
            direction = "increase" if change > 0 else "decrease"
            
            # Simple rule-based analysis (in production, use OpenAI)
            analysis_parts = []
            recommendations = []
            
            if abs(change) >= 50:
                analysis_parts.append(
                    f"A significant {abs(change):.1f}% {direction} in revenue was detected."
                )
                if change < 0:
                    analysis_parts.append(
                        "This dramatic drop may indicate a major issue that requires immediate attention."
                    )
                    recommendations.append("Review recent content performance")
                    recommendations.append("Check for any YouTube policy changes")
                    recommendations.append("Analyze traffic sources for anomalies")
                else:
                    analysis_parts.append(
                        "This significant growth suggests your content strategy is working well."
                    )
                    recommendations.append("Identify which content drove this growth")
                    recommendations.append("Consider doubling down on successful formats")
            elif abs(change) >= 30:
                analysis_parts.append(
                    f"A notable {abs(change):.1f}% {direction} in revenue was observed."
                )
                if change < 0:
                    recommendations.append("Review recent video performance metrics")
                    recommendations.append("Check for seasonal patterns")
                else:
                    recommendations.append("Analyze what's driving the growth")
            else:
                analysis_parts.append(
                    f"A moderate {abs(change):.1f}% {direction} in revenue was detected."
                )
                recommendations.append("Continue monitoring trends")
            
            # Update alert with AI analysis
            alert.ai_analysis = " ".join(analysis_parts)
            alert.ai_recommendations = {"recommendations": recommendations}
            
            session.commit()
            
            return {
                "alert_id": alert_id,
                "analysis": alert.ai_analysis,
                "recommendations": recommendations,
            }
            
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def update_revenue_goal_progress(self, goal_id: str) -> Optional[dict]:
    """Update revenue goal progress based on actual revenue.
    
    Requirements: 18.4
    
    Args:
        goal_id: Revenue goal ID
        
    Returns:
        Updated goal progress
    """
    from sqlalchemy import select, func, and_
    from datetime import datetime
    
    try:
        with get_sync_session() as session:
            goal_uuid = uuid.UUID(goal_id)
            
            # Get goal
            result = session.execute(
                select(RevenueGoal).where(RevenueGoal.id == goal_uuid)
            )
            goal = result.scalar_one_or_none()
            
            if not goal or goal.status != GoalStatus.ACTIVE.value:
                return None
            
            # Get revenue for the goal period
            query = select(func.sum(RevenueRecord.total_revenue)).where(
                and_(
                    RevenueRecord.record_date >= goal.start_date,
                    RevenueRecord.record_date <= goal.end_date,
                )
            )
            if goal.account_id:
                query = query.where(RevenueRecord.account_id == goal.account_id)
            
            result = session.execute(query)
            current_amount = result.scalar() or 0.0
            
            # Update progress
            goal.current_amount = current_amount
            if goal.target_amount > 0:
                goal.progress_percentage = (current_amount / goal.target_amount) * 100
            
            # Check if goal is achieved
            if goal.progress_percentage >= 100:
                goal.status = GoalStatus.ACHIEVED.value
                goal.achieved_at = datetime.utcnow()
            
            # Calculate forecast
            today = date.today()
            if goal.start_date <= today <= goal.end_date:
                days_elapsed = (today - goal.start_date).days + 1
                total_days = (goal.end_date - goal.start_date).days + 1
                days_remaining = total_days - days_elapsed
                
                if days_elapsed > 0:
                    daily_rate = current_amount / days_elapsed
                    goal.forecast_amount = current_amount + (daily_rate * days_remaining)
                    if goal.target_amount > 0:
                        goal.forecast_probability = min(
                            1.0, goal.forecast_amount / goal.target_amount
                        )
            
            session.commit()
            
            # Check if we need to send progress notification
            if goal.notify_at_percentage:
                for threshold in goal.notify_at_percentage:
                    if (
                        goal.progress_percentage >= threshold
                        and (goal.last_notification_percentage or 0) < threshold
                    ):
                        # Send notification
                        create_goal_progress_alert.delay(
                            str(goal.user_id),
                            str(goal.id),
                            threshold,
                        )
                        goal.last_notification_percentage = threshold
                        session.commit()
                        break
            
            return {
                "goal_id": goal_id,
                "current_amount": current_amount,
                "progress_percentage": goal.progress_percentage,
                "forecast_amount": goal.forecast_amount,
            }
            
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def create_goal_progress_alert(
    self,
    user_id: str,
    goal_id: str,
    threshold: int,
) -> Optional[dict]:
    """Create an alert for goal progress milestone.
    
    Requirements: 18.4
    
    Args:
        user_id: User ID
        goal_id: Revenue goal ID
        threshold: Progress threshold reached
        
    Returns:
        Alert data
    """
    from sqlalchemy import select
    
    try:
        with get_sync_session() as session:
            user_uuid = uuid.UUID(user_id)
            goal_uuid = uuid.UUID(goal_id)
            
            # Get goal
            result = session.execute(
                select(RevenueGoal).where(RevenueGoal.id == goal_uuid)
            )
            goal = result.scalar_one_or_none()
            
            if not goal:
                return None
            
            # Determine severity based on threshold
            if threshold >= 100:
                severity = AlertSeverity.INFO.value
                title = f"🎉 Goal Achieved: {goal.name}"
                message = (
                    f"Congratulations! You've achieved your revenue goal of "
                    f"${goal.target_amount:.2f}. Current amount: ${goal.current_amount:.2f}"
                )
            else:
                severity = AlertSeverity.INFO.value
                title = f"Goal Progress: {goal.name} at {threshold}%"
                message = (
                    f"You've reached {threshold}% of your revenue goal. "
                    f"Current: ${goal.current_amount:.2f} / Target: ${goal.target_amount:.2f}"
                )
            
            # Create alert
            alert = RevenueAlert(
                user_id=user_uuid,
                account_id=goal.account_id,
                alert_type=AlertType.GOAL_PROGRESS.value,
                severity=severity,
                title=title,
                message=message,
                metric_name="goal_progress",
                current_value=goal.current_amount,
                change_percentage=goal.progress_percentage,
            )
            
            session.add(alert)
            session.commit()
            
            return {
                "alert_id": str(alert.id),
                "goal_id": goal_id,
                "threshold": threshold,
            }
            
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task
def check_all_accounts_for_trends(threshold_percent: float = 20.0) -> dict:
    """Check all accounts for revenue trend changes.
    
    This task should be scheduled to run daily.
    
    Requirements: 18.3
    
    Args:
        threshold_percent: Minimum percentage change to trigger alert
        
    Returns:
        Summary of detected trends
    """
    from sqlalchemy import select, distinct
    
    with get_sync_session() as session:
        # Get all unique user-account pairs with revenue records
        result = session.execute(
            select(
                distinct(RevenueRecord.account_id),
            ).join(
                # In production, join with youtube_accounts to get user_id
            )
        )
        
        # For now, return empty - in production this would iterate accounts
        return {
            "checked_accounts": 0,
            "alerts_created": 0,
        }


@celery_app.task
def update_all_goal_progress() -> dict:
    """Update progress for all active revenue goals.
    
    This task should be scheduled to run daily.
    
    Requirements: 18.4
    
    Returns:
        Summary of updated goals
    """
    from sqlalchemy import select
    
    with get_sync_session() as session:
        # Get all active goals
        result = session.execute(
            select(RevenueGoal).where(RevenueGoal.status == GoalStatus.ACTIVE.value)
        )
        goals = result.scalars().all()
        
        updated_count = 0
        for goal in goals:
            update_revenue_goal_progress.delay(str(goal.id))
            updated_count += 1
        
        return {
            "goals_queued": updated_count,
        }
