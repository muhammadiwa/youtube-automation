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
}

export default adminApi
