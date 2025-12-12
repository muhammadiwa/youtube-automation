"""Admin Promotional Service for discount codes and promotions.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5 - Promotional & Marketing Tools
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import DiscountCode, DiscountType, TrialCode, SystemConfig, ConfigCategory
from app.modules.admin.schemas import (
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
    DiscountCodeListResponse,
    DiscountCodeValidationResponse,
)
from app.modules.admin.promotional_schemas import (
    ReferralProgramConfig,
    ReferralProgramConfigUpdate,
    ReferralProgramConfigResponse,
    ReferralRewards,
    TrialExtensionRequest,
    TrialExtensionResponse,
    TrialCodeCreate,
    TrialCodeResponse,
    TrialCodeListResponse,
    PromotionAnalyticsResponse,
    ReferralAnalytics,
    DiscountCodeAnalytics,
    TopReferrer,
)
from app.modules.admin.audit import AdminAuditService, AdminAuditEvent

logger = logging.getLogger(__name__)


class DiscountCodeNotFoundError(Exception):
    """Raised when discount code is not found."""
    pass


class DiscountCodeExistsError(Exception):
    """Raised when discount code already exists."""
    pass


class DiscountCodeValidationError(Exception):
    """Raised when discount code validation fails."""
    pass


class AdminPromotionalService:
    """Service for admin promotional operations.
    
    Requirements: 14.1, 14.2 - Promotional & Marketing Tools
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Discount Code CRUD (14.1, 14.2) ====================

    async def create_discount_code(
        self,
        data: DiscountCodeCreate,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DiscountCodeResponse:
        """Create a new discount code.
        
        Requirements: 14.1 - Create discount code with percentage or fixed discount,
        validity period, and usage limit.
        
        Args:
            data: Discount code creation data
            admin_id: Admin creating the code
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created discount code
            
        Raises:
            DiscountCodeExistsError: If code already exists
            DiscountCodeValidationError: If validation fails
        """
        # Validate code doesn't already exist
        existing = await self._get_by_code(data.code)
        if existing:
            raise DiscountCodeExistsError(f"Discount code '{data.code}' already exists")
        
        # Validate dates
        if data.valid_until <= data.valid_from:
            raise DiscountCodeValidationError("valid_until must be after valid_from")
        
        # Validate percentage value
        if data.discount_type == "percentage" and data.discount_value > 100:
            raise DiscountCodeValidationError("Percentage discount cannot exceed 100%")
        
        # Create discount code
        discount_code = DiscountCode(
            code=data.code.upper(),  # Normalize to uppercase
            discount_type=data.discount_type,
            discount_value=data.discount_value,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            usage_limit=data.usage_limit,
            usage_count=0,
            applicable_plans=data.applicable_plans,
            is_active=True,
            created_by=admin_id,
        )
        
        self.session.add(discount_code)
        await self.session.commit()
        await self.session.refresh(discount_code)
        
        # Log audit
        await self._log_audit(
            admin_id=admin_id,
            action="discount_code_created",
            resource_id=discount_code.id,
            details={
                "code": discount_code.code,
                "discount_type": discount_code.discount_type,
                "discount_value": discount_code.discount_value,
                "valid_from": discount_code.valid_from.isoformat(),
                "valid_until": discount_code.valid_until.isoformat(),
                "usage_limit": discount_code.usage_limit,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return self._to_response(discount_code)

    async def get_discount_codes(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> DiscountCodeListResponse:
        """Get all discount codes with pagination.
        
        Requirements: 14.2 - Display all codes with usage count
        
        Args:
            page: Page number
            page_size: Items per page
            is_active: Filter by active status
            search: Search by code
            
        Returns:
            Paginated discount code list
        """
        query = select(DiscountCode)
        
        # Apply filters
        if is_active is not None:
            query = query.where(DiscountCode.is_active == is_active)
        
        if search:
            query = query.where(DiscountCode.code.ilike(f"%{search}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(DiscountCode.created_at.desc())
        query = query.limit(page_size).offset(offset)
        
        result = await self.session.execute(query)
        discount_codes = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size
        
        return DiscountCodeListResponse(
            items=[self._to_response(dc) for dc in discount_codes],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_discount_code(
        self,
        discount_code_id: uuid.UUID,
    ) -> DiscountCodeResponse:
        """Get discount code by ID.
        
        Args:
            discount_code_id: Discount code ID
            
        Returns:
            Discount code details
            
        Raises:
            DiscountCodeNotFoundError: If not found
        """
        discount_code = await self._get_by_id(discount_code_id)
        if not discount_code:
            raise DiscountCodeNotFoundError(f"Discount code {discount_code_id} not found")
        
        return self._to_response(discount_code)

    async def update_discount_code(
        self,
        discount_code_id: uuid.UUID,
        data: DiscountCodeUpdate,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DiscountCodeResponse:
        """Update a discount code.
        
        Args:
            discount_code_id: Discount code ID
            data: Update data
            admin_id: Admin performing the update
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated discount code
            
        Raises:
            DiscountCodeNotFoundError: If not found
            DiscountCodeValidationError: If validation fails
        """
        discount_code = await self._get_by_id(discount_code_id)
        if not discount_code:
            raise DiscountCodeNotFoundError(f"Discount code {discount_code_id} not found")
        
        # Track changes for audit
        changes = {}
        
        if data.discount_type is not None:
            changes["discount_type"] = {"old": discount_code.discount_type, "new": data.discount_type}
            discount_code.discount_type = data.discount_type
        
        if data.discount_value is not None:
            # Validate percentage value
            if (data.discount_type or discount_code.discount_type) == "percentage" and data.discount_value > 100:
                raise DiscountCodeValidationError("Percentage discount cannot exceed 100%")
            changes["discount_value"] = {"old": discount_code.discount_value, "new": data.discount_value}
            discount_code.discount_value = data.discount_value
        
        if data.valid_from is not None:
            changes["valid_from"] = {"old": discount_code.valid_from.isoformat(), "new": data.valid_from.isoformat()}
            discount_code.valid_from = data.valid_from
        
        if data.valid_until is not None:
            changes["valid_until"] = {"old": discount_code.valid_until.isoformat(), "new": data.valid_until.isoformat()}
            discount_code.valid_until = data.valid_until
        
        # Validate dates after update
        if discount_code.valid_until <= discount_code.valid_from:
            raise DiscountCodeValidationError("valid_until must be after valid_from")
        
        if data.usage_limit is not None:
            changes["usage_limit"] = {"old": discount_code.usage_limit, "new": data.usage_limit}
            discount_code.usage_limit = data.usage_limit
        
        if data.applicable_plans is not None:
            changes["applicable_plans"] = {"old": discount_code.applicable_plans, "new": data.applicable_plans}
            discount_code.applicable_plans = data.applicable_plans
        
        if data.is_active is not None:
            changes["is_active"] = {"old": discount_code.is_active, "new": data.is_active}
            discount_code.is_active = data.is_active
        
        await self.session.commit()
        await self.session.refresh(discount_code)
        
        # Log audit
        if changes:
            await self._log_audit(
                admin_id=admin_id,
                action="discount_code_updated",
                resource_id=discount_code.id,
                details={
                    "code": discount_code.code,
                    "changes": changes,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        return self._to_response(discount_code)

    async def delete_discount_code(
        self,
        discount_code_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Delete a discount code.
        
        Requirements: 14.2 - Delete discount codes
        
        Args:
            discount_code_id: Discount code ID
            admin_id: Admin performing the deletion
            ip_address: Request IP address
            user_agent: Request user agent
            
        Raises:
            DiscountCodeNotFoundError: If not found
        """
        discount_code = await self._get_by_id(discount_code_id)
        if not discount_code:
            raise DiscountCodeNotFoundError(f"Discount code {discount_code_id} not found")
        
        code = discount_code.code
        
        await self.session.delete(discount_code)
        await self.session.commit()
        
        # Log audit
        await self._log_audit(
            admin_id=admin_id,
            action="discount_code_deleted",
            resource_id=discount_code_id,
            details={
                "code": code,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def validate_discount_code(
        self,
        code: str,
        plan: Optional[str] = None,
    ) -> DiscountCodeValidationResponse:
        """Validate a discount code.
        
        Property 15: Discount Code Validation
        - Code is valid only if current_date is between valid_from and valid_until
        - Code is valid only if usage_count < usage_limit (when usage_limit is set)
        
        Args:
            code: Discount code to validate
            plan: Plan to check applicability
            
        Returns:
            Validation result
        """
        discount_code = await self._get_by_code(code.upper())
        
        if not discount_code:
            return DiscountCodeValidationResponse(
                is_valid=False,
                message="Discount code not found",
            )
        
        # Check if code is valid using the model method
        if not discount_code.is_valid():
            # Determine specific reason
            now = datetime.utcnow()
            if not discount_code.is_active:
                message = "Discount code is inactive"
            elif now < discount_code.valid_from:
                message = "Discount code is not yet valid"
            elif now > discount_code.valid_until:
                message = "Discount code has expired"
            elif discount_code.usage_limit and discount_code.usage_count >= discount_code.usage_limit:
                message = "Discount code usage limit reached"
            else:
                message = "Discount code is not valid"
            
            return DiscountCodeValidationResponse(
                is_valid=False,
                code=discount_code.code,
                message=message,
            )
        
        # Check plan applicability
        if plan and discount_code.applicable_plans and plan not in discount_code.applicable_plans:
            return DiscountCodeValidationResponse(
                is_valid=False,
                code=discount_code.code,
                message=f"Discount code is not applicable to plan '{plan}'",
            )
        
        return DiscountCodeValidationResponse(
            is_valid=True,
            code=discount_code.code,
            discount_type=discount_code.discount_type,
            discount_value=discount_code.discount_value,
            message="Discount code is valid",
        )

    async def increment_usage(
        self,
        code: str,
    ) -> None:
        """Increment usage count for a discount code.
        
        Args:
            code: Discount code
            
        Raises:
            DiscountCodeNotFoundError: If not found
        """
        discount_code = await self._get_by_code(code.upper())
        if not discount_code:
            raise DiscountCodeNotFoundError(f"Discount code '{code}' not found")
        
        discount_code.usage_count += 1
        await self.session.commit()

    # ==================== Helper Methods ====================

    async def _get_by_id(self, discount_code_id: uuid.UUID) -> Optional[DiscountCode]:
        """Get discount code by ID."""
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.id == discount_code_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_code(self, code: str) -> Optional[DiscountCode]:
        """Get discount code by code string."""
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    def _to_response(self, discount_code: DiscountCode) -> DiscountCodeResponse:
        """Convert discount code model to response schema."""
        return DiscountCodeResponse(
            id=discount_code.id,
            code=discount_code.code,
            discount_type=discount_code.discount_type,
            discount_value=discount_code.discount_value,
            valid_from=discount_code.valid_from,
            valid_until=discount_code.valid_until,
            usage_limit=discount_code.usage_limit,
            usage_count=discount_code.usage_count,
            applicable_plans=discount_code.applicable_plans,
            is_active=discount_code.is_active,
            is_valid=discount_code.is_valid(),
            created_by=discount_code.created_by,
            created_at=discount_code.created_at,
            updated_at=discount_code.updated_at,
        )

    async def _log_audit(
        self,
        admin_id: uuid.UUID,
        action: str,
        resource_id: uuid.UUID,
        details: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log an admin action for audit purposes."""
        from app.modules.admin.models import Admin
        
        # Get admin record
        result = await self.session.execute(
            select(Admin).where(Admin.user_id == admin_id)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            AdminAuditService.log(
                admin_id=admin.id,
                admin_user_id=admin_id,
                event=AdminAuditEvent.SUBSCRIPTION_MODIFIED,  # Using existing event type
                resource_type="discount_code",
                resource_id=str(resource_id),
                details={**details, "action": action},
                ip_address=ip_address,
                user_agent=user_agent,
            )

    # ==================== Referral Program Config (Requirements 14.3) ====================

    async def get_referral_config(self) -> ReferralProgramConfigResponse:
        """Get referral program configuration.
        
        Requirements: 14.3 - Configure referral program rewards
        
        Returns:
            ReferralProgramConfigResponse with current config
        """
        config = await self._get_or_create_referral_config()
        return ReferralProgramConfigResponse(
            config=ReferralProgramConfig(**config.value),
            updated_by=config.updated_by,
            message="Referral program configuration retrieved successfully"
        )

    async def update_referral_config(
        self,
        data: ReferralProgramConfigUpdate,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ReferralProgramConfigResponse:
        """Update referral program configuration.
        
        Requirements: 14.3 - Configure referral program rewards
        
        Args:
            data: Partial update data
            admin_id: Admin performing the update
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            ReferralProgramConfigResponse with updated config
        """
        config = await self._get_or_create_referral_config()
        
        # Store previous value for audit
        previous_value = config.value.copy()
        
        # Merge update with existing config
        new_value = {**config.value}
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                if field == "rewards" and isinstance(value, dict):
                    # Merge rewards
                    new_value["rewards"] = {**new_value.get("rewards", {}), **value}
                else:
                    new_value[field] = value
        
        # Validate merged config
        validated = ReferralProgramConfig(**new_value)
        
        # Update config
        config.value = validated.model_dump()
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(config)
        
        # Log audit
        await self._log_audit(
            admin_id=admin_id,
            action="referral_config_updated",
            resource_id=config.id,
            details={
                "previous_value": previous_value,
                "new_value": config.value,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ReferralProgramConfigResponse(
            config=ReferralProgramConfig(**config.value),
            updated_by=admin_id,
            message="Referral program configuration updated successfully"
        )

    async def _get_or_create_referral_config(self) -> SystemConfig:
        """Get or create referral program configuration."""
        key = "referral_program"
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        
        if config is None:
            default_config = ReferralProgramConfig()
            config = SystemConfig(
                key=key,
                value=default_config.model_dump(),
                category="promotions",
                description="Referral program configuration"
            )
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
        
        return config

    # ==================== Trial Extension (Requirements 14.4) ====================

    async def extend_user_trial(
        self,
        user_id: uuid.UUID,
        data: TrialExtensionRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TrialExtensionResponse:
        """Extend a user's trial period.
        
        Requirements: 14.4 - Extend trial for specific user
        
        Args:
            user_id: User ID to extend trial for
            data: Trial extension request data
            admin_id: Admin performing the extension
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            TrialExtensionResponse with extension details
        """
        from app.modules.billing.models import Subscription
        
        # Get user's subscription
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise TrialCodeNotFoundError(f"No subscription found for user {user_id}")
        
        # Store previous trial end
        previous_trial_end = subscription.trial_end
        
        # Calculate new trial end
        if subscription.trial_end and subscription.trial_end > datetime.utcnow():
            # Extend from current trial end
            new_trial_end = subscription.trial_end + timedelta(days=data.days)
        else:
            # Start new trial from now
            new_trial_end = datetime.utcnow() + timedelta(days=data.days)
            if not subscription.trial_start:
                subscription.trial_start = datetime.utcnow()
        
        subscription.trial_end = new_trial_end
        
        # If subscription was not trialing, set it to trialing
        if subscription.status not in ["trialing", "active"]:
            subscription.status = "trialing"
        
        await self.session.commit()
        await self.session.refresh(subscription)
        
        # Log audit
        await self._log_audit(
            admin_id=admin_id,
            action="trial_extended",
            resource_id=user_id,
            details={
                "user_id": str(user_id),
                "previous_trial_end": previous_trial_end.isoformat() if previous_trial_end else None,
                "new_trial_end": new_trial_end.isoformat(),
                "days_extended": data.days,
                "reason": data.reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return TrialExtensionResponse(
            user_id=user_id,
            previous_trial_end=previous_trial_end,
            new_trial_end=new_trial_end,
            days_extended=data.days,
            reason=data.reason,
            extended_at=datetime.utcnow(),
            extended_by=admin_id,
            message=f"Trial extended by {data.days} days successfully"
        )

    async def create_trial_code(
        self,
        data: TrialCodeCreate,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TrialCodeResponse:
        """Create a new trial code.
        
        Requirements: 14.4 - Create extended trial codes
        
        Args:
            data: Trial code creation data
            admin_id: Admin creating the code
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Created trial code
        """
        # Validate code doesn't already exist
        existing = await self._get_trial_code_by_code(data.code)
        if existing:
            raise TrialCodeExistsError(f"Trial code '{data.code}' already exists")
        
        # Validate dates
        if data.valid_until <= data.valid_from:
            raise TrialCodeValidationError("valid_until must be after valid_from")
        
        # Create trial code
        trial_code = TrialCode(
            code=data.code.upper(),
            trial_days=data.trial_days,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            usage_limit=data.usage_limit,
            usage_count=0,
            applicable_plans=data.applicable_plans,
            description=data.description,
            is_active=True,
            created_by=admin_id,
        )
        
        self.session.add(trial_code)
        await self.session.commit()
        await self.session.refresh(trial_code)
        
        # Log audit
        await self._log_audit(
            admin_id=admin_id,
            action="trial_code_created",
            resource_id=trial_code.id,
            details={
                "code": trial_code.code,
                "trial_days": trial_code.trial_days,
                "valid_from": trial_code.valid_from.isoformat(),
                "valid_until": trial_code.valid_until.isoformat(),
                "usage_limit": trial_code.usage_limit,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return self._trial_code_to_response(trial_code)

    async def get_trial_codes(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> TrialCodeListResponse:
        """Get all trial codes with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            is_active: Filter by active status
            search: Search by code
            
        Returns:
            Paginated trial code list
        """
        query = select(TrialCode)
        
        # Apply filters
        if is_active is not None:
            query = query.where(TrialCode.is_active == is_active)
        
        if search:
            query = query.where(TrialCode.code.ilike(f"%{search}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(TrialCode.created_at.desc())
        query = query.limit(page_size).offset(offset)
        
        result = await self.session.execute(query)
        trial_codes = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size
        
        return TrialCodeListResponse(
            items=[self._trial_code_to_response(tc) for tc in trial_codes],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def _get_trial_code_by_code(self, code: str) -> Optional[TrialCode]:
        """Get trial code by code string."""
        result = await self.session.execute(
            select(TrialCode).where(TrialCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    def _trial_code_to_response(self, trial_code: TrialCode) -> TrialCodeResponse:
        """Convert trial code model to response schema."""
        return TrialCodeResponse(
            id=trial_code.id,
            code=trial_code.code,
            trial_days=trial_code.trial_days,
            valid_from=trial_code.valid_from,
            valid_until=trial_code.valid_until,
            usage_limit=trial_code.usage_limit,
            usage_count=trial_code.usage_count,
            applicable_plans=trial_code.applicable_plans or [],
            description=trial_code.description,
            is_active=trial_code.is_active,
            is_valid=trial_code.is_valid(),
            created_by=trial_code.created_by,
            created_at=trial_code.created_at,
            updated_at=trial_code.updated_at,
        )

    # ==================== Promotion Analytics (Requirements 14.5) ====================

    async def get_promotion_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PromotionAnalyticsResponse:
        """Get promotion analytics.
        
        Requirements: 14.5 - Show conversion rate, revenue generated, top referrers
        
        Args:
            start_date: Start of analytics period
            end_date: End of analytics period
            
        Returns:
            PromotionAnalyticsResponse with analytics data
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Get discount code stats
        discount_stats = await self._get_discount_code_stats()
        
        # Get trial code stats
        trial_stats = await self._get_trial_code_stats()
        
        # Get top discount codes
        top_discount_codes = await self._get_top_discount_codes(limit=10)
        
        # Get referral analytics (placeholder - would need referral tracking table)
        referral_analytics = ReferralAnalytics(
            total_referrals=0,
            successful_referrals=0,
            pending_referrals=0,
            total_rewards_given=0.0,
            conversion_rate=0.0,
        )
        
        # Get top referrers (placeholder - would need referral tracking table)
        top_referrers: list[TopReferrer] = []
        
        return PromotionAnalyticsResponse(
            total_discount_codes=discount_stats["total"],
            active_discount_codes=discount_stats["active"],
            total_trial_codes=trial_stats["total"],
            active_trial_codes=trial_stats["active"],
            total_discount_usage=discount_stats["total_usage"],
            total_discount_amount=discount_stats["total_discount_amount"],
            discount_revenue_impact=discount_stats["revenue_impact"],
            referral_analytics=referral_analytics,
            top_discount_codes=top_discount_codes,
            top_referrers=top_referrers,
            period_start=start_date,
            period_end=end_date,
            overall_conversion_rate=0.0,  # Would need conversion tracking
            discount_conversion_rate=0.0,  # Would need conversion tracking
            referral_conversion_rate=0.0,  # Would need conversion tracking
        )

    async def _get_discount_code_stats(self) -> dict:
        """Get discount code statistics."""
        # Total discount codes
        total_result = await self.session.execute(
            select(func.count()).select_from(DiscountCode)
        )
        total = total_result.scalar() or 0
        
        # Active discount codes
        now = datetime.utcnow()
        active_result = await self.session.execute(
            select(func.count()).select_from(DiscountCode).where(
                and_(
                    DiscountCode.is_active == True,
                    DiscountCode.valid_from <= now,
                    DiscountCode.valid_until >= now,
                )
            )
        )
        active = active_result.scalar() or 0
        
        # Total usage
        usage_result = await self.session.execute(
            select(func.sum(DiscountCode.usage_count))
        )
        total_usage = usage_result.scalar() or 0
        
        # Calculate estimated discount amount (simplified)
        codes_result = await self.session.execute(select(DiscountCode))
        codes = codes_result.scalars().all()
        
        total_discount_amount = 0.0
        for code in codes:
            if code.discount_type == "percentage":
                # Estimate based on average order value of $50
                total_discount_amount += code.usage_count * 50 * (code.discount_value / 100)
            else:
                total_discount_amount += code.usage_count * code.discount_value
        
        return {
            "total": total,
            "active": active,
            "total_usage": total_usage,
            "total_discount_amount": total_discount_amount,
            "revenue_impact": total_discount_amount,  # Simplified
        }

    async def _get_trial_code_stats(self) -> dict:
        """Get trial code statistics."""
        # Total trial codes
        total_result = await self.session.execute(
            select(func.count()).select_from(TrialCode)
        )
        total = total_result.scalar() or 0
        
        # Active trial codes
        now = datetime.utcnow()
        active_result = await self.session.execute(
            select(func.count()).select_from(TrialCode).where(
                and_(
                    TrialCode.is_active == True,
                    TrialCode.valid_from <= now,
                    TrialCode.valid_until >= now,
                )
            )
        )
        active = active_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
        }

    async def _get_top_discount_codes(self, limit: int = 10) -> list[DiscountCodeAnalytics]:
        """Get top performing discount codes."""
        result = await self.session.execute(
            select(DiscountCode)
            .where(DiscountCode.usage_count > 0)
            .order_by(DiscountCode.usage_count.desc())
            .limit(limit)
        )
        codes = result.scalars().all()
        
        analytics = []
        for code in codes:
            # Calculate estimated metrics
            if code.discount_type == "percentage":
                avg_discount = 50 * (code.discount_value / 100)  # Assuming $50 avg order
            else:
                avg_discount = code.discount_value
            
            total_discount = code.usage_count * avg_discount
            # Estimate revenue generated (assuming 80% conversion after discount)
            revenue_generated = code.usage_count * 50 * 0.8
            
            analytics.append(DiscountCodeAnalytics(
                code=code.code,
                usage_count=code.usage_count,
                total_discount_given=total_discount,
                revenue_generated=revenue_generated,
                conversion_rate=0.8,  # Placeholder
                average_order_value=50.0,  # Placeholder
            ))
        
        return analytics


# Additional exception classes
class TrialCodeNotFoundError(Exception):
    """Raised when trial code or subscription is not found."""
    pass


class TrialCodeExistsError(Exception):
    """Raised when trial code already exists."""
    pass


class TrialCodeValidationError(Exception):
    """Raised when trial code validation fails."""
    pass
