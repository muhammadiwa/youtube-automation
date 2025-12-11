# Payment Gateway Integration Guide

## Supported Gateways

| Gateway | Currencies | Payment Methods |
|---------|------------|-----------------|
| **Stripe** | USD, EUR, GBP, JPY, AUD, CAD, SGD | Card, Apple Pay, Google Pay |
| **PayPal** | USD, EUR, GBP, AUD, CAD | PayPal Balance, Card via PayPal |
| **Midtrans** | IDR | GoPay, OVO, DANA, ShopeePay, Bank Transfer, QRIS |
| **Xendit** | IDR, PHP, USD | OVO, DANA, LinkAja, GCash, GrabPay, Bank Transfer |

## Payment Flow

### 1. Create Payment
```
Frontend → POST /api/payments → Backend creates transaction → Gateway creates checkout
```

### 2. User Checkout
```
User redirected to gateway checkout page → User completes payment
```

### 3. Return & Verify
```
Gateway redirects to success URL with parameters → Frontend calls verify endpoint → Backend verifies with gateway → Subscription activated
```

### 4. Webhook (Backup)
```
Gateway sends webhook → Backend updates transaction → Subscription activated (if not already)
```

## Gateway-Specific Flows

### Stripe
1. **Create**: `POST /api/payments` → Returns `checkout_url`
2. **Checkout**: User redirected to Stripe Checkout
3. **Return**: Stripe redirects to `success_url?session_id={CHECKOUT_SESSION_ID}`
4. **Verify**: `POST /api/payments/stripe/verify` with `session_id`
5. **Webhook**: `checkout.session.completed` event

### PayPal
1. **Create**: `POST /api/payments` → Returns `checkout_url` (PayPal approval URL)
2. **Checkout**: User approves on PayPal
3. **Return**: PayPal redirects to `success_url?token={ORDER_ID}&PayerID={PAYER_ID}`
4. **Verify**: `POST /api/payments/paypal/verify` with `order_id` → Captures payment
5. **Webhook**: `CHECKOUT.ORDER.APPROVED` event

### Midtrans
1. **Create**: `POST /api/payments` → Returns `checkout_url` (Snap redirect URL)
2. **Checkout**: User pays via Snap popup/redirect
3. **Return**: Midtrans redirects to `finish_url?order_id={ORDER_ID}&transaction_status={STATUS}`
4. **Verify**: `POST /api/payments/midtrans/verify` with `order_id`
5. **Webhook**: HTTP notification to webhook URL

### Xendit
1. **Create**: `POST /api/payments` → Returns `checkout_url` (Invoice URL)
2. **Checkout**: User pays via Invoice page
3. **Return**: Xendit redirects to `success_url?external_id={ORDER_ID}`
4. **Verify**: `POST /api/payments/xendit/verify` with `invoice_id` or use generic verify
5. **Webhook**: Callback to webhook URL

## Configuration

### Environment Variables

```env
# Stripe
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# PayPal
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_SANDBOX=true

# Midtrans
MIDTRANS_SERVER_KEY=...
MIDTRANS_CLIENT_KEY=...
MIDTRANS_SANDBOX=true

# Xendit
XENDIT_SECRET_KEY=xnd_development_...
XENDIT_CALLBACK_TOKEN=...
```

### Configuration Scripts

```bash
cd backend

# Configure each gateway
python -m scripts.configure_stripe
python -m scripts.configure_paypal
python -m scripts.configure_midtrans
python -m scripts.configure_xendit
```

## Webhook URLs

Set these URLs in each gateway's dashboard:

| Gateway | Webhook URL |
|---------|-------------|
| Stripe | `https://your-domain.com/api/payments/webhook/stripe` |
| PayPal | `https://your-domain.com/api/payments/webhook/paypal` |
| Midtrans | `https://your-domain.com/api/payments/webhook/midtrans` |
| Xendit | `https://your-domain.com/api/payments/webhook/xendit` |

## Testing

### Stripe Test Cards
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

### PayPal Sandbox
- Use sandbox accounts from PayPal Developer Dashboard

### Midtrans Sandbox
- Use test payment methods in sandbox mode

### Xendit Test Mode
- Use development API keys (start with `xnd_development_`)

## Error Handling

1. **Payment Failed**: User redirected to `/dashboard/billing/checkout/failed`
2. **Verification Failed**: Retry button available, webhook will handle as backup
3. **Gateway Unavailable**: Fallback to alternative gateway option

## Subscription Activation

After successful payment verification:
1. Transaction status updated to `completed`
2. Subscription created/updated with correct `plan_tier` and `billing_cycle`
3. `current_period_end` calculated based on billing cycle (30 days for monthly, 365 for yearly)
4. Transaction linked to subscription via `subscription_id`
