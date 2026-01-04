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
    authorization_url?: string  // Backend returns this
    state: string
}

export interface AccountFilters {
    status?: "active" | "expired" | "error"
    search?: string
}

// Backend response type (snake_case)
interface BackendYouTubeAccount {
    id: string
    user_id: string
    channel_id: string
    channel_title: string
    thumbnail_url?: string | null
    subscriber_count: number
    video_count: number
    view_count?: number
    is_monetized: boolean
    has_live_streaming_enabled: boolean
    strike_count: number
    token_expires_at?: string | null
    daily_quota_used?: number
    status: "active" | "expired" | "error"
    last_sync_at?: string | null
    // Stream key info
    has_stream_key?: boolean
    stream_key_masked?: string | null
    rtmp_url?: string | null
    created_at?: string
    updated_at?: string
}

// Transform backend response to frontend format
function transformAccount(account: BackendYouTubeAccount): YouTubeAccount {
    return {
        id: account.id,
        userId: account.user_id,
        channelId: account.channel_id,
        channelTitle: account.channel_title,
        thumbnailUrl: account.thumbnail_url || "",
        subscriberCount: account.subscriber_count || 0,
        videoCount: account.video_count || 0,
        viewCount: account.view_count || 0,
        isMonetized: account.is_monetized || false,
        hasLiveStreamingEnabled: account.has_live_streaming_enabled || false,
        strikeCount: account.strike_count || 0,
        tokenExpiresAt: account.token_expires_at || "",
        lastSyncAt: account.last_sync_at || "",
        status: account.status || "error",
        hasStreamKey: account.has_stream_key || false,
        streamKeyMasked: account.stream_key_masked || null,
        rtmpUrl: account.rtmp_url || null,
    }
}

export const accountsApi = {
    /**
     * Get all YouTube accounts for current user
     */
    async getAccounts(filters?: AccountFilters): Promise<YouTubeAccount[]> {
        try {
            const params = filters ? { ...filters } as Record<string, string | number | boolean | undefined> : undefined

            const response = await apiClient.get<BackendYouTubeAccount[] | { items: BackendYouTubeAccount[] } | { accounts: BackendYouTubeAccount[] }>("/accounts", params)

            // Handle different response formats and transform
            let accounts: BackendYouTubeAccount[] = []
            if (Array.isArray(response)) {
                accounts = response
            } else if (response && typeof response === 'object') {
                if ('items' in response && Array.isArray(response.items)) {
                    accounts = response.items
                } else if ('accounts' in response && Array.isArray(response.accounts)) {
                    accounts = response.accounts
                }
            }

            return accounts.map(transformAccount)
        } catch (error) {
            console.error("[accountsApi.getAccounts] Failed to fetch accounts:", error)
            return []
        }
    },

    /**
     * Get single YouTube account by ID
     */
    async getAccount(accountId: string): Promise<YouTubeAccount> {
        const response = await apiClient.get<BackendYouTubeAccount>(`/accounts/${accountId}`)
        return transformAccount(response)
    },

    /**
     * Get account health status
     */
    async getAccountHealth(accountId: string): Promise<AccountHealth> {
        const response = await apiClient.get<{
            account_id: string
            channel_title: string
            status: "active" | "expired" | "error"
            is_token_expired: boolean
            is_token_expiring_soon: boolean
            token_expires_at?: string | null
            quota_usage_percent: number
            daily_quota_used: number
            last_sync_at?: string | null
            last_error?: string | null
        }>(`/accounts/${accountId}/health`)
        return {
            status: response.status,
            tokenExpiresAt: response.token_expires_at || "",
            quotaUsage: response.daily_quota_used,
            quotaLimit: 10000,
            lastSyncAt: response.last_sync_at || "",
        }
    },

    /**
     * Get quota usage for account
     */
    async getQuotaUsage(accountId: string): Promise<QuotaUsage> {
        const response = await apiClient.get<{
            account_id: string
            daily_quota_used: number
            daily_limit: number
            usage_percent: number
            quota_reset_at?: string | null
            is_approaching_limit: boolean
        }>(`/accounts/${accountId}/quota`)
        return {
            used: response.daily_quota_used,
            limit: response.daily_limit,
            percentage: response.usage_percent,
        }
    },

    /**
     * Initiate OAuth flow to connect new account
     */
    async initiateOAuth(): Promise<OAuthUrl> {
        const response = await apiClient.post<{ authorization_url: string; state: string }>("/accounts/oauth/initiate")
        // Map backend response to frontend expected format
        return {
            url: response.authorization_url,
            authorization_url: response.authorization_url,
            state: response.state,
        }
    },

    /**
     * Handle OAuth callback
     * Note: This is typically handled by backend redirect, but kept for compatibility
     */
    async handleOAuthCallback(code: string, state: string): Promise<YouTubeAccount> {
        const response = await apiClient.post<BackendYouTubeAccount>("/accounts/oauth/callback", { code, state })
        return transformAccount(response)
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
        const response = await apiClient.post<BackendYouTubeAccount>(`/accounts/${accountId}/sync`)
        return transformAccount(response)
    },

    /**
     * Sync stream key from YouTube Live Streaming API
     */
    async syncStreamKey(accountId: string): Promise<{
        success: boolean
        message: string
        hasStreamKey: boolean
        streamKeyMasked: string | null
        rtmpUrl: string | null
    }> {
        const response = await apiClient.post<{
            success: boolean
            message: string
            has_stream_key: boolean
            stream_key_masked: string | null
            rtmp_url: string | null
        }>(`/accounts/${accountId}/sync-stream-key`)
        return {
            success: response.success,
            message: response.message,
            hasStreamKey: response.has_stream_key,
            streamKeyMasked: response.stream_key_masked,
            rtmpUrl: response.rtmp_url,
        }
    },

    /**
     * Get stream key status for account
     */
    async getStreamKeyStatus(accountId: string): Promise<{
        accountId: string
        channelTitle: string
        hasStreamKey: boolean
        streamKeyMasked: string | null
        streamKey: string | null
        rtmpUrl: string | null
        defaultStreamId: string | null
        hasLiveStreamingEnabled: boolean
        lastSyncAt: string | null
    }> {
        const response = await apiClient.get<{
            account_id: string
            channel_title: string
            has_stream_key: boolean
            stream_key_masked: string | null
            stream_key: string | null
            rtmp_url: string | null
            default_stream_id: string | null
            has_live_streaming_enabled: boolean
            last_sync_at: string | null
        }>(`/accounts/${accountId}/stream-key-status`)
        return {
            accountId: response.account_id,
            channelTitle: response.channel_title,
            hasStreamKey: response.has_stream_key,
            streamKeyMasked: response.stream_key_masked,
            streamKey: response.stream_key,
            rtmpUrl: response.rtmp_url,
            defaultStreamId: response.default_stream_id,
            hasLiveStreamingEnabled: response.has_live_streaming_enabled,
            lastSyncAt: response.last_sync_at,
        }
    },
}

export default accountsApi
