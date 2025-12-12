import apiClient from "./client"

// ============ Payment Gateway Types ============
export type GatewayProvider = "stripe" | "paypal" | "midtrans" | "xendit"

export interface PaymentGateway {
    id: string
    provider: GatewayProvider
    display_name: string
    is_enabled: boolean
    is_default: boolean
    sandbox_mode: boolean
    supported_currencies: string[]
    supported_payment_methods: string[]
    transaction_fee_percent: number
    fixed_fee: number
    min_amount: number
    max_amount?: number
    icon_url?: string
    description?: string
    has_credentials?: boolean
}

export interface GatewayPublicInfo {
    provider: GatewayProvider
    display_name: string
    supported_currencies: string[]
    supported_payment_methods: string[]
    min_amount: number
    max_amount?: number
    is_default?: boolean
}

export interface GatewayStatistics {
    provider: GatewayProvider
    total_transactions: number
    successful_transactions: number
    failed_transactions: number
    success_rate: number
    total_volume: number
    average_transaction: number
    last_transaction_at?: string
    health_status: "healthy" | "degraded" | "down"
    transactions_24h?: number
    success_rate_24h?: number
}

export interface GatewayCredentials {
    api_key: string
    api_secret: string
    webhook_secret?: string
    sandbox_mode: boolean
}

export interface CheckoutSession {
    payment_id: string
    checkout_url?: string
    gateway_provider: GatewayProvider
    status: "pending" | "completed" | "failed" | "cancelled"
    error_message?: string
}

export interface PaymentResult {
    success: boolean
    payment_id?: string
    error_message?: string
    gateway: GatewayProvider
}

// ============ Plan Types ============
export type PlanTier = "free" | "basic" | "pro" | "enterprise"

export interface PlanFeature {
    name: string
    included: boolean
    description?: string
}

export interface PlanLimits {
    max_accounts: number
    max_videos_per_month: number
    max_streams_per_month: number
    max_storage_gb: number
    max_bandwidth_gb: number
    ai_generations_per_month: number
}

export interface Plan {
    id: string
    name: string
    slug: PlanTier
    price_monthly: number
    price_yearly: number
    features: PlanFeature[]
    limits: PlanLimits
}

// ============ Subscription Types ============
export interface Subscription {
    id: string
    user_id: string
    plan_tier: PlanTier  // Backend returns plan_tier, not plan
    billing_cycle: "monthly" | "yearly"
    status: "active" | "cancelled" | "expired" | "past_due"
    current_period_start: string
    current_period_end: string
    cancel_at_period_end: boolean
    created_at: string
    updated_at: string
}

// ============ Usage Types ============
export interface UsageMetrics {
    accounts_used: number
    accounts_limit: number
    videos_uploaded: number
    videos_limit: number
    streams_created: number
    streams_limit: number
    storage_used_gb: number
    storage_limit_gb: number
    bandwidth_used_gb: number
    bandwidth_limit_gb: number
    ai_generations_used: number
    ai_generations_limit: number
    period_start: string
    period_end: string
}

export interface UsageWarning {
    type: string
    current_usage: number
    limit: number
    percentage: number
    threshold: "50" | "75" | "90" | "100"
    message: string
}

// ============ Invoice Types ============
export interface Invoice {
    id: string
    number: string
    amount: number
    currency: string
    status: "draft" | "open" | "paid" | "void" | "uncollectible"
    due_date: string
    paid_at?: string
    pdf_url?: string
    created_at: string
    gateway_provider?: GatewayProvider
}

// ============ Payment Transaction Types ============
export interface PaymentTransaction {
    id: string
    user_id: string
    gateway_provider: GatewayProvider
    gateway_payment_id?: string
    amount: number
    currency: string
    status: "pending" | "completed" | "failed" | "cancelled" | "refunded"
    payment_method?: string
    description?: string
    error_message?: string
    attempt_count: number
    created_at: string
    completed_at?: string
}

// ============ Payment Method Types ============
export interface PaymentMethod {
    id: string
    type: "card" | "bank_account" | "paypal"
    brand?: string
    last4: string
    exp_month?: number
    exp_year?: number
    is_default: boolean
}

// Helper to get current user ID from localStorage/session
function getCurrentUserId(): string {
    if (typeof window !== "undefined") {
        const userId = localStorage.getItem("user_id")
        if (userId) return userId
    }
    // Return a placeholder - in production this should come from auth context
    return "current"
}

export const billingApi = {
    // ============ Plans ============
    async getPlans(): Promise<Plan[]> {
        const response = await apiClient.get<{ plans: Plan[] } | Plan[]>("/billing/plans")

        // Backend returns { plans: [...] } format from database
        if (response && typeof response === "object" && "plans" in response && Array.isArray(response.plans)) {
            return response.plans.map(plan => ({
                id: plan.id,
                name: plan.name,
                slug: (plan.slug || plan.id) as PlanTier,
                price_monthly: typeof plan.price_monthly === "number" ? plan.price_monthly : 0,
                price_yearly: typeof plan.price_yearly === "number" ? plan.price_yearly : 0,
                features: Array.isArray(plan.features) ? plan.features : [],
                limits: plan.limits || {
                    max_accounts: 1,
                    max_videos_per_month: 5,
                    max_streams_per_month: 0,
                    max_storage_gb: 1,
                    max_bandwidth_gb: 5,
                    ai_generations_per_month: 0,
                },
            }))
        }

        // If response is already an array (legacy format)
        if (Array.isArray(response)) {
            return response.map(plan => ({
                ...plan,
                slug: (plan.slug || plan.id) as PlanTier,
            }))
        }

        return []
    },

    // ============ Subscription ============
    async getSubscription(): Promise<Subscription | null> {
        try {
            const userId = getCurrentUserId()
            return await apiClient.get<Subscription>(`/billing/subscriptions/${userId}`)
        } catch (error) {
            console.error("Failed to fetch subscription:", error)
            return null
        }
    },

    async getSubscriptionStatus(): Promise<{
        subscription: Subscription
        features: Record<string, boolean>
        limits: PlanLimits
    } | null> {
        try {
            const userId = getCurrentUserId()
            return await apiClient.get(`/billing/subscriptions/${userId}/status`)
        } catch (error) {
            console.error("Failed to fetch subscription status:", error)
            return null
        }
    },

    async cancelSubscription(cancelAtPeriodEnd: boolean = true): Promise<Subscription> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/subscriptions/${userId}/cancel?cancel_at_period_end=${cancelAtPeriodEnd}`)
    },

    async resumeSubscription(): Promise<Subscription> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/subscriptions/${userId}/reactivate`)
    },

    // ============ Usage ============
    async getUsage(): Promise<UsageMetrics> {
        const userId = getCurrentUserId()
        const response = await apiClient.get<any>(`/billing/usage/${userId}/dashboard`)
        // Map backend response to frontend format
        return {
            accounts_used: response.api_calls?.current || 0,
            accounts_limit: response.api_calls?.limit || -1,
            videos_uploaded: response.encoding_minutes?.current || 0,
            videos_limit: response.encoding_minutes?.limit || -1,
            streams_created: 0,
            streams_limit: -1,
            storage_used_gb: response.storage_gb?.current || 0,
            storage_limit_gb: response.storage_gb?.limit || -1,
            bandwidth_used_gb: response.bandwidth_gb?.current || 0,
            bandwidth_limit_gb: response.bandwidth_gb?.limit || -1,
            ai_generations_used: 0,
            ai_generations_limit: -1,
            period_start: response.period_start || new Date().toISOString(),
            period_end: response.period_end || new Date().toISOString(),
        }
    },

    async getUsageWarnings(): Promise<UsageWarning[]> {
        try {
            const userId = getCurrentUserId()
            const dashboard = await apiClient.get<any>(`/billing/usage/${userId}/dashboard`)
            return dashboard.warnings || []
        } catch (error) {
            console.error("Failed to fetch usage warnings:", error)
            return []
        }
    },

    async exportUsage(format: "csv" | "json", startDate: string, endDate: string): Promise<{ download_url: string }> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/usage/${userId}/export?start_date=${startDate}&end_date=${endDate}`)
    },

    // ============ Payment History (Transactions) ============
    async getInvoices(): Promise<Invoice[]> {
        // Get payment transactions and map to Invoice format for display
        try {
            const transactions = await this.getPaymentTransactions()
            return transactions.map(tx => ({
                id: tx.id,
                number: tx.description || `Payment ${tx.id.slice(0, 8)}`,
                amount: tx.amount,
                currency: tx.currency,
                status: tx.status === "completed" ? "paid" : tx.status === "pending" ? "open" : "void",
                due_date: tx.created_at,
                paid_at: tx.completed_at,
                created_at: tx.created_at,
                gateway_provider: tx.gateway_provider,
            }))
        } catch (error) {
            console.error("Failed to fetch payment history:", error)
            return []
        }
    },

    async getPaymentTransactions(): Promise<PaymentTransaction[]> {
        try {
            const response = await apiClient.get<PaymentTransaction[]>("/payments/history", { includeUserId: true })
            return response || []
        } catch (error) {
            console.error("Failed to fetch payment transactions:", error)
            return []
        }
    },

    async getInvoice(invoiceId: string): Promise<Invoice> {
        const userId = getCurrentUserId()
        return await apiClient.get(`/billing/invoices/${userId}/${invoiceId}`)
    },

    // ============ Payment Methods ============
    async getPaymentMethods(): Promise<PaymentMethod[]> {
        try {
            const userId = getCurrentUserId()
            const response = await apiClient.get<{ payment_methods: PaymentMethod[] } | PaymentMethod[]>(`/billing/payment-methods/${userId}`)
            if (response && typeof response === "object" && "payment_methods" in response) {
                return response.payment_methods || []
            }
            if (Array.isArray(response)) {
                return response
            }
            return []
        } catch (error) {
            console.error("Failed to fetch payment methods:", error)
            return []
        }
    },

    async addPaymentMethod(data: { type: string; token: string }): Promise<PaymentMethod> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/payment-methods/${userId}`, data)
    },

    async setDefaultPaymentMethod(methodId: string): Promise<PaymentMethod> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/payment-methods/${userId}/${methodId}/set-default`)
    },

    async removePaymentMethod(methodId: string): Promise<void> {
        const userId = getCurrentUserId()
        return await apiClient.delete(`/billing/payment-methods/${userId}/${methodId}`)
    },

    // ============ Payment Gateways (Public) ============
    async getEnabledGateways(currency?: string): Promise<GatewayPublicInfo[]> {
        try {
            const params = currency ? { currency } : {}
            const response = await apiClient.get<GatewayPublicInfo[]>("/payments/gateways", params)
            return response || []
        } catch (error) {
            console.error("Failed to fetch gateways:", error)
            return []
        }
    },

    // ============ Currency Conversion ============
    async convertCurrency(amount: number, fromCurrency: string = "USD", toCurrency: string = "IDR"): Promise<{
        from_currency: string
        to_currency: string
        amount: number
        converted_amount: number
        exchange_rate: number
    }> {
        return await apiClient.get("/payments/currency/convert", {
            amount,
            from_currency: fromCurrency,
            to_currency: toCurrency,
        })
    },

    async getExchangeRate(fromCurrency: string = "USD", toCurrency: string = "IDR"): Promise<{
        from_currency: string
        to_currency: string
        rate: number
    }> {
        return await apiClient.get("/payments/currency/rate", {
            from_currency: fromCurrency,
            to_currency: toCurrency,
        })
    },

    // ============ Discount Code ============
    async validateDiscountCode(code: string, plan?: string, amount?: number): Promise<{
        is_valid: boolean
        code?: string
        discount_type?: "percentage" | "fixed"
        discount_value?: number
        discount_amount?: number
        final_amount?: number
        message: string
    }> {
        return await apiClient.post("/payments/discount-code/validate", {
            code,
            plan,
            amount: amount || 0,
        })
    },

    async applyDiscountCode(code: string, amount: number): Promise<{
        success: boolean
        code: string
        discount_amount: number
        new_usage_count: number
        message: string
    }> {
        return await apiClient.post("/payments/discount-code/apply", {
            code,
            amount,
        }, { includeUserId: true })
    },

    async createPayment(data: {
        amount: number
        currency: string
        description: string
        preferred_gateway?: GatewayProvider
        subscription_id?: string
        success_url: string
        cancel_url: string
        metadata?: Record<string, any>
    }): Promise<CheckoutSession> {
        // This endpoint requires X-User-ID header which is automatically added by apiClient
        return await apiClient.post("/payments", data, { includeUserId: true })
    },

    async getPaymentStatus(paymentId: string): Promise<CheckoutSession> {
        return await apiClient.get(`/payments/${paymentId}/status`)
    },

    async verifyPayment(paymentId: string): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/${paymentId}/verify`)
    },

    async verifyPayPalPayment(paypalOrderId: string): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/paypal/verify`, { order_id: paypalOrderId })
    },

    async verifyStripePayment(sessionId: string): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/stripe/verify`, { session_id: sessionId })
    },

    async verifyMidtransPayment(orderId: string): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/midtrans/verify`, { order_id: orderId })
    },

    async verifyXenditPayment(invoiceId: string): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/xendit/verify`, { invoice_id: invoiceId })
    },

    async getAlternativeGateways(paymentId: string): Promise<GatewayPublicInfo[]> {
        return await apiClient.get(`/payments/${paymentId}/alternatives`)
    },

    async retryPaymentWithGateway(paymentId: string, gateway: GatewayProvider): Promise<CheckoutSession> {
        return await apiClient.post(`/payments/${paymentId}/retry`, { alternative_gateway: gateway })
    },

    // ============ Stripe Checkout (for subscription) ============
    async createStripeCheckout(data: {
        plan_tier: PlanTier
        success_url: string
        cancel_url: string
        trial_days?: number
    }): Promise<{ session_id: string; checkout_url: string }> {
        const userId = getCurrentUserId()
        const email = localStorage.getItem("user_email") || ""
        return await apiClient.post(`/billing/stripe/checkout-session/${userId}?email=${encodeURIComponent(email)}`, data)
    },

    async createBillingPortal(returnUrl: string): Promise<{ portal_url: string }> {
        const userId = getCurrentUserId()
        return await apiClient.post(`/billing/stripe/billing-portal/${userId}`, { return_url: returnUrl })
    },

    // ============ Admin: Gateway Management ============
    async getAllGateways(): Promise<PaymentGateway[]> {
        try {
            const response = await apiClient.get<PaymentGateway[]>("/admin/payment-gateways")
            return response || []
        } catch (error) {
            console.error("Failed to fetch all gateways:", error)
            return []
        }
    },

    async getGateway(provider: GatewayProvider): Promise<PaymentGateway> {
        return await apiClient.get(`/admin/payment-gateways/${provider}`)
    },

    async enableGateway(provider: GatewayProvider): Promise<{ provider: string; is_enabled: boolean; message: string }> {
        return await apiClient.post(`/admin/payment-gateways/${provider}/enable`)
    },

    async disableGateway(provider: GatewayProvider): Promise<{ provider: string; is_enabled: boolean; message: string }> {
        return await apiClient.post(`/admin/payment-gateways/${provider}/disable`)
    },

    async setDefaultGateway(provider: GatewayProvider): Promise<PaymentGateway> {
        return await apiClient.post(`/admin/payment-gateways/${provider}/set-default`)
    },

    async configureGateway(provider: GatewayProvider, credentials: GatewayCredentials & {
        display_name?: string
        transaction_fee_percent?: number
        fixed_fee?: number
        min_amount?: number
        max_amount?: number
    }): Promise<PaymentGateway> {
        return await apiClient.post(`/admin/payment-gateways/${provider}/configure`, credentials)
    },

    async validateGatewayCredentials(provider: GatewayProvider): Promise<{ valid: boolean; message?: string; error?: string }> {
        return await apiClient.post(`/admin/payment-gateways/${provider}/validate`)
    },

    async getGatewayStatistics(): Promise<{
        gateways: GatewayStatistics[]
        total_volume: number
        total_transactions: number
        overall_success_rate: number
    }> {
        try {
            const response = await apiClient.get<{
                gateways: GatewayStatistics[]
                total_volume: number
                total_transactions: number
                overall_success_rate: number
            }>("/admin/payment-gateways/statistics/all")
            return response || { gateways: [], total_volume: 0, total_transactions: 0, overall_success_rate: 0 }
        } catch (error) {
            console.error("Failed to fetch gateway statistics:", error)
            return { gateways: [], total_volume: 0, total_transactions: 0, overall_success_rate: 0 }
        }
    },

    async getGatewayStatistic(provider: GatewayProvider): Promise<GatewayStatistics> {
        return await apiClient.get(`/admin/payment-gateways/${provider}/statistics`)
    },

    async initializeDefaultGateways(): Promise<PaymentGateway[]> {
        return await apiClient.post("/admin/payment-gateways/initialize")
    },

    // ============ Billing Dashboard ============
    async getBillingDashboard(): Promise<{
        subscription: Subscription | null
        usage: UsageMetrics
        invoices: Invoice[]
        payment_methods: PaymentMethod[]
    }> {
        const userId = getCurrentUserId()
        return await apiClient.get(`/billing/dashboard/${userId}`)
    },
}

export default billingApi
