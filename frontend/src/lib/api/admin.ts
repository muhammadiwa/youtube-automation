import apiClient from "./client"
import type { AdminUser, AdminAccessVerification, Admin2FAResponse } from "@/types/admin"

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

    /**
     * Get admin dashboard stats
     */
    async getDashboardStats(): Promise<{
        totalUsers: number
        activeUsers: number
        totalRevenue: number
        mrr: number
        arr: number
        activeStreams: number
        totalVideos: number
    }> {
        return apiClient.get("/admin/analytics/platform")
    },
}

export default adminApi
