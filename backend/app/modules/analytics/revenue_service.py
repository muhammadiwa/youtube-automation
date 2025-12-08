"""Service layer for revenue tracking functionality.

Implements business logic for revenue dashboard, goals, alerts, and tax reports.
Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional, List
import csv
import io

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.revenue_repository import (
    RevenueRecordRepository,
    RevenueGoalRepository,
    RevenueAlertRepository,
)
from app.modules.analytics.revenue_schemas import (
    RevenueRecordCreate,
    RevenueRecordResponse,
    RevenueDashboardRequest,
    RevenueDashboardResponse,
    AccountRevenue,
    RevenueBreakdown,
    RevenueGoalCreate,
    RevenueGoalUpdate,
    RevenueGoalResponse,
    RevenueAlertCreate,
    RevenueAlertResponse,
    TaxReportRequest,
    TaxReportResponse,
    TaxReportSummary,
    MonthlyRevenueSummary,
    AlertType,
    AlertSeverity,
    GoalStatus,
)
from app.modules.analytics.revenue_models import RevenueRecord, RevenueGoal


class RevenueService:
    """Service for revenue tracking operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.record_repo = RevenueRecordRepository(session)
        self.goal_repo = RevenueGoalRepository(session)
        self.alert_repo = RevenueAlertRepository(session)

    # ============== Revenue Records ==============

    async def create_revenue_record(
        self, data: RevenueRecordCreate
    ) -> RevenueRecordResponse:
        """Create or update a revenue record."""
        record = await self.record_repo.upsert(data)
        return RevenueRecordResponse.model_validate(record)

    async def get_revenue_records(
        self,
        account_ids: Optional[List[uuid.UUID]],
        start_date: date,
        end_date: date,
    ) -> List[RevenueRecordResponse]:
        """Get revenue records for accounts within a date range."""
        records = await self.record_repo.get_by_date_range(
            account_ids, start_date, end_date
        )
        return [RevenueRecordResponse.model_validate(r) for r in records]

    # ============== Revenue Dashboard ==============

    async def get_revenue_dashboard(
        self,
        user_id: uuid.UUID,
        request: RevenueDashboardRequest,
        account_titles: Optional[dict[uuid.UUID, str]] = None,
    ) -> RevenueDashboardResponse:
        """Get revenue dashboard with breakdown by source.
        
        Requirements: 18.1, 18.2
        """
        account_titles = account_titles or {}
        
        # Get current period totals
        current_totals = await self.record_repo.get_total_by_date_range(
            request.account_ids, request.start_date, request.end_date
        )

        # Calculate comparison period (same duration, immediately before)
        period_days = (request.end_date - request.start_date).days + 1
        comparison_end = request.start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days - 1)

        # Get comparison period totals
        comparison_totals = await self.record_repo.get_total_by_date_range(
            request.account_ids, comparison_start, comparison_end
        )

        # Calculate changes
        revenue_change = current_totals["total_revenue"] - comparison_totals["total_revenue"]
        revenue_change_percent = 0.0
        if comparison_totals["total_revenue"] > 0:
            revenue_change_percent = (revenue_change / comparison_totals["total_revenue"]) * 100

        # Create breakdown
        breakdown = RevenueBreakdown(
            ad_revenue=current_totals["ad_revenue"],
            membership_revenue=current_totals["membership_revenue"],
            super_chat_revenue=current_totals["super_chat_revenue"],
            super_sticker_revenue=current_totals["super_sticker_revenue"],
            merchandise_revenue=current_totals["merchandise_revenue"],
            youtube_premium_revenue=current_totals["youtube_premium_revenue"],
            total_revenue=current_totals["total_revenue"],
        )

        # Get per-account breakdown
        accounts = []
        if request.account_ids:
            for account_id in request.account_ids:
                account_current = await self.record_repo.get_total_by_account(
                    account_id, request.start_date, request.end_date
                )
                account_previous = await self.record_repo.get_total_by_account(
                    account_id, comparison_start, comparison_end
                )
                
                account_change = account_current["total_revenue"] - account_previous["total_revenue"]
                account_change_percent = 0.0
                if account_previous["total_revenue"] > 0:
                    account_change_percent = (account_change / account_previous["total_revenue"]) * 100

                accounts.append(AccountRevenue(
                    account_id=account_id,
                    channel_title=account_titles.get(account_id),
                    total_revenue=account_current["total_revenue"],
                    ad_revenue=account_current["ad_revenue"],
                    membership_revenue=account_current["membership_revenue"],
                    super_chat_revenue=account_current["super_chat_revenue"],
                    super_sticker_revenue=account_current["super_sticker_revenue"],
                    merchandise_revenue=account_current["merchandise_revenue"],
                    youtube_premium_revenue=account_current["youtube_premium_revenue"],
                    revenue_change=account_change,
                    revenue_change_percent=account_change_percent,
                ))

        return RevenueDashboardResponse(
            total_revenue=current_totals["total_revenue"],
            ad_revenue=current_totals["ad_revenue"],
            membership_revenue=current_totals["membership_revenue"],
            super_chat_revenue=current_totals["super_chat_revenue"],
            super_sticker_revenue=current_totals["super_sticker_revenue"],
            merchandise_revenue=current_totals["merchandise_revenue"],
            youtube_premium_revenue=current_totals["youtube_premium_revenue"],
            revenue_change=revenue_change,
            revenue_change_percent=revenue_change_percent,
            breakdown=breakdown,
            accounts=accounts,
            start_date=request.start_date,
            end_date=request.end_date,
            comparison_start_date=comparison_start,
            comparison_end_date=comparison_end,
        )

    def calculate_revenue_breakdown(self, records: List[RevenueRecord]) -> RevenueBreakdown:
        """Calculate revenue breakdown from records.
        
        Property 25: Revenue Source Breakdown - Sum of sources equals total.
        """
        ad_revenue = sum(r.ad_revenue for r in records)
        membership_revenue = sum(r.membership_revenue for r in records)
        super_chat_revenue = sum(r.super_chat_revenue for r in records)
        super_sticker_revenue = sum(r.super_sticker_revenue for r in records)
        merchandise_revenue = sum(r.merchandise_revenue for r in records)
        youtube_premium_revenue = sum(r.youtube_premium_revenue for r in records)
        
        total_revenue = (
            ad_revenue + membership_revenue + super_chat_revenue +
            super_sticker_revenue + merchandise_revenue + youtube_premium_revenue
        )

        return RevenueBreakdown(
            ad_revenue=ad_revenue,
            membership_revenue=membership_revenue,
            super_chat_revenue=super_chat_revenue,
            super_sticker_revenue=super_sticker_revenue,
            merchandise_revenue=merchandise_revenue,
            youtube_premium_revenue=youtube_premium_revenue,
            total_revenue=total_revenue,
        )

    # ============== Revenue Alerting ==============

    async def detect_trend_changes(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        threshold_percent: float = 20.0,
    ) -> Optional[RevenueAlertResponse]:
        """Detect significant revenue trend changes.
        
        Requirements: 18.3
        """
        today = date.today()
        
        # Compare last 7 days to previous 7 days
        current_end = today
        current_start = today - timedelta(days=6)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)

        current_totals = await self.record_repo.get_total_by_account(
            account_id, current_start, current_end
        )
        previous_totals = await self.record_repo.get_total_by_account(
            account_id, previous_start, previous_end
        )

        if previous_totals["total_revenue"] == 0:
            return None

        change_percent = (
            (current_totals["total_revenue"] - previous_totals["total_revenue"])
            / previous_totals["total_revenue"]
        ) * 100

        # Check if change exceeds threshold
        if abs(change_percent) >= threshold_percent:
            severity = AlertSeverity.INFO
            if abs(change_percent) >= 50:
                severity = AlertSeverity.CRITICAL
            elif abs(change_percent) >= 30:
                severity = AlertSeverity.WARNING

            direction = "increased" if change_percent > 0 else "decreased"
            title = f"Revenue {direction} by {abs(change_percent):.1f}%"
            message = (
                f"Your revenue has {direction} from ${previous_totals['total_revenue']:.2f} "
                f"to ${current_totals['total_revenue']:.2f} compared to the previous week."
            )

            alert_data = RevenueAlertCreate(
                user_id=user_id,
                account_id=account_id,
                alert_type=AlertType.TREND_CHANGE,
                severity=severity,
                title=title,
                message=message,
                metric_name="total_revenue",
                previous_value=previous_totals["total_revenue"],
                current_value=current_totals["total_revenue"],
                change_percentage=change_percent,
            )

            alert = await self.alert_repo.create(alert_data)
            return RevenueAlertResponse.model_validate(alert)

        return None

    async def get_alerts(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[RevenueAlertResponse]:
        """Get revenue alerts for a user."""
        from app.modules.analytics.revenue_schemas import AlertStatus
        
        status = AlertStatus.UNREAD if unread_only else None
        alerts = await self.alert_repo.get_by_user(user_id, status, limit)
        return [RevenueAlertResponse.model_validate(a) for a in alerts]

    # ============== Revenue Goals ==============

    async def create_goal(
        self, user_id: uuid.UUID, data: RevenueGoalCreate
    ) -> RevenueGoalResponse:
        """Create a new revenue goal.
        
        Requirements: 18.4
        """
        goal = await self.goal_repo.create(user_id, data)
        return RevenueGoalResponse.model_validate(goal)

    async def get_goals(
        self,
        user_id: uuid.UUID,
        active_only: bool = False,
    ) -> List[RevenueGoalResponse]:
        """Get revenue goals for a user."""
        status = GoalStatus.ACTIVE if active_only else None
        goals = await self.goal_repo.get_by_user(user_id, status)
        return [RevenueGoalResponse.model_validate(g) for g in goals]

    async def update_goal(
        self, goal_id: uuid.UUID, data: RevenueGoalUpdate
    ) -> Optional[RevenueGoalResponse]:
        """Update a revenue goal."""
        goal = await self.goal_repo.update(goal_id, data)
        if goal:
            return RevenueGoalResponse.model_validate(goal)
        return None

    async def update_goal_progress(
        self, goal_id: uuid.UUID
    ) -> Optional[RevenueGoalResponse]:
        """Update goal progress based on actual revenue.
        
        Requirements: 18.4
        """
        goal = await self.goal_repo.get_by_id(goal_id)
        if not goal:
            return None

        # Get revenue for the goal period
        account_ids = [goal.account_id] if goal.account_id else None
        totals = await self.record_repo.get_total_by_date_range(
            account_ids, goal.start_date, goal.end_date
        )

        # Update progress
        updated_goal = await self.goal_repo.update_progress(
            goal_id, totals["total_revenue"]
        )
        
        if updated_goal:
            # Calculate forecast
            await self._update_goal_forecast(updated_goal)
            return RevenueGoalResponse.model_validate(updated_goal)
        return None

    async def _update_goal_forecast(self, goal: RevenueGoal) -> None:
        """Update goal forecast based on current progress."""
        today = date.today()
        
        if today < goal.start_date:
            return
        
        if today > goal.end_date:
            # Goal period has ended
            if goal.status == GoalStatus.ACTIVE.value:
                if goal.current_amount >= goal.target_amount:
                    goal.status = GoalStatus.ACHIEVED.value
                    goal.achieved_at = datetime.utcnow()
                else:
                    goal.status = GoalStatus.MISSED.value
            return

        # Calculate days elapsed and remaining
        days_elapsed = (today - goal.start_date).days + 1
        total_days = (goal.end_date - goal.start_date).days + 1
        days_remaining = total_days - days_elapsed

        if days_elapsed > 0:
            # Calculate daily rate
            daily_rate = goal.current_amount / days_elapsed
            
            # Forecast total
            goal.forecast_amount = goal.current_amount + (daily_rate * days_remaining)
            
            # Calculate probability (simple linear model)
            if goal.target_amount > 0:
                goal.forecast_probability = min(
                    1.0, goal.forecast_amount / goal.target_amount
                )

        await self.session.commit()

    async def delete_goal(self, goal_id: uuid.UUID) -> bool:
        """Delete a revenue goal."""
        return await self.goal_repo.delete(goal_id)

    # ============== Tax Reports ==============

    async def generate_tax_report(
        self,
        user_id: uuid.UUID,
        request: TaxReportRequest,
        account_titles: Optional[dict[uuid.UUID, str]] = None,
    ) -> TaxReportResponse:
        """Generate tax-relevant revenue summary.
        
        Requirements: 18.5
        """
        account_titles = account_titles or {}
        
        # Get date range for the year
        start_date = date(request.year, 1, 1)
        end_date = date(request.year, 12, 31)

        # Get all records for the year
        records = await self.record_repo.get_by_date_range(
            request.account_ids, start_date, end_date
        )

        # Group by account
        account_records: dict[uuid.UUID, List[RevenueRecord]] = {}
        for record in records:
            if record.account_id not in account_records:
                account_records[record.account_id] = []
            account_records[record.account_id].append(record)

        # Calculate summaries per account
        accounts = []
        total_revenue = 0.0

        for account_id, acc_records in account_records.items():
            breakdown = self.calculate_revenue_breakdown(acc_records)
            accounts.append(TaxReportSummary(
                account_id=account_id,
                channel_title=account_titles.get(account_id),
                total_revenue=breakdown.total,
                ad_revenue=breakdown.ad,
                membership_revenue=breakdown.membership,
                super_chat_revenue=breakdown.super_chat,
                super_sticker_revenue=breakdown.super_sticker,
                merchandise_revenue=breakdown.merchandise,
                youtube_premium_revenue=breakdown.youtube_premium,
            ))
            total_revenue += breakdown.total

        return TaxReportResponse(
            year=request.year,
            total_revenue=total_revenue,
            accounts=accounts,
            generated_at=datetime.utcnow(),
        )

    async def export_tax_report_csv(
        self,
        user_id: uuid.UUID,
        request: TaxReportRequest,
        account_titles: Optional[dict[uuid.UUID, str]] = None,
    ) -> str:
        """Export tax report as CSV string.
        
        Requirements: 18.5
        """
        report = await self.generate_tax_report(user_id, request, account_titles)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Account ID",
            "Channel Title",
            "Ad Revenue",
            "Membership Revenue",
            "Super Chat Revenue",
            "Super Sticker Revenue",
            "Merchandise Revenue",
            "YouTube Premium Revenue",
            "Total Revenue",
            "Currency",
        ])
        
        # Data rows
        for account in report.accounts:
            writer.writerow([
                str(account.account_id),
                account.channel_title or "",
                f"{account.ad_revenue:.2f}",
                f"{account.membership_revenue:.2f}",
                f"{account.super_chat_revenue:.2f}",
                f"{account.super_sticker_revenue:.2f}",
                f"{account.merchandise_revenue:.2f}",
                f"{account.youtube_premium_revenue:.2f}",
                f"{account.total_revenue:.2f}",
                account.currency,
            ])
        
        # Total row
        writer.writerow([
            "TOTAL",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            f"{report.total_revenue:.2f}",
            "USD",
        ])
        
        return output.getvalue()

    async def get_monthly_breakdown(
        self,
        account_ids: Optional[List[uuid.UUID]],
        year: int,
    ) -> List[MonthlyRevenueSummary]:
        """Get monthly revenue breakdown for a year."""
        summaries = []
        
        for month in range(1, 13):
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            totals = await self.record_repo.get_total_by_date_range(
                account_ids, start_date, end_date
            )
            
            summaries.append(MonthlyRevenueSummary(
                month=month,
                year=year,
                total_revenue=totals["total_revenue"],
                ad_revenue=totals["ad_revenue"],
                membership_revenue=totals["membership_revenue"],
                super_chat_revenue=totals["super_chat_revenue"],
                super_sticker_revenue=totals["super_sticker_revenue"],
                merchandise_revenue=totals["merchandise_revenue"],
                youtube_premium_revenue=totals["youtube_premium_revenue"],
            ))
        
        return summaries
