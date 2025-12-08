"""FastAPI router for competitor module.

Exposes REST API endpoints for competitor tracking and analysis.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.competitor.service import (
    CompetitorService,
    CompetitorServiceError,
    CompetitorNotFoundError,
    CompetitorAlreadyExistsError,
    InvalidDateRangeError,
)
from app.modules.competitor.youtube_api import ChannelNotFoundError
from app.modules.competitor.schemas import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorListResponse,
    CompetitorMetricResponse,
    CompetitorTrendData,
    CompetitorContentResponse,
    CompetitorContentListResponse,
    ComparisonRequest,
    ComparisonResponse,
    AnalysisRequest,
    AnalysisResponse,
    ExportRequest,
    ExportResponse,
)

router = APIRouter(prefix="/competitors", tags=["competitors"])


def get_service(session: AsyncSession = Depends(get_db)) -> CompetitorService:
    """Dependency to get competitor service."""
    return CompetitorService(session)


# Placeholder for auth dependency - should be replaced with actual auth
async def get_current_user_id() -> uuid.UUID:
    """Get current user ID from auth context.

    This is a placeholder - in production, this would extract
    the user ID from the JWT token.
    """
    # TODO: Implement actual auth
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# ============================================
# Competitor CRUD Endpoints
# ============================================

@router.post(
    "",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a competitor to track",
)
async def add_competitor(
    data: CompetitorCreate,
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Add a new competitor channel to track.

    Requirements: 19.1
    """
    try:
        competitor = await service.add_competitor(user_id, data)
        return CompetitorResponse.model_validate(competitor)
    except CompetitorAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"YouTube channel not found: {data.channel_id}",
        )
    except CompetitorServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "",
    response_model=CompetitorListResponse,
    summary="List all competitors",
)
async def list_competitors(
    active_only: bool = Query(False, description="Only return active competitors"),
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get all competitors for the current user.

    Requirements: 19.1
    """
    competitors = await service.get_user_competitors(user_id, active_only)
    return CompetitorListResponse(
        competitors=[CompetitorResponse.model_validate(c) for c in competitors],
        total=len(competitors),
    )


@router.get(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Get competitor details",
)
async def get_competitor(
    competitor_id: uuid.UUID,
    service: CompetitorService = Depends(get_service),
):
    """Get details for a specific competitor.

    Requirements: 19.1
    """
    try:
        competitor = await service.get_competitor(competitor_id)
        return CompetitorResponse.model_validate(competitor)
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )


@router.patch(
    "/{competitor_id}",
    response_model=CompetitorResponse,
    summary="Update competitor settings",
)
async def update_competitor(
    competitor_id: uuid.UUID,
    data: CompetitorUpdate,
    service: CompetitorService = Depends(get_service),
):
    """Update competitor tracking settings.

    Requirements: 19.1
    """
    try:
        competitor = await service.update_competitor(competitor_id, data)
        return CompetitorResponse.model_validate(competitor)
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )


@router.delete(
    "/{competitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove competitor",
)
async def remove_competitor(
    competitor_id: uuid.UUID,
    service: CompetitorService = Depends(get_service),
):
    """Stop tracking a competitor.

    Requirements: 19.1
    """
    try:
        await service.remove_competitor(competitor_id)
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )


# ============================================
# Metrics and Tracking Endpoints
# ============================================

@router.post(
    "/{competitor_id}/sync",
    response_model=CompetitorResponse,
    summary="Sync competitor metrics",
)
async def sync_competitor(
    competitor_id: uuid.UUID,
    service: CompetitorService = Depends(get_service),
):
    """Manually sync metrics for a competitor from YouTube.

    Requirements: 19.1
    """
    try:
        competitor = await service.sync_competitor_metrics(competitor_id)
        return CompetitorResponse.model_validate(competitor)
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )
    except CompetitorServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{competitor_id}/metrics",
    response_model=list[CompetitorMetricResponse],
    summary="Get competitor metrics history",
)
async def get_competitor_metrics(
    competitor_id: uuid.UUID,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    service: CompetitorService = Depends(get_service),
):
    """Get historical metrics for a competitor.

    Requirements: 19.1, 19.2
    """
    try:
        metrics = await service.get_competitor_metrics(
            competitor_id, start_date, end_date
        )
        return [CompetitorMetricResponse.model_validate(m) for m in metrics]
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{competitor_id}/trends",
    response_model=CompetitorTrendData,
    summary="Get competitor trend data",
)
async def get_competitor_trends(
    competitor_id: uuid.UUID,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    service: CompetitorService = Depends(get_service),
):
    """Get trend data for charts.

    Requirements: 19.2
    """
    try:
        return await service.get_trend_data(competitor_id, start_date, end_date)
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Content Endpoints
# ============================================

@router.get(
    "/{competitor_id}/content",
    response_model=CompetitorContentListResponse,
    summary="Get competitor content",
)
async def get_competitor_content(
    competitor_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    service: CompetitorService = Depends(get_service),
):
    """Get recent content from a competitor.

    Requirements: 19.3
    """
    content = await service.get_competitor_content(competitor_id, limit)
    return CompetitorContentListResponse(
        content=[CompetitorContentResponse.model_validate(c) for c in content],
        total=len(content),
    )


@router.post(
    "/{competitor_id}/check-content",
    response_model=CompetitorContentListResponse,
    summary="Check for new content",
)
async def check_new_content(
    competitor_id: uuid.UUID,
    service: CompetitorService = Depends(get_service),
):
    """Manually check for new content from a competitor.

    Requirements: 19.3
    """
    try:
        new_content = await service.check_new_content(competitor_id)
        return CompetitorContentListResponse(
            content=[CompetitorContentResponse.model_validate(c) for c in new_content],
            total=len(new_content),
        )
    except CompetitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor not found: {competitor_id}",
        )
    except CompetitorServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================
# Comparison Endpoints
# ============================================

@router.post(
    "/compare",
    response_model=ComparisonResponse,
    summary="Compare competitors",
)
async def compare_competitors(
    data: ComparisonRequest,
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Compare multiple competitors with optional user accounts.

    Requirements: 19.2
    """
    try:
        return await service.compare_channels(
            user_id=user_id,
            competitor_ids=data.competitor_ids,
            account_ids=data.account_ids,
            start_date=data.start_date,
            end_date=data.end_date,
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Analysis Endpoints
# ============================================

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI analysis",
)
async def generate_analysis(
    data: AnalysisRequest,
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Generate AI-powered competitor analysis.

    Requirements: 19.4
    """
    try:
        analysis = await service.generate_analysis(
            user_id=user_id,
            competitor_ids=data.competitor_ids,
            analysis_type=data.analysis_type,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        return AnalysisResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            competitor_ids=analysis.competitor_ids,
            analysis_type=analysis.analysis_type,
            start_date=analysis.start_date,
            end_date=analysis.end_date,
            summary=analysis.summary,
            insights=[],  # Will be populated from JSON
            recommendations=[],  # Will be populated from JSON
            trend_data=analysis.trend_data,
            status=analysis.status,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except CompetitorServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/analyses",
    response_model=list[AnalysisResponse],
    summary="List analyses",
)
async def list_analyses(
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get all analyses for the current user.

    Requirements: 19.4
    """
    analyses = await service.get_user_analyses(user_id, limit)
    return [
        AnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            competitor_ids=a.competitor_ids,
            analysis_type=a.analysis_type,
            start_date=a.start_date,
            end_date=a.end_date,
            summary=a.summary,
            insights=[],
            recommendations=[],
            trend_data=a.trend_data,
            status=a.status,
            created_at=a.created_at,
            completed_at=a.completed_at,
        )
        for a in analyses
    ]


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get analysis details",
)
async def get_analysis(
    analysis_id: uuid.UUID,
    service: CompetitorService = Depends(get_service),
):
    """Get details for a specific analysis.

    Requirements: 19.4
    """
    try:
        analysis = await service.get_analysis(analysis_id)
        return AnalysisResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            competitor_ids=analysis.competitor_ids,
            analysis_type=analysis.analysis_type,
            start_date=analysis.start_date,
            end_date=analysis.end_date,
            summary=analysis.summary,
            insights=[],
            recommendations=[],
            trend_data=analysis.trend_data,
            status=analysis.status,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
        )
    except CompetitorServiceError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {analysis_id}",
        )


# ============================================
# Export Endpoints
# ============================================

@router.post(
    "/export",
    response_model=ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export analysis",
)
async def export_analysis(
    data: ExportRequest,
    service: CompetitorService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Export competitor analysis to file.

    Requirements: 19.5
    """
    try:
        analysis = await service.export_analysis(
            user_id=user_id,
            competitor_ids=data.competitor_ids,
            start_date=data.start_date,
            end_date=data.end_date,
            export_format=data.export_format,
            include_trend_data=data.include_trend_data,
            include_insights=data.include_insights,
        )
        return ExportResponse(
            analysis_id=analysis.id,
            export_format=data.export_format,
            file_path=analysis.export_file_path,
            status=analysis.status,
            created_at=analysis.created_at,
        )
    except InvalidDateRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except CompetitorServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
