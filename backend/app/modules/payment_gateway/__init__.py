"""Payment Gateway Module.

Provides multi-payment gateway support for Stripe, PayPal, Midtrans, and Xendit.

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

from app.modules.payment_gateway.models import (
    PaymentGatewayConfig,
    PaymentTransaction,
    GatewayStatistics,
    GatewayProvider,
    PaymentStatus,
    GatewayHealthStatus,
)
from app.modules.payment_gateway.interface import (
    PaymentGatewayInterface,
    CreatePaymentDTO,
    PaymentResult,
    PaymentVerification,
    RefundResult,
    WebhookResult,
    ValidationResult,
    encrypt_credential,
    decrypt_credential,
)
from app.modules.payment_gateway.service import (
    PaymentGatewayFactory,
    GatewayManagerService,
    PaymentService,
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

__all__ = [
    # Models
    "PaymentGatewayConfig",
    "PaymentTransaction",
    "GatewayStatistics",
    "GatewayProvider",
    "PaymentStatus",
    "GatewayHealthStatus",
    # Interface
    "PaymentGatewayInterface",
    "CreatePaymentDTO",
    "PaymentResult",
    "PaymentVerification",
    "RefundResult",
    "WebhookResult",
    "ValidationResult",
    "encrypt_credential",
    "decrypt_credential",
    # Services
    "PaymentGatewayFactory",
    "GatewayManagerService",
    "PaymentService",
    # Repositories
    "PaymentGatewayRepository",
    "PaymentTransactionRepository",
    "GatewayStatisticsRepository",
    # Gateways
    "StripeGateway",
    "PayPalGateway",
    "MidtransGateway",
    "XenditGateway",
]
