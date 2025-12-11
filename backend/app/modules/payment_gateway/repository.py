"""Repository for Payment Gateway data access.

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment_gateway.models import (
    PaymentGatewayConfig,
    PaymentTransaction,
    GatewayStatistics,
    GatewayProvider,
    PaymentStatus,
    GATEWAY_DEFAULTS,
)


class PaymentGatewayRepository:
    """Repository for payment gateway configuration operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_configs(self) -> list[PaymentGatewayConfig]:
        """Get all gateway configurations."""
        result = await self.session.execute(
            select(PaymentGatewayConfig).order_by(PaymentGatewayConfig.provider)
        )
        return list(result.scalars().all())
    
    async def get_enabled_configs(self) -> list[PaymentGatewayConfig]:
        """Get all enabled gateway configurations."""
        result = await self.session.execute(
            select(PaymentGatewayConfig)
            .where(PaymentGatewayConfig.is_enabled == True)
            .order_by(PaymentGatewayConfig.provider)
        )
        return list(result.scalars().all())
    
    async def get_config_by_provider(
        self, 
        provider: str
    ) -> Optional[PaymentGatewayConfig]:
        """Get gateway configuration by provider."""
        result = await self.session.execute(
            select(PaymentGatewayConfig)
            .where(PaymentGatewayConfig.provider == provider)
        )
        return result.scalar_one_or_none()
    
    async def get_default_config(self) -> Optional[PaymentGatewayConfig]:
        """Get the default gateway configuration."""
        result = await self.session.execute(
            select(PaymentGatewayConfig)
            .where(
                and_(
                    PaymentGatewayConfig.is_enabled == True,
                    PaymentGatewayConfig.is_default == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_config(
        self, 
        provider: str,
        display_name: str,
        api_key_encrypted: str,
        api_secret_encrypted: str,
        webhook_secret_encrypted: Optional[str] = None,
        sandbox_mode: bool = True,
        **kwargs
    ) -> PaymentGatewayConfig:
        """Create a new gateway configuration."""
        defaults = GATEWAY_DEFAULTS.get(provider, {})
        
        config = PaymentGatewayConfig(
            provider=provider,
            display_name=display_name or defaults.get("display_name", provider),
            api_key_encrypted=api_key_encrypted,
            api_secret_encrypted=api_secret_encrypted,
            webhook_secret_encrypted=webhook_secret_encrypted,
            sandbox_mode=sandbox_mode,
            supported_currencies=defaults.get("supported_currencies", []),
            supported_payment_methods=defaults.get("supported_payment_methods", []),
            transaction_fee_percent=kwargs.get("transaction_fee_percent", defaults.get("transaction_fee_percent", 0)),
            fixed_fee=kwargs.get("fixed_fee", defaults.get("fixed_fee", 0)),
            min_amount=kwargs.get("min_amount", defaults.get("min_amount", 0)),
            max_amount=kwargs.get("max_amount", defaults.get("max_amount")),
            is_enabled=False,
            is_default=False,
        )
        
        self.session.add(config)
        await self.session.flush()
        return config
    
    async def update_config(
        self, 
        provider: str, 
        **kwargs
    ) -> Optional[PaymentGatewayConfig]:
        """Update gateway configuration."""
        config = await self.get_config_by_provider(provider)
        if not config:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        
        await self.session.flush()
        return config
    
    async def enable_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Enable a gateway."""
        return await self.update_config(provider, is_enabled=True)
    
    async def disable_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Disable a gateway."""
        return await self.update_config(provider, is_enabled=False, is_default=False)
    
    async def set_default_gateway(self, provider: str) -> Optional[PaymentGatewayConfig]:
        """Set a gateway as default (clears other defaults)."""
        # Clear existing default
        await self.session.execute(
            update(PaymentGatewayConfig)
            .where(PaymentGatewayConfig.is_default == True)
            .values(is_default=False)
        )
        
        # Set new default
        return await self.update_config(provider, is_default=True, is_enabled=True)
    
    async def initialize_default_configs(self) -> list[PaymentGatewayConfig]:
        """Initialize default gateway configurations (without credentials)."""
        configs = []
        for provider in GatewayProvider:
            existing = await self.get_config_by_provider(provider.value)
            if not existing:
                defaults = GATEWAY_DEFAULTS.get(provider.value, {})
                config = PaymentGatewayConfig(
                    provider=provider.value,
                    display_name=defaults.get("display_name", provider.value),
                    supported_currencies=defaults.get("supported_currencies", []),
                    supported_payment_methods=defaults.get("supported_payment_methods", []),
                    transaction_fee_percent=defaults.get("transaction_fee_percent", 0),
                    fixed_fee=defaults.get("fixed_fee", 0),
                    min_amount=defaults.get("min_amount", 0),
                    max_amount=defaults.get("max_amount"),
                    is_enabled=False,
                    is_default=False,
                    sandbox_mode=True,
                )
                self.session.add(config)
                configs.append(config)
        
        await self.session.flush()
        return configs


class PaymentTransactionRepository:
    """Repository for payment transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_transaction(
        self,
        user_id: uuid.UUID,
        gateway_provider: str,
        amount: float,
        currency: str,
        description: str,
        subscription_id: Optional[uuid.UUID] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> PaymentTransaction:
        """Create a new payment transaction."""
        transaction = PaymentTransaction(
            user_id=user_id,
            subscription_id=subscription_id,
            gateway_provider=gateway_provider,
            amount=amount,
            currency=currency,
            description=description,
            status=PaymentStatus.PENDING.value,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_metadata=metadata,
        )
        
        self.session.add(transaction)
        await self.session.flush()
        return transaction
    
    async def get_transaction(
        self, 
        transaction_id: uuid.UUID
    ) -> Optional[PaymentTransaction]:
        """Get transaction by ID."""
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_transaction_by_gateway_id(
        self, 
        gateway_payment_id: str
    ) -> Optional[PaymentTransaction]:
        """Get transaction by gateway payment ID."""
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.gateway_payment_id == gateway_payment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_transactions(
        self, 
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentTransaction]:
        """Get transactions for a user."""
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.user_id == user_id)
            .order_by(PaymentTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def update_transaction(
        self, 
        transaction_id: uuid.UUID, 
        **kwargs
    ) -> Optional[PaymentTransaction]:
        """Update transaction."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(transaction, key):
                setattr(transaction, key, value)
        
        await self.session.flush()
        return transaction
    
    async def mark_completed(
        self, 
        transaction_id: uuid.UUID,
        gateway_payment_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        gateway_response: Optional[dict] = None,
    ) -> Optional[PaymentTransaction]:
        """Mark transaction as completed."""
        return await self.update_transaction(
            transaction_id,
            status=PaymentStatus.COMPLETED.value,
            gateway_payment_id=gateway_payment_id,
            payment_method=payment_method,
            gateway_response=gateway_response,
            completed_at=datetime.utcnow(),
        )
    
    async def mark_failed(
        self, 
        transaction_id: uuid.UUID,
        error_message: str,
        error_code: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        """Mark transaction as failed."""
        return await self.update_transaction(
            transaction_id,
            status=PaymentStatus.FAILED.value,
            error_message=error_message,
            error_code=error_code,
        )
    
    async def increment_attempt(
        self, 
        transaction_id: uuid.UUID,
        previous_gateway: str,
    ) -> Optional[PaymentTransaction]:
        """Increment attempt count for retry."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return None
        
        transaction.attempt_count += 1
        transaction.previous_gateway = previous_gateway
        await self.session.flush()
        return transaction


class GatewayStatisticsRepository:
    """Repository for gateway statistics operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_statistics(self, provider: str) -> Optional[GatewayStatistics]:
        """Get statistics for a gateway."""
        result = await self.session.execute(
            select(GatewayStatistics)
            .where(GatewayStatistics.provider == provider)
        )
        return result.scalar_one_or_none()
    
    async def get_all_statistics(self) -> list[GatewayStatistics]:
        """Get statistics for all gateways."""
        result = await self.session.execute(
            select(GatewayStatistics).order_by(GatewayStatistics.provider)
        )
        return list(result.scalars().all())
    
    async def get_or_create_statistics(self, provider: str) -> GatewayStatistics:
        """Get or create statistics for a gateway."""
        stats = await self.get_statistics(provider)
        if not stats:
            stats = GatewayStatistics(provider=provider)
            self.session.add(stats)
            await self.session.flush()
        return stats
    
    async def record_transaction(
        self, 
        provider: str, 
        amount: float, 
        success: bool
    ) -> GatewayStatistics:
        """Record a transaction in statistics."""
        stats = await self.get_or_create_statistics(provider)
        stats.record_transaction(amount, success)
        await self.session.flush()
        return stats
    
    async def initialize_all_statistics(self) -> list[GatewayStatistics]:
        """Initialize statistics for all gateway providers."""
        stats_list = []
        for provider in GatewayProvider:
            stats = await self.get_or_create_statistics(provider.value)
            stats_list.append(stats)
        return stats_list
