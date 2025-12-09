import apiClient from "./client"

// ============ Subscription Types ============
export interface Subscription {
    id: string
    user_id: string
    plan: "free" | "basic" | "pro" | "enterprise"
    status: "active" | "cancelled" | "expired" | "past_due"
    current_period_start: string
    current_period_end: string
    cancel_at_period_end: boolean
    created_at: string
    updated_at: string
}

export interface Plan {
    id: string
    name: string
    slug: "free" | "basic" | "pro" | "enterprise"
    price_monthly: number
    price_yearly: number
    features: PlanFeature[]
    limits: PlanLimits
}

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

export const billingApi = {
    // ============ Subscription ============
    async getSubscription(): Promise<Subscription | null> {
        try {
            return await apiClient.get("/billing/subscription")
        } catch (error) {
            return null
        }
    },

    async getPlans(): Promise<Plan[]> {
        try {
            return await apiClient.get("/billing/plans")
        } catch (error) {
            // Return default plans for development
            return [
                {
                    id: "free",
                    name: "Free",
                    slug: "free",
                    price_monthly: 0,
                    price_yearly: 0,
                    features: [
                        { name: "1 YouTube Account", included: true },
                        { name: "5 Videos/month", included: true },
                        { name: "Basic Analytics", included: true },
                        { name: "AI Features", included: false },
                        { name: "Live Streaming", included: false },
                    ],
                    limits: {
                        max_accounts: 1,
                        max_videos_per_month: 5,
                        max_streams_per_month: 0,
                        max_storage_gb: 1,
                        max_bandwidth_gb: 5,
                        ai_generations_per_month: 0,
                    },
                },
                {
                    id: "basic",
                    name: "Basic",
                    slug: "basic",
                    price_monthly: 9.99,
                    price_yearly: 99.99,
                    features: [
                        { name: "3 YouTube Accounts", included: true },
                        { name: "50 Videos/month", included: true },
                        { name: "Advanced Analytics", included: true },
                        { name: "AI Features (100/month)", included: true },
                        { name: "Live Streaming (5/month)", included: true },
                    ],
                    limits: {
                        max_accounts: 3,
                        max_videos_per_month: 50,
                        max_streams_per_month: 5,
                        max_storage_gb: 10,
                        max_bandwidth_gb: 50,
                        ai_generations_per_month: 100,
                    },
                },
                {
                    id: "pro",
                    name: "Pro",
                    slug: "pro",
                    price_monthly: 29.99,
                    price_yearly: 299.99,
                    features: [
                        { name: "10 YouTube Accounts", included: true },
                        { name: "Unlimited Videos", included: true },
                        { name: "Full Analytics Suite", included: true },
                        { name: "AI Features (500/month)", included: true },
                        { name: "Unlimited Streaming", included: true },
                    ],
                    limits: {
                        max_accounts: 10,
                        max_videos_per_month: -1,
                        max_streams_per_month: -1,
                        max_storage_gb: 100,
                        max_bandwidth_gb: 500,
                        ai_generations_per_month: 500,
                    },
                },
                {
                    id: "enterprise",
                    name: "Enterprise",
                    slug: "enterprise",
                    price_monthly: 99.99,
                    price_yearly: 999.99,
                    features: [
                        { name: "Unlimited Accounts", included: true },
                        { name: "Unlimited Everything", included: true },
                        { name: "Priority Support", included: true },
                        { name: "Custom Integrations", included: true },
                        { name: "Dedicated Account Manager", included: true },
                    ],
                    limits: {
                        max_accounts: -1,
                        max_videos_per_month: -1,
                        max_streams_per_month: -1,
                        max_storage_gb: -1,
                        max_bandwidth_gb: -1,
                        ai_generations_per_month: -1,
                    },
                },
            ]
        }
    },

    async subscribeToPlan(planId: string, billingCycle: "monthly" | "yearly"): Promise<{ checkout_url: string }> {
        return await apiClient.post("/billing/subscribe", { plan_id: planId, billing_cycle: billingCycle })
    },

    async cancelSubscription(): Promise<Subscription> {
        return await apiClient.post("/billing/subscription/cancel")
    },

    async resumeSubscription(): Promise<Subscription> {
        return await apiClient.post("/billing/subscription/resume")
    },

    // ============ Usage ============
    async getUsage(): Promise<UsageMetrics> {
        try {
            return await apiClient.get("/billing/usage")
        } catch (error) {
            return {
                accounts_used: 0,
                accounts_limit: 1,
                videos_uploaded: 0,
                videos_limit: 5,
                streams_created: 0,
                streams_limit: 0,
                storage_used_gb: 0,
                storage_limit_gb: 1,
                bandwidth_used_gb: 0,
                bandwidth_limit_gb: 5,
                ai_generations_used: 0,
                ai_generations_limit: 0,
                period_start: new Date().toISOString(),
                period_end: new Date().toISOString(),
            }
        }
    },

    async getUsageWarnings(): Promise<UsageWarning[]> {
        try {
            return await apiClient.get("/billing/usage/warnings")
        } catch (error) {
            return []
        }
    },

    async exportUsage(format: "csv" | "json"): Promise<{ download_url: string }> {
        return await apiClient.get("/billing/usage/export", { format })
    },

    // ============ Invoices ============
    async getInvoices(): Promise<Invoice[]> {
        try {
            return await apiClient.get("/billing/invoices")
        } catch (error) {
            return []
        }
    },

    async getInvoice(invoiceId: string): Promise<Invoice> {
        return await apiClient.get(`/billing/invoices/${invoiceId}`)
    },

    // ============ Payment Methods ============
    async getPaymentMethods(): Promise<PaymentMethod[]> {
        try {
            return await apiClient.get("/billing/payment-methods")
        } catch (error) {
            return []
        }
    },

    async addPaymentMethod(data: { type: string; token: string }): Promise<PaymentMethod> {
        return await apiClient.post("/billing/payment-methods", data)
    },

    async setDefaultPaymentMethod(methodId: string): Promise<PaymentMethod> {
        return await apiClient.post(`/billing/payment-methods/${methodId}/default`)
    },

    async removePaymentMethod(methodId: string): Promise<void> {
        return await apiClient.delete(`/billing/payment-methods/${methodId}`)
    },
}

export default billingApi
