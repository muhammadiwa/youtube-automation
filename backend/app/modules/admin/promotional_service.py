"""Admin Promotional Service for discount codes and promotions.

Requirements: 14.1, 14.2 - Promotional & Marketing Tools
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import DiscountCode, DiscountType
from app.modules.admin.schemas import (
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
    DiscountCodeListResponse,
    DiscountCodeValidationResponse,
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
