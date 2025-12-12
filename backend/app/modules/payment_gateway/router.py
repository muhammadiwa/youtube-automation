"""Payment Gateway Admin Router.

Provides API endpoints for:
- CRUD operations for gateway configuration (Requirements: 30.6)
- Credential validation endpoint (Requirements: 30.7)
- Statistics endpoint per gateway (Requirements: 30.6)
- Enable/disable gateway (Requirements: 30.2)

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.payment_gateway.service import (
    GatewayManagerService,
    PaymentService,
)
from app.modules.payment_gateway.schemas import (
    GatewayProvider,
    GatewayConfigCreate,
    GatewayConfigUpdate,
    GatewayConfigResponse,
    GatewayPublicInfo,
    GatewayStatisticsResponse,
    AllGatewayStatisticsResponse,
    ValidationResult,
    EnableDisableResponse,
    CreatePaymentRequest,
    PaymentResponse,
    PaymentStatusResponse,
    PaymentTransactionResponse,
    RetryPaymentRequest,
)

# Admin router for gateway management
admin_router = APIRouter(prefix="/admin/payment-gateways", tags=["Payment Gateway Admin"])

# Public router for payment processing
payment_router = APIRouter(prefix="/payments", tags=["Payments"])


# ==================== Admin Endpoints ====================

@admin_router.get("", response_model=list[GatewayConfigResponse])
async def list_all_gateways(
    session: AsyncSession = Depends(get_session),
):
    """List all payment gateway configurations.
    
    Requirements: 30.6 - Gateway dashboard
    
    Returns all configured gateways with their status and settings.
    Credentials are not exposed.
    """
    service = GatewayManagerService(session)
    configs = await service.get_all_gateways()
    
    return [
        GatewayConfigResponse(
            id=c.id,
            provider=c.provider,
            display_name=c.display_name,
            is_enabled=c.is_enabled,
            is_default=c.is_default,
            sandbox_mode=c.sandbox_mode,
            supported_currencies=c.supported_currencies,
            supported_payment_methods=c.supported_payment_methods,
            transaction_fee_percent=c.transaction_fee_percent,
            fixed_fee=c.fixed_fee,
            min_amount=c.min_amount,
            max_amount=c.max_amount,
            has_credentials=c.has_credentials(),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


@admin_router.get("/{provider}", response_model=GatewayConfigResponse)
async def get_gateway(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific gateway configuration.
    
    Requirements: 30.6 - Gateway dashboard
    """
    service = GatewayManagerService(session)
    config = await service.get_gateway(provider.value)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway {provider.value} not found",
        )
    
    return GatewayConfigResponse(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        is_enabled=config.is_enabled,
        is_default=config.is_default,
        sandbox_mode=config.sandbox_mode,
        supported_currencies=config.supported_currencies,
        supported_payment_methods=config.supported_payment_methods,
        transaction_fee_percent=config.transaction_fee_percent,
        fixed_fee=config.fixed_fee,
        min_amount=config.min_amount,
        max_amount=config.max_amount,
        has_credentials=config.has_credentials(),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@admin_router.post("/{provider}/configure", response_model=GatewayConfigResponse)
async def configure_gateway(
    provider: GatewayProvider,
    data: GatewayConfigCreate,
    session: AsyncSession = Depends(get_session),
):
    """Configure gateway credentials.
    
    Requirements: 30.4 - Encrypted credentials via KMS
    Requirements: 30.7 - Validate API keys before saving
    
    Creates or updates gateway configuration with encrypted credentials.
    """
    service = GatewayManagerService(session)
    
    config = await service.configure_gateway(
        provider=provider.value,
        api_key=data.api_key,
        api_secret=data.api_secret,
        webhook_secret=data.webhook_secret,
        sandbox_mode=data.sandbox_mode,
        display_name=data.display_name,
        transaction_fee_percent=data.transaction_fee_percent,
        fixed_fee=data.fixed_fee,
        min_amount=data.min_amount,
        max_amount=data.max_amount,
    )
    
    await session.commit()
    
    return GatewayConfigResponse(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        is_enabled=config.is_enabled,
        is_default=config.is_default,
        sandbox_mode=config.sandbox_mode,
        supported_currencies=config.supported_currencies,
        supported_payment_methods=config.supported_payment_methods,
        transaction_fee_percent=config.transaction_fee_percent,
        fixed_fee=config.fixed_fee,
        min_amount=config.min_amount,
        max_amount=config.max_amount,
        has_credentials=config.has_credentials(),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@admin_router.patch("/{provider}", response_model=GatewayConfigResponse)
async def update_gateway(
    provider: GatewayProvider,
    data: GatewayConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update gateway configuration.
    
    Requirements: 30.6 - Gateway configuration management
    
    Updates non-credential settings. Use /configure endpoint for credentials.
    """
    service = GatewayManagerService(session)
    
    config = await service.get_gateway(provider.value)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway {provider.value} not found",
        )
    
    # Build update kwargs
    update_kwargs = {}
    if data.display_name is not None:
        update_kwargs["display_name"] = data.display_name
    if data.sandbox_mode is not None:
        update_kwargs["sandbox_mode"] = data.sandbox_mode
    if data.transaction_fee_percent is not None:
        update_kwargs["transaction_fee_percent"] = data.transaction_fee_percent
    if data.fixed_fee is not None:
        update_kwargs["fixed_fee"] = data.fixed_fee
    if data.min_amount is not None:
        update_kwargs["min_amount"] = data.min_amount
    if data.max_amount is not None:
        update_kwargs["max_amount"] = data.max_amount
    
    # Handle credential updates if provided
    if data.api_key or data.api_secret:
        if not (data.api_key and data.api_secret):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both api_key and api_secret must be provided together",
            )
        config = await service.configure_gateway(
            provider=provider.value,
            api_key=data.api_key,
            api_secret=data.api_secret,
            webhook_secret=data.webhook_secret,
            **update_kwargs,
        )
    elif update_kwargs:
        from app.modules.payment_gateway.repository import PaymentGatewayRepository
        repo = PaymentGatewayRepository(session)
        config = await repo.update_config(provider.value, **update_kwargs)
    
    await session.commit()
    
    return GatewayConfigResponse(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        is_enabled=config.is_enabled,
        is_default=config.is_default,
        sandbox_mode=config.sandbox_mode,
        supported_currencies=config.supported_currencies,
        supported_payment_methods=config.supported_payment_methods,
        transaction_fee_percent=config.transaction_fee_percent,
        fixed_fee=config.fixed_fee,
        min_amount=config.min_amount,
        max_amount=config.max_amount,
        has_credentials=config.has_credentials(),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@admin_router.post("/{provider}/enable", response_model=EnableDisableResponse)
async def enable_gateway(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Enable a payment gateway.
    
    Requirements: 30.2 - Enable gateway dynamically without system restart
    
    Gateway must have credentials configured before enabling.
    """
    service = GatewayManagerService(session)
    
    try:
        config = await service.enable_gateway(provider.value)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {provider.value} not found",
            )
        
        await session.commit()
        
        return EnableDisableResponse(
            provider=provider.value,
            is_enabled=True,
            message=f"Gateway {provider.value} enabled successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@admin_router.post("/{provider}/disable", response_model=EnableDisableResponse)
async def disable_gateway(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Disable a payment gateway.
    
    Requirements: 30.2 - Disable gateway dynamically without system restart
    """
    service = GatewayManagerService(session)
    
    config = await service.disable_gateway(provider.value)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gateway {provider.value} not found",
        )
    
    await session.commit()
    
    return EnableDisableResponse(
        provider=provider.value,
        is_enabled=False,
        message=f"Gateway {provider.value} disabled successfully",
    )


@admin_router.post("/{provider}/set-default", response_model=GatewayConfigResponse)
async def set_default_gateway(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Set a gateway as the default.
    
    Requirements: 30.2 - Gateway configuration management
    
    The gateway will be automatically enabled if not already.
    """
    service = GatewayManagerService(session)
    
    try:
        config = await service.set_default_gateway(provider.value)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {provider.value} not found",
            )
        
        await session.commit()
        
        return GatewayConfigResponse(
            id=config.id,
            provider=config.provider,
            display_name=config.display_name,
            is_enabled=config.is_enabled,
            is_default=config.is_default,
            sandbox_mode=config.sandbox_mode,
            supported_currencies=config.supported_currencies,
            supported_payment_methods=config.supported_payment_methods,
            transaction_fee_percent=config.transaction_fee_percent,
            fixed_fee=config.fixed_fee,
            min_amount=config.min_amount,
            max_amount=config.max_amount,
            has_credentials=config.has_credentials(),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@admin_router.post("/{provider}/validate", response_model=ValidationResult)
async def validate_gateway_credentials(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Validate gateway API credentials.
    
    Requirements: 30.7 - Validate API keys before saving
    
    Tests the configured credentials against the gateway's API.
    """
    service = GatewayManagerService(session)
    result = await service.validate_gateway_credentials(provider.value)
    return result


@admin_router.get("/{provider}/statistics", response_model=GatewayStatisticsResponse)
async def get_gateway_statistics(
    provider: GatewayProvider,
    session: AsyncSession = Depends(get_session),
):
    """Get statistics for a specific gateway.
    
    Requirements: 30.6 - Transaction statistics, success rates, health status
    """
    service = GatewayManagerService(session)
    stats = await service.get_gateway_statistics(provider.value)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statistics for gateway {provider.value} not found",
        )
    
    return GatewayStatisticsResponse(
        provider=stats.provider,
        total_transactions=stats.total_transactions,
        successful_transactions=stats.successful_transactions,
        failed_transactions=stats.failed_transactions,
        success_rate=stats.success_rate,
        total_volume=stats.total_volume,
        average_transaction=stats.average_transaction,
        health_status=stats.health_status,
        last_transaction_at=stats.last_transaction_at,
        transactions_24h=stats.transactions_24h,
        success_rate_24h=stats.success_rate_24h,
    )


@admin_router.get("/statistics/all", response_model=AllGatewayStatisticsResponse)
async def get_all_gateway_statistics(
    session: AsyncSession = Depends(get_session),
):
    """Get statistics for all gateways.
    
    Requirements: 30.6 - Gateway dashboard with statistics
    """
    service = GatewayManagerService(session)
    all_stats = await service.get_all_gateway_statistics()
    
    gateway_stats = [
        GatewayStatisticsResponse(
            provider=s.provider,
            total_transactions=s.total_transactions,
            successful_transactions=s.successful_transactions,
            failed_transactions=s.failed_transactions,
            success_rate=s.success_rate,
            total_volume=s.total_volume,
            average_transaction=s.average_transaction,
            health_status=s.health_status,
            last_transaction_at=s.last_transaction_at,
            transactions_24h=s.transactions_24h,
            success_rate_24h=s.success_rate_24h,
        )
        for s in all_stats
    ]
    
    total_volume = sum(s.total_volume for s in all_stats)
    total_transactions = sum(s.total_transactions for s in all_stats)
    total_successful = sum(s.successful_transactions for s in all_stats)
    overall_success_rate = (
        (total_successful / total_transactions * 100) 
        if total_transactions > 0 else 0.0
    )
    
    return AllGatewayStatisticsResponse(
        gateways=gateway_stats,
        total_volume=total_volume,
        total_transactions=total_transactions,
        overall_success_rate=overall_success_rate,
    )


@admin_router.post("/initialize", response_model=list[GatewayConfigResponse])
async def initialize_default_gateways(
    session: AsyncSession = Depends(get_session),
):
    """Initialize default gateway configurations.
    
    Creates placeholder configurations for all supported providers.
    Useful for initial setup.
    """
    service = GatewayManagerService(session)
    configs = await service.initialize_default_gateways()
    await session.commit()
    
    return [
        GatewayConfigResponse(
            id=c.id,
            provider=c.provider,
            display_name=c.display_name,
            is_enabled=c.is_enabled,
            is_default=c.is_default,
            sandbox_mode=c.sandbox_mode,
            supported_currencies=c.supported_currencies,
            supported_payment_methods=c.supported_payment_methods,
            transaction_fee_percent=c.transaction_fee_percent,
            fixed_fee=c.fixed_fee,
            min_amount=c.min_amount,
            max_amount=c.max_amount,
            has_credentials=c.has_credentials(),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


# ==================== Public Payment Endpoints ====================

@payment_router.get("/gateways", response_model=list[GatewayPublicInfo])
async def list_available_gateways(
    currency: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """List available payment gateways.
    
    Requirements: 30.3 - Display only enabled payment gateways
    
    Args:
        currency: Optional currency filter. If not provided, returns all enabled gateways.
    
    Returns public information about enabled gateways.
    """
    service = PaymentService(session)
    
    if currency:
        configs = await service.get_available_gateways(currency)
    else:
        # Get all enabled gateways
        configs = await service.gateway_manager.get_enabled_gateways()
    
    return [
        GatewayPublicInfo(
            provider=c.provider,
            display_name=c.display_name,
            supported_currencies=c.supported_currencies,
            supported_payment_methods=c.supported_payment_methods,
            min_amount=c.min_amount,
            max_amount=c.max_amount,
            is_default=c.is_default,
        )
        for c in configs
    ]


@payment_router.post("", response_model=PaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    user_id: uuid.UUID = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_session),
):
    """Create a new payment.
    
    Requirements: 30.4 - Process payment through gateway
    
    Creates a payment transaction and processes it through the selected gateway.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating payment: user_id={user_id}, amount={data.amount}, currency={data.currency}, gateway={data.preferred_gateway}")
    
    service = PaymentService(session)
    
    try:
        # Create transaction
        transaction = await service.create_payment(
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            gateway_provider=data.preferred_gateway.value if data.preferred_gateway else None,
            subscription_id=data.subscription_id,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata=data.metadata,
        )
        
        # Process payment
        transaction = await service.process_payment(transaction.id)
        await session.commit()
        
        return PaymentResponse(
            payment_id=transaction.id,
            gateway_provider=transaction.gateway_provider,
            status=transaction.status,
            checkout_url=transaction.checkout_url,
            error_message=transaction.error_message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


from pydantic import BaseModel


class PayPalVerifyRequest(BaseModel):
    order_id: str


class CurrencyConversionResponse(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    exchange_rate: float


# ==================== Currency Conversion ====================

@payment_router.get("/currency/convert")
async def convert_currency_endpoint(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "IDR",
):
    """Convert amount between currencies.
    
    Useful for displaying prices in local currency when using gateways
    that only support specific currencies (e.g., Midtrans for IDR).
    
    Args:
        amount: Amount to convert
        from_currency: Source currency (default: USD)
        to_currency: Target currency (default: IDR)
        
    Returns:
        Converted amount and exchange rate
    """
    from app.modules.payment_gateway.currency import convert_currency, get_exchange_rate
    
    rate = await get_exchange_rate(from_currency.upper(), to_currency.upper())
    converted = await convert_currency(amount, from_currency.upper(), to_currency.upper())
    
    return CurrencyConversionResponse(
        from_currency=from_currency.upper(),
        to_currency=to_currency.upper(),
        amount=amount,
        converted_amount=converted,
        exchange_rate=rate,
    )


@payment_router.get("/currency/rate")
async def get_exchange_rate_endpoint(
    from_currency: str = "USD",
    to_currency: str = "IDR",
):
    """Get exchange rate between currencies.
    
    Args:
        from_currency: Source currency (default: USD)
        to_currency: Target currency (default: IDR)
        
    Returns:
        Exchange rate
    """
    from app.modules.payment_gateway.currency import get_exchange_rate
    
    rate = await get_exchange_rate(from_currency.upper(), to_currency.upper())
    
    return {
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "rate": rate,
    }


# ==================== IMPORTANT: Specific routes MUST be defined BEFORE parameterized routes ====================

@payment_router.get("/history", response_model=list[PaymentTransactionResponse])
async def get_payment_history(
    user_id: uuid.UUID = Header(..., alias="X-User-ID"),
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """Get payment history for a user.
    
    Returns list of payment transactions for the authenticated user.
    """
    service = PaymentService(session)
    transactions = await service.get_user_transactions(user_id, limit, offset)
    
    return [
        PaymentTransactionResponse(
            id=tx.id,
            user_id=tx.user_id,
            subscription_id=tx.subscription_id,
            gateway_provider=tx.gateway_provider,
            gateway_payment_id=tx.gateway_payment_id,
            amount=tx.amount,
            currency=tx.currency,
            status=tx.status,
            payment_method=tx.payment_method,
            description=tx.description,
            error_message=tx.error_message,
            attempt_count=tx.attempt_count,
            created_at=tx.created_at,
            completed_at=tx.completed_at,
        )
        for tx in transactions
    ]


@payment_router.post("/paypal/verify", response_model=PaymentTransactionResponse)
async def verify_paypal_payment(
    data: PayPalVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify and capture PayPal payment by order ID.
    
    This endpoint is called when user returns from PayPal approval page.
    PayPal returns with 'token' parameter which is the order ID.
    
    This will:
    1. Find the transaction by PayPal order ID (gateway_payment_id)
    2. Verify the order status with PayPal
    3. Capture the order if approved
    4. Update transaction status
    """
    service = PaymentService(session)
    
    try:
        transaction = await service.verify_paypal_by_order_id(data.order_id)
        await session.commit()
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            gateway_provider=transaction.gateway_provider,
            gateway_payment_id=transaction.gateway_payment_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            payment_method=transaction.payment_method,
            description=transaction.description,
            error_message=transaction.error_message,
            attempt_count=transaction.attempt_count,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class StripeVerifyRequest(BaseModel):
    session_id: str


@payment_router.post("/stripe/verify", response_model=PaymentTransactionResponse)
async def verify_stripe_payment(
    data: StripeVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify Stripe payment by session ID.
    
    This endpoint is called when user returns from Stripe Checkout.
    Stripe redirects with session_id in the success URL.
    """
    service = PaymentService(session)
    
    try:
        transaction = await service.verify_by_gateway_id(data.session_id)
        await session.commit()
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            gateway_provider=transaction.gateway_provider,
            gateway_payment_id=transaction.gateway_payment_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            payment_method=transaction.payment_method,
            description=transaction.description,
            error_message=transaction.error_message,
            attempt_count=transaction.attempt_count,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class MidtransVerifyRequest(BaseModel):
    order_id: str


@payment_router.post("/midtrans/verify", response_model=PaymentTransactionResponse)
async def verify_midtrans_payment(
    data: MidtransVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify Midtrans payment by order ID.
    
    This endpoint is called when user returns from Midtrans Snap.
    Midtrans redirects with order_id in the finish URL.
    """
    service = PaymentService(session)
    
    try:
        # For Midtrans, order_id is our transaction ID
        transaction_id = uuid.UUID(data.order_id)
        transaction = await service.verify_payment(transaction_id)
        await session.commit()
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            gateway_provider=transaction.gateway_provider,
            gateway_payment_id=transaction.gateway_payment_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            payment_method=transaction.payment_method,
            description=transaction.description,
            error_message=transaction.error_message,
            attempt_count=transaction.attempt_count,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class XenditVerifyRequest(BaseModel):
    invoice_id: str


@payment_router.post("/xendit/verify", response_model=PaymentTransactionResponse)
async def verify_xendit_payment(
    data: XenditVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify Xendit payment by invoice ID.
    
    This endpoint is called when user returns from Xendit Invoice.
    Xendit redirects with invoice_id in the success URL.
    """
    service = PaymentService(session)
    
    try:
        transaction = await service.verify_by_gateway_id(data.invoice_id)
        await session.commit()
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            gateway_provider=transaction.gateway_provider,
            gateway_payment_id=transaction.gateway_payment_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            payment_method=transaction.payment_method,
            description=transaction.description,
            error_message=transaction.error_message,
            attempt_count=transaction.attempt_count,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@payment_router.post("/{payment_id}/verify", response_model=PaymentTransactionResponse)
async def verify_payment(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Verify payment status with gateway.
    
    Requirements: 30.4 - Payment verification
    
    Checks the payment status directly with the gateway.
    """
    service = PaymentService(session)
    
    try:
        transaction = await service.verify_payment(payment_id)
        await session.commit()
        
        return PaymentTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            subscription_id=transaction.subscription_id,
            gateway_provider=transaction.gateway_provider,
            gateway_payment_id=transaction.gateway_payment_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            payment_method=transaction.payment_method,
            description=transaction.description,
            error_message=transaction.error_message,
            attempt_count=transaction.attempt_count,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@payment_router.get("/{payment_id}/alternatives", response_model=list[GatewayPublicInfo])
async def get_alternative_gateways(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get alternative gateways for a failed payment.
    
    Requirements: 30.5 - Allow retry with alternative gateway
    """
    service = PaymentService(session)
    configs = await service.get_alternative_gateways(payment_id)
    
    return [
        GatewayPublicInfo(
            provider=c.provider,
            display_name=c.display_name,
            supported_currencies=c.supported_currencies,
            supported_payment_methods=c.supported_payment_methods,
            min_amount=c.min_amount,
            max_amount=c.max_amount,
        )
        for c in configs
    ]


@payment_router.post("/{payment_id}/retry", response_model=PaymentResponse)
async def retry_payment(
    payment_id: uuid.UUID,
    data: RetryPaymentRequest,
    session: AsyncSession = Depends(get_session),
):
    """Retry a failed payment with an alternative gateway.
    
    Requirements: 30.5 - Retry with alternative gateway on failure
    """
    service = PaymentService(session)
    
    try:
        transaction = await service.retry_with_alternative_gateway(
            payment_id,
            data.alternative_gateway.value,
        )
        await session.commit()
        
        return PaymentResponse(
            payment_id=transaction.id,
            gateway_provider=transaction.gateway_provider,
            status=transaction.status,
            checkout_url=transaction.checkout_url,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Discount Code Endpoints (Public) ====================

from app.modules.payment_gateway.schemas import (
    ApplyDiscountCodeRequest,
    DiscountCodePublicResponse,
)


@payment_router.post("/discount-code/validate", response_model=DiscountCodePublicResponse)
async def validate_discount_code(
    data: ApplyDiscountCodeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Validate and calculate discount for a promo code.
    
    This is a public endpoint for users to validate discount codes during checkout.
    
    Args:
        data: Discount code, plan, and original amount
        
    Returns:
        Validation result with calculated discount amount
    """
    from sqlalchemy import select
    from app.modules.admin.models import DiscountCode
    
    # Find the discount code
    result = await session.execute(
        select(DiscountCode).where(DiscountCode.code == data.code.upper())
    )
    discount_code = result.scalar_one_or_none()
    
    if not discount_code:
        return DiscountCodePublicResponse(
            is_valid=False,
            message="Invalid discount code"
        )
    
    # Check if code is valid (active, within date range, usage limit)
    if not discount_code.is_valid():
        if not discount_code.is_active:
            return DiscountCodePublicResponse(
                is_valid=False,
                message="This discount code is no longer active"
            )
        if discount_code.usage_limit and discount_code.usage_count >= discount_code.usage_limit:
            return DiscountCodePublicResponse(
                is_valid=False,
                message="This discount code has reached its usage limit"
            )
        return DiscountCodePublicResponse(
            is_valid=False,
            message="This discount code has expired"
        )
    
    # Check plan applicability
    if data.plan and discount_code.applicable_plans:
        if data.plan.lower() not in [p.lower() for p in discount_code.applicable_plans]:
            return DiscountCodePublicResponse(
                is_valid=False,
                message=f"This discount code is not applicable to the {data.plan} plan"
            )
    
    # Calculate discount
    discount_amount = discount_code.calculate_discount(data.amount)
    final_amount = max(0, data.amount - discount_amount)
    
    return DiscountCodePublicResponse(
        is_valid=True,
        code=discount_code.code,
        discount_type=discount_code.discount_type,
        discount_value=discount_code.discount_value,
        discount_amount=round(discount_amount, 2),
        final_amount=round(final_amount, 2),
        message=f"Discount code applied! You save ${discount_amount:.2f}"
    )


@payment_router.post("/discount-code/apply")
async def apply_discount_code(
    data: ApplyDiscountCodeRequest,
    user_id: uuid.UUID = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_session),
):
    """Apply a discount code and increment usage count.
    
    This should be called after successful payment to track usage.
    
    Args:
        data: Discount code and amount info
        user_id: User applying the code
        
    Returns:
        Updated discount info
    """
    from sqlalchemy import select
    from app.modules.admin.models import DiscountCode
    
    # Find the discount code
    result = await session.execute(
        select(DiscountCode).where(DiscountCode.code == data.code.upper())
    )
    discount_code = result.scalar_one_or_none()
    
    if not discount_code or not discount_code.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired discount code"
        )
    
    # Increment usage count
    discount_code.usage_count += 1
    await session.commit()
    
    discount_amount = discount_code.calculate_discount(data.amount)
    
    return {
        "success": True,
        "code": discount_code.code,
        "discount_amount": round(discount_amount, 2),
        "new_usage_count": discount_code.usage_count,
        "message": "Discount code applied successfully"
    }


@payment_router.post("/webhook/{provider}")
async def handle_webhook(
    provider: GatewayProvider,
    payload: dict,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    x_callback_token: Optional[str] = Header(None, alias="X-Callback-Token"),
    session: AsyncSession = Depends(get_session),
):
    """Handle webhook callback from a payment gateway.
    
    Requirements: 30.4 - Webhook handling for payment status updates
    
    Different gateways use different signature headers:
    - Stripe: Stripe-Signature
    - PayPal: X-Signature
    - Midtrans: signature_key in payload
    - Xendit: X-Callback-Token
    """
    # Determine signature based on provider
    signature = ""
    if provider == GatewayProvider.STRIPE:
        signature = stripe_signature or ""
    elif provider == GatewayProvider.XENDIT:
        signature = x_callback_token or ""
    elif provider == GatewayProvider.MIDTRANS:
        signature = payload.get("signature_key", "")
    else:
        signature = x_signature or ""
    
    service = PaymentService(session)
    transaction = await service.handle_webhook(provider.value, payload, signature)
    await session.commit()
    
    if transaction:
        return {"status": "processed", "payment_id": str(transaction.id)}
    return {"status": "acknowledged"}


# ==================== Parameterized routes MUST be at the end ====================

@payment_router.get("/{payment_id}", response_model=PaymentTransactionResponse)
async def get_payment(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get payment transaction details.
    
    Requirements: 30.6 - Transaction tracking
    """
    service = PaymentService(session)
    transaction = await service.get_transaction(payment_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    
    return PaymentTransactionResponse(
        id=transaction.id,
        user_id=transaction.user_id,
        subscription_id=transaction.subscription_id,
        gateway_provider=transaction.gateway_provider,
        gateway_payment_id=transaction.gateway_payment_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        payment_method=transaction.payment_method,
        description=transaction.description,
        error_message=transaction.error_message,
        attempt_count=transaction.attempt_count,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
    )


@payment_router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get payment status.
    
    Requirements: 30.4 - Payment status tracking
    """
    service = PaymentService(session)
    transaction = await service.get_transaction(payment_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    
    return PaymentStatusResponse(
        payment_id=transaction.id,
        gateway_provider=transaction.gateway_provider,
        status=transaction.status,
        amount=transaction.amount,
        currency=transaction.currency,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
        error_message=transaction.error_message,
    )
