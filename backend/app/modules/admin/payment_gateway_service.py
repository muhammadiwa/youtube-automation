"""Admin Payment Gateway Service for managing payment gateways.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5 - Payment Gateway Administration
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.audit import AdminAuditService, AdminAuditEvent
from app.modules.admin.payment_gateway_schemas import (
    GatewayResponse,
    GatewayListResponse,
    GatewayHealthInfo,
    GatewayStatsInfo,
    GatewayStatusUpdateRequest,
    GatewayStatusUpdateResponse,
    GatewayCredentialsUpdateRequest,
    GatewayCredentialsUpdateResponse,
    GatewayDetailedStats,
    GatewayStatsResponse,
    GatewayHealthAlert,
    GatewayHealthAlertListResponse,
    GatewayFailoverSuggestion,
)
from app.modules.payment_gateway.models import (
    PaymentGatewayConfig,
    GatewayStatistics,
    PaymentTransaction,
    GatewayHealthStatus,
    PaymentStatus,
)
from app.modules.payment_gateway.interface import encrypt_credential, ValidationResult
from app.modules.payment_gateway.service import PaymentGatewayFactory, GatewayManagerService

logger = logging.getLogger(__name__)


class GatewayNotFoundError(Exception):
    """Raised when gateway is not found."""
    pass


class GatewayCredentialsInvalidError(Exception):
    """Raised when gateway credentials are invalid."""
    pass


class AdminPaymentGatewayService:
    """Service for admin payment gateway operations.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5 - Payment Gateway Administration
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gateway_manager = GatewayManagerService(session)
    
    async def get_all_gateways(self) -> GatewayListResponse:
        """Get all payment gateways with status, health, and stats.
        
        Requirements: 5.1 - Display all gateways with status, health, and transaction stats
        
        Returns:
            GatewayListResponse with all gateways
        """
        # Get all gateway configs
        configs = await self.gateway_manager.get_all_gateways()
        
        items = []
        for config in configs:
            # Get statistics for this gateway
            stats = await self._get_gateway_statistics(config.provider)
            health = self._build_health_info(stats)
            stats_info = self._build_stats_info(stats)
            
            items.append(GatewayResponse(
                id=config.id,
                provider=config.provider,
                display_name=config.display_name,
                is_enabled=config.is_enabled,
                is_default=config.is_default,
                sandbox_mode=config.sandbox_mode,
                has_credentials=config.has_credentials(),
                supported_currencies=config.supported_currencies or [],
                supported_payment_methods=config.supported_payment_methods or [],
                transaction_fee_percent=config.transaction_fee_percent,
                fixed_fee=config.fixed_fee,
                min_amount=config.min_amount,
                max_amount=config.max_amount,
                health=health,
                stats=stats_info,
                created_at=config.created_at,
                updated_at=config.updated_at,
            ))
        
        return GatewayListResponse(
            items=items,
            total=len(items),
        )
    
    async def update_gateway_status(
        self,
        provider: str,
        data: GatewayStatusUpdateRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> GatewayStatusUpdateResponse:
        """Enable or disable a payment gateway.
        
        Requirements: 5.2 - Enable/disable gateway dynamically without system restart
        
        Args:
            provider: Gateway provider identifier
            data: Status update request
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            GatewayStatusUpdateResponse
            
        Raises:
            GatewayNotFoundError: If gateway not found
            ValueError: If trying to enable gateway without credentials
        """
        config = await self.gateway_manager.get_gateway(provider)
        if not config:
            raise GatewayNotFoundError(f"Gateway {provider} not found")
        
        if data.is_enabled:
            # Enable gateway
            updated = await self.gateway_manager.enable_gateway(provider)
            action = "gateway_enabled"
            message = f"Gateway {provider} has been enabled"
        else:
            # Disable gateway
            updated = await self.gateway_manager.disable_gateway(provider)
            action = "gateway_disabled"
            message = f"Gateway {provider} has been disabled"
        
        if not updated:
            raise GatewayNotFoundError(f"Failed to update gateway {provider}")
        
        # Create audit log
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.SYSTEM_CONFIG_CHANGED,
            resource_type="payment_gateway",
            resource_id=str(config.id),
            details={
                "action": action,
                "provider": provider,
                "is_enabled": data.is_enabled,
                "reason": data.reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return GatewayStatusUpdateResponse(
            provider=provider,
            is_enabled=data.is_enabled,
            updated_at=datetime.utcnow(),
            message=message,
        )
    
    async def update_gateway_credentials(
        self,
        provider: str,
        data: GatewayCredentialsUpdateRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> GatewayCredentialsUpdateResponse:
        """Update gateway credentials.
        
        Requirements: 5.3 - Validate credentials before saving and encrypt sensitive data
        
        Args:
            provider: Gateway provider identifier
            data: Credentials update request
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            GatewayCredentialsUpdateResponse
            
        Raises:
            GatewayNotFoundError: If gateway not found
            GatewayCredentialsInvalidError: If credentials validation fails
        """
        config = await self.gateway_manager.get_gateway(provider)
        if not config:
            raise GatewayNotFoundError(f"Gateway {provider} not found")
        
        credentials_valid = True
        validation_message = "Credentials saved successfully"
        
        # Validate credentials before saving if requested
        if data.validate_before_save:
            validation_result = await self._validate_credentials(
                provider=provider,
                api_key=data.api_key,
                api_secret=data.api_secret,
                sandbox_mode=data.sandbox_mode,
            )
            
            if not validation_result.is_valid:
                raise GatewayCredentialsInvalidError(
                    f"Credentials validation failed: {validation_result.message}"
                )
            
            credentials_valid = validation_result.is_valid
            validation_message = validation_result.message
        
        # Configure gateway with encrypted credentials
        await self.gateway_manager.configure_gateway(
            provider=provider,
            api_key=data.api_key,
            api_secret=data.api_secret,
            webhook_secret=data.webhook_secret,
            sandbox_mode=data.sandbox_mode,
        )
        
        # Create audit log (don't log actual credentials)
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.SYSTEM_CONFIG_CHANGED,
            resource_type="payment_gateway",
            resource_id=str(config.id),
            details={
                "action": "gateway_credentials_updated",
                "provider": provider,
                "sandbox_mode": data.sandbox_mode,
                "credentials_validated": data.validate_before_save,
                "validation_result": credentials_valid,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return GatewayCredentialsUpdateResponse(
            provider=provider,
            credentials_valid=credentials_valid,
            sandbox_mode=data.sandbox_mode,
            updated_at=datetime.utcnow(),
            message=validation_message,
        )
    
    async def get_gateway_statistics(
        self,
        provider: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> GatewayStatsResponse:
        """Get detailed statistics for a gateway.
        
        Requirements: 5.4 - Show success rate, failure rate, total volume, average transaction
        
        Args:
            provider: Gateway provider identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            GatewayStatsResponse with detailed statistics
            
        Raises:
            GatewayNotFoundError: If gateway not found
        """
        config = await self.gateway_manager.get_gateway(provider)
        if not config:
            raise GatewayNotFoundError(f"Gateway {provider} not found")
        
        # Get base statistics
        stats = await self._get_gateway_statistics(provider)
        
        # Calculate 24h volume
        volume_24h = await self._calculate_volume_24h(provider)
        
        # Calculate failure rate
        failure_rate = 0.0
        if stats and stats.total_transactions > 0:
            failure_rate = (stats.failed_transactions / stats.total_transactions) * 100
        
        detailed_stats = GatewayDetailedStats(
            provider=provider,
            display_name=config.display_name,
            total_transactions=stats.total_transactions if stats else 0,
            successful_transactions=stats.successful_transactions if stats else 0,
            failed_transactions=stats.failed_transactions if stats else 0,
            success_rate=stats.success_rate if stats else 0.0,
            failure_rate=failure_rate,
            success_rate_24h=stats.success_rate_24h if stats else 0.0,
            total_volume=stats.total_volume if stats else 0.0,
            average_transaction=stats.average_transaction if stats else 0.0,
            transactions_24h=stats.transactions_24h if stats else 0,
            volume_24h=volume_24h,
            health_status=stats.health_status if stats else GatewayHealthStatus.HEALTHY.value,
            last_transaction_at=stats.last_transaction_at if stats else None,
            last_success_at=stats.last_success_at if stats else None,
            last_failure_at=stats.last_failure_at if stats else None,
            stats_since=stats.created_at if stats else None,
        )
        
        return GatewayStatsResponse(
            stats=detailed_stats,
            period_start=start_date,
            period_end=end_date,
        )
    
    async def check_gateway_health(
        self,
        provider: str,
    ) -> tuple[bool, Optional[GatewayHealthAlert]]:
        """Check gateway health and generate alert if degraded.
        
        Requirements: 5.5 - Alert admin when gateway health degrades
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            Tuple of (is_healthy, alert if degraded)
        """
        config = await self.gateway_manager.get_gateway(provider)
        if not config:
            return False, None
        
        stats = await self._get_gateway_statistics(provider)
        if not stats:
            return True, None  # No stats yet, assume healthy
        
        # Check if health is degraded or down
        if stats.health_status == GatewayHealthStatus.HEALTHY.value:
            return True, None
        
        # Generate alert
        alert_type = "degraded" if stats.health_status == GatewayHealthStatus.DEGRADED.value else "down"
        severity = "warning" if alert_type == "degraded" else "critical"
        
        # Get alternative gateways
        alternatives = await self._get_alternative_gateways(provider)
        
        suggested_action = None
        if alternatives:
            suggested_action = f"Consider failing over to {alternatives[0]}"
        
        alert = GatewayHealthAlert(
            id=uuid.uuid4(),
            provider=provider,
            alert_type=alert_type,
            severity=severity,
            message=f"Gateway {provider} health is {stats.health_status}. Success rate: {stats.success_rate:.1f}%",
            health_status=stats.health_status,
            success_rate=stats.success_rate,
            suggested_action=suggested_action,
            alternative_gateways=alternatives,
            created_at=datetime.utcnow(),
        )
        
        return False, alert
    
    async def get_failover_suggestion(
        self,
        provider: str,
    ) -> Optional[GatewayFailoverSuggestion]:
        """Get failover suggestion for a degraded gateway.
        
        Requirements: 5.5 - Suggest failover to alternative gateway
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            GatewayFailoverSuggestion if failover is recommended
        """
        config = await self.gateway_manager.get_gateway(provider)
        if not config:
            return None
        
        stats = await self._get_gateway_statistics(provider)
        if not stats or stats.health_status == GatewayHealthStatus.HEALTHY.value:
            return None
        
        # Find best alternative gateway
        alternatives = await self._get_alternative_gateways(provider)
        if not alternatives:
            return None
        
        # Get stats for best alternative
        best_alternative = alternatives[0]
        alt_stats = await self._get_gateway_statistics(best_alternative)
        alt_config = await self.gateway_manager.get_gateway(best_alternative)
        
        if not alt_stats or not alt_config:
            return None
        
        return GatewayFailoverSuggestion(
            current_gateway=provider,
            current_health_status=stats.health_status,
            current_success_rate=stats.success_rate,
            suggested_gateway=best_alternative,
            suggested_gateway_health=alt_stats.health_status,
            suggested_gateway_success_rate=alt_stats.success_rate,
            reason=f"Gateway {provider} has degraded health ({stats.success_rate:.1f}% success rate). "
                   f"{best_alternative} is healthy with {alt_stats.success_rate:.1f}% success rate.",
            auto_failover_available=alt_config.is_enabled,
        )
    
    # ==================== Private Helper Methods ====================
    
    async def _get_gateway_statistics(self, provider: str) -> Optional[GatewayStatistics]:
        """Get statistics for a gateway."""
        result = await self.session.execute(
            select(GatewayStatistics).where(GatewayStatistics.provider == provider)
        )
        return result.scalar_one_or_none()
    
    def _build_health_info(self, stats: Optional[GatewayStatistics]) -> GatewayHealthInfo:
        """Build health info from statistics."""
        if not stats:
            return GatewayHealthInfo(
                status=GatewayHealthStatus.HEALTHY.value,
                success_rate=0.0,
                success_rate_24h=0.0,
                last_transaction_at=None,
                last_failure_at=None,
            )
        
        return GatewayHealthInfo(
            status=stats.health_status,
            success_rate=stats.success_rate,
            success_rate_24h=stats.success_rate_24h,
            last_transaction_at=stats.last_transaction_at,
            last_failure_at=stats.last_failure_at,
        )
    
    def _build_stats_info(self, stats: Optional[GatewayStatistics]) -> GatewayStatsInfo:
        """Build stats info from statistics."""
        if not stats:
            return GatewayStatsInfo()
        
        return GatewayStatsInfo(
            total_transactions=stats.total_transactions,
            successful_transactions=stats.successful_transactions,
            failed_transactions=stats.failed_transactions,
            total_volume=stats.total_volume,
            average_transaction=stats.average_transaction,
            transactions_24h=stats.transactions_24h,
        )
    
    async def _validate_credentials(
        self,
        provider: str,
        api_key: str,
        api_secret: str,
        sandbox_mode: bool,
    ) -> ValidationResult:
        """Validate gateway credentials by making a test API call."""
        try:
            # Create a temporary config for validation
            from app.modules.payment_gateway.models import PaymentGatewayConfig, GATEWAY_DEFAULTS
            
            defaults = GATEWAY_DEFAULTS.get(provider, {})
            
            temp_config = PaymentGatewayConfig(
                id=uuid.uuid4(),
                provider=provider,
                display_name=defaults.get("display_name", provider.title()),
                is_enabled=False,
                is_default=False,
                api_key_encrypted=encrypt_credential(api_key),
                api_secret_encrypted=encrypt_credential(api_secret),
                sandbox_mode=sandbox_mode,
                supported_currencies=defaults.get("supported_currencies", []),
                supported_payment_methods=defaults.get("supported_payment_methods", []),
                transaction_fee_percent=defaults.get("transaction_fee_percent", 0.0),
                fixed_fee=defaults.get("fixed_fee", 0.0),
                min_amount=defaults.get("min_amount", 0.0),
                max_amount=defaults.get("max_amount"),
            )
            
            gateway = PaymentGatewayFactory.create(temp_config)
            return await gateway.validate_credentials()
            
        except Exception as e:
            logger.error(f"Error validating {provider} credentials: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Validation error: {str(e)}",
            )
    
    async def _calculate_volume_24h(self, provider: str) -> float:
        """Calculate transaction volume in last 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        result = await self.session.execute(
            select(func.sum(PaymentTransaction.amount))
            .where(PaymentTransaction.gateway_provider == provider)
            .where(PaymentTransaction.status == PaymentStatus.COMPLETED.value)
            .where(PaymentTransaction.created_at >= cutoff)
        )
        
        volume = result.scalar_one_or_none()
        return float(volume) if volume else 0.0
    
    async def _get_alternative_gateways(self, exclude_provider: str) -> list[str]:
        """Get list of healthy alternative gateways."""
        enabled_gateways = await self.gateway_manager.get_enabled_gateways()
        
        alternatives = []
        for gateway in enabled_gateways:
            if gateway.provider == exclude_provider:
                continue
            
            stats = await self._get_gateway_statistics(gateway.provider)
            if stats and stats.health_status == GatewayHealthStatus.HEALTHY.value:
                alternatives.append(gateway.provider)
        
        return alternatives
