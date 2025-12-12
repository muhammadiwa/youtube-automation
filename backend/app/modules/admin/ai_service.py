"""AI Service Management for Admin Panel.

Requirements: 13.1-13.5 - AI Service Management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import SystemConfig, ConfigCategory
from app.modules.admin.ai_schemas import (
    AIDashboardMetrics,
    AIFeatureUsage,
    AILimitsConfig,
    AIPlanLimits,
    AILimitsUpdate,
    AIGlobalLimitsUpdate,
    AILogsResponse,
    AILogEntry,
    AILogsFilter,
    AIBudgetStatus,
    AIBudgetConfig,
    AIBudgetConfigUpdate,
    AIBudgetAlert,
    AIModelConfig,
    AIFeatureModelConfig,
    AIModelConfigUpdate,
    AIDefaultModelUpdate,
    AIConfigUpdateResponse,
)


# Default AI limits per plan
DEFAULT_AI_LIMITS = {
    "limits_by_plan": [
        {
            "plan_id": "free",
            "plan_name": "Free",
            "max_title_generations": 10,
            "max_description_generations": 10,
            "max_thumbnail_generations": 5,
            "max_chatbot_messages": 50,
            "max_total_tokens": 10000,
        },
        {
            "plan_id": "starter",
            "plan_name": "Starter",
            "max_title_generations": 100,
            "max_description_generations": 100,
            "max_thumbnail_generations": 50,
            "max_chatbot_messages": 500,
            "max_total_tokens": 100000,
        },
        {
            "plan_id": "professional",
            "plan_name": "Professional",
            "max_title_generations": 500,
            "max_description_generations": 500,
            "max_thumbnail_generations": 200,
            "max_chatbot_messages": 2000,
            "max_total_tokens": 500000,
        },
        {
            "plan_id": "enterprise",
            "plan_name": "Enterprise",
            "max_title_generations": 2000,
            "max_description_generations": 2000,
            "max_thumbnail_generations": 1000,
            "max_chatbot_messages": 10000,
            "max_total_tokens": 2000000,
        },
    ],
    "global_daily_limit": 10000,
    "throttle_at_percentage": 90,
}

# Default AI budget configuration
DEFAULT_AI_BUDGET = {
    "monthly_budget_usd": 1000.0,
    "alert_thresholds": [50, 75, 90, 100],
    "enable_throttling": True,
    "throttle_at_percentage": 90,
    "disable_at_percentage": 100,
}

# Default AI model configuration
DEFAULT_AI_MODELS = {
    "default_model": "gpt-4",
    "features": [
        {
            "feature": "titles",
            "model": "gpt-4",
            "max_tokens": 500,
            "temperature": 0.8,
            "top_p": 1.0,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.3,
            "timeout_seconds": 30,
        },
        {
            "feature": "descriptions",
            "model": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.2,
            "timeout_seconds": 45,
        },
        {
            "feature": "thumbnails",
            "model": "gpt-4",
            "max_tokens": 300,
            "temperature": 0.9,
            "top_p": 1.0,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
            "timeout_seconds": 30,
        },
        {
            "feature": "chatbot",
            "model": "gpt-3.5-turbo",
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "timeout_seconds": 10,
        },
        {
            "feature": "tags",
            "model": "gpt-3.5-turbo",
            "max_tokens": 300,
            "temperature": 0.5,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "timeout_seconds": 20,
        },
    ],
    "available_models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
}


class AdminAIService:
    """Service for managing AI services from admin panel.
    
    Requirements: 13.1-13.5 - AI Service Management
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_config(self, key: str) -> Optional[SystemConfig]:
        """Get configuration by key."""
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
        """Get configuration or create with default value."""
        config = await self._get_config(key)
        if config is None:
            config = SystemConfig(
                key=key,
                value=default_value,
                category=category,
                description=f"AI {category} configuration"
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config

    # ==================== AI Dashboard (Requirements 13.1) ====================

    async def get_ai_dashboard(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AIDashboardMetrics:
        """Get AI dashboard metrics.
        
        Requirements: 13.1 - Display total API calls, costs, and usage by feature
        
        Args:
            start_date: Start of reporting period (defaults to start of current month)
            end_date: End of reporting period (defaults to now)
            
        Returns:
            AIDashboardMetrics with usage statistics
        """
        # Default to current month
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get budget config
        budget_config = await self._get_or_create_config(
            "ai_budget",
            ConfigCategory.AI.value,
            DEFAULT_AI_BUDGET
        )
        monthly_budget = budget_config.value.get("monthly_budget_usd", 1000.0)
        throttle_at = budget_config.value.get("throttle_at_percentage", 90)

        # Try to get actual usage from AI logs table if it exists
        # For now, we'll generate sample metrics based on config
        # In production, this would query the ai_logs table
        
        usage_by_feature = await self._get_usage_by_feature(start_date, end_date)
        
        total_api_calls = sum(f.api_calls for f in usage_by_feature)
        total_tokens = sum(f.tokens_used for f in usage_by_feature)
        total_cost = sum(f.cost_usd for f in usage_by_feature)
        
        budget_used_pct = (total_cost / monthly_budget * 100) if monthly_budget > 0 else 0
        is_throttled = budget_used_pct >= throttle_at

        return AIDashboardMetrics(
            total_api_calls=total_api_calls,
            total_tokens_used=total_tokens,
            total_cost_usd=round(total_cost, 2),
            monthly_budget_usd=monthly_budget,
            budget_used_percentage=round(budget_used_pct, 2),
            usage_by_feature=usage_by_feature,
            period_start=start_date,
            period_end=end_date,
            is_throttled=is_throttled,
        )

    async def _get_usage_by_feature(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[AIFeatureUsage]:
        """Get AI usage statistics by feature.
        
        In production, this queries the ai_logs table.
        For now, returns aggregated data from available sources.
        """
        # Try to query AILog model if it exists
        try:
            from app.modules.ai.models import AILog
            
            result = await self.db.execute(
                select(
                    AILog.feature,
                    func.count(AILog.id).label("api_calls"),
                    func.sum(AILog.total_tokens).label("tokens_used"),
                    func.sum(AILog.cost_usd).label("cost_usd"),
                    func.avg(AILog.latency_ms).label("avg_latency"),
                    func.count(AILog.id).filter(AILog.status == "success").label("success_count"),
                ).where(
                    and_(
                        AILog.created_at >= start_date,
                        AILog.created_at <= end_date,
                    )
                ).group_by(AILog.feature)
            )
            
            rows = result.all()
            usage = []
            for row in rows:
                total = row.api_calls or 0
                success = row.success_count or 0
                success_rate = (success / total * 100) if total > 0 else 100.0
                
                usage.append(AIFeatureUsage(
                    feature=row.feature,
                    api_calls=total,
                    tokens_used=row.tokens_used or 0,
                    cost_usd=round(row.cost_usd or 0, 4),
                    success_rate=round(success_rate, 2),
                    avg_latency_ms=round(row.avg_latency or 0, 2),
                ))
            
            return usage if usage else self._get_default_usage()
            
        except Exception:
            # AILog model doesn't exist or query failed
            return self._get_default_usage()

    def _get_default_usage(self) -> list[AIFeatureUsage]:
        """Return default/empty usage statistics."""
        features = ["titles", "descriptions", "thumbnails", "chatbot", "tags"]
        return [
            AIFeatureUsage(
                feature=f,
                api_calls=0,
                tokens_used=0,
                cost_usd=0.0,
                success_rate=100.0,
                avg_latency_ms=0.0,
            )
            for f in features
        ]

    # ==================== AI Limits Config (Requirements 13.2) ====================

    async def get_ai_limits(self) -> AILimitsConfig:
        """Get AI generation limits configuration.
        
        Requirements: 13.2 - Configure generation limits per plan
        
        Returns:
            AILimitsConfig with limits for each plan
        """
        config = await self._get_or_create_config(
            "ai_limits",
            ConfigCategory.AI.value,
            DEFAULT_AI_LIMITS
        )
        
        limits_data = config.value.get("limits_by_plan", DEFAULT_AI_LIMITS["limits_by_plan"])
        limits = [AIPlanLimits(**l) for l in limits_data]
        
        return AILimitsConfig(
            limits_by_plan=limits,
            global_daily_limit=config.value.get("global_daily_limit", 10000),
            throttle_at_percentage=config.value.get("throttle_at_percentage", 90),
        )

    async def update_ai_limits(
        self,
        data: AILimitsUpdate,
        admin_id: uuid.UUID,
    ) -> AIConfigUpdateResponse:
        """Update AI limits for a specific plan.
        
        Requirements: 13.2 - Configure generation limits per plan
        
        Args:
            data: Limits update data
            admin_id: Admin performing the update
            
        Returns:
            AIConfigUpdateResponse with update details
        """
        config = await self._get_or_create_config(
            "ai_limits",
            ConfigCategory.AI.value,
            DEFAULT_AI_LIMITS
        )
        
        previous_value = config.value.copy()
        limits_data = config.value.get("limits_by_plan", [])
        
        # Find and update the plan
        plan_found = False
        update_data = data.model_dump(exclude_unset=True, exclude={"plan_id"})
        
        for i, plan in enumerate(limits_data):
            if plan.get("plan_id") == data.plan_id:
                plan_found = True
                for field, value in update_data.items():
                    if value is not None:
                        limits_data[i][field] = value
                break
        
        if not plan_found:
            raise ValueError(f"Plan with id '{data.plan_id}' not found")
        
        config.value["limits_by_plan"] = limits_data
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AIConfigUpdateResponse(
            category="ai_limits",
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"AI limits for plan '{data.plan_id}' updated successfully",
        )

    async def update_global_ai_limits(
        self,
        data: AIGlobalLimitsUpdate,
        admin_id: uuid.UUID,
    ) -> AIConfigUpdateResponse:
        """Update global AI limits.
        
        Args:
            data: Global limits update data
            admin_id: Admin performing the update
            
        Returns:
            AIConfigUpdateResponse with update details
        """
        config = await self._get_or_create_config(
            "ai_limits",
            ConfigCategory.AI.value,
            DEFAULT_AI_LIMITS
        )
        
        previous_value = config.value.copy()
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                config.value[field] = value
        
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AIConfigUpdateResponse(
            category="ai_limits",
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message="Global AI limits updated successfully",
        )

    # ==================== AI Logs (Requirements 13.3) ====================

    async def get_ai_logs(
        self,
        filters: Optional[AILogsFilter] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AILogsResponse:
        """Get AI API logs with filtering and pagination.
        
        Requirements: 13.3 - Show request/response with latency and tokens
        
        Args:
            filters: Optional filters for logs
            page: Page number
            page_size: Items per page
            
        Returns:
            AILogsResponse with paginated logs
        """
        try:
            from app.modules.ai.models import AILog
            
            query = select(AILog)
            
            # Apply filters
            if filters:
                conditions = []
                if filters.user_id:
                    conditions.append(AILog.user_id == filters.user_id)
                if filters.feature:
                    conditions.append(AILog.feature == filters.feature)
                if filters.status:
                    conditions.append(AILog.status == filters.status)
                if filters.start_date:
                    conditions.append(AILog.created_at >= filters.start_date)
                if filters.end_date:
                    conditions.append(AILog.created_at <= filters.end_date)
                if filters.min_latency_ms is not None:
                    conditions.append(AILog.latency_ms >= filters.min_latency_ms)
                if filters.max_latency_ms is not None:
                    conditions.append(AILog.latency_ms <= filters.max_latency_ms)
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination and ordering
            offset = (page - 1) * page_size
            query = query.order_by(desc(AILog.created_at)).offset(offset).limit(page_size)
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            log_entries = [
                AILogEntry(
                    id=log.id,
                    user_id=log.user_id,
                    feature=log.feature,
                    model=log.model,
                    request_summary=log.request_summary or "",
                    response_summary=log.response_summary,
                    tokens_input=log.tokens_input or 0,
                    tokens_output=log.tokens_output or 0,
                    total_tokens=log.total_tokens or 0,
                    latency_ms=log.latency_ms or 0,
                    cost_usd=log.cost_usd or 0,
                    status=log.status,
                    error_message=log.error_message,
                    created_at=log.created_at,
                )
                for log in logs
            ]
            
            total_pages = (total + page_size - 1) // page_size
            
            return AILogsResponse(
                logs=log_entries,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
            
        except Exception:
            # AILog model doesn't exist
            return AILogsResponse(
                logs=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )

    # ==================== AI Budget (Requirements 13.4) ====================

    async def get_ai_budget_status(self) -> AIBudgetStatus:
        """Get current AI budget status.
        
        Requirements: 13.4 - Alert when costs exceed budget
        
        Returns:
            AIBudgetStatus with current budget information
        """
        # Get budget config
        config = await self._get_or_create_config(
            "ai_budget",
            ConfigCategory.AI.value,
            DEFAULT_AI_BUDGET
        )
        
        monthly_budget = config.value.get("monthly_budget_usd", 1000.0)
        alert_thresholds = config.value.get("alert_thresholds", [50, 75, 90, 100])
        enable_throttling = config.value.get("enable_throttling", True)
        throttle_at = config.value.get("throttle_at_percentage", 90)
        
        # Get current month spend
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_spend = await self._get_current_month_spend(month_start, now)
        
        remaining = max(0, monthly_budget - current_spend)
        budget_used_pct = (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0
        
        # Calculate projected spend
        days_in_month = 30  # Simplified
        days_elapsed = (now - month_start).days + 1
        daily_avg = current_spend / days_elapsed if days_elapsed > 0 else 0
        projected_spend = daily_avg * days_in_month
        
        is_over_budget = current_spend >= monthly_budget
        is_throttled = enable_throttling and budget_used_pct >= throttle_at
        
        # Get alerts sent (from a separate tracking mechanism)
        alerts_sent = await self._get_alerts_sent_this_month()
        
        return AIBudgetStatus(
            monthly_budget_usd=monthly_budget,
            current_spend_usd=round(current_spend, 2),
            remaining_budget_usd=round(remaining, 2),
            budget_used_percentage=round(budget_used_pct, 2),
            projected_monthly_spend=round(projected_spend, 2),
            is_over_budget=is_over_budget,
            is_throttled=is_throttled,
            throttle_threshold_percentage=throttle_at,
            alert_thresholds=alert_thresholds,
            alerts_sent=alerts_sent,
        )

    async def _get_current_month_spend(
        self,
        month_start: datetime,
        month_end: datetime,
    ) -> float:
        """Get total AI spend for current month."""
        try:
            from app.modules.ai.models import AILog
            
            result = await self.db.execute(
                select(func.sum(AILog.cost_usd)).where(
                    and_(
                        AILog.created_at >= month_start,
                        AILog.created_at <= month_end,
                    )
                )
            )
            return result.scalar() or 0.0
        except Exception:
            return 0.0

    async def _get_alerts_sent_this_month(self) -> list[int]:
        """Get list of alert thresholds that have been triggered this month."""
        # In production, this would query an alerts table
        # For now, return empty list
        return []

    async def update_ai_budget_config(
        self,
        data: AIBudgetConfigUpdate,
        admin_id: uuid.UUID,
    ) -> AIConfigUpdateResponse:
        """Update AI budget configuration.
        
        Requirements: 13.4 - Configure budget and throttling
        
        Args:
            data: Budget config update data
            admin_id: Admin performing the update
            
        Returns:
            AIConfigUpdateResponse with update details
        """
        config = await self._get_or_create_config(
            "ai_budget",
            ConfigCategory.AI.value,
            DEFAULT_AI_BUDGET
        )
        
        previous_value = config.value.copy()
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                config.value[field] = value
        
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AIConfigUpdateResponse(
            category="ai_budget",
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message="AI budget configuration updated successfully",
        )

    async def check_and_send_budget_alerts(self) -> list[AIBudgetAlert]:
        """Check budget status and send alerts if thresholds are crossed.
        
        Requirements: 13.4 - Alert when costs exceed budget
        
        Returns:
            List of alerts that were triggered
        """
        status = await self.get_ai_budget_status()
        alerts = []
        
        for threshold in status.alert_thresholds:
            if status.budget_used_percentage >= threshold and threshold not in status.alerts_sent:
                alert_type = "over_budget" if threshold >= 100 else (
                    "critical" if threshold >= 90 else "warning"
                )
                
                alert = AIBudgetAlert(
                    alert_type=alert_type,
                    threshold_percentage=threshold,
                    current_spend_usd=status.current_spend_usd,
                    monthly_budget_usd=status.monthly_budget_usd,
                    message=f"AI budget has reached {threshold}% ({status.current_spend_usd:.2f} USD of {status.monthly_budget_usd:.2f} USD)",
                    created_at=datetime.utcnow(),
                    acknowledged=False,
                )
                alerts.append(alert)
                
                # In production, send notification to admins here
                # await self._send_budget_alert_notification(alert)
        
        return alerts

    # ==================== AI Model Config (Requirements 13.5) ====================

    async def get_ai_model_config(self) -> AIModelConfig:
        """Get AI model configuration.
        
        Requirements: 13.5 - Configure model version and parameters per feature
        
        Returns:
            AIModelConfig with model settings for each feature
        """
        config = await self._get_or_create_config(
            "ai_models",
            ConfigCategory.AI.value,
            DEFAULT_AI_MODELS
        )
        
        features_data = config.value.get("features", DEFAULT_AI_MODELS["features"])
        features = [AIFeatureModelConfig(**f) for f in features_data]
        
        return AIModelConfig(
            default_model=config.value.get("default_model", "gpt-4"),
            features=features,
            available_models=config.value.get("available_models", DEFAULT_AI_MODELS["available_models"]),
        )

    async def update_ai_model_config(
        self,
        data: AIModelConfigUpdate,
        admin_id: uuid.UUID,
    ) -> AIConfigUpdateResponse:
        """Update AI model configuration for a specific feature.
        
        Requirements: 13.5 - Configure model version and parameters per feature
        
        Args:
            data: Model config update data
            admin_id: Admin performing the update
            
        Returns:
            AIConfigUpdateResponse with update details
        """
        config = await self._get_or_create_config(
            "ai_models",
            ConfigCategory.AI.value,
            DEFAULT_AI_MODELS
        )
        
        previous_value = config.value.copy()
        features_data = config.value.get("features", [])
        
        # Find and update the feature
        feature_found = False
        update_data = data.model_dump(exclude_unset=True, exclude={"feature"})
        
        for i, feature in enumerate(features_data):
            if feature.get("feature") == data.feature:
                feature_found = True
                for field, value in update_data.items():
                    if value is not None:
                        features_data[i][field] = value
                break
        
        if not feature_found:
            # Add new feature config
            new_feature = {"feature": data.feature, **update_data}
            features_data.append(new_feature)
        
        config.value["features"] = features_data
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AIConfigUpdateResponse(
            category="ai_models",
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"AI model config for feature '{data.feature}' updated successfully",
        )

    async def update_default_ai_model(
        self,
        data: AIDefaultModelUpdate,
        admin_id: uuid.UUID,
    ) -> AIConfigUpdateResponse:
        """Update default AI model.
        
        Args:
            data: Default model update data
            admin_id: Admin performing the update
            
        Returns:
            AIConfigUpdateResponse with update details
        """
        config = await self._get_or_create_config(
            "ai_models",
            ConfigCategory.AI.value,
            DEFAULT_AI_MODELS
        )
        
        # Validate model is available
        available_models = config.value.get("available_models", [])
        if data.default_model not in available_models:
            raise ValueError(f"Model '{data.default_model}' is not available. Available models: {available_models}")
        
        previous_value = config.value.copy()
        config.value["default_model"] = data.default_model
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AIConfigUpdateResponse(
            category="ai_models",
            previous_value=previous_value,
            new_value=config.value,
            updated_by=admin_id,
            updated_at=config.updated_at,
            message=f"Default AI model updated to '{data.default_model}'",
        )
