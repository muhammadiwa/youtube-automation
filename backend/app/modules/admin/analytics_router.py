"""Admin Analytics Router.

API endpoints for admin platform analytics.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 17.1, 17.2, 17.3, 17.4, 17.5
"""

from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import require_permission
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.analytics_service import AdminAnalyticsService
from app.modules.admin.analytics_schemas import (
    PlatformMetricsResponse,
    GrowthMetricsResponse,
    RealtimeMetricsResponse,
    CohortAnalysisResponse,
    FunnelAnalysisResponse,
    GeographicDistributionResponse,
    UsageHeatmapResponse,
    FeatureAdoptionResponse,
    ExportRequest,
    ExportResponse,
)

router = APIRouter(prefix="/analytics", tags=["admin-analytics"])


# ==================== Platform Metrics (2.1) ====================

@router.get("/platform", response_model=PlatformMetricsResponse)
async def get_platform_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for period metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for period metrics"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get platform-wide metrics.
    
    Requirements: 2.1 - Display key metrics (total users, active users, MRR, ARR,
    total streams, total videos)
    
    Returns total users, active users, MRR, ARR, streams, videos, and comparisons
    with the previous period.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_platform_metrics(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Growth Metrics (2.2) ====================

@router.get("/growth", response_model=GrowthMetricsResponse)
async def get_growth_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    granularity: Literal["daily", "weekly", "monthly"] = Query("daily", description="Data granularity"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get growth metrics over time.
    
    Requirements: 2.2 - Show user growth chart, revenue growth chart, and churn rate over time
    
    Returns user growth, revenue growth, and churn rate data points for charting.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_growth_metrics(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


# ==================== Real-time Metrics (2.3) ====================

@router.get("/realtime", response_model=RealtimeMetricsResponse)
async def get_realtime_metrics(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get real-time platform metrics.
    
    Requirements: 2.3 - Display active streams count, concurrent users, API requests per minute
    
    Returns current active streams, concurrent users, API RPM, and other real-time stats.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_realtime_metrics()


# ==================== Cohort Analysis (17.1) ====================

@router.get("/cohort", response_model=CohortAnalysisResponse)
async def get_cohort_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for cohorts"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    granularity: Literal["weekly", "monthly"] = Query("monthly", description="Retention granularity"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get cohort retention analysis.
    
    Requirements: 17.1 - Display user retention by signup month with weekly/monthly breakdown
    
    Returns cohort data with retention percentages for each period.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_cohort_analysis(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


# ==================== Funnel Analysis (17.2) ====================

@router.get("/funnel", response_model=FunnelAnalysisResponse)
async def get_funnel_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get conversion funnel analysis.
    
    Requirements: 17.2 - Show conversion rates (signup → verify → connect account → first stream → paid)
    
    Returns funnel stages with conversion and drop-off rates.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_funnel_analysis(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Geographic Distribution (17.3) ====================

@router.get("/geographic", response_model=GeographicDistributionResponse)
async def get_geographic_distribution(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get user geographic distribution.
    
    Requirements: 17.3 - Display user map with country/region breakdown
    
    Returns user counts by country and region.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_geographic_distribution()


# ==================== Usage Heatmap (17.4) ====================

@router.get("/heatmap", response_model=UsageHeatmapResponse)
async def get_usage_heatmap(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get usage heatmap by hour and day.
    
    Requirements: 17.4 - Show peak usage times by hour and day of week
    
    Returns heatmap data with activity counts for each hour/day combination.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_usage_heatmap(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Feature Adoption (17.5) ====================

@router.get("/features", response_model=FeatureAdoptionResponse)
async def get_feature_adoption(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get feature adoption statistics.
    
    Requirements: 17.5 - Display usage statistics per feature with trend indicators
    
    Returns adoption rates and usage counts for each platform feature.
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAnalyticsService(session)
    return await service.get_feature_adoption(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== Dashboard Export (2.5) ====================

@router.post("/export", response_model=ExportResponse)
async def export_dashboard(
    request: Request,
    data: ExportRequest,
    admin: Admin = Depends(require_permission(AdminPermission.EXPORT_DATA)),
    session: AsyncSession = Depends(get_session),
):
    """Export dashboard data.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    
    Generates a CSV or PDF export with the selected metrics and returns
    a download URL.
    
    Requires EXPORT_DATA permission.
    """
    service = AdminAnalyticsService(session)
    return await service.export_dashboard(
        request=data,
        admin_id=admin.user_id,
    )


@router.get("/export/{export_id}", response_model=ExportResponse)
async def get_export_status(
    export_id: str,
    admin: Admin = Depends(require_permission(AdminPermission.EXPORT_DATA)),
    session: AsyncSession = Depends(get_session),
):
    """Get status of a dashboard export.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    
    Returns the current status and download URL (if completed) for an export job.
    
    Requires EXPORT_DATA permission.
    """
    from fastapi import HTTPException
    
    service = AdminAnalyticsService(session)
    result = await service.get_export_status(export_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return result


@router.get("/export/{export_id}/download")
async def download_export(
    export_id: str,
    admin: Admin = Depends(require_permission(AdminPermission.EXPORT_DATA)),
    session: AsyncSession = Depends(get_session),
):
    """Download an exported file.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    
    Returns the exported file for download.
    
    Requires EXPORT_DATA permission.
    """
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from app.modules.admin.models import DashboardExport, ExportStatus
    from sqlalchemy import select
    import os
    
    result = await session.execute(
        select(DashboardExport).where(DashboardExport.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    if export.status != ExportStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Export not completed")
    
    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Determine media type
    if export.format == "csv":
        media_type = "text/csv"
        filename = f"dashboard_export_{export_id}.csv"
    else:
        media_type = "text/plain"
        filename = f"dashboard_export_{export_id}.txt"
    
    return FileResponse(
        path=export.file_path,
        media_type=media_type,
        filename=filename,
    )
