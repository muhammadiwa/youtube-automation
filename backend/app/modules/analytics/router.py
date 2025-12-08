"""Analytics API router.

Implements REST endpoints for analytics and reporting.
Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 18.1, 18.2, 18.3, 18.4, 18.5
"""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.analytics.service import (
    AnalyticsService,
    InvalidDateRangeError,
    ReportNotFoundError,
)
from app.modules.analytics.schemas import (
    DateRangeRequest,
    DashboardMetrics,
    AccountMetrics,
    ChannelComparisonRequest,
    ChannelComparisonResponse,
    ReportGenerationRequest,
    AnalyticsReportResponse,
    AnalyticsSnapshotResponse,
    AIInsightsResponse,
    AIInsight,
)
from app.modules.analytics.revenue_router import router as revenue_router

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Include revenue sub-router
router.include_router(revenue_router)


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    start_date: date = Query(..., description="Start date for metrics"),
    end_date: date = Query(..., description="End date for metrics"),
    account_ids: Optional[str] = Query(
        None, description="Comma-separated account IDs"
    ),
    db: AsyncSession = Depends(get_db),
    # user_id would come from auth dependency in production
):
    """Get aggregated dashboard metrics with period comparison.

    Requirements: 17.1, 17.2
    """
    service = AnalyticsService(db)

    # Parse account IDs if provided
    parsed_account_ids = None
    if account_ids:
        try:
            parsed_account_ids = [
                uuid.UUID(aid.strip()) for aid in account_ids.split(",")
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )

    try:
        # In production, user_id would come from auth
        user_id = uuid.uuid4()  # Placeholder
        return await service.get_dashboard_metrics(
            user_id, start_date, end_date, parsed_account_ids
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/accounts/{account_id}", response_model=AccountMetrics)
async def get_account_metrics(
    account_id: uuid.UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics for a specific account.

    Requirements: 17.1, 17.2
    """
    service = AnalyticsService(db)
    return await service.get_account_metrics(account_id, start_date, end_date)


@router.post("/compare", response_model=ChannelComparisonResponse)
async def compare_channels(
    request: ChannelComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compare metrics across multiple channels.

    Requirements: 17.5
    """
    service = AnalyticsService(db)
    try:
        return await service.compare_channels(
            request.account_ids, request.start_date, request.end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/snapshots", response_model=list[AnalyticsSnapshotResponse])
async def get_snapshots(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_ids: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics snapshots within a date range.

    Requirements: 17.2
    """
    service = AnalyticsService(db)

    parsed_account_ids = None
    if account_ids:
        try:
            parsed_account_ids = [
                uuid.UUID(aid.strip()) for aid in account_ids.split(",")
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )

    return await service.get_snapshots_by_date_range(
        start_date, end_date, parsed_account_ids
    )


@router.post("/reports", response_model=AnalyticsReportResponse)
async def create_report(
    request: ReportGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new analytics report.

    Requirements: 17.3, 17.4
    """
    service = AnalyticsService(db)

    try:
        # In production, user_id would come from auth
        user_id = uuid.uuid4()  # Placeholder
        report = await service.create_report(
            user_id=user_id,
            title=request.title,
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            account_ids=request.account_ids,
            include_ai_insights=request.include_ai_insights,
        )
        return report
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a report by ID.

    Requirements: 17.3
    """
    service = AnalyticsService(db)
    try:
        return await service.get_report(report_id)
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )


@router.get("/reports", response_model=list[AnalyticsReportResponse])
async def get_user_reports(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get reports for the current user.

    Requirements: 17.3
    """
    service = AnalyticsService(db)
    # In production, user_id would come from auth
    user_id = uuid.uuid4()  # Placeholder
    return await service.get_user_reports(user_id, limit)


@router.get("/insights", response_model=AIInsightsResponse)
async def get_ai_insights(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_ids: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered insights for analytics data.

    Requirements: 17.4
    """
    service = AnalyticsService(db)

    parsed_account_ids = None
    if account_ids:
        try:
            parsed_account_ids = [
                uuid.UUID(aid.strip()) for aid in account_ids.split(",")
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )

    from datetime import datetime
    insights = await service.generate_ai_insights(
        start_date, end_date, parsed_account_ids
    )

    return AIInsightsResponse(
        insights=insights,
        generated_at=datetime.utcnow(),
        period_start=start_date,
        period_end=end_date,
    )
