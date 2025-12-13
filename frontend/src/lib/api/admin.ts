import apiClient from "./client"
import type {
    AdminUser,
    AdminAccessVerification,
    Admin2FAResponse,
    PlatformMetrics,
    GrowthMetrics,
    RealtimeMetrics,
    ExportRequest,
    ExportResponse,
    UserFilters,
    UserListResponse,
    UserDetail,
    UserSuspendRequest,
    UserSuspendResponse,
    UserActivateResponse,
    ImpersonateRequest,
    ImpersonateResponse,
    PasswordResetResponse,
    UserStatsResponse,
    AdminSubscriptionFilters,
    AdminSubscriptionListResponse,
    AdminSubscription,
    SubscriptionUpgradeRequest,
    SubscriptionDowngradeRequest,
    SubscriptionExtendRequest,
    RefundRequest,
    RefundResponse,
    RevenueAnalytics,
} from "@/types/admin"

/**
 * Admin API client
 */
const adminApi = {
    /**
     * Check if current user is an admin
     */
    async checkAdminStatus(): Promise<AdminUser | null> {
        try {
            const response = await apiClient.get<{
                id: string
                user_id: string
                role: string
                permissions: string[]
                is_active: boolean
                last_login_at: string | null
                created_at: string
            }>("/admin/me")

            // Transform snake_case to camelCase
            return {
                id: response.id,
                userId: response.user_id,
                role: response.role as "admin" | "super_admin",
                permissions: response.permissions,
                isActive: response.is_active,
                lastLoginAt: response.last_login_at,
                createdAt: response.created_at,
            }
        } catch {
            return null
        }
    },

    /**
     * Verify admin access - checks if user has admin role
     * Returns admin info and whether 2FA is required
     */
    async verifyAdminAccess(): Promise<AdminAccessVerification> {
        const response = await apiClient.get<{
            is_admin: boolean
            admin_id: string
            role: string
            permissions: string[]
            requires_2fa: boolean
        }>("/admin/verify-access")

        // Transform snake_case to camelCase
        return {
            isAdmin: response.is_admin,
            adminId: response.admin_id,
            role: response.role as "admin" | "super_admin",
            permissions: response.permissions,
            requires2FA: response.requires_2fa,
        }
    },

    /**
     * Verify 2FA code for admin access
     * Returns admin session token on success
     */
    async verify2FA(totpCode: string): Promise<Admin2FAResponse> {
        const response = await apiClient.post<{
            verified: boolean
            admin_session_token: string
            expires_at: string
        }>("/admin/verify-2fa", {
            totp_code: totpCode,
        })

        // Transform snake_case to camelCase
        return {
            verified: response.verified,
            adminSessionToken: response.admin_session_token,
            expiresAt: response.expires_at,
        }
    },

    // ==================== Analytics API ====================

    /**
     * Get platform-wide metrics
     * Requirements: 2.1
     */
    async getPlatformMetrics(params?: {
        start_date?: string
        end_date?: string
    }): Promise<PlatformMetrics> {
        const searchParams = new URLSearchParams()
        if (params?.start_date) searchParams.set("start_date", params.start_date)
        if (params?.end_date) searchParams.set("end_date", params.end_date)
        const query = searchParams.toString()
        return apiClient.get(`/admin/analytics/platform${query ? `?${query}` : ""}`)
    },

    /**
     * Get growth metrics over time
     * Requirements: 2.2
     */
    async getGrowthMetrics(params?: {
        start_date?: string
        end_date?: string
        granularity?: "daily" | "weekly" | "monthly"
    }): Promise<GrowthMetrics> {
        const searchParams = new URLSearchParams()
        if (params?.start_date) searchParams.set("start_date", params.start_date)
        if (params?.end_date) searchParams.set("end_date", params.end_date)
        if (params?.granularity) searchParams.set("granularity", params.granularity)
        const query = searchParams.toString()
        return apiClient.get(`/admin/analytics/growth${query ? `?${query}` : ""}`)
    },

    /**
     * Get real-time platform metrics
     * Requirements: 2.3
     */
    async getRealtimeMetrics(): Promise<RealtimeMetrics> {
        return apiClient.get("/admin/analytics/realtime")
    },

    /**
     * Export dashboard data
     * Requirements: 2.5
     */
    async exportDashboard(data: ExportRequest): Promise<ExportResponse> {
        return apiClient.post("/admin/analytics/export", data)
    },

    /**
     * Get export status
     * Requirements: 2.5
     */
    async getExportStatus(exportId: string): Promise<ExportResponse> {
        return apiClient.get(`/admin/analytics/export/${exportId}`)
    },

    /**
     * Get export download URL
     * Requirements: 2.5
     */
    getExportDownloadUrl(exportId: string): string {
        return `/admin/analytics/export/${exportId}/download`
    },

    // ==================== User Management API ====================

    /**
     * Get user statistics for admin dashboard
     * Requirements: 3.1
     */
    async getUserStats(): Promise<UserStatsResponse> {
        return apiClient.get("/admin/users/stats")
    },

    /**
     * Get paginated list of users with filters
     * Requirements: 3.1
     */
    async getUsers(params: {
        page?: number
        page_size?: number
        filters?: UserFilters
    }): Promise<UserListResponse> {
        const searchParams = new URLSearchParams()
        if (params.page) searchParams.set("page", params.page.toString())
        if (params.page_size) searchParams.set("page_size", params.page_size.toString())
        if (params.filters?.status) searchParams.set("status", params.filters.status)
        if (params.filters?.plan) searchParams.set("plan", params.filters.plan)
        if (params.filters?.search) searchParams.set("search", params.filters.search)
        if (params.filters?.registered_after) searchParams.set("registered_after", params.filters.registered_after)
        if (params.filters?.registered_before) searchParams.set("registered_before", params.filters.registered_before)
        const query = searchParams.toString()
        return apiClient.get(`/admin/users${query ? `?${query}` : ""}`)
    },

    /**
     * Get detailed user information
     * Requirements: 3.2
     */
    async getUserDetail(userId: string): Promise<UserDetail> {
        return apiClient.get(`/admin/users/${userId}`)
    },

    /**
     * Suspend a user
     * Requirements: 3.3
     */
    async suspendUser(userId: string, data: UserSuspendRequest): Promise<UserSuspendResponse> {
        return apiClient.post(`/admin/users/${userId}/suspend`, data)
    },

    /**
     * Activate a suspended user
     * Requirements: 3.4
     */
    async activateUser(userId: string): Promise<UserActivateResponse> {
        return apiClient.post(`/admin/users/${userId}/activate`, {})
    },

    /**
     * Impersonate a user
     * Requirements: 3.5
     */
    async impersonateUser(userId: string, data?: ImpersonateRequest): Promise<ImpersonateResponse> {
        return apiClient.post(`/admin/users/${userId}/impersonate`, data || {})
    },

    /**
     * Reset user password
     * Requirements: 3.6
     */
    async resetUserPassword(userId: string): Promise<PasswordResetResponse> {
        return apiClient.post(`/admin/users/${userId}/reset-password`, {})
    },

    // ==================== Subscription Management API ====================

    /**
     * Get paginated list of subscriptions with filters
     * Requirements: 4.1
     */
    async getSubscriptions(params: {
        page?: number
        page_size?: number
        filters?: AdminSubscriptionFilters
    }): Promise<AdminSubscriptionListResponse> {
        const searchParams = new URLSearchParams()
        if (params.page) searchParams.set("page", params.page.toString())
        if (params.page_size) searchParams.set("page_size", params.page_size.toString())
        if (params.filters?.plan) searchParams.set("plan", params.filters.plan)
        if (params.filters?.status) searchParams.set("status", params.filters.status)
        if (params.filters?.user_search) searchParams.set("user_search", params.filters.user_search)
        const query = searchParams.toString()
        return apiClient.get(`/admin/subscriptions${query ? `?${query}` : ""}`)
    },

    /**
     * Get subscription details
     * Requirements: 4.1
     */
    async getSubscription(subscriptionId: string): Promise<AdminSubscription> {
        return apiClient.get(`/admin/subscriptions/${subscriptionId}`)
    },

    /**
     * Upgrade subscription to a higher plan
     * Requirements: 4.2
     */
    async upgradeSubscription(subscriptionId: string, data: SubscriptionUpgradeRequest): Promise<AdminSubscription> {
        return apiClient.post(`/admin/subscriptions/${subscriptionId}/upgrade`, data)
    },

    /**
     * Downgrade subscription to a lower plan
     * Requirements: 4.2
     */
    async downgradeSubscription(subscriptionId: string, data: SubscriptionDowngradeRequest): Promise<AdminSubscription> {
        return apiClient.post(`/admin/subscriptions/${subscriptionId}/downgrade`, data)
    },

    /**
     * Extend subscription by adding days
     * Requirements: 4.3
     */
    async extendSubscription(subscriptionId: string, data: SubscriptionExtendRequest): Promise<AdminSubscription> {
        return apiClient.post(`/admin/subscriptions/${subscriptionId}/extend`, data)
    },

    /**
     * Process refund for a payment
     * Requirements: 4.4
     */
    async processRefund(paymentId: string, data: RefundRequest): Promise<RefundResponse> {
        return apiClient.post(`/admin/payments/${paymentId}/refund`, data)
    },

    /**
     * Get revenue analytics
     * Requirements: 4.5
     */
    async getRevenueAnalytics(params?: {
        start_date?: string
        end_date?: string
    }): Promise<RevenueAnalytics> {
        const searchParams = new URLSearchParams()
        if (params?.start_date) searchParams.set("start_date", params.start_date)
        if (params?.end_date) searchParams.set("end_date", params.end_date)
        const query = searchParams.toString()
        return apiClient.get(`/admin/analytics/revenue${query ? `?${query}` : ""}`)
    },

    // ==================== Promotional API ====================

    /**
     * Get paginated list of discount codes
     * Requirements: 14.2
     */
    async getDiscountCodes(params: {
        page?: number
        page_size?: number
        is_active?: boolean
        search?: string
    }): Promise<import("@/types/admin").DiscountCodeListResponse> {
        const searchParams = new URLSearchParams()
        if (params.page) searchParams.set("page", params.page.toString())
        if (params.page_size) searchParams.set("page_size", params.page_size.toString())
        if (params.is_active !== undefined) searchParams.set("is_active", params.is_active.toString())
        if (params.search) searchParams.set("search", params.search)
        const query = searchParams.toString()
        return apiClient.get(`/admin/promotions/discount-codes${query ? `?${query}` : ""}`)
    },

    /**
     * Get discount code by ID
     * Requirements: 14.2
     */
    async getDiscountCode(discountCodeId: string): Promise<import("@/types/admin").DiscountCode> {
        return apiClient.get(`/admin/promotions/discount-codes/${discountCodeId}`)
    },

    /**
     * Create a new discount code
     * Requirements: 14.1
     */
    async createDiscountCode(data: import("@/types/admin").DiscountCodeCreateRequest): Promise<import("@/types/admin").DiscountCode> {
        return apiClient.post("/admin/promotions/discount-codes", data)
    },

    /**
     * Update a discount code
     * Requirements: 14.1
     */
    async updateDiscountCode(discountCodeId: string, data: import("@/types/admin").DiscountCodeUpdateRequest): Promise<import("@/types/admin").DiscountCode> {
        return apiClient.put(`/admin/promotions/discount-codes/${discountCodeId}`, data)
    },

    /**
     * Delete a discount code
     * Requirements: 14.2
     */
    async deleteDiscountCode(discountCodeId: string): Promise<void> {
        return apiClient.delete(`/admin/promotions/discount-codes/${discountCodeId}`)
    },

    /**
     * Validate a discount code
     * Requirements: 14.1
     */
    async validateDiscountCode(code: string, plan?: string): Promise<import("@/types/admin").DiscountCodeValidationResponse> {
        return apiClient.post("/admin/promotions/discount-codes/validate", { code, plan })
    },

    // ==================== Moderation API ====================

    /**
     * Get moderation queue with filters
     * Requirements: 6.1
     */
    async getModerationQueue(params: {
        page?: number
        page_size?: number
        filters?: import("@/types/admin").ModerationFilters
    }): Promise<import("@/types/admin").ContentReportListResponse> {
        const searchParams = new URLSearchParams()
        if (params.page) searchParams.set("page", params.page.toString())
        if (params.page_size) searchParams.set("page_size", params.page_size.toString())
        if (params.filters?.status) searchParams.set("status", params.filters.status)
        if (params.filters?.severity) searchParams.set("severity", params.filters.severity)
        if (params.filters?.content_type) searchParams.set("content_type", params.filters.content_type)
        if (params.filters?.search) searchParams.set("search", params.filters.search)
        const query = searchParams.toString()
        return apiClient.get(`/admin/moderation/queue${query ? `?${query}` : ""}`)
    },

    /**
     * Get report detail
     * Requirements: 6.2
     */
    async getReportDetail(reportId: string): Promise<import("@/types/admin").ContentReportDetail> {
        return apiClient.get(`/admin/moderation/reports/${reportId}`)
    },

    /**
     * Approve content and dismiss reports
     * Requirements: 6.3
     */
    async approveContent(reportId: string, data?: import("@/types/admin").ContentApproveRequest): Promise<import("@/types/admin").ContentApproveResponse> {
        return apiClient.post(`/admin/moderation/reports/${reportId}/approve`, data || {})
    },

    /**
     * Remove content
     * Requirements: 6.4
     */
    async removeContent(reportId: string, data: import("@/types/admin").ContentRemoveRequest): Promise<import("@/types/admin").ContentRemoveResponse> {
        return apiClient.post(`/admin/moderation/reports/${reportId}/remove`, data)
    },

    /**
     * Warn a user
     * Requirements: 6.5
     */
    async warnUser(userId: string, data: import("@/types/admin").UserWarnRequest): Promise<import("@/types/admin").UserWarnResponse> {
        return apiClient.post(`/admin/moderation/users/${userId}/warn`, data)
    },

    // ==================== System Monitoring API ====================

    /**
     * Get system health status
     * Requirements: 7.1, 7.2
     */
    async getSystemHealth(): Promise<import("@/types/admin").SystemHealthResponse> {
        return apiClient.get("/admin/system/health")
    },

    /**
     * Get job queue status
     * Requirements: 7.3
     */
    async getJobQueueStatus(): Promise<import("@/types/admin").JobQueueResponse> {
        return apiClient.get("/admin/system/jobs")
    },

    /**
     * Get worker status
     * Requirements: 7.4
     */
    async getWorkerStatus(): Promise<import("@/types/admin").WorkerStatusResponse> {
        return apiClient.get("/admin/system/workers")
    },

    /**
     * Restart a worker
     * Requirements: 12.2
     */
    async restartWorker(workerId: string, data?: import("@/types/admin").WorkerRestartRequest): Promise<import("@/types/admin").WorkerRestartResponse> {
        return apiClient.post(`/admin/system/workers/${workerId}/restart`, data || {})
    },

    /**
     * Get error alerts
     * Requirements: 7.5
     */
    async getErrorAlerts(limit?: number): Promise<import("@/types/admin").ErrorAlertsResponse> {
        const searchParams = new URLSearchParams()
        if (limit) searchParams.set("limit", limit.toString())
        const query = searchParams.toString()
        return apiClient.get(`/admin/system/alerts${query ? `?${query}` : ""}`)
    },

    // ==================== Quota Management API ====================

    /**
     * Get quota dashboard
     * Requirements: 11.1
     */
    async getQuotaDashboard(): Promise<import("@/types/admin").QuotaDashboardResponse> {
        return apiClient.get("/admin/quota")
    },

    /**
     * Get quota alerts
     * Requirements: 11.2
     */
    async getQuotaAlerts(): Promise<import("@/types/admin").QuotaAlertsResponse> {
        return apiClient.get("/admin/quota/alerts")
    },

    // ==================== Compliance & Audit API ====================

    /**
     * Get audit logs with filtering
     * Requirements: 8.1, 8.2
     */
    async getAuditLogs(
        page: number = 1,
        pageSize: number = 20,
        filters?: import("@/types/admin").AuditLogFilters
    ): Promise<import("@/types/admin").AuditLogListResponse> {
        const searchParams = new URLSearchParams()
        searchParams.set("page", page.toString())
        searchParams.set("page_size", pageSize.toString())
        if (filters?.date_from) searchParams.set("date_from", filters.date_from)
        if (filters?.date_to) searchParams.set("date_to", filters.date_to)
        if (filters?.actor_id) searchParams.set("actor_id", filters.actor_id)
        if (filters?.action_type) searchParams.set("action_type", filters.action_type)
        if (filters?.resource_type) searchParams.set("resource_type", filters.resource_type)
        if (filters?.resource_id) searchParams.set("resource_id", filters.resource_id)
        if (filters?.event_type) searchParams.set("event_type", filters.event_type)
        if (filters?.search) searchParams.set("search", filters.search)
        return apiClient.get(`/admin/audit-logs?${searchParams.toString()}`)
    },

    /**
     * Export audit logs
     * Requirements: 8.3
     */
    async exportAuditLogs(
        data: import("@/types/admin").AuditLogExportRequest
    ): Promise<import("@/types/admin").AuditLogExportResponse> {
        return apiClient.post("/admin/audit-logs/export", data)
    },

    /**
     * Get security dashboard
     * Requirements: 8.4, 8.5
     */
    async getSecurityDashboard(): Promise<import("@/types/admin").SecurityDashboardResponse> {
        return apiClient.get("/admin/security")
    },

    /**
     * Get data export requests
     * Requirements: 15.1
     */
    async getDataExportRequests(
        page: number = 1,
        pageSize: number = 20,
        status?: string
    ): Promise<import("@/types/admin").DataExportRequestListResponse> {
        const searchParams = new URLSearchParams()
        searchParams.set("page", page.toString())
        searchParams.set("page_size", pageSize.toString())
        if (status) searchParams.set("status", status)
        return apiClient.get(`/admin/compliance/export-requests?${searchParams.toString()}`)
    },

    /**
     * Process data export request
     * Requirements: 15.1
     */
    async processDataExport(
        requestId: string
    ): Promise<import("@/types/admin").ProcessDataExportResponse> {
        return apiClient.post(`/admin/compliance/export-requests/${requestId}/process`, {})
    },

    /**
     * Download data export
     * Requirements: 15.1
     */
    async downloadDataExport(
        requestId: string
    ): Promise<Record<string, unknown>> {
        return apiClient.get(`/admin/compliance/exports/${requestId}/download`)
    },

    /**
     * Get deletion requests
     * Requirements: 15.2
     */
    async getDeletionRequests(
        page: number = 1,
        pageSize: number = 20,
        status?: string
    ): Promise<import("@/types/admin").DeletionRequestListResponse> {
        const searchParams = new URLSearchParams()
        searchParams.set("page", page.toString())
        searchParams.set("page_size", pageSize.toString())
        if (status) searchParams.set("status", status)
        return apiClient.get(`/admin/compliance/deletion-requests?${searchParams.toString()}`)
    },

    /**
     * Process deletion request
     * Requirements: 15.2
     */
    async processDeletion(
        requestId: string
    ): Promise<import("@/types/admin").ProcessDeletionResponse> {
        return apiClient.post(`/admin/compliance/deletion-requests/${requestId}/process`, {})
    },

    /**
     * Cancel deletion request
     * Requirements: 15.2
     */
    async cancelDeletion(
        requestId: string,
        data?: import("@/types/admin").CancelDeletionRequest
    ): Promise<import("@/types/admin").CancelDeletionResponse> {
        return apiClient.post(`/admin/compliance/deletion-requests/${requestId}/cancel`, data || {})
    },

    // ==================== Payment Gateway API ====================

    /**
     * Get all payment gateways
     * Requirements: 5.1
     */
    async getPaymentGateways(): Promise<PaymentGateway[]> {
        // Backend returns array directly, not wrapped in { items: [...] }
        return apiClient.get<PaymentGateway[]>("/admin/payment-gateways")
    },

    /**
     * Update gateway status (enable/disable)
     * Requirements: 5.2
     */
    async updateGatewayStatus(
        provider: string,
        data: { is_enabled: boolean; reason?: string }
    ): Promise<{ provider: string; is_enabled: boolean; updated_at: string; message: string }> {
        return apiClient.put(`/admin/payment-gateways/${provider}/status`, data)
    },

    /**
     * Update gateway credentials
     * Requirements: 5.3
     */
    async updateGatewayCredentials(
        provider: string,
        credentials: {
            api_key: string
            api_secret: string
            webhook_secret?: string
            sandbox_mode: boolean
        }
    ): Promise<{ provider: string; credentials_valid: boolean; sandbox_mode: boolean; updated_at: string; message: string }> {
        return apiClient.put(`/admin/payment-gateways/${provider}/credentials`, {
            ...credentials,
            validate_before_save: true,
        })
    },

    /**
     * Set gateway as default
     * Requirements: 5.2
     */
    async setDefaultGateway(
        provider: string
    ): Promise<{ provider: string; is_default: boolean; updated_at: string; message: string }> {
        return apiClient.put(`/admin/payment-gateways/${provider}/default`, {})
    },

    /**
     * Get gateway statistics
     * Requirements: 5.4
     */
    async getGatewayStats(
        provider: string,
        params?: { start_date?: string; end_date?: string }
    ): Promise<GatewayStatsResponse> {
        const searchParams = new URLSearchParams()
        if (params?.start_date) searchParams.set("start_date", params.start_date)
        if (params?.end_date) searchParams.set("end_date", params.end_date)
        const query = searchParams.toString()
        return apiClient.get(`/admin/payment-gateways/${provider}/stats${query ? `?${query}` : ""}`)
    },

    /**
     * Get gateway health
     * Requirements: 5.5
     */
    async getGatewayHealth(provider: string): Promise<GatewayHealthAlert> {
        return apiClient.get(`/admin/payment-gateways/${provider}/health`)
    },
}

// Payment Gateway types for admin API - matches backend response exactly
interface PaymentGateway {
    id: string
    provider: string
    display_name: string
    is_enabled: boolean
    is_default: boolean
    sandbox_mode: boolean
    has_credentials: boolean
    supported_currencies: string[]
    supported_payment_methods: string[]
    transaction_fee_percent: number
    fixed_fee: number
    min_amount: number
    max_amount: number | null
    created_at: string
    updated_at: string
}

interface GatewayStatsResponse {
    stats: {
        provider: string
        display_name: string
        primary_currency: string
        total_transactions: number
        successful_transactions: number
        failed_transactions: number
        success_rate: number
        failure_rate: number
        success_rate_24h: number
        // Volume in original currency
        total_volume: number
        average_transaction: number
        // Volume converted to USD for comparison
        total_volume_usd: number
        average_transaction_usd: number
        transactions_24h: number
        volume_24h: number
        volume_24h_usd: number
        health_status: string
        last_transaction_at?: string
        last_success_at?: string
        last_failure_at?: string
        stats_since?: string
    }
    period_start?: string
    period_end?: string
}

interface GatewayHealthAlert {
    id: string
    provider: string
    alert_type: string
    severity: string
    message: string
    health_status: string
    success_rate: number
    suggested_action?: string
    alternative_gateways: string[]
    created_at: string
    acknowledged: boolean
    acknowledged_at?: string
    acknowledged_by?: string
}

export default adminApi
