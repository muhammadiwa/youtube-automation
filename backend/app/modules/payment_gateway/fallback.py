"""Payment Fallback Logic for handling gateway failures.

Implements automatic retry with alternative gateways when payment fails.
Requirements: 30.5 - Retry with alternative gateway on failure

This module provides:
- Automatic fallback to alternative gateways
- Failed attempt tracking per gateway
- Gateway health-based selection
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment_gateway.models import (
    PaymentGatewayConfig,
    PaymentTransaction,
    PaymentStatus,
    GatewayStatistics,
    GatewayHealthStatus,
)
from app.modules.payment_gateway.repository import (
    PaymentGatewayRepository,
    PaymentTransactionRepository,
    GatewayStatisticsRepository,
)
from app.modules.payment_gateway.service import PaymentGatewayFactory
from app.modules.payment_gateway.interface import CreatePaymentDTO

logger = logging.getLogger(__name__)


# Maximum number of retry attempts across all gateways
MAX_TOTAL_ATTEMPTS = 3

# Minimum success rate for a gateway to be considered for fallback
MIN_FALLBACK_SUCCESS_RATE = 50.0


class PaymentFallbackService:
    """Service for handling payment fallback logic.
    
    Requirements: 30.5 - Retry with alternative gateway on failure
    
    Provides intelligent fallback selection based on:
    - Gateway health status
    - Historical success rates
    - Currency support
    - Previous failed attempts
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gateway_repo = PaymentGatewayRepository(session)
        self.transaction_repo = PaymentTransactionRepository(session)
        self.stats_repo = GatewayStatisticsRepository(session)
    
    async def get_fallback_gateways(
        self,
        transaction: PaymentTransaction,
        exclude_providers: Optional[list[str]] = None,
    ) -> list[PaymentGatewayConfig]:
        """Get available fallback gateways for a failed transaction.
        
        Requirements: 30.5 - Allow retry with alternative gateway
        
        Args:
            transaction: Failed payment transaction
            exclude_providers: Providers to exclude (e.g., already tried)
            
        Returns:
            List of available fallback gateways, sorted by health/success rate
        """
        exclude = set(exclude_providers or [])
        exclude.add(transaction.gateway_provider)
        
        # Also exclude the previous gateway if set
        if transaction.previous_gateway:
            exclude.add(transaction.previous_gateway)
        
        # Get all enabled gateways
        enabled = await self.gateway_repo.get_enabled_configs()
        
        # Filter by currency support and exclusions
        candidates = [
            g for g in enabled 
            if g.provider not in exclude 
            and g.supports_currency(transaction.currency)
        ]
        
        if not candidates:
            return []
        
        # Get statistics for ranking
        stats_map = {}
        for gateway in candidates:
            stats = await self.stats_repo.get_statistics(gateway.provider)
            if stats:
                stats_map[gateway.provider] = stats
        
        # Sort by health status and success rate
        def sort_key(gateway: PaymentGatewayConfig) -> tuple:
            stats = stats_map.get(gateway.provider)
            if not stats:
                return (2, 0.0)  # Unknown health, 0% success
            
            health_order = {
                GatewayHealthStatus.HEALTHY.value: 0,
                GatewayHealthStatus.DEGRADED.value: 1,
                GatewayHealthStatus.DOWN.value: 2,
            }
            return (
                health_order.get(stats.health_status, 2),
                -stats.success_rate,  # Negative for descending order
            )
        
        candidates.sort(key=sort_key)
        
        # Filter out gateways with very low success rates
        return [
            g for g in candidates
            if (
                g.provider not in stats_map 
                or stats_map[g.provider].success_rate >= MIN_FALLBACK_SUCCESS_RATE
                or stats_map[g.provider].total_transactions < 10  # Not enough data
            )
        ]
    
    async def can_retry(self, transaction: PaymentTransaction) -> bool:
        """Check if a transaction can be retried.
        
        Args:
            transaction: Payment transaction
            
        Returns:
            True if retry is allowed
        """
        # Check status
        if not transaction.can_retry():
            return False
        
        # Check attempt count
        if transaction.attempt_count >= MAX_TOTAL_ATTEMPTS:
            return False
        
        return True
    
    async def select_best_fallback(
        self,
        transaction: PaymentTransaction,
    ) -> Optional[PaymentGatewayConfig]:
        """Select the best fallback gateway for a failed transaction.
        
        Requirements: 30.5 - Intelligent fallback selection
        
        Args:
            transaction: Failed payment transaction
            
        Returns:
            Best available fallback gateway or None
        """
        if not await self.can_retry(transaction):
            return None
        
        fallbacks = await self.get_fallback_gateways(transaction)
        return fallbacks[0] if fallbacks else None
    
    async def execute_fallback(
        self,
        transaction_id: uuid.UUID,
        fallback_provider: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        """Execute fallback to an alternative gateway.
        
        Requirements: 30.5 - Retry with alternative gateway on failure
        
        Args:
            transaction_id: Original transaction ID
            fallback_provider: Specific provider to use (auto-select if None)
            
        Returns:
            Updated transaction or None if fallback not possible
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found for fallback")
            return None
        
        if not await self.can_retry(transaction):
            logger.info(
                f"Transaction {transaction_id} cannot be retried "
                f"(status={transaction.status}, attempts={transaction.attempt_count})"
            )
            return None
        
        # Select fallback gateway
        if fallback_provider:
            config = await self.gateway_repo.get_config_by_provider(fallback_provider)
            if not config or not config.is_enabled:
                logger.error(f"Fallback gateway {fallback_provider} not available")
                return None
            if not config.supports_currency(transaction.currency):
                logger.error(
                    f"Fallback gateway {fallback_provider} "
                    f"doesn't support {transaction.currency}"
                )
                return None
        else:
            config = await self.select_best_fallback(transaction)
            if not config:
                logger.info(f"No fallback gateway available for {transaction_id}")
                return None
        
        logger.info(
            f"Executing fallback for {transaction_id}: "
            f"{transaction.gateway_provider} -> {config.provider}"
        )
        
        # Record the attempt
        previous_gateway = transaction.gateway_provider
        await self.transaction_repo.increment_attempt(transaction_id, previous_gateway)
        
        # Update gateway provider
        await self.transaction_repo.update_transaction(
            transaction_id,
            gateway_provider=config.provider,
            status=PaymentStatus.PENDING.value,
            error_message=None,
            error_code=None,
            gateway_payment_id=None,
            checkout_url=None,
        )
        
        # Process with new gateway
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        gateway = PaymentGatewayFactory.create(config)
        
        payment_dto = CreatePaymentDTO(
            order_id=str(transaction.id),
            amount=transaction.amount,
            currency=transaction.currency,
            description=transaction.description or "",
            success_url=transaction.success_url,
            cancel_url=transaction.cancel_url,
            metadata=transaction.payment_metadata,
        )
        
        result = await gateway.create_payment(payment_dto)
        
        # Update transaction with result
        if result.status == PaymentStatus.FAILED.value:
            await self.transaction_repo.mark_failed(
                transaction_id,
                error_message=result.error_message or "Fallback payment failed",
                error_code=result.error_code,
            )
            await self.stats_repo.record_transaction(
                config.provider, 
                transaction.amount, 
                success=False
            )
            
            # Try another fallback if available
            if transaction.attempt_count < MAX_TOTAL_ATTEMPTS - 1:
                return await self.execute_fallback(transaction_id)
        else:
            await self.transaction_repo.update_transaction(
                transaction_id,
                gateway_payment_id=result.payment_id,
                checkout_url=result.checkout_url,
                status=result.status,
                gateway_response=result.gateway_response,
            )
        
        return await self.transaction_repo.get_transaction(transaction_id)
    
    async def get_failed_attempts_summary(
        self,
        transaction_id: uuid.UUID,
    ) -> dict:
        """Get summary of failed attempts for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Summary dict with attempt details
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            return {}
        
        return {
            "transaction_id": str(transaction_id),
            "current_gateway": transaction.gateway_provider,
            "previous_gateway": transaction.previous_gateway,
            "attempt_count": transaction.attempt_count,
            "max_attempts": MAX_TOTAL_ATTEMPTS,
            "can_retry": await self.can_retry(transaction),
            "status": transaction.status,
            "error_message": transaction.error_message,
        }


async def track_gateway_failure(
    session: AsyncSession,
    provider: str,
    amount: float,
    error_message: Optional[str] = None,
) -> None:
    """Track a gateway failure for statistics.
    
    Requirements: 30.5 - Track failed attempts per gateway
    
    Args:
        session: Database session
        provider: Gateway provider
        amount: Transaction amount
        error_message: Optional error message
    """
    stats_repo = GatewayStatisticsRepository(session)
    await stats_repo.record_transaction(provider, amount, success=False)
    
    logger.warning(
        f"Gateway failure recorded: provider={provider}, "
        f"amount={amount}, error={error_message}"
    )


async def track_gateway_success(
    session: AsyncSession,
    provider: str,
    amount: float,
) -> None:
    """Track a gateway success for statistics.
    
    Args:
        session: Database session
        provider: Gateway provider
        amount: Transaction amount
    """
    stats_repo = GatewayStatisticsRepository(session)
    await stats_repo.record_transaction(provider, amount, success=True)
