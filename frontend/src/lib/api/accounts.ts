import apiClient from "./client"
import type { YouTubeAccount } from "@/types"

export interface AccountHealth {
    status: "active" | "expired" | "error"
    tokenExpiresAt: string
    quotaUsage: number
    quotaLimit: number
    lastSyncAt: string
}

export interface QuotaUsage {
    used: number
    limit: number
    percentage: number
}

export interface OAuthUrl {
    url: string
    state: string
}

export interface AccountFilters {
    status?: "active" | "expired" | "error"
    search?: string
}

export const accountsApi = {
    /**
     * Get all YouTube accounts for current user
     */
    async getAccounts(filters?: AccountFilters): Promise<YouTubeAccount[]> {
        try {
            const params = filters ? { ...filters } as Record<string, string | number | boolean | undefined> : undefined
            const response = await apiClient.get<YouTubeAccount[] | { items: YouTubeAccount[] } | { accounts: YouTubeAccount[] }>("/accounts", params)

            // Handle different response formats
            if (Array.isArray(response)) {
                return response
            }
            if (response && typeof response === 'object') {
                if ('items' in response && Array.isArray(response.items)) {
                    return response.items
                }
                if ('accounts' in response && Array.isArray(response.accounts)) {
                    return response.accounts
                }
            }
            return []
        } catch (error) {
            console.error("Failed to fetch accounts:", error)
            return []
        }
    },

    /**
     * Get single YouTube account by ID
     */
    async getAccount(accountId: string): Promise<YouTubeAccount> {
        return apiClient.get(`/accounts/${accountId}`)
    },

    /**
     * Get account health status
     */
    async getAccountHealth(accountId: string): Promise<AccountHealth> {
        return apiClient.get(`/accounts/${accountId}/health`)
    },

    /**
     * Get quota usage for account
     */
    async getQuotaUsage(accountId: string): Promise<QuotaUsage> {
        return apiClient.get(`/accounts/${accountId}/quota`)
    },

    /**
     * Initiate OAuth flow to connect new account
     */
    async initiateOAuth(): Promise<OAuthUrl> {
        return apiClient.post("/accounts/oauth/initiate")
    },

    /**
     * Handle OAuth callback
     */
    async handleOAuthCallback(code: string, state: string): Promise<YouTubeAccount> {
        return apiClient.post("/accounts/oauth/callback", { code, state })
    },

    /**
     * Manually refresh account token
     */
    async refreshToken(accountId: string): Promise<void> {
        return apiClient.post(`/accounts/${accountId}/refresh-token`)
    },

    /**
     * Disconnect/remove account
     */
    async disconnectAccount(accountId: string): Promise<void> {
        return apiClient.delete(`/accounts/${accountId}`)
    },

    /**
     * Sync account data from YouTube
     */
    async syncAccount(accountId: string): Promise<YouTubeAccount> {
        return apiClient.post(`/accounts/${accountId}/sync`)
    },
}

export default accountsApi
