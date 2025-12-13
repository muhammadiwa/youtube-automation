"""Global Configuration Router for Admin Panel.

Requirements: 19-29 - Global Configuration Management
"""

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.config_service import GlobalConfigService
from app.modules.admin.config_schemas import (
    AuthConfig, AuthConfigUpdate,
    UploadConfig, UploadConfigUpdate,
    StreamingConfig, StreamingConfigUpdate,
    AIConfig, AIConfigUpdate,
    ModerationConfig, ModerationConfigUpdate,
    NotificationConfig, NotificationConfigUpdate,
    JobQueueConfig, JobQueueConfigUpdate,
    ConfigUpdateResponse,
    PlanConfig, PlanConfigCreate, PlanConfigUpdate, PlanConfigListResponse,
    EmailTemplate, EmailTemplateUpdate, EmailTemplateListResponse,
    EmailTemplatePreview, EmailTemplatePreviewResponse,
    FeatureFlag, FeatureFlagUpdate, FeatureFlagListResponse,
    BrandingConfig, BrandingConfigUpdate,
    ResourceLimitCheckResult,
)
from app.modules.admin.middleware import require_permission
from app.modules.admin.models import Admin, AdminPermission

router = APIRouter(prefix="/config", tags=["Admin Configuration"])


def get_config_service(db: AsyncSession = Depends(get_session)) -> GlobalConfigService:
    """Get GlobalConfigService instance."""
    return GlobalConfigService(db)


# ==================== Auth Config Endpoints (Requirements 19.1-19.5) ====================


@router.get(
    "/auth",
    response_model=AuthConfig,
    summary="Get authentication configuration",
    description="Get global authentication and security configuration settings."
)
async def get_auth_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> AuthConfig:
    """Get authentication configuration.
    
    Requirements: 19.1-19.5 - Global Authentication Configuration
    """
    return await service.get_auth_config()


@router.put(
    "/auth",
    response_model=ConfigUpdateResponse,
    summary="Update authentication configuration",
    description="Update global authentication and security configuration settings."
)
async def update_auth_config(
    data: AuthConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update authentication configuration.
    
    Requirements: 19.1-19.5 - Global Authentication Configuration
    """
    return await service.update_auth_config(data, admin.id)


# ==================== Upload Config Endpoints (Requirements 20.1-20.5) ====================


@router.get(
    "/upload",
    response_model=UploadConfig,
    summary="Get upload configuration",
    description="Get global video upload configuration settings."
)
async def get_upload_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> UploadConfig:
    """Get upload configuration.
    
    Requirements: 20.1-20.5 - Global Upload & Video Configuration
    """
    return await service.get_upload_config()


@router.put(
    "/upload",
    response_model=ConfigUpdateResponse,
    summary="Update upload configuration",
    description="Update global video upload configuration settings."
)
async def update_upload_config(
    data: UploadConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update upload configuration.
    
    Requirements: 20.1-20.5 - Global Upload & Video Configuration
    """
    return await service.update_upload_config(data, admin.id)


# ==================== Streaming Config Endpoints (Requirements 21.1-21.5) ====================


@router.get(
    "/streaming",
    response_model=StreamingConfig,
    summary="Get streaming configuration",
    description="Get global live streaming configuration settings."
)
async def get_streaming_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> StreamingConfig:
    """Get streaming configuration.
    
    Requirements: 21.1-21.5 - Global Streaming Configuration
    """
    return await service.get_streaming_config()


@router.put(
    "/streaming",
    response_model=ConfigUpdateResponse,
    summary="Update streaming configuration",
    description="Update global live streaming configuration settings."
)
async def update_streaming_config(
    data: StreamingConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update streaming configuration.
    
    Requirements: 21.1-21.5 - Global Streaming Configuration
    """
    return await service.update_streaming_config(data, admin.id)


# ==================== AI Config Endpoints (Requirements 22.1-22.5) ====================


@router.get(
    "/ai",
    response_model=AIConfig,
    summary="Get AI configuration",
    description="Get global AI service configuration settings."
)
async def get_ai_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> AIConfig:
    """Get AI configuration.
    
    Requirements: 22.1-22.5 - Global AI Service Configuration
    """
    return await service.get_ai_config()


@router.put(
    "/ai",
    response_model=ConfigUpdateResponse,
    summary="Update AI configuration",
    description="Update global AI service configuration settings."
)
async def update_ai_config(
    data: AIConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update AI configuration.
    
    Requirements: 22.1-22.5 - Global AI Service Configuration
    """
    return await service.update_ai_config(data, admin.id)


# ==================== Moderation Config Endpoints (Requirements 23.1-23.5) ====================


@router.get(
    "/moderation",
    response_model=ModerationConfig,
    summary="Get moderation configuration",
    description="Get global chat and comment moderation configuration settings."
)
async def get_moderation_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ModerationConfig:
    """Get moderation configuration.
    
    Requirements: 23.1-23.5 - Global Moderation Configuration
    """
    return await service.get_moderation_config()


@router.put(
    "/moderation",
    response_model=ConfigUpdateResponse,
    summary="Update moderation configuration",
    description="Update global chat and comment moderation configuration settings."
)
async def update_moderation_config(
    data: ModerationConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update moderation configuration.
    
    Requirements: 23.1-23.5 - Global Moderation Configuration
    """
    return await service.update_moderation_config(data, admin.id)


# ==================== Notification Config Endpoints (Requirements 24.1-24.5) ====================


@router.get(
    "/notification",
    response_model=NotificationConfig,
    summary="Get notification configuration",
    description="Get global notification system configuration settings."
)
async def get_notification_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> NotificationConfig:
    """Get notification configuration.
    
    Requirements: 24.1-24.5 - Global Notification Configuration
    """
    return await service.get_notification_config()


@router.put(
    "/notification",
    response_model=ConfigUpdateResponse,
    summary="Update notification configuration",
    description="Update global notification system configuration settings."
)
async def update_notification_config(
    data: NotificationConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update notification configuration.
    
    Requirements: 24.1-24.5 - Global Notification Configuration
    """
    return await service.update_notification_config(data, admin.id)


# ==================== Job Queue Config Endpoints (Requirements 25.1-25.5) ====================


@router.get(
    "/jobs",
    response_model=JobQueueConfig,
    summary="Get job queue configuration",
    description="Get global job queue and worker configuration settings."
)
async def get_job_queue_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> JobQueueConfig:
    """Get job queue configuration.
    
    Requirements: 25.1-25.5 - Global Job Queue Configuration
    """
    return await service.get_job_queue_config()


@router.put(
    "/jobs",
    response_model=ConfigUpdateResponse,
    summary="Update job queue configuration",
    description="Update global job queue and worker configuration settings."
)
async def update_job_queue_config(
    data: JobQueueConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update job queue configuration.
    
    Requirements: 25.1-25.5 - Global Job Queue Configuration
    """
    return await service.update_job_queue_config(data, admin.id)


# ==================== Plan Config Endpoints (Requirements 26.1-26.5) ====================


@router.get(
    "/plans",
    response_model=PlanConfigListResponse,
    summary="Get all plan configurations",
    description="Get all subscription plan configurations."
)
async def get_plan_configs(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> PlanConfigListResponse:
    """Get all plan configurations.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    return await service.get_plan_configs()


@router.get(
    "/plans/{plan_slug}",
    response_model=PlanConfig,
    summary="Get plan configuration",
    description="Get a specific subscription plan configuration."
)
async def get_plan_config(
    plan_slug: str,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> PlanConfig:
    """Get a specific plan configuration.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    plan = await service.get_plan_config(plan_slug)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with slug '{plan_slug}' not found"
        )
    return plan


@router.post(
    "/plans",
    response_model=PlanConfig,
    status_code=status.HTTP_201_CREATED,
    summary="Create plan configuration",
    description="Create a new subscription plan configuration."
)
async def create_plan_config(
    data: PlanConfigCreate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> PlanConfig:
    """Create a new plan configuration.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    try:
        return await service.create_plan_config(data, admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/plans/{plan_slug}",
    response_model=ConfigUpdateResponse,
    summary="Update plan configuration",
    description="Update a specific subscription plan configuration."
)
async def update_plan_config(
    plan_slug: str,
    data: PlanConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update a specific plan configuration.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    try:
        return await service.update_plan_config(plan_slug, data, admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/plans/{plan_slug}",
    summary="Delete plan configuration",
    description="Delete a subscription plan configuration."
)
async def delete_plan_config(
    plan_slug: str,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> dict:
    """Delete a plan configuration.
    
    Requirements: 26.1-26.5 - Subscription Plan Configuration
    """
    try:
        return await service.delete_plan_config(plan_slug, admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Email Template Endpoints (Requirements 27.1-27.5) ====================


@router.get(
    "/email-templates",
    response_model=EmailTemplateListResponse,
    summary="Get all email templates",
    description="Get all email templates."
)
async def get_email_templates(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> EmailTemplateListResponse:
    """Get all email templates.
    
    Requirements: 27.1-27.5 - Email Template Management
    """
    return await service.get_email_templates()


@router.get(
    "/email-templates/{template_id}",
    response_model=EmailTemplate,
    summary="Get email template",
    description="Get a specific email template."
)
async def get_email_template(
    template_id: str,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> EmailTemplate:
    """Get a specific email template.
    
    Requirements: 27.1-27.5 - Email Template Management
    """
    template = await service.get_email_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template with id '{template_id}' not found"
        )
    return template


@router.put(
    "/email-templates/{template_id}",
    response_model=ConfigUpdateResponse,
    summary="Update email template",
    description="Update a specific email template."
)
async def update_email_template(
    template_id: str,
    data: EmailTemplateUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update a specific email template.
    
    Requirements: 27.1-27.5 - Email Template Management
    """
    try:
        return await service.update_email_template(template_id, data, admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/email-templates/{template_id}/preview",
    response_model=EmailTemplatePreviewResponse,
    summary="Preview email template",
    description="Preview an email template with sample data."
)
async def preview_email_template(
    template_id: str,
    data: EmailTemplatePreview,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> EmailTemplatePreviewResponse:
    """Preview an email template with sample data.
    
    Requirements: 27.3 - Preview template with sample data
    """
    try:
        return await service.preview_email_template(template_id, data.sample_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Feature Flag Endpoints (Requirements 28.1-28.5) ====================


@router.get(
    "/feature-flags",
    response_model=FeatureFlagListResponse,
    summary="Get all feature flags",
    description="Get all feature flags."
)
async def get_feature_flags(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> FeatureFlagListResponse:
    """Get all feature flags.
    
    Requirements: 28.1-28.5 - Feature Flag Management
    """
    return await service.get_feature_flags()


@router.get(
    "/feature-flags/{flag_name}",
    response_model=FeatureFlag,
    summary="Get feature flag",
    description="Get a specific feature flag."
)
async def get_feature_flag(
    flag_name: str,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> FeatureFlag:
    """Get a specific feature flag.
    
    Requirements: 28.1-28.5 - Feature Flag Management
    """
    flag = await service.get_feature_flag(flag_name)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{flag_name}' not found"
        )
    return flag


@router.put(
    "/feature-flags/{flag_name}",
    response_model=ConfigUpdateResponse,
    summary="Update feature flag",
    description="Update a specific feature flag."
)
async def update_feature_flag(
    flag_name: str,
    data: FeatureFlagUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update a specific feature flag.
    
    Requirements: 28.1-28.5 - Feature Flag Management
    """
    try:
        return await service.update_feature_flag(flag_name, data, admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Branding Config Endpoints (Requirements 29.1-29.5) ====================


@router.get(
    "/branding",
    response_model=BrandingConfig,
    summary="Get branding configuration",
    description="Get platform branding configuration."
)
async def get_branding_config(
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> BrandingConfig:
    """Get branding configuration.
    
    Requirements: 29.1-29.5 - Platform Branding Configuration
    """
    return await service.get_branding_config()


@router.put(
    "/branding",
    response_model=ConfigUpdateResponse,
    summary="Update branding configuration",
    description="Update platform branding configuration."
)
async def update_branding_config(
    data: BrandingConfigUpdate,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Update branding configuration.
    
    Requirements: 29.1-29.5 - Platform Branding Configuration
    """
    return await service.update_branding_config(data, admin.id)


@router.post(
    "/branding/logo",
    response_model=ConfigUpdateResponse,
    summary="Upload logo",
    description="Upload platform logo."
)
async def upload_logo(
    file: UploadFile = File(...),
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.MANAGE_CONFIG))] = None,
    service: GlobalConfigService = Depends(get_config_service),
) -> ConfigUpdateResponse:
    """Upload platform logo.
    
    Requirements: 29.2 - Upload logo with dimension and format validation
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/svg+xml", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size of 5MB"
        )
    
    # Save file to storage
    storage_dir = "storage/branding"
    os.makedirs(storage_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.split(".")[-1] if file.filename else "png"
    filename = f"logo_{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(storage_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update branding config with logo URL
    logo_url = f"/storage/branding/{filename}"
    return await service.update_logo_url(logo_url, admin.id)


# ==================== Resource Limit Warning Endpoints (Requirements 16.2) ====================


from pydantic import BaseModel as PydanticBaseModel


class ResourceUsageInput(PydanticBaseModel):
    """Input for checking resource limits."""
    resource_type: str
    current_usage: float
    limit: float


class CheckResourceLimitsRequest(PydanticBaseModel):
    """Request body for checking resource limits."""
    user_id: uuid.UUID
    resources: list[ResourceUsageInput]


@router.post(
    "/resource-limits/check",
    response_model=ResourceLimitCheckResult,
    summary="Check resource limits",
    description="Check resource limits for a user and generate warnings at 75% and 90% thresholds."
)
async def check_resource_limits(
    request: CheckResourceLimitsRequest,
    admin: Annotated[Admin, Depends(require_permission(AdminPermission.VIEW_SYSTEM))],
    service: GlobalConfigService = Depends(get_config_service),
) -> ResourceLimitCheckResult:
    """Check resource limits and generate warnings.
    
    Requirements: 16.2 - Send warning notification at 75% and 90% thresholds
    
    Property 14: Resource Limit Warnings
    - For any user resource usage check, warnings SHALL be sent at 75% and 90% of plan limits.
    """
    resource_usages = [
        {
            "resource_type": r.resource_type,
            "current_usage": r.current_usage,
            "limit": r.limit
        }
        for r in request.resources
    ]
    return service.check_resource_limits(request.user_id, resource_usages)
