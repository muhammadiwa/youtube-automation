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
            const response = await apiClient.get<AdminUser>("/admin/me")
            return response
        } catch {
            return null
        }
    },

    /**
     * Verify admin access - checks if user has admin role
     * Returns admin info and whether 2FA is required
     */
    async verifyAdminAccess(): Promise<AdminAccessVerification> {
        return apiClient.get<AdminAccessVerification>("/admin/verify-access")
    },

    /**
     * Verify 2FA code for admin access
     * Returns admin session token on success
     */
    async verify2FA(totpCode: string): Promise<Admin2FAResponse> {
        return apiClient.post<Admin2FAResponse>("/admin/verify-2fa", {
            totp_code: totpCode,
        })
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
}

export default adminApi
