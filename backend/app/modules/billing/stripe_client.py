"""Stripe client for payment processing.

Implements Stripe integration for subscriptions, payments, and invoices.
Requirements: 28.3 - Stripe integration, Invoice generation
"""

import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

import stripe
from stripe import Customer, Subscription as StripeSubscription, PaymentMethod as StripePaymentMethod
from stripe import Invoice as StripeInvoice, PaymentIntent

from app.core.config import settings


# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


@dataclass
class StripeCustomerData:
    """Data for a Stripe customer."""
    id: str
    email: str
    name: Optional[str] = None
    default_payment_method: Optional[str] = None


@dataclass
class StripeSubscriptionData:
    """Data for a Stripe subscription."""
    id: str
    customer_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    price_id: str
    cancel_at_period_end: bool
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None


@dataclass
class StripePaymentMethodData:
    """Data for a Stripe payment method."""
    id: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None


@dataclass
class StripeInvoiceData:
    """Data for a Stripe invoice."""
    id: str
    customer_id: str
    subscription_id: Optional[str]
    status: str
    subtotal: int
    tax: int
    total: int
    amount_paid: int
    amount_due: int
    currency: str
    period_start: datetime
    period_end: datetime
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    payment_intent_id: Optional[str] = None



class StripeClient:
    """Client for Stripe API operations.
    
    Requirements: 28.3 - Stripe integration, Invoice generation
    """

    # Plan tier to Stripe price ID mapping
    PLAN_PRICE_IDS = {
        "basic": settings.STRIPE_PRICE_ID_BASIC,
        "pro": settings.STRIPE_PRICE_ID_PRO,
        "enterprise": settings.STRIPE_PRICE_ID_ENTERPRISE,
    }

    def __init__(self):
        """Initialize Stripe client."""
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")

    # ==================== Customer Management ====================

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StripeCustomerData:
        """Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata (e.g., user_id)
            
        Returns:
            StripeCustomerData with customer details
        """
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )
        return StripeCustomerData(
            id=customer.id,
            email=customer.email,
            name=customer.name,
            default_payment_method=customer.invoice_settings.default_payment_method if customer.invoice_settings else None,
        )

    def get_customer(self, customer_id: str) -> Optional[StripeCustomerData]:
        """Get a Stripe customer by ID.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            StripeCustomerData or None if not found
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            if customer.deleted:
                return None
            return StripeCustomerData(
                id=customer.id,
                email=customer.email,
                name=customer.name,
                default_payment_method=customer.invoice_settings.default_payment_method if customer.invoice_settings else None,
            )
        except stripe.error.InvalidRequestError:
            return None

    def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        default_payment_method: Optional[str] = None,
    ) -> StripeCustomerData:
        """Update a Stripe customer.
        
        Args:
            customer_id: Stripe customer ID
            email: New email (optional)
            name: New name (optional)
            default_payment_method: New default payment method ID (optional)
            
        Returns:
            Updated StripeCustomerData
        """
        update_params = {}
        if email:
            update_params["email"] = email
        if name:
            update_params["name"] = name
        if default_payment_method:
            update_params["invoice_settings"] = {
                "default_payment_method": default_payment_method
            }

        customer = stripe.Customer.modify(customer_id, **update_params)
        return StripeCustomerData(
            id=customer.id,
            email=customer.email,
            name=customer.name,
            default_payment_method=customer.invoice_settings.default_payment_method if customer.invoice_settings else None,
        )

    # ==================== Payment Method Management ====================

    def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str,
    ) -> StripePaymentMethodData:
        """Attach a payment method to a customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            customer_id: Stripe customer ID
            
        Returns:
            StripePaymentMethodData with payment method details
        """
        pm = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )
        return self._payment_method_to_data(pm)

    def detach_payment_method(self, payment_method_id: str) -> bool:
        """Detach a payment method from its customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            True if successful
        """
        stripe.PaymentMethod.detach(payment_method_id)
        return True

    def get_payment_method(self, payment_method_id: str) -> Optional[StripePaymentMethodData]:
        """Get a payment method by ID.
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            StripePaymentMethodData or None if not found
        """
        try:
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            return self._payment_method_to_data(pm)
        except stripe.error.InvalidRequestError:
            return None

    def list_payment_methods(
        self,
        customer_id: str,
        type: str = "card",
    ) -> list[StripePaymentMethodData]:
        """List payment methods for a customer.
        
        Args:
            customer_id: Stripe customer ID
            type: Payment method type (default: card)
            
        Returns:
            List of StripePaymentMethodData
        """
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type=type,
        )
        return [self._payment_method_to_data(pm) for pm in payment_methods.data]

    def _payment_method_to_data(self, pm: StripePaymentMethod) -> StripePaymentMethodData:
        """Convert Stripe PaymentMethod to StripePaymentMethodData."""
        card = pm.card if pm.card else None
        return StripePaymentMethodData(
            id=pm.id,
            card_brand=card.brand if card else None,
            card_last4=card.last4 if card else None,
            card_exp_month=card.exp_month if card else None,
            card_exp_year=card.exp_year if card else None,
        )


    # ==================== Subscription Management ====================

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        payment_method_id: Optional[str] = None,
        trial_days: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> StripeSubscriptionData:
        """Create a new subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            payment_method_id: Payment method to use (optional)
            trial_days: Number of trial days (optional)
            metadata: Additional metadata
            
        Returns:
            StripeSubscriptionData with subscription details
        """
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": metadata or {},
            "expand": ["latest_invoice.payment_intent"],
        }
        
        if payment_method_id:
            params["default_payment_method"] = payment_method_id
        
        if trial_days:
            params["trial_period_days"] = trial_days

        subscription = stripe.Subscription.create(**params)
        return self._subscription_to_data(subscription)

    def get_subscription(self, subscription_id: str) -> Optional[StripeSubscriptionData]:
        """Get a subscription by ID.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            StripeSubscriptionData or None if not found
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return self._subscription_to_data(subscription)
        except stripe.error.InvalidRequestError:
            return None

    def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        cancel_at_period_end: Optional[bool] = None,
        payment_method_id: Optional[str] = None,
    ) -> StripeSubscriptionData:
        """Update a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            price_id: New price ID for plan change (optional)
            cancel_at_period_end: Whether to cancel at period end (optional)
            payment_method_id: New default payment method (optional)
            
        Returns:
            Updated StripeSubscriptionData
        """
        params = {}
        
        if price_id:
            # Get current subscription to find the item ID
            sub = stripe.Subscription.retrieve(subscription_id)
            params["items"] = [{
                "id": sub["items"]["data"][0].id,
                "price": price_id,
            }]
            params["proration_behavior"] = "create_prorations"
        
        if cancel_at_period_end is not None:
            params["cancel_at_period_end"] = cancel_at_period_end
        
        if payment_method_id:
            params["default_payment_method"] = payment_method_id

        subscription = stripe.Subscription.modify(subscription_id, **params)
        return self._subscription_to_data(subscription)

    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True,
    ) -> StripeSubscriptionData:
        """Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            cancel_at_period_end: If True, cancel at end of period; if False, cancel immediately
            
        Returns:
            Updated StripeSubscriptionData
        """
        if cancel_at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            subscription = stripe.Subscription.cancel(subscription_id)
        
        return self._subscription_to_data(subscription)

    def reactivate_subscription(self, subscription_id: str) -> StripeSubscriptionData:
        """Reactivate a subscription that was set to cancel at period end.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Updated StripeSubscriptionData
        """
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False,
        )
        return self._subscription_to_data(subscription)

    def _subscription_to_data(self, sub: StripeSubscription) -> StripeSubscriptionData:
        """Convert Stripe Subscription to StripeSubscriptionData."""
        return StripeSubscriptionData(
            id=sub.id,
            customer_id=sub.customer,
            status=sub.status,
            current_period_start=datetime.fromtimestamp(sub.current_period_start),
            current_period_end=datetime.fromtimestamp(sub.current_period_end),
            price_id=sub["items"]["data"][0].price.id if sub["items"]["data"] else "",
            cancel_at_period_end=sub.cancel_at_period_end,
            trial_start=datetime.fromtimestamp(sub.trial_start) if sub.trial_start else None,
            trial_end=datetime.fromtimestamp(sub.trial_end) if sub.trial_end else None,
        )

    def get_price_id_for_plan(self, plan_tier: str) -> Optional[str]:
        """Get the Stripe price ID for a plan tier.
        
        Args:
            plan_tier: Plan tier (basic, pro, enterprise)
            
        Returns:
            Stripe price ID or None if not configured
        """
        return self.PLAN_PRICE_IDS.get(plan_tier)


    # ==================== Invoice Management ====================

    def get_invoice(self, invoice_id: str) -> Optional[StripeInvoiceData]:
        """Get an invoice by ID.
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            StripeInvoiceData or None if not found
        """
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return self._invoice_to_data(invoice)
        except stripe.error.InvalidRequestError:
            return None

    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
        starting_after: Optional[str] = None,
    ) -> list[StripeInvoiceData]:
        """List invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            starting_after: Cursor for pagination
            
        Returns:
            List of StripeInvoiceData
        """
        params = {
            "customer": customer_id,
            "limit": limit,
        }
        if starting_after:
            params["starting_after"] = starting_after

        invoices = stripe.Invoice.list(**params)
        return [self._invoice_to_data(inv) for inv in invoices.data]

    def create_invoice(
        self,
        customer_id: str,
        auto_advance: bool = True,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StripeInvoiceData:
        """Create a new invoice.
        
        Requirements: 28.3 - Invoice generation
        
        Args:
            customer_id: Stripe customer ID
            auto_advance: Whether to auto-finalize the invoice
            description: Invoice description
            metadata: Additional metadata
            
        Returns:
            StripeInvoiceData with invoice details
        """
        params = {
            "customer": customer_id,
            "auto_advance": auto_advance,
            "metadata": metadata or {},
        }
        if description:
            params["description"] = description

        invoice = stripe.Invoice.create(**params)
        return self._invoice_to_data(invoice)

    def add_invoice_item(
        self,
        customer_id: str,
        amount: int,
        currency: str = "usd",
        description: Optional[str] = None,
        invoice_id: Optional[str] = None,
    ) -> str:
        """Add an item to an invoice.
        
        Args:
            customer_id: Stripe customer ID
            amount: Amount in cents
            currency: Currency code
            description: Item description
            invoice_id: Invoice ID to add to (optional, uses next invoice if not specified)
            
        Returns:
            Invoice item ID
        """
        params = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
        }
        if description:
            params["description"] = description
        if invoice_id:
            params["invoice"] = invoice_id

        item = stripe.InvoiceItem.create(**params)
        return item.id

    def finalize_invoice(self, invoice_id: str) -> StripeInvoiceData:
        """Finalize a draft invoice.
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Finalized StripeInvoiceData
        """
        invoice = stripe.Invoice.finalize_invoice(invoice_id)
        return self._invoice_to_data(invoice)

    def pay_invoice(
        self,
        invoice_id: str,
        payment_method_id: Optional[str] = None,
    ) -> StripeInvoiceData:
        """Pay an invoice.
        
        Args:
            invoice_id: Stripe invoice ID
            payment_method_id: Payment method to use (optional)
            
        Returns:
            Paid StripeInvoiceData
        """
        params = {}
        if payment_method_id:
            params["payment_method"] = payment_method_id

        invoice = stripe.Invoice.pay(invoice_id, **params)
        return self._invoice_to_data(invoice)

    def void_invoice(self, invoice_id: str) -> StripeInvoiceData:
        """Void an invoice.
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Voided StripeInvoiceData
        """
        invoice = stripe.Invoice.void_invoice(invoice_id)
        return self._invoice_to_data(invoice)

    def send_invoice(self, invoice_id: str) -> StripeInvoiceData:
        """Send an invoice to the customer.
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            StripeInvoiceData
        """
        invoice = stripe.Invoice.send_invoice(invoice_id)
        return self._invoice_to_data(invoice)

    def get_upcoming_invoice(self, customer_id: str) -> Optional[StripeInvoiceData]:
        """Get the upcoming invoice for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            StripeInvoiceData for upcoming invoice or None
        """
        try:
            invoice = stripe.Invoice.upcoming(customer=customer_id)
            return self._invoice_to_data(invoice)
        except stripe.error.InvalidRequestError:
            return None

    def _invoice_to_data(self, inv: StripeInvoice) -> StripeInvoiceData:
        """Convert Stripe Invoice to StripeInvoiceData."""
        return StripeInvoiceData(
            id=inv.id if inv.id else f"upcoming_{inv.customer}",
            customer_id=inv.customer,
            subscription_id=inv.subscription,
            status=inv.status or "draft",
            subtotal=inv.subtotal,
            tax=inv.tax or 0,
            total=inv.total,
            amount_paid=inv.amount_paid,
            amount_due=inv.amount_due,
            currency=inv.currency,
            period_start=datetime.fromtimestamp(inv.period_start) if inv.period_start else datetime.utcnow(),
            period_end=datetime.fromtimestamp(inv.period_end) if inv.period_end else datetime.utcnow(),
            invoice_pdf=inv.invoice_pdf,
            hosted_invoice_url=inv.hosted_invoice_url,
            payment_intent_id=inv.payment_intent if isinstance(inv.payment_intent, str) else (inv.payment_intent.id if inv.payment_intent else None),
        )


    # ==================== Checkout Session ====================

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = "subscription",
        trial_days: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            mode: Checkout mode (subscription, payment)
            trial_days: Trial period days (optional)
            metadata: Additional metadata
            
        Returns:
            Dict with session_id and url
        """
        params = {
            "customer": customer_id,
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
        }
        
        if trial_days and mode == "subscription":
            params["subscription_data"] = {"trial_period_days": trial_days}

        session = stripe.checkout.Session.create(**params)
        return {
            "session_id": session.id,
            "url": session.url,
        }

    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> dict:
        """Create a Stripe Billing Portal session.
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal
            
        Returns:
            Dict with session_id and url
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return {
            "session_id": session.id,
            "url": session.url,
        }

    # ==================== Webhook Handling ====================

    @staticmethod
    def construct_webhook_event(
        payload: bytes,
        sig_header: str,
    ) -> stripe.Event:
        """Construct and verify a webhook event.
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Verified Stripe Event
            
        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}")


# Singleton instance
_stripe_client: Optional[StripeClient] = None


def get_stripe_client() -> StripeClient:
    """Get the Stripe client singleton.
    
    Returns:
        StripeClient instance
    """
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client
