"""Global Configuration Service for Admin Panel.

Requirements: 19-29 - Global Configuration Management
"""

import re
import uuid
from datetime import datetime
from typing import Optional, TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import SystemConfig, ConfigCategory
from app.modules.billing.models import Plan
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
    EmailTemplatePreviewResponse,
    FeatureFlag, FeatureFlagUpdate, FeatureFlagListResponse,
    BrandingConfig, BrandingConfigUpdate,
    ResourceUsage, ResourceLimitWarning, ResourceLimitCheckResult,
)

# Type variable for config models
T = TypeVar('T')


# Default configurations
DEFAULT_CONFIGS = {
    ConfigCategory.AUTH.value: AuthConfig().model_dump(),
    ConfigCategory.UPLOAD.value: UploadConfig().model_dump(),
    ConfigCategory.STREAMING.value: StreamingConfig().model_dump(),
    ConfigCategory.AI.value: AIConfig().model_dump(),
    ConfigCategory.MODERATION.value: ModerationConfig().model_dump(),
    ConfigCategory.NOTIFICATION.value: NotificationConfig().model_dump(),
    ConfigCategory.JOBS.value: JobQueueConfig().model_dump(),
    ConfigCategory.BRANDING.value: BrandingConfig().model_dump(),
}

# Default subscription plans
DEFAULT_PLANS = [
    {
        "plan_id": "free",
        "plan_name": "Free",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "max_youtube_accounts": 1,
        "max_videos_per_month": 5,
        "max_streams_per_month": 5,
        "max_storage_gb": 1.0,
        "max_bandwidth_gb": 10.0,
        "max_ai_generations_per_month": 10,
        "max_concurrent_streams": 1,
        "max_simulcast_platforms": 1,
        "enable_analytics": False,
        "enable_competitor_analysis": False,
        "enable_ai_features": False,
        "enable_api_access": False,
        "api_rate_limit_per_minute": 30,
        "support_level": "community",
        "is_active": True,
    },
    {
        "plan_id": "starter",
        "plan_name": "Starter",
        "price_monthly": 19.99,
        "price_yearly": 199.99,
        "max_youtube_accounts": 3,
        "max_videos_per_month": 50,
        "max_streams_per_month": 30,
        "max_storage_gb": 10.0,
        "max_bandwidth_gb": 100.0,
        "max_ai_generations_per_month": 100,
        "max_concurrent_streams": 2,
        "max_simulcast_platforms": 2,
        "enable_analytics": True,
        "enable_competitor_analysis": False,
        "enable_ai_features": True,
        "enable_api_access": False,
        "api_rate_limit_per_minute": 60,
        "support_level": "email",
        "is_active": True,
    },
    {
        "plan_id": "professional",
        "plan_name": "Professional",
        "price_monthly": 49.99,
        "price_yearly": 499.99,
        "max_youtube_accounts": 10,
        "max_videos_per_month": 200,
        "max_streams_per_month": 100,
        "max_storage_gb": 50.0,
        "max_bandwidth_gb": 500.0,
        "max_ai_generations_per_month": 500,
        "max_concurrent_streams": 5,
        "max_simulcast_platforms": 5,
        "enable_analytics": True,
        "enable_competitor_analysis": True,
        "enable_ai_features": True,
        "enable_api_access": True,
        "api_rate_limit_per_minute": 300,
        "support_level": "priority",
        "is_active": True,
    },
    {
        "plan_id": "enterprise",
        "plan_name": "Enterprise",
        "price_monthly": 199.99,
        "price_yearly": 1999.99,
        "max_youtube_accounts": 50,
        "max_videos_per_month": 1000,
        "max_streams_per_month": 500,
        "max_storage_gb": 500.0,
        "max_bandwidth_gb": 5000.0,
        "max_ai_generations_per_month": 2000,
        "max_concurrent_streams": 20,
        "max_simulcast_platforms": 10,
        "enable_analytics": True,
        "enable_competitor_analysis": True,
        "enable_ai_features": True,
        "enable_api_access": True,
        "api_rate_limit_per_minute": 1000,
        "support_level": "dedicated",
        "is_active": True,
    },
]

# Default email templates
DEFAULT_EMAIL_TEMPLATES = [
    {
        "template_id": "welcome",
        "template_name": "Welcome Email",
        "subject": "Welcome to {{platform_name}}!",
        "body_html": "<h1>Welcome, {{user_name}}!</h1><p>Thank you for joining {{platform_name}}.</p>",
        "body_text": "Welcome, {{user_name}}! Thank you for joining {{platform_name}}.",
        "variables": ["user_name", "platform_name"],
        "is_active": True,
        "category": "onboarding",
    },
    {
        "template_id": "password_reset",
        "template_name": "Password Reset",
        "subject": "Reset Your Password",
        "body_html": "<h1>Password Reset</h1><p>Click <a href='{{reset_link}}'>here</a> to reset your password.</p>",
        "body_text": "Click the following link to reset your password: {{reset_link}}",
        "variables": ["reset_link", "user_name"],
        "is_active": True,
        "category": "security",
    },
    {
        "template_id": "subscription_confirmation",
        "template_name": "Subscription Confirmation",
        "subject": "Your {{plan_name}} Subscription is Active",
        "body_html": "<h1>Subscription Confirmed</h1><p>Your {{plan_name}} subscription is now active.</p>",
        "body_text": "Your {{plan_name}} subscription is now active.",
        "variables": ["plan_name", "user_name", "start_date", "end_date"],
        "is_active": True,
        "category": "billing",
    },
    {
        "template_id": "resource_warning",
        "template_name": "Resource Limit Warning",
        "subject": "You're approaching your {{resource_type}} limit",
        "body_html": "<h1>Resource Warning</h1><p>You've used {{percentage}}% of your {{resource_type}} limit.</p>",
        "body_text": "You've used {{percentage}}% of your {{resource_type}} limit.",
        "variables": ["resource_type", "percentage", "current_usage", "limit"],
        "is_active": True,
        "category": "alerts",
    },
]

# Default feature flags
DEFAULT_FEATURE_FLAGS = [
    {
        "flag_name": "new_dashboard",
        "description": "New dashboard UI with improved analytics",
        "is_enabled": False,
        "enabled_for_plans": [],
        "enabled_for_users": [],
        "rollout_percentage": 0,
    },
    {
        "flag_name": "ai_thumbnail_generation",
        "description": "AI-powered thumbnail generation feature",
        "is_enabled": True,
        "enabled_for_plans": ["starter", "professional", "enterprise"],
        "enabled_for_users": [],
        "rollout_percentage": 100,
    },
    {
        "flag_name": "multi_platform_streaming",
        "description": "Stream to multiple platforms simultaneously",
        "is_enabled": True,
        "enabled_for_plans": ["professional", "enterprise"],
        "enabled_for_users": [],
        "rollout_percentage": 100,
    },
    {
        "flag_name": "advanced_analytics",
        "description": "Advanced analytics and competitor analysis",
        "is_enabled": True,
        "enabled_for_plans": ["professional", "enterprise"],
        "enabled_for_users": [],
        "rollout_percentage": 100,
    },
]


class GlobalConfigService:
    """Service for managing global platform configuration.
    
    Requirements: 19-29 - Global Configuration Management
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_config(self, key: str) -> Optional[SystemConfig]:
        """Get configuration by key.
        
        Args:
            key: Configuration key
            
        Returns:
            SystemConfig or None if not found
        """
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_config(
        self, 
        key: str, 
        category: str,
        default_value: dict
    ) -> SystemConfig:
        """Get configuration or create with default value.
        
        Args:
            key: Configuration key
            category: Configuration category
            default_value: Default configuration value
            
        Returns:
            SystemConfig instance
        """
        config = await self._get_config(key)
        if config is None:
            config = SystemConfig(
                key=key,
                value=default_value,
                category=category,
                description=f"Default {category} configuration"
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config

    async def _update_config(
        self,
        key: str,
        category: str,
        update_data: dict,
        admin_id: uuid.UUID,
        config_class: Type[T]
    ) -> ConfigUpdateResponse:
        """Update configuration with partial data.
        
        Args:
            key: Configuration key
            category: Configuration category
            update_data: Partial update data
            admin_id: Admin performing the update
            config_class: Pydantic model class for validation
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        
        # Get or create config
        default_value = DEFAULT_CONFIGS.get(category, {})
        config = await self._get_or_create_config(key, category, default_value)
        
        # Store previous value (deep copy to avoid reference issues)
        previous_value = copy.deepcopy(config.value)
        
        # Merge update with existing config
        new_value = copy.deepcopy(config.value)
        for field, value in update_data.items():
            if value is not None:
                new_value[field] = value
        
        # Validate merged config
        validated = config_class(**new_value)
        
        # Update config
        config.value = validated.model_dump()
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        # Mark the JSON column as modified to ensure SQLAlchemy persists the change
        flag_modified(config, "value")
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return ConfigUpdateResponse(
            key=key,
            category=category,
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"{category.capitalize()} configuration updated successfully"
        )

    # ==================== Auth Config (Requirements 19.1-19.5) ====================

    async def get_auth_config(self) -> AuthConfig:
        """Get authentication configuration.
        
        Requirements: 19.1-19.5 - Global Authentication Configuration
        
        Returns:
            AuthConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.AUTH.value,
            ConfigCategory.AUTH.value,
            DEFAULT_CONFIGS[ConfigCategory.AUTH.value]
        )
        return AuthConfig(**config.value)

    async def update_auth_config(
        self, 
        data: AuthConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update authentication configuration.
        
        Requirements: 19.1-19.5 - Global Authentication Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.AUTH.value,
            ConfigCategory.AUTH.value,
            update_data,
            admin_id,
            AuthConfig
        )

    # ==================== Upload Config (Requirements 20.1-20.5) ====================

    async def get_upload_config(self) -> UploadConfig:
        """Get upload configuration.
        
        Requirements: 20.1-20.5 - Global Upload & Video Configuration
        
        Returns:
            UploadConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.UPLOAD.value,
            ConfigCategory.UPLOAD.value,
            DEFAULT_CONFIGS[ConfigCategory.UPLOAD.value]
        )
        return UploadConfig(**config.value)

    async def update_upload_config(
        self, 
        data: UploadConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update upload configuration.
        
        Requirements: 20.1-20.5 - Global Upload & Video Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.UPLOAD.value,
            ConfigCategory.UPLOAD.value,
            update_data,
            admin_id,
            UploadConfig
        )

    # ==================== Streaming Config (Requirements 21.1-21.5) ====================

    async def get_streaming_config(self) -> StreamingConfig:
        """Get streaming configuration.
        
        Requirements: 21.1-21.5 - Global Streaming Configuration
        
        Returns:
            StreamingConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.STREAMING.value,
            ConfigCategory.STREAMING.value,
            DEFAULT_CONFIGS[ConfigCategory.STREAMING.value]
        )
        return StreamingConfig(**config.value)

    async def update_streaming_config(
        self, 
        data: StreamingConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update streaming configuration.
        
        Requirements: 21.1-21.5 - Global Streaming Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.STREAMING.value,
            ConfigCategory.STREAMING.value,
            update_data,
            admin_id,
            StreamingConfig
        )

    # ==================== AI Config (Requirements 22.1-22.5) ====================

    async def get_ai_config(self) -> AIConfig:
        """Get AI configuration.
        
        Requirements: 22.1-22.5 - Global AI Service Configuration
        
        Returns:
            AIConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.AI.value,
            ConfigCategory.AI.value,
            DEFAULT_CONFIGS[ConfigCategory.AI.value]
        )
        return AIConfig(**config.value)

    async def update_ai_config(
        self, 
        data: AIConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update AI configuration.
        
        Requirements: 22.1-22.5 - Global AI Service Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.AI.value,
            ConfigCategory.AI.value,
            update_data,
            admin_id,
            AIConfig
        )

    # ==================== Moderation Config (Requirements 23.1-23.5) ====================

    async def get_moderation_config(self) -> ModerationConfig:
        """Get moderation configuration.
        
        Requirements: 23.1-23.5 - Global Moderation Configuration
        
        Returns:
            ModerationConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.MODERATION.value,
            ConfigCategory.MODERATION.value,
            DEFAULT_CONFIGS[ConfigCategory.MODERATION.value]
        )
        return ModerationConfig(**config.value)

    async def update_moderation_config(
        self, 
        data: ModerationConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update moderation configuration.
        
        Requirements: 23.1-23.5 - Global Moderation Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.MODERATION.value,
            ConfigCategory.MODERATION.value,
            update_data,
            admin_id,
            ModerationConfig
        )

    # ==================== Notification Config (Requirements 24.1-24.5) ====================

    async def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration.
        
        Requirements: 24.1-24.5 - Global Notification Configuration
        
        Returns:
            NotificationConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.NOTIFICATION.value,
            ConfigCategory.NOTIFICATION.value,
            DEFAULT_CONFIGS[ConfigCategory.NOTIFICATION.value]
        )
        return NotificationConfig(**config.value)

    async def update_notification_config(
        self, 
        data: NotificationConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update notification configuration.
        
        Requirements: 24.1-24.5 - Global Notification Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.NOTIFICATION.value,
            ConfigCategory.NOTIFICATION.value,
            update_data,
            admin_id,
            NotificationConfig
        )

    # ==================== Job Queue Config (Requirements 25.1-25.5) ====================

    async def get_job_queue_config(self) -> JobQueueConfig:
        """Get job queue configuration.
        
        Requirements: 25.1-25.5 - Global Job Queue Configuration
        
        Returns:
            JobQueueConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.JOBS.value,
            ConfigCategory.JOBS.value,
            DEFAULT_CONFIGS[ConfigCategory.JOBS.value]
        )
        return JobQueueConfig(**config.value)

    async def update_job_queue_config(
        self, 
        data: JobQueueConfigUpdate, 
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update job queue configuration.
        
        Requirements: 25.1-25.5 - Global Job Queue Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.JOBS.value,
            ConfigCategory.JOBS.value,
            update_data,
            admin_id,
            JobQueueConfig
        )

    # ==================== Plan Config (Requirements 26.1-26.5) ====================

    def _plan_to_config(self, plan: Plan) -> PlanConfig:
        """Convert Plan model to PlanConfig schema.
        
        Maps fields from the plans table to the admin config schema format.
        """
        return PlanConfig(
            id=str(plan.id),
            slug=plan.slug,
            name=plan.name,
            description=plan.description,
            price_monthly=plan.price_monthly / 100,  # Convert cents to dollars
            price_yearly=plan.price_yearly / 100,    # Convert cents to dollars
            currency=plan.currency,
            max_accounts=plan.max_accounts,
            max_videos_per_month=plan.max_videos_per_month,
            max_streams_per_month=plan.max_streams_per_month,
            max_storage_gb=plan.max_storage_gb,
            max_bandwidth_gb=plan.max_bandwidth_gb,
            ai_generations_per_month=plan.ai_generations_per_month,
            api_calls_per_month=plan.api_calls_per_month,
            encoding_minutes_per_month=plan.encoding_minutes_per_month,
            concurrent_streams=plan.concurrent_streams,
            features=plan.features or [],
            display_features=plan.display_features or [],
            stripe_price_id_monthly=plan.stripe_price_id_monthly,
            stripe_price_id_yearly=plan.stripe_price_id_yearly,
            stripe_product_id=plan.stripe_product_id,
            icon=plan.icon,
            color=plan.color,
            is_active=plan.is_active,
            is_popular=plan.is_popular,
            sort_order=plan.sort_order,
        )

    async def get_plan_configs(self) -> PlanConfigListResponse:
        """Get all subscription plan configurations from the plans table.
        
        Requirements: 26.1-26.5 - Subscription Plan Configuration
        
        Returns:
            PlanConfigListResponse with all plans
        """
        result = await self.db.execute(
            select(Plan).order_by(Plan.sort_order)
        )
        plans = result.scalars().all()
        
        plan_configs = [self._plan_to_config(plan) for plan in plans]
        return PlanConfigListResponse(plans=plan_configs, total=len(plan_configs))

    async def get_plan_config(self, plan_id: str) -> Optional[PlanConfig]:
        """Get a specific plan configuration from the plans table.
        
        Args:
            plan_id: Plan slug identifier
            
        Returns:
            PlanConfig or None if not found
        """
        result = await self.db.execute(
            select(Plan).where(Plan.slug == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if plan is None:
            return None
        
        return self._plan_to_config(plan)

    async def create_plan_config(
        self,
        data: PlanConfigCreate,
        admin_id: uuid.UUID
    ) -> PlanConfig:
        """Create a new plan configuration in the plans table.
        
        Requirements: 26.1-26.5 - Subscription Plan Configuration
        
        Args:
            data: Plan creation data
            admin_id: Admin performing the creation
            
        Returns:
            Created PlanConfig
        """
        # Auto-generate slug from name if not provided
        slug = data.slug
        if not slug:
            # Generate slug: lowercase, replace spaces with underscore, remove special chars
            slug = re.sub(r'[^a-z0-9_]', '', data.name.lower().replace(' ', '_'))
            if len(slug) < 2:
                slug = f"plan_{slug}"
        
        # Check if slug already exists
        result = await self.db.execute(
            select(Plan).where(Plan.slug == slug)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Plan with slug '{slug}' already exists")
        
        # Create new plan
        plan = Plan(
            slug=slug,
            name=data.name,
            description=data.description,
            price_monthly=int(data.price_monthly * 100),  # Convert dollars to cents
            price_yearly=int(data.price_yearly * 100),
            currency=data.currency,
            max_accounts=data.max_accounts,
            max_videos_per_month=data.max_videos_per_month,
            max_streams_per_month=data.max_streams_per_month,
            max_storage_gb=data.max_storage_gb,
            max_bandwidth_gb=data.max_bandwidth_gb,
            ai_generations_per_month=data.ai_generations_per_month,
            api_calls_per_month=data.api_calls_per_month,
            encoding_minutes_per_month=data.encoding_minutes_per_month,
            concurrent_streams=data.concurrent_streams,
            features=data.features,
            display_features=data.display_features,
            stripe_price_id_monthly=data.stripe_price_id_monthly,
            stripe_price_id_yearly=data.stripe_price_id_yearly,
            stripe_product_id=data.stripe_product_id,
            icon=data.icon,
            color=data.color,
            is_active=data.is_active,
            is_popular=data.is_popular,
            sort_order=data.sort_order,
        )
        
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        
        return self._plan_to_config(plan)

    async def update_plan_config(
        self,
        plan_slug: str,
        data: PlanConfigUpdate,
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update a specific plan configuration in the plans table.
        
        Requirements: 26.1-26.5 - Subscription Plan Configuration
        
        Args:
            plan_slug: Plan slug identifier
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        # Get the plan from the plans table
        result = await self.db.execute(
            select(Plan).where(Plan.slug == plan_slug)
        )
        plan = result.scalar_one_or_none()
        
        if plan is None:
            raise ValueError(f"Plan with slug '{plan_slug}' not found")
        
        # Store previous value for response
        previous_config = self._plan_to_config(plan)
        previous_value = previous_config.model_dump()
        
        # Get update data
        update_data = data.model_dump(exclude_unset=True)
        
        # Update fields directly - schema fields match model fields
        for field, value in update_data.items():
            if value is None:
                continue
            
            # Handle price conversion (dollars to cents)
            if field == "price_monthly":
                plan.price_monthly = int(value * 100)
            elif field == "price_yearly":
                plan.price_yearly = int(value * 100)
            elif hasattr(plan, field):
                setattr(plan, field, value)
        
        # Update timestamp
        plan.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(plan)
        
        # Get new value for response
        new_config = self._plan_to_config(plan)
        
        return ConfigUpdateResponse(
            key=ConfigCategory.PLANS.value,
            category=ConfigCategory.PLANS.value,
            previous_value=previous_value,
            new_value=new_config.model_dump(),
            updated_by=admin_id,
            updated_at=plan.updated_at,
            message=f"Plan '{plan_slug}' configuration updated successfully"
        )

    async def delete_plan_config(
        self,
        plan_slug: str,
        admin_id: uuid.UUID
    ) -> dict:
        """Delete a plan configuration from the plans table.
        
        Args:
            plan_slug: Plan slug identifier
            admin_id: Admin performing the deletion
            
        Returns:
            Deletion confirmation
        """
        # Get the plan from the plans table
        result = await self.db.execute(
            select(Plan).where(Plan.slug == plan_slug)
        )
        plan = result.scalar_one_or_none()
        
        if plan is None:
            raise ValueError(f"Plan with slug '{plan_slug}' not found")
        
        # Delete the plan
        await self.db.delete(plan)
        await self.db.commit()
        
        return {
            "message": f"Plan '{plan_slug}' deleted successfully",
            "deleted_by": str(admin_id),
            "deleted_at": datetime.utcnow().isoformat()
        }

    # ==================== Email Template Config (Requirements 27.1-27.5) ====================

    async def get_email_templates(self) -> EmailTemplateListResponse:
        """Get all email templates.
        
        Requirements: 27.1-27.5 - Email Template Management
        
        Returns:
            EmailTemplateListResponse with all templates
        """
        config = await self._get_or_create_config(
            ConfigCategory.EMAIL_TEMPLATES.value,
            ConfigCategory.EMAIL_TEMPLATES.value,
            {"templates": DEFAULT_EMAIL_TEMPLATES}
        )
        templates_data = config.value.get("templates", DEFAULT_EMAIL_TEMPLATES)
        templates = [EmailTemplate(**t) for t in templates_data]
        return EmailTemplateListResponse(templates=templates, total=len(templates))

    async def get_email_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get a specific email template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            EmailTemplate or None if not found
        """
        config = await self._get_or_create_config(
            ConfigCategory.EMAIL_TEMPLATES.value,
            ConfigCategory.EMAIL_TEMPLATES.value,
            {"templates": DEFAULT_EMAIL_TEMPLATES}
        )
        templates_data = config.value.get("templates", DEFAULT_EMAIL_TEMPLATES)
        for template in templates_data:
            if template.get("template_id") == template_id:
                return EmailTemplate(**template)
        return None

    async def update_email_template(
        self,
        template_id: str,
        data: EmailTemplateUpdate,
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update a specific email template.
        
        Requirements: 27.1-27.5 - Email Template Management
        
        Args:
            template_id: Template identifier
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        
        config = await self._get_or_create_config(
            ConfigCategory.EMAIL_TEMPLATES.value,
            ConfigCategory.EMAIL_TEMPLATES.value,
            {"templates": DEFAULT_EMAIL_TEMPLATES}
        )
        
        # Deep copy to avoid reference issues
        templates_data = copy.deepcopy(config.value.get("templates", DEFAULT_EMAIL_TEMPLATES))
        previous_value = {"templates": copy.deepcopy(templates_data)}
        
        # Find and update the template
        template_found = False
        update_data = data.model_dump(exclude_unset=True)
        
        for i, template in enumerate(templates_data):
            if template.get("template_id") == template_id:
                template_found = True
                for field, value in update_data.items():
                    if value is not None:
                        templates_data[i][field] = value
                break
        
        if not template_found:
            raise ValueError(f"Email template with id '{template_id}' not found")
        
        # Validate template syntax (check for unclosed braces)
        updated_template = templates_data[i]
        self._validate_template_syntax(updated_template.get("body_html", ""))
        self._validate_template_syntax(updated_template.get("body_text", ""))
        self._validate_template_syntax(updated_template.get("subject", ""))
        
        # Update config
        config.value = {"templates": templates_data}
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        # Mark the JSON column as modified
        flag_modified(config, "value")
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return ConfigUpdateResponse(
            key=ConfigCategory.EMAIL_TEMPLATES.value,
            category=ConfigCategory.EMAIL_TEMPLATES.value,
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"Email template '{template_id}' updated successfully"
        )

    def _validate_template_syntax(self, template_content: str) -> None:
        """Validate template syntax for unclosed braces.
        
        Requirements: 27.5 - Prevent saving templates with syntax errors
        
        Args:
            template_content: Template content to validate
            
        Raises:
            ValueError: If template has syntax errors
        """
        # Check for balanced braces
        open_braces = template_content.count("{{")
        close_braces = template_content.count("}}")
        
        if open_braces != close_braces:
            raise ValueError(
                f"Template syntax error: Unbalanced braces. "
                f"Found {open_braces} opening '{{{{' and {close_braces} closing '}}}}'"
            )

    async def preview_email_template(
        self,
        template_id: str,
        sample_data: dict
    ) -> EmailTemplatePreviewResponse:
        """Preview an email template with sample data.
        
        Requirements: 27.3 - Preview template with sample data
        
        Args:
            template_id: Template identifier
            sample_data: Sample data for template variables
            
        Returns:
            EmailTemplatePreviewResponse with rendered content
        """
        template = await self.get_email_template(template_id)
        if template is None:
            raise ValueError(f"Email template with id '{template_id}' not found")
        
        # Render template with sample data
        subject = self._render_template(template.subject, sample_data)
        body_html = self._render_template(template.body_html, sample_data)
        body_text = self._render_template(template.body_text, sample_data)
        
        return EmailTemplatePreviewResponse(
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )

    def _render_template(self, template: str, data: dict) -> str:
        """Render a template string with data.
        
        Args:
            template: Template string with {{variable}} placeholders
            data: Data dictionary for variable substitution
            
        Returns:
            Rendered template string
        """
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    # ==================== Feature Flag Config (Requirements 28.1-28.5) ====================

    async def get_feature_flags(self) -> FeatureFlagListResponse:
        """Get all feature flags.
        
        Requirements: 28.1-28.5 - Feature Flag Management
        
        Returns:
            FeatureFlagListResponse with all flags
        """
        config = await self._get_or_create_config(
            ConfigCategory.FEATURE_FLAGS.value,
            ConfigCategory.FEATURE_FLAGS.value,
            {"flags": DEFAULT_FEATURE_FLAGS}
        )
        flags_data = config.value.get("flags", DEFAULT_FEATURE_FLAGS)
        flags = [FeatureFlag(**f) for f in flags_data]
        return FeatureFlagListResponse(flags=flags, total=len(flags))

    async def get_feature_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a specific feature flag.
        
        Args:
            flag_name: Flag name
            
        Returns:
            FeatureFlag or None if not found
        """
        config = await self._get_or_create_config(
            ConfigCategory.FEATURE_FLAGS.value,
            ConfigCategory.FEATURE_FLAGS.value,
            {"flags": DEFAULT_FEATURE_FLAGS}
        )
        flags_data = config.value.get("flags", DEFAULT_FEATURE_FLAGS)
        for flag in flags_data:
            if flag.get("flag_name") == flag_name:
                return FeatureFlag(**flag)
        return None

    async def update_feature_flag(
        self,
        flag_name: str,
        data: FeatureFlagUpdate,
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update a specific feature flag.
        
        Requirements: 28.1-28.5 - Feature Flag Management
        
        Args:
            flag_name: Flag name
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        
        config = await self._get_or_create_config(
            ConfigCategory.FEATURE_FLAGS.value,
            ConfigCategory.FEATURE_FLAGS.value,
            {"flags": DEFAULT_FEATURE_FLAGS}
        )
        
        # Deep copy to avoid reference issues
        flags_data = copy.deepcopy(config.value.get("flags", DEFAULT_FEATURE_FLAGS))
        previous_value = {"flags": copy.deepcopy(flags_data)}
        
        # Find and update the flag
        flag_found = False
        update_data = data.model_dump(exclude_unset=True)
        
        for i, flag in enumerate(flags_data):
            if flag.get("flag_name") == flag_name:
                flag_found = True
                for field, value in update_data.items():
                    if value is not None:
                        flags_data[i][field] = value
                break
        
        if not flag_found:
            raise ValueError(f"Feature flag '{flag_name}' not found")
        
        # Update config
        config.value = {"flags": flags_data}
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        # Mark the JSON column as modified
        flag_modified(config, "value")
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return ConfigUpdateResponse(
            key=ConfigCategory.FEATURE_FLAGS.value,
            category=ConfigCategory.FEATURE_FLAGS.value,
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"Feature flag '{flag_name}' updated successfully"
        )

    # ==================== Branding Config (Requirements 29.1-29.5) ====================

    async def get_branding_config(self) -> BrandingConfig:
        """Get branding configuration.
        
        Requirements: 29.1-29.5 - Platform Branding Configuration
        
        Returns:
            BrandingConfig instance
        """
        config = await self._get_or_create_config(
            ConfigCategory.BRANDING.value,
            ConfigCategory.BRANDING.value,
            DEFAULT_CONFIGS[ConfigCategory.BRANDING.value]
        )
        return BrandingConfig(**config.value)

    async def update_branding_config(
        self,
        data: BrandingConfigUpdate,
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update branding configuration.
        
        Requirements: 29.1-29.5 - Platform Branding Configuration
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        update_data = data.model_dump(exclude_unset=True)
        return await self._update_config(
            ConfigCategory.BRANDING.value,
            ConfigCategory.BRANDING.value,
            update_data,
            admin_id,
            BrandingConfig
        )

    async def update_logo_url(
        self,
        logo_url: str,
        admin_id: uuid.UUID
    ) -> ConfigUpdateResponse:
        """Update logo URL in branding configuration.
        
        Requirements: 29.2 - Upload logo
        
        Args:
            logo_url: URL of the uploaded logo
            admin_id: Admin performing the update
            
        Returns:
            ConfigUpdateResponse with previous and new values
        """
        return await self.update_branding_config(
            BrandingConfigUpdate(logo_url=logo_url),
            admin_id
        )

    # ==================== Resource Limit Warnings (Requirements 16.2) ====================

    def check_resource_limits(
        self,
        user_id: uuid.UUID,
        resource_usages: list[dict]
    ) -> ResourceLimitCheckResult:
        """Check resource limits and generate warnings.
        
        Requirements: 16.2 - Send warning notification at 75% and 90% thresholds
        
        Property 14: Resource Limit Warnings
        - For any user resource usage check, warnings SHALL be sent at 75% and 90% of plan limits.
        
        Args:
            user_id: User identifier
            resource_usages: List of resource usage dicts with keys:
                - resource_type: Type of resource (storage, bandwidth, etc.)
                - current_usage: Current usage amount
                - limit: Plan limit for the resource
                
        Returns:
            ResourceLimitCheckResult with warnings and resource statuses
        """
        warnings = []
        resources = []
        
        for usage in resource_usages:
            resource_type = usage.get("resource_type", "unknown")
            current_usage = float(usage.get("current_usage", 0))
            limit = float(usage.get("limit", 1))
            
            # Avoid division by zero
            if limit <= 0:
                percentage = 0.0
            else:
                percentage = (current_usage / limit) * 100
            
            # Determine warning level
            warning_level = None
            if percentage >= 90:
                warning_level = "warning_90"
                warnings.append(ResourceLimitWarning(
                    user_id=user_id,
                    resource_type=resource_type,
                    current_usage=current_usage,
                    limit=limit,
                    percentage=percentage,
                    threshold=90,
                    message=f"Critical: You've used {percentage:.1f}% of your {resource_type} limit. "
                            f"Consider upgrading your plan to avoid service interruption."
                ))
            elif percentage >= 75:
                warning_level = "warning_75"
                warnings.append(ResourceLimitWarning(
                    user_id=user_id,
                    resource_type=resource_type,
                    current_usage=current_usage,
                    limit=limit,
                    percentage=percentage,
                    threshold=75,
                    message=f"Warning: You've used {percentage:.1f}% of your {resource_type} limit. "
                            f"Consider upgrading your plan."
                ))
            
            resources.append(ResourceUsage(
                user_id=user_id,
                resource_type=resource_type,
                current_usage=current_usage,
                limit=limit,
                percentage=percentage,
                warning_level=warning_level
            ))
        
        return ResourceLimitCheckResult(
            user_id=user_id,
            warnings=warnings,
            resources=resources
        )
