"""Payment Gateway Service for managing gateways and processing payments.

Implements Gateway Manager Service for:
- Enable/disable gateway dynamically (Requirements: 30.2)
- Get enabled gateways for user (Requirements: 30.3)
- Route payment to selected gateway (Requirements: 30.4)
- Payment fallback logic (Requirements: 30.5)

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment_gateway.interface import (
    PaymentGatewayInterface,
    CreatePaymentDTO,
    encrypt_credential,
    ValidationResult,
)
from app.modules.payment_gateway.models import (
    PaymentGatewayConfig,
    PaymentTransaction,
    GatewayProvider,
    PaymentStatus,
)
from app.modules.payment_gateway.repository import (
    PaymentGatewayRepository,
    PaymentTransactionRepository,
    GatewayStatisticsRepository,
)
from app.modules.payment_gateway.gateways import (
    StripeGateway,
    PayPalGateway,
    MidtransGateway,
    XenditGateway,
)

logger = logging.getLogger(__name__)


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances.
    
    Requirements: 30.1 - Support multiple gateway providers
    """
    
    _gateways: dict[str, Type[PaymentGatewayInterface]] = {
        GatewayProvider.STRIPE.value: StripeGateway,
        GatewayProvider.PAYPAL.value: PayPalGateway,
        GatewayProvider.MIDTRANS.value: MidtransGateway,
        GatewayProvider.XENDIT.value: XenditGateway,
    }
    
    @classmethod
    def create(cls, config: PaymentGatewayConfig) -> PaymentGatewayInterface:
        """Create a gateway instance from configuration.
        
        Args:
            config: PaymentGatewayConfig model instance
            
        Returns:
            Configured gateway instance
            
        Raises:
            ValueError: If provider is not supported
        """
        gateway_class = cls._gateways.get(config.provider)
        if not gateway_class:
            raise ValueError(f"Unsupported gateway provider: {config.provider}")
        return gateway_class(config)
    
    @classmethod
    def register(
        cls, 
        provider: str, 
        gateway_class: Type[PaymentGatewayInterface]
    ) -> None:
        """Register a new gateway implementation.
        
        Args:
            provider: Provider identifier
            gateway_class: Gateway implementation class
        """
        cls._gateways[provider] = gateway_class
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider identifiers."""
        return list(cls._gateways.keys())


class GatewayManagerService:
    """Service for managing payment gateway configurations.
    
    Handles:
    - Enable/disable gateway dynamically (Requirements: 30.2)
    - Get enabled gateways for user (Requirements: 30.3)
    - Gateway configuration CRUD
    - Credential validation (Requirements: 30.7)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gateway_repo = PaymentGatewayRepository(session)
        self.stats_repo = GatewayStatisticsRepository(session)
    
    async def get_all_gateways(self) -> list[PaymentGatewayConfig]:
        """Get all gateway configurations.
        
        Returns:
            List of all gateway configurations
        """
        return await self.gateway_repo.get_all_configs()
    
    async def get_enabled_gateways(self) -> list[PaymentGatewayConfig]:
        """Get all enabled gateway configurations.
        
        Requirements: 30.3 - Display only enabled payment gateways
        
        Returns:
            List of enabled gateway configurations
        """
        return await self.gateway_repo.get_enabled_configs()
    
    async def get_enabled_gateways_for_currency(
        self, 
        currency: str
    ) -> list[PaymentGatewayConfig]:
        """Get enabled gateways that support a specific currency.
        
        Requirements: 30.3 - Display only enabled payment gateways
        
        Args:
            currency: Currency code (e.g., USD, IDR)
            
        Returns:
            List of enabled gateways supporting the currency
        """
        enabled = await self.gateway_repo.get_enabled_configs()
        return [g for g in enabled if g.supports_currency(currency)]
    
    async def get_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Get gateway configuration by provider.
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            Gateway configuration or None
        """
        return await self.gateway_repo.get_config_by_provider(provider)
    
    async def get_default_gateway(self) -> Optional[PaymentGatewayConfig]:
        """Get the default gateway configuration.
        
        Returns:
            Default gateway configuration or None
        """
        return await self.gateway_repo.get_default_config()
    
    async def enable_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Enable a payment gateway.
        
        Requirements: 30.2 - Enable gateway dynamically without system restart
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            Updated gateway configuration or None if not found
            
        Raises:
            ValueError: If gateway has no credentials configured
        """
        config = await self.gateway_repo.get_config_by_provider(provider)
        if not config:
            return None
        
        if not config.has_credentials():
            raise ValueError(
                f"Cannot enable gateway {provider}: credentials not configured"
            )
        
        return await self.gateway_repo.enable_gateway(provider)
    
    async def disable_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Disable a payment gateway.
        
        Requirements: 30.2 - Disable gateway dynamically without system restart
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            Updated gateway configuration or None if not found
        """
        return await self.gateway_repo.disable_gateway(provider)
    
    async def set_default_gateway(
        self, 
        provider: str
    ) -> Optional[PaymentGatewayConfig]:
        """Set a gateway as the default.
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            Updated gateway configuration or None if not found
            
        Raises:
            ValueError: If gateway is not enabled or has no credentials
        """
        config = await self.gateway_repo.get_config_by_provider(provider)
        if not config:
            return None
        
        if not config.has_credentials():
            raise ValueError(
                f"Cannot set {provider} as default: credentials not configured"
            )
        
        return await self.gateway_repo.set_default_gateway(provider)
    
    async def configure_gateway(
        self,
        provider: str,
        api_key: str,
        api_secret: str,
        webhook_secret: Optional[str] = None,
        sandbox_mode: bool = True,
        display_name: Optional[str] = None,
        **kwargs
    ) -> PaymentGatewayConfig:
        """Configure or update gateway credentials.
        
        Requirements: 30.4 - Encrypted credentials via KMS
        
        Args:
            provider: Gateway provider identifier
            api_key: API key (will be encrypted)
            api_secret: API secret (will be encrypted)
            webhook_secret: Optional webhook secret (will be encrypted)
            sandbox_mode: Whether to use sandbox/test mode
            display_name: Optional display name
            **kwargs: Additional configuration options
            
        Returns:
            Created or updated gateway configuration
        """
        # Encrypt credentials
        api_key_encrypted = encrypt_credential(api_key)
        api_secret_encrypted = encrypt_credential(api_secret)
        webhook_secret_encrypted = (
            encrypt_credential(webhook_secret) if webhook_secret else None
        )
        
        # Check if config exists
        existing = await self.gateway_repo.get_config_by_provider(provider)
        
        if existing:
            # Update existing config
            return await self.gateway_repo.update_config(
                provider,
                api_key_encrypted=api_key_encrypted,
                api_secret_encrypted=api_secret_encrypted,
                webhook_secret_encrypted=webhook_secret_encrypted,
                sandbox_mode=sandbox_mode,
                display_name=display_name,
                **kwargs
            )
        else:
            # Create new config
            return await self.gateway_repo.create_config(
                provider=provider,
                display_name=display_name or provider.title(),
                api_key_encrypted=api_key_encrypted,
                api_secret_encrypted=api_secret_encrypted,
                webhook_secret_encrypted=webhook_secret_encrypted,
                sandbox_mode=sandbox_mode,
                **kwargs
            )
    
    async def validate_gateway_credentials(
        self, 
        provider: str
    ) -> ValidationResult:
        """Validate gateway API credentials.
        
        Requirements: 30.7 - Validate API keys before saving
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            ValidationResult indicating if credentials are valid
        """
        config = await self.gateway_repo.get_config_by_provider(provider)
        if not config:
            return ValidationResult(
                is_valid=False,
                message=f"Gateway {provider} not found",
            )
        
        if not config.has_credentials():
            return ValidationResult(
                is_valid=False,
                message=f"Gateway {provider} has no credentials configured",
            )
        
        try:
            gateway = PaymentGatewayFactory.create(config)
            return await gateway.validate_credentials()
        except Exception as e:
            logger.error(f"Error validating {provider} credentials: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Error validating credentials: {str(e)}",
            )
    
    async def get_gateway_statistics(self, provider: str):
        """Get statistics for a gateway.
        
        Requirements: 30.6 - Gateway dashboard with statistics
        
        Args:
            provider: Gateway provider identifier
            
        Returns:
            GatewayStatistics or None
        """
        return await self.stats_repo.get_statistics(provider)
    
    async def get_all_gateway_statistics(self):
        """Get statistics for all gateways.
        
        Requirements: 30.6 - Gateway dashboard with statistics
        
        Returns:
            List of GatewayStatistics
        """
        return await self.stats_repo.get_all_statistics()
    
    async def initialize_default_gateways(self) -> list[PaymentGatewayConfig]:
        """Initialize default gateway configurations.
        
        Creates placeholder configurations for all supported providers
        without credentials.
        
        Returns:
            List of created configurations
        """
        configs = await self.gateway_repo.initialize_default_configs()
        await self.stats_repo.initialize_all_statistics()
        return configs


class PaymentService:
    """Service for processing payments through configured gateways.
    
    Handles:
    - Route payment to selected gateway (Requirements: 30.4)
    - Payment fallback logic (Requirements: 30.5)
    - Transaction tracking
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gateway_repo = PaymentGatewayRepository(session)
        self.transaction_repo = PaymentTransactionRepository(session)
        self.stats_repo = GatewayStatisticsRepository(session)
        self.gateway_manager = GatewayManagerService(session)
    
    async def get_available_gateways(
        self, 
        currency: str
    ) -> list[PaymentGatewayConfig]:
        """Get available gateways for a payment.
        
        Requirements: 30.3 - Display only enabled payment gateways
        
        Args:
            currency: Payment currency
            
        Returns:
            List of enabled gateways supporting the currency
        """
        return await self.gateway_manager.get_enabled_gateways_for_currency(currency)
    
    async def create_payment(
        self,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        description: str,
        gateway_provider: Optional[str] = None,
        subscription_id: Optional[uuid.UUID] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> PaymentTransaction:
        """Create a new payment transaction.
        
        Requirements: 30.4 - Process payment through gateway
        
        Args:
            user_id: User ID
            amount: Payment amount
            currency: Currency code
            description: Payment description
            gateway_provider: Preferred gateway (uses default if not specified)
            subscription_id: Optional subscription ID
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL
            metadata: Additional metadata
            
        Returns:
            Created payment transaction
            
        Raises:
            ValueError: If no suitable gateway is available
        """
        # Get gateway configuration
        if gateway_provider:
            config = await self.gateway_repo.get_config_by_provider(gateway_provider)
            if not config or not config.is_enabled:
                raise ValueError(f"Gateway {gateway_provider} is not available")
            if not config.supports_currency(currency):
                raise ValueError(
                    f"Gateway {gateway_provider} does not support {currency}"
                )
        else:
            # Use default gateway or first available
            config = await self.gateway_repo.get_default_config()
            if not config:
                available = await self.gateway_manager.get_enabled_gateways_for_currency(
                    currency
                )
                if not available:
                    raise ValueError(f"No gateway available for {currency}")
                config = available[0]
        
        # Create transaction record
        transaction = await self.transaction_repo.create_transaction(
            user_id=user_id,
            gateway_provider=config.provider,
            amount=amount,
            currency=currency,
            description=description,
            subscription_id=subscription_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        
        return transaction
    
    async def process_payment(
        self, 
        transaction_id: uuid.UUID
    ) -> PaymentTransaction:
        """Process a payment through its configured gateway.
        
        Requirements: 30.4 - Process payment through gateway
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Updated transaction with gateway response
            
        Raises:
            ValueError: If transaction not found or gateway unavailable
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        config = await self.gateway_repo.get_config_by_provider(
            transaction.gateway_provider
        )
        if not config or not config.is_enabled:
            raise ValueError(
                f"Gateway {transaction.gateway_provider} is not available"
            )
        
        # Create gateway instance and process payment
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
                error_message=result.error_message or "Payment creation failed",
                error_code=result.error_code,
            )
            # Record failed transaction in statistics
            await self.stats_repo.record_transaction(
                config.provider, 
                transaction.amount, 
                success=False
            )
        else:
            await self.transaction_repo.update_transaction(
                transaction_id,
                gateway_payment_id=result.payment_id,
                checkout_url=result.checkout_url,
                status=result.status,
                gateway_response=result.gateway_response,
            )
        
        return await self.transaction_repo.get_transaction(transaction_id)
    
    async def retry_with_alternative_gateway(
        self,
        transaction_id: uuid.UUID,
        alternative_provider: str,
    ) -> PaymentTransaction:
        """Retry a failed payment with an alternative gateway.
        
        Requirements: 30.5 - Retry with alternative gateway on failure
        
        Args:
            transaction_id: Original transaction ID
            alternative_provider: Alternative gateway provider
            
        Returns:
            Updated transaction
            
        Raises:
            ValueError: If transaction cannot be retried or gateway unavailable
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if not transaction.can_retry():
            raise ValueError(
                f"Transaction {transaction_id} cannot be retried (status: {transaction.status})"
            )
        
        # Verify alternative gateway is available
        config = await self.gateway_repo.get_config_by_provider(alternative_provider)
        if not config or not config.is_enabled:
            raise ValueError(f"Gateway {alternative_provider} is not available")
        
        if not config.supports_currency(transaction.currency):
            raise ValueError(
                f"Gateway {alternative_provider} does not support {transaction.currency}"
            )
        
        # Record the retry attempt
        previous_gateway = transaction.gateway_provider
        await self.transaction_repo.increment_attempt(transaction_id, previous_gateway)
        
        # Update gateway provider
        await self.transaction_repo.update_transaction(
            transaction_id,
            gateway_provider=alternative_provider,
            status=PaymentStatus.PENDING.value,
            error_message=None,
            error_code=None,
            gateway_payment_id=None,
            checkout_url=None,
        )
        
        # Process with new gateway
        return await self.process_payment(transaction_id)
    
    async def get_alternative_gateways(
        self,
        transaction_id: uuid.UUID,
    ) -> list[PaymentGatewayConfig]:
        """Get alternative gateways for a failed transaction.
        
        Requirements: 30.5 - Allow retry with alternative gateway
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            List of alternative gateways
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            return []
        
        # Get enabled gateways for the currency
        available = await self.gateway_manager.get_enabled_gateways_for_currency(
            transaction.currency
        )
        
        # Exclude the current/failed gateway
        return [g for g in available if g.provider != transaction.gateway_provider]
    
    async def verify_payment(
        self, 
        transaction_id: uuid.UUID
    ) -> PaymentTransaction:
        """Verify payment status with gateway.
        
        For PayPal, this will also capture the order if it's approved.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Updated transaction
        """
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction or not transaction.gateway_payment_id:
            raise ValueError(f"Transaction {transaction_id} not found or not processed")
        
        # If transaction is already completed, just return it
        if transaction.status == PaymentStatus.COMPLETED.value:
            logger.info(f"Transaction {transaction_id} is already completed")
            return transaction
        
        config = await self.gateway_repo.get_config_by_provider(
            transaction.gateway_provider
        )
        if not config:
            raise ValueError(f"Gateway {transaction.gateway_provider} not found")
        
        gateway = PaymentGatewayFactory.create(config)
        
        # For PayPal, we need to capture the order after user approval
        if transaction.gateway_provider == "paypal":
            from app.modules.payment_gateway.gateways.paypal import PayPalGateway
            if isinstance(gateway, PayPalGateway):
                # First check order status
                verification = await gateway.verify_payment(transaction.gateway_payment_id)
                
                # If order is already completed, no need to capture
                if verification.status == PaymentStatus.COMPLETED.value:
                    return await self._update_transaction_from_verification(
                        transaction_id, config, transaction, verification
                    )
                
                # If order is approved but not captured, capture it
                if verification.status == PaymentStatus.PENDING.value:
                    capture_result = await gateway.capture_order(transaction.gateway_payment_id)
                    if capture_result.status == PaymentStatus.COMPLETED.value:
                        verification.status = PaymentStatus.COMPLETED.value
                        verification.gateway_response = capture_result.gateway_response
                    elif capture_result.status == PaymentStatus.FAILED.value:
                        # Don't mark as failed immediately - check order status again
                        recheck = await gateway.verify_payment(transaction.gateway_payment_id)
                        if recheck.status == PaymentStatus.COMPLETED.value:
                            verification.status = PaymentStatus.COMPLETED.value
                            verification.gateway_response = recheck.gateway_response
                        else:
                            verification.status = PaymentStatus.FAILED.value
                        
                return await self._update_transaction_from_verification(
                    transaction_id, config, transaction, verification
                )
        
        verification = await gateway.verify_payment(transaction.gateway_payment_id)
        
        return await self._update_transaction_from_verification(
            transaction_id, config, transaction, verification
        )
    
    async def verify_paypal_by_order_id(
        self,
        paypal_order_id: str
    ) -> PaymentTransaction:
        """Verify and capture PayPal payment by order ID.
        
        This is called when user returns from PayPal with the order token.
        
        Args:
            paypal_order_id: PayPal order ID (token parameter from return URL)
            
        Returns:
            Updated transaction
        """
        # Find transaction by PayPal order ID
        transaction = await self.transaction_repo.get_transaction_by_gateway_id(
            paypal_order_id
        )
        
        if not transaction:
            raise ValueError(f"Transaction with PayPal order {paypal_order_id} not found")
        
        if transaction.gateway_provider != "paypal":
            raise ValueError(f"Transaction is not a PayPal payment")
        
        # Use the standard verify_payment which handles PayPal capture
        return await self.verify_payment(transaction.id)
    
    async def verify_by_gateway_id(
        self,
        gateway_payment_id: str
    ) -> PaymentTransaction:
        """Verify payment by gateway payment ID.
        
        This is a generic method that works for Stripe (session_id), 
        Xendit (invoice_id), etc.
        
        Args:
            gateway_payment_id: Gateway-specific payment ID
            
        Returns:
            Updated transaction
        """
        # Find transaction by gateway payment ID
        transaction = await self.transaction_repo.get_transaction_by_gateway_id(
            gateway_payment_id
        )
        
        if not transaction:
            raise ValueError(f"Transaction with gateway ID {gateway_payment_id} not found")
        
        # Use the standard verify_payment
        return await self.verify_payment(transaction.id)
    
    async def _update_transaction_from_verification(
        self,
        transaction_id: uuid.UUID,
        config: PaymentGatewayConfig,
        transaction: PaymentTransaction,
        verification,
    ) -> PaymentTransaction:
        """Update transaction based on verification result."""
        # Update transaction status
        if verification.status == PaymentStatus.COMPLETED.value:
            await self.transaction_repo.mark_completed(
                transaction_id,
                gateway_payment_id=transaction.gateway_payment_id,
                payment_method=verification.payment_method,
                gateway_response=verification.gateway_response,
            )
            # Record successful transaction in statistics
            await self.stats_repo.record_transaction(
                config.provider, 
                transaction.amount, 
                success=True
            )
            
            # Create or update subscription based on payment metadata
            try:
                await self._activate_subscription_from_payment(transaction)
            except Exception as e:
                logger.error(f"Failed to activate subscription for transaction {transaction_id}: {e}")
            
        elif verification.status == PaymentStatus.FAILED.value:
            await self.transaction_repo.mark_failed(
                transaction_id,
                error_message="Payment verification failed",
            )
            # Record failed transaction in statistics
            await self.stats_repo.record_transaction(
                config.provider, 
                transaction.amount, 
                success=False
            )
        else:
            await self.transaction_repo.update_transaction(
                transaction_id,
                status=verification.status,
                gateway_response=verification.gateway_response,
            )
        
        return await self.transaction_repo.get_transaction(transaction_id)
    
    async def _activate_subscription_from_payment(
        self,
        transaction: PaymentTransaction
    ) -> None:
        """Create or update subscription after successful payment.
        
        Args:
            transaction: Completed payment transaction
        """
        from datetime import timedelta
        from sqlalchemy import select
        from app.modules.billing.models import Subscription, SubscriptionStatus
        
        logger.info(f"Activating subscription for transaction {transaction.id}")
        logger.info(f"Transaction metadata: {transaction.payment_metadata}")
        logger.info(f"Transaction description: {transaction.description}")
        
        # Get plan info from transaction metadata
        metadata = transaction.payment_metadata or {}
        plan_slug = metadata.get("plan_slug")
        billing_cycle = metadata.get("billing_cycle")
        
        # If billing_cycle not in metadata, try to detect from description
        if not billing_cycle:
            description = transaction.description or ""
            if "yearly" in description.lower() or "annual" in description.lower():
                billing_cycle = "yearly"
            else:
                billing_cycle = "monthly"
            logger.info(f"Detected billing_cycle from description: {billing_cycle}")
        
        logger.info(f"Plan slug: {plan_slug}, Billing cycle: {billing_cycle}")
        
        if not plan_slug:
            logger.warning(f"No plan_slug in transaction {transaction.id} metadata: {metadata}")
            return
        
        # Calculate subscription period
        now = datetime.utcnow()
        if billing_cycle == "yearly":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        # Check if user already has a subscription
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == transaction.user_id)
        )
        existing_sub = result.scalar_one_or_none()
        
        subscription_id = None
        
        try:
            if existing_sub:
                # Update existing subscription
                existing_sub.plan_tier = plan_slug
                existing_sub.billing_cycle = billing_cycle
                existing_sub.status = SubscriptionStatus.ACTIVE.value
                existing_sub.current_period_start = now
                existing_sub.current_period_end = period_end
                existing_sub.cancel_at_period_end = False
                existing_sub.canceled_at = None
                subscription_id = existing_sub.id
                logger.info(f"Updated subscription {subscription_id} for user {transaction.user_id} to plan {plan_slug} ({billing_cycle})")
            else:
                # Create new subscription
                new_sub = Subscription(
                    user_id=transaction.user_id,
                    plan_tier=plan_slug,
                    billing_cycle=billing_cycle,
                    status=SubscriptionStatus.ACTIVE.value,
                    current_period_start=now,
                    current_period_end=period_end,
                )
                self.session.add(new_sub)
                await self.session.flush()  # Get the ID
                subscription_id = new_sub.id
                logger.info(f"Created subscription {subscription_id} for user {transaction.user_id} with plan {plan_slug} ({billing_cycle})")
            
            # Update transaction with subscription_id
            if subscription_id:
                logger.info(f"Updating transaction {transaction.id} with subscription_id {subscription_id}")
                await self.transaction_repo.update_transaction(
                    transaction.id,
                    subscription_id=subscription_id
                )
                logger.info(f"Successfully linked transaction to subscription")
        except Exception as e:
            logger.error(f"Error in subscription activation: {e}")
            raise
    
    async def handle_webhook(
        self,
        provider: str,
        payload: dict,
        signature: str,
    ) -> Optional[PaymentTransaction]:
        """Handle webhook callback from a gateway.
        
        Args:
            provider: Gateway provider
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            Updated transaction or None
        """
        config = await self.gateway_repo.get_config_by_provider(provider)
        if not config:
            logger.error(f"Webhook received for unknown provider: {provider}")
            return None
        
        gateway = PaymentGatewayFactory.create(config)
        result = await gateway.handle_webhook(payload, signature)
        
        if not result.is_valid:
            logger.error(f"Invalid webhook from {provider}: {result.error_message}")
            return None
        
        if not result.payment_id:
            logger.info(f"Webhook from {provider} has no payment_id")
            return None
        
        # Try to find transaction by gateway payment ID or order ID
        transaction = await self.transaction_repo.get_transaction_by_gateway_id(
            result.payment_id
        )
        
        if not transaction:
            # Try as UUID (our order_id)
            try:
                tx_id = uuid.UUID(result.payment_id)
                transaction = await self.transaction_repo.get_transaction(tx_id)
            except (ValueError, TypeError):
                pass
        
        if not transaction:
            logger.warning(f"Transaction not found for webhook payment_id: {result.payment_id}")
            return None
        
        # Update transaction based on webhook status
        if result.status == PaymentStatus.COMPLETED.value:
            await self.transaction_repo.mark_completed(
                transaction.id,
                gateway_payment_id=result.payment_id,
                gateway_response={"webhook_event": result.event_type},
            )
            await self.stats_repo.record_transaction(
                provider, 
                transaction.amount, 
                success=True
            )
        elif result.status == PaymentStatus.FAILED.value:
            await self.transaction_repo.mark_failed(
                transaction.id,
                error_message=f"Payment failed via webhook: {result.event_type}",
            )
            await self.stats_repo.record_transaction(
                provider, 
                transaction.amount, 
                success=False
            )
        elif result.status:
            await self.transaction_repo.update_transaction(
                transaction.id,
                status=result.status,
            )
        
        return await self.transaction_repo.get_transaction(transaction.id)
    
    async def get_transaction(
        self, 
        transaction_id: uuid.UUID
    ) -> Optional[PaymentTransaction]:
        """Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction or None
        """
        return await self.transaction_repo.get_transaction(transaction_id)
    
    async def get_user_transactions(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentTransaction]:
        """Get transactions for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of transactions
            offset: Offset for pagination
            
        Returns:
            List of transactions
        """
        return await self.transaction_repo.get_user_transactions(
            user_id, limit, offset
        )
