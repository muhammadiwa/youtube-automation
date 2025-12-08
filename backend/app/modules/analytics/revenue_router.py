"""API routes for revenue tracking.

Implements REST endpoints for revenue dashboard, goals, alerts, and tax reports.
Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.analytics.revenue_service import RevenueService
from app.modules.analytics.revenue_schemas import (
    RevenueRecordCreate,
    RevenueRecordResponse,
    RevenueDashboardRequest,
    RevenueDashboardResponse,
    RevenueGoalCreate,
    RevenueGoalUpdate,
    RevenueGoalResponse,
    RevenueAlertResponse,
    TaxReportRequest,
    TaxReportResponse,
    MonthlyRevenueSummary,
)

router = APIRouter(prefix="/revenue", tags=["revenue"])


# ============== Revenue Records ==============

@router.post("/records", response_model=RevenueRecordResponse)
async def create_revenue_record(
    data: RevenueRecordCreate,
    session: AsyncSession = Depends(get_session),
) -> RevenueRecordResponse:
    """Create or update a revenue record for an account.
    
    Requirements: 18.1
    """
    service = RevenueService(session)
    return await service.create_revenue_record(data)


@router.get("/records", response_model=List[RevenueRecordResponse])
async def get_revenue_records(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_ids: Optional[List[uuid.UUID]] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[RevenueRecordResponse]:
    """Get revenue records for accounts within a date range.
    
    Requirements: 18.1
    """
    service = RevenueService(session)
    return await service.get_revenue_records(account_ids, start_date, end_date)


# ============== Revenue Dashboard ==============

@router.post("/dashboard", response_model=RevenueDashboardResponse)
async def get_revenue_dashboard(
    request: RevenueDashboardRequest,
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    session: AsyncSession = Depends(get_session),
) -> RevenueDashboardResponse:
    """Get revenue dashboard with breakdown by source.
    
    Requirements: 18.1, 18.2
    """
    service = RevenueService(session)
    # In production, fetch account titles from account service
    return await service.get_revenue_dashboard(user_id, request)


# ============== Revenue Goals ==============

@router.post("/goals", response_model=RevenueGoalResponse)
async def create_revenue_goal(
    data: RevenueGoalCreate,
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    session: AsyncSession = Depends(get_session),
) -> RevenueGoalResponse:
    """Create a new revenue goal.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    return await service.create_goal(user_id, data)


@router.get("/goals", response_model=List[RevenueGoalResponse])
async def get_revenue_goals(
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> List[RevenueGoalResponse]:
    """Get revenue goals for a user.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    return await service.get_goals(user_id, active_only)


@router.get("/goals/{goal_id}", response_model=RevenueGoalResponse)
async def get_revenue_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RevenueGoalResponse:
    """Get a specific revenue goal.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    goals = await service.goal_repo.get_by_id(goal_id)
    if not goals:
        raise HTTPException(status_code=404, detail="Goal not found")
    return RevenueGoalResponse.model_validate(goals)


@router.patch("/goals/{goal_id}", response_model=RevenueGoalResponse)
async def update_revenue_goal(
    goal_id: uuid.UUID,
    data: RevenueGoalUpdate,
    session: AsyncSession = Depends(get_session),
) -> RevenueGoalResponse:
    """Update a revenue goal.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    result = await service.update_goal(goal_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return result


@router.post("/goals/{goal_id}/refresh", response_model=RevenueGoalResponse)
async def refresh_goal_progress(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RevenueGoalResponse:
    """Refresh goal progress based on actual revenue.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    result = await service.update_goal_progress(goal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return result


@router.delete("/goals/{goal_id}")
async def delete_revenue_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a revenue goal.
    
    Requirements: 18.4
    """
    service = RevenueService(session)
    success = await service.delete_goal(goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"success": True}


# ============== Revenue Alerts ==============

@router.get("/alerts", response_model=List[RevenueAlertResponse])
async def get_revenue_alerts(
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> List[RevenueAlertResponse]:
    """Get revenue alerts for a user.
    
    Requirements: 18.3
    """
    service = RevenueService(session)
    return await service.get_alerts(user_id, unread_only, limit)


@router.post("/alerts/{alert_id}/read", response_model=RevenueAlertResponse)
async def mark_alert_as_read(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RevenueAlertResponse:
    """Mark an alert as read.
    
    Requirements: 18.3
    """
    service = RevenueService(session)
    result = await service.alert_repo.mark_as_read(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return RevenueAlertResponse.model_validate(result)


@router.post("/alerts/{alert_id}/dismiss", response_model=RevenueAlertResponse)
async def dismiss_alert(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RevenueAlertResponse:
    """Dismiss an alert.
    
    Requirements: 18.3
    """
    service = RevenueService(session)
    result = await service.alert_repo.dismiss(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return RevenueAlertResponse.model_validate(result)


@router.post("/alerts/detect-trends")
async def detect_trend_changes(
    user_id: uuid.UUID = Query(...),
    account_id: uuid.UUID = Query(...),
    threshold_percent: float = Query(20.0, ge=5.0, le=100.0),
    session: AsyncSession = Depends(get_session),
) -> Optional[RevenueAlertResponse]:
    """Detect significant revenue trend changes for an account.
    
    Requirements: 18.3
    """
    service = RevenueService(session)
    return await service.detect_trend_changes(user_id, account_id, threshold_percent)


# ============== Tax Reports ==============

@router.post("/tax-report", response_model=TaxReportResponse)
async def generate_tax_report(
    request: TaxReportRequest,
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    session: AsyncSession = Depends(get_session),
) -> TaxReportResponse:
    """Generate tax-relevant revenue summary.
    
    Requirements: 18.5
    """
    service = RevenueService(session)
    return await service.generate_tax_report(user_id, request)


@router.post("/tax-report/export")
async def export_tax_report(
    request: TaxReportRequest,
    user_id: uuid.UUID = Query(...),  # In production, get from auth
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export tax report as CSV.
    
    Requirements: 18.5
    """
    service = RevenueService(session)
    csv_content = await service.export_tax_report_csv(user_id, request)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=tax_report_{request.year}.csv"
        },
    )


@router.get("/monthly-breakdown", response_model=List[MonthlyRevenueSummary])
async def get_monthly_breakdown(
    year: int = Query(..., ge=2000, le=2100),
    account_ids: Optional[List[uuid.UUID]] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[MonthlyRevenueSummary]:
    """Get monthly revenue breakdown for a year.
    
    Requirements: 18.5
    """
    service = RevenueService(session)
    return await service.get_monthly_breakdown(account_ids, year)
