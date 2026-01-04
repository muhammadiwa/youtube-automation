"""Analytics API router.

Implements REST endpoints for analytics and reporting.
Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

import uuid
from datetime import date, datetime, timedelta
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
    AnalyticsOverviewResponse,
    TimeSeriesDataPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_period_to_dates(period: str) -> tuple[date, date]:
    """Convert period string to start and end dates."""
    end_date = date.today()
    if period == "7d":
        start_date = end_date - timedelta(days=7)
    elif period == "30d":
        start_date = end_date - timedelta(days=30)
    elif period == "90d":
        start_date = end_date - timedelta(days=90)
    elif period == "1y":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
    return start_date, end_date


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview for dashboard.
    
    This endpoint provides a simplified overview with period-based filtering.
    Used by the client dashboard home page.
    If no analytics snapshots exist, falls back to account statistics.
    
    Requirements: 17.1, 17.2
    """
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    
    service = AnalyticsService(db)
    
    # Parse period to dates
    start_date, end_date = _parse_period_to_dates(period)
    
    # Parse account ID if provided
    account_ids = None
    if account_id:
        try:
            account_ids = [uuid.UUID(account_id)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )
    
    try:
        # Get dashboard metrics
        user_id = uuid.uuid4()  # Placeholder - in production from auth
        metrics = await service.get_dashboard_metrics(
            user_id, start_date, end_date, account_ids
        )
        
        # If no data from snapshots, try to get from account stats
        if metrics.total_views == 0 and metrics.total_subscribers == 0:
            # Query accounts directly
            query = select(YouTubeAccount).where(YouTubeAccount.status == "active")
            if account_ids:
                query = query.where(YouTubeAccount.id.in_(account_ids))
            
            result = await db.execute(query)
            accounts = result.scalars().all()
            
            if accounts:
                total_views = sum(a.view_count or 0 for a in accounts)
                total_subscribers = sum(a.subscriber_count or 0 for a in accounts)
                
                return AnalyticsOverviewResponse(
                    total_views=total_views,
                    total_subscribers=total_subscribers,
                    total_watch_time=0,
                    views_change=0,
                    subscribers_change=0,
                    watch_time_change=0,
                    period=period,
                )
        
        # Calculate watch time change (compare with previous period)
        period_days = (end_date - start_date).days + 1
        comparison_end = start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days - 1)
        
        comparison_metrics = await service.snapshot_repo.get_aggregated_metrics(
            comparison_start, comparison_end, account_ids
        )
        
        current_watch_time = metrics.total_watch_time_minutes
        previous_watch_time = comparison_metrics.get("total_watch_time_minutes", 0)
        
        if previous_watch_time > 0:
            watch_time_change = ((current_watch_time - previous_watch_time) / previous_watch_time) * 100
        else:
            watch_time_change = 100.0 if current_watch_time > 0 else 0.0
        
        return AnalyticsOverviewResponse(
            total_views=metrics.total_views,
            total_subscribers=metrics.total_subscribers,
            total_watch_time=metrics.total_watch_time_minutes,
            views_change=metrics.views_change_percent,
            subscribers_change=metrics.subscriber_change_percent,
            watch_time_change=watch_time_change,
            period=period,
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/views/timeseries", response_model=list[TimeSeriesDataPoint])
async def get_views_timeseries(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("day", description="Granularity: hour, day, week, month"),
    db: AsyncSession = Depends(get_db),
):
    """Get views time series data for charts.
    
    Returns daily/weekly/monthly view counts for the specified period.
    If no analytics snapshots exist, returns account view count as single point.
    
    Requirements: 17.1, 17.2
    """
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    
    service = AnalyticsService(db)
    
    # Parse dates
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
    else:
        end = date.today()
        start = end - timedelta(days=30)
    
    # Parse account ID
    account_ids = None
    if account_id:
        try:
            account_ids = [uuid.UUID(account_id)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )
    
    # Get snapshots for the date range
    snapshots = await service.get_snapshots_by_date_range(start, end, account_ids)
    
    # Aggregate by date
    views_by_date: dict[date, int] = {}
    for snapshot in snapshots:
        snapshot_date = snapshot.snapshot_date
        if snapshot_date not in views_by_date:
            views_by_date[snapshot_date] = 0
        views_by_date[snapshot_date] += snapshot.total_views
    
    # If no snapshots, get current view count from accounts
    if not views_by_date:
        query = select(YouTubeAccount).where(YouTubeAccount.status == "active")
        if account_ids:
            query = query.where(YouTubeAccount.id.in_(account_ids))
        
        result = await db.execute(query)
        accounts = result.scalars().all()
        
        if accounts:
            total_views = sum(a.view_count or 0 for a in accounts)
            # Put current total at today's date
            views_by_date[end] = total_views
    
    # Convert to time series format
    result = []
    current_date = start
    while current_date <= end:
        result.append(TimeSeriesDataPoint(
            date=current_date.isoformat(),
            value=views_by_date.get(current_date, 0),
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/subscribers/timeseries", response_model=list[TimeSeriesDataPoint])
async def get_subscribers_timeseries(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("day", description="Granularity: hour, day, week, month"),
    db: AsyncSession = Depends(get_db),
):
    """Get subscribers time series data for charts.
    
    Returns daily/weekly/monthly subscriber counts for the specified period.
    If no analytics snapshots exist, returns account subscriber count as single point.
    
    Requirements: 17.1, 17.2
    """
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    
    service = AnalyticsService(db)
    
    # Parse dates
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
    else:
        end = date.today()
        start = end - timedelta(days=30)
    
    # Parse account ID
    account_ids = None
    if account_id:
        try:
            account_ids = [uuid.UUID(account_id)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )
    
    # Get snapshots for the date range
    snapshots = await service.get_snapshots_by_date_range(start, end, account_ids)
    
    # Aggregate by date - use subscriber_count (total) not subscriber_change
    subscribers_by_date: dict[date, int] = {}
    for snapshot in snapshots:
        snapshot_date = snapshot.snapshot_date
        if snapshot_date not in subscribers_by_date:
            subscribers_by_date[snapshot_date] = 0
        subscribers_by_date[snapshot_date] += snapshot.subscriber_count
    
    # If no snapshots, get current subscriber count from accounts
    if not subscribers_by_date:
        query = select(YouTubeAccount).where(YouTubeAccount.status == "active")
        if account_ids:
            query = query.where(YouTubeAccount.id.in_(account_ids))
        
        result = await db.execute(query)
        accounts = result.scalars().all()
        
        if accounts:
            total_subscribers = sum(a.subscriber_count or 0 for a in accounts)
            # Put current total at today's date
            subscribers_by_date[end] = total_subscribers
    
    # Convert to time series format
    result = []
    current_date = start
    while current_date <= end:
        result.append(TimeSeriesDataPoint(
            date=current_date.isoformat(),
            value=subscribers_by_date.get(current_date, 0),
        ))
        current_date += timedelta(days=1)
    
    return result


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
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    
    service = AnalyticsService(db)
    try:
        result = await service.compare_channels(
            request.account_ids, request.start_date, request.end_date
        )
        
        # If all channels have zero data, try to get from account stats
        all_zero = all(
            ch.total_views == 0 and ch.subscriber_count == 0 
            for ch in result.channels
        )
        
        if all_zero:
            # Query accounts directly
            account_result = await db.execute(
                select(YouTubeAccount).where(YouTubeAccount.id.in_(request.account_ids))
            )
            accounts = {str(a.id): a for a in account_result.scalars().all()}
            
            # Update channels with account data
            for channel in result.channels:
                account = accounts.get(str(channel.account_id))
                if account:
                    channel.subscriber_count = account.subscriber_count or 0
                    channel.total_views = account.view_count or 0
                    channel.channel_title = account.channel_title
        
        return result
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


@router.get("/ai-insights", response_model=list[AIInsight])
async def get_ai_insights_simple(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered insights for dashboard (simplified endpoint).
    
    This is an alias endpoint that returns insights in a simpler format
    for the frontend dashboard.

    Requirements: 17.4
    """
    service = AnalyticsService(db)
    
    # Default to last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    parsed_account_ids = None
    if account_id:
        try:
            parsed_account_ids = [uuid.UUID(account_id)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account ID format",
            )

    insights = await service.generate_ai_insights(
        start_date, end_date, parsed_account_ids
    )

    return insights[:limit]


@router.post("/sync/{account_id}")
async def trigger_account_sync(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual analytics sync for a specific account.
    
    This queues a background task to fetch the latest analytics data
    from YouTube for the specified account.

    Requirements: 17.1
    """
    service = AnalyticsService(db)
    return await service.trigger_sync(account_id)


@router.post("/sync")
async def trigger_all_accounts_sync(
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual analytics sync for all accounts.
    
    This queues background tasks to fetch the latest analytics data
    from YouTube for all active accounts.

    Requirements: 17.1
    """
    service = AnalyticsService(db)
    return await service.trigger_sync_all()


@router.get("/channel/{account_id}/metrics")
async def get_channel_metrics(
    account_id: uuid.UUID,
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed channel metrics including traffic sources and demographics.
    
    Returns comprehensive analytics data for a specific channel.
    Falls back to account statistics if no analytics snapshots exist.

    Requirements: 17.1, 17.2
    """
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    
    service = AnalyticsService(db)
    
    # Parse period to dates
    start_date, end_date = _parse_period_to_dates(period)
    
    # Get basic metrics
    account_metrics = await service.get_account_metrics(account_id, start_date, end_date)
    
    # Get detailed metrics (traffic sources, demographics, top videos)
    detailed = await service.get_channel_detailed_metrics(account_id, start_date, end_date)
    
    # If no data from snapshots, try to get from account stats
    if account_metrics.total_views == 0 and account_metrics.subscriber_count == 0:
        result = await db.execute(
            select(YouTubeAccount).where(YouTubeAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if account:
            return {
                "account_id": str(account_id),
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "subscribers": account.subscriber_count or 0,
                "subscriber_change": 0,
                "views": account.view_count or 0,
                "views_change": 0,
                "watch_time": 0,
                "engagement_rate": 0,
                "traffic_sources": {},
                "demographics": {},
                "top_videos": [],
            }
    
    return {
        "account_id": str(account_id),
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "subscribers": account_metrics.subscriber_count,
        "subscriber_change": account_metrics.subscriber_change,
        "views": account_metrics.total_views,
        "views_change": account_metrics.views_change,
        "watch_time": account_metrics.watch_time_minutes,
        "engagement_rate": account_metrics.engagement_rate,
        "traffic_sources": detailed["traffic_sources"],
        "demographics": detailed["demographics"],
        "top_videos": detailed["top_videos"],
    }
