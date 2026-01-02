import apiClient from "./client"
import type { YouTubeAccount } from "@/types"

// ============ Monitoring Types ============

// Backend response types (snake_case)
interface BackendChannelGridItem {
    account_id: string
    channel_id: string
    channel_title: string
    thumbnail_url?: string | null
    subscriber_count: number
    video_count: number
    view_count: number
    status: "live" | "scheduled" | "offline" | "error" | "token_expired"
    is_monetized: boolean
    has_live_streaming_enabled: boolean
    strike_count: number
    token_expires_at?: string | null
    is_token_expired: boolean
    is_token_expiring_soon: boolean
    daily_quota_used: number
    quota_usage_percent: number
    current_stream_id?: string | null
    current_stream_title?: string | null
    current_viewer_count?: number | null
    stream_started_at?: string | null
    next_scheduled_stream_id?: string | null
    next_scheduled_stream_title?: string | null
    next_scheduled_at?: string | null
    has_critical_issue: boolean
    issues: Array<{
        severity: "critical" | "warning" | "info"
        message: string
        detected_at: string
    }>
    last_sync_at?: string | null
    last_error?: string | null
}

interface BackendChannelGridResponse {
    channels: BackendChannelGridItem[]
    total: number
    filtered_count: number
    filters_applied: string[]
}

// Frontend types (camelCase)
export interface ChannelStatus {
    accountId: string
    account: YouTubeAccount
    streamStatus: "live" | "scheduled" | "offline" | "error"
    currentViewers?: number
    currentStreamId?: string
    currentStreamTitle?: string
    healthStatus: "healthy" | "warning" | "critical" | "offline"
    lastActivity?: string
    uptime?: number
    bitrate?: number
    droppedFrames?: number
    tokenStatus: "valid" | "expiring" | "expired"
    quotaUsage: number
    quotaLimit: number
    hasActiveAlerts: boolean
    alertCount: number
}

export interface MonitoringFilters {
    status?: "all" | "live" | "scheduled" | "offline" | "error"
    healthStatus?: "all" | "healthy" | "warning" | "critical"
    tokenStatus?: "all" | "valid" | "expiring" | "expired"
    search?: string
}

export interface MonitoringStats {
    totalChannels: number
    liveChannels: number
    scheduledChannels: number
    offlineChannels: number
    errorChannels: number
    healthyChannels: number
    warningChannels: number
    criticalChannels: number
}

export interface ChannelGridResponse {
    items: ChannelStatus[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface LayoutPreferences {
    grid_size: "small" | "medium" | "large"
    auto_refresh: boolean
    refresh_interval: number
    displayed_metrics: string[]
}

// Transform backend channel to frontend format
function transformChannel(channel: BackendChannelGridItem): ChannelStatus {
    // Determine health status based on issues
    let healthStatus: "healthy" | "warning" | "critical" | "offline" = "healthy"
    if (channel.has_critical_issue || channel.is_token_expired || channel.status === "error") {
        healthStatus = "critical"
    } else if (channel.is_token_expiring_soon || channel.quota_usage_percent >= 80) {
        healthStatus = "warning"
    } else if (channel.status === "offline") {
        healthStatus = "offline"
    }

    // Determine token status
    let tokenStatus: "valid" | "expiring" | "expired" = "valid"
    if (channel.is_token_expired) {
        tokenStatus = "expired"
    } else if (channel.is_token_expiring_soon) {
        tokenStatus = "expiring"
    }

    // Map status (token_expired -> error for frontend)
    const streamStatus = channel.status === "token_expired" ? "error" : channel.status

    return {
        accountId: channel.account_id,
        account: {
            id: channel.account_id,
            userId: "",
            channelId: channel.channel_id,
            channelTitle: channel.channel_title,
            thumbnailUrl: channel.thumbnail_url || "",
            subscriberCount: channel.subscriber_count,
            videoCount: channel.video_count,
            isMonetized: channel.is_monetized,
            hasLiveStreamingEnabled: channel.has_live_streaming_enabled,
            strikeCount: channel.strike_count,
            tokenExpiresAt: channel.token_expires_at || "",
            lastSyncAt: channel.last_sync_at || "",
            status: channel.is_token_expired ? "expired" : (channel.status === "error" ? "error" : "active"),
            hasStreamKey: false,
            streamKeyMasked: null,
            rtmpUrl: null,
        },
        streamStatus,
        currentViewers: channel.current_viewer_count || undefined,
        currentStreamId: channel.current_stream_id || undefined,
        currentStreamTitle: channel.current_stream_title || undefined,
        healthStatus,
        lastActivity: channel.last_sync_at || undefined,
        tokenStatus,
        quotaUsage: channel.daily_quota_used,
        quotaLimit: 10000,
        hasActiveAlerts: channel.has_critical_issue || channel.issues.length > 0,
        alertCount: channel.issues.length,
    }
}

export const monitoringApi = {
    /**
     * Get all channel statuses for monitoring grid
     * Backend: GET /monitoring/channels
     */
    async getChannelStatuses(filters?: MonitoringFilters): Promise<ChannelStatus[]> {
        try {
            const params: Record<string, string | number | boolean | undefined> = {
                status_filter: filters?.status !== "all" ? filters?.status : undefined,
                search: filters?.search,
                page: 1,
                page_size: 50,
            }
            const response = await apiClient.get<BackendChannelGridResponse>("/monitoring/channels", params)

            if (response && typeof response === 'object' && 'channels' in response) {
                return response.channels.map(transformChannel)
            }
            return []
        } catch (error) {
            console.error("Failed to fetch channel statuses:", error)
            return []
        }
    },

    /**
     * Get monitoring statistics summary (computed from channel data)
     */
    async getStats(): Promise<MonitoringStats> {
        try {
            // Backend doesn't have a dedicated stats endpoint, compute from channels
            const channels = await this.getChannelStatuses()
            return {
                totalChannels: channels.length,
                liveChannels: channels.filter(c => c.streamStatus === "live").length,
                scheduledChannels: channels.filter(c => c.streamStatus === "scheduled").length,
                offlineChannels: channels.filter(c => c.streamStatus === "offline").length,
                errorChannels: channels.filter(c => c.streamStatus === "error").length,
                healthyChannels: channels.filter(c => c.healthStatus === "healthy").length,
                warningChannels: channels.filter(c => c.healthStatus === "warning").length,
                criticalChannels: channels.filter(c => c.healthStatus === "critical").length,
            }
        } catch (error) {
            console.error("Failed to fetch monitoring stats:", error)
            return {
                totalChannels: 0,
                liveChannels: 0,
                scheduledChannels: 0,
                offlineChannels: 0,
                errorChannels: 0,
                healthyChannels: 0,
                warningChannels: 0,
                criticalChannels: 0,
            }
        }
    },

    /**
     * Get detailed metrics for a specific channel
     * Backend: GET /monitoring/channels/{account_id}
     */
    async getChannelDetails(accountId: string): Promise<ChannelStatus> {
        return apiClient.get(`/monitoring/channels/${accountId}`)
    },

    /**
     * Get user's layout preferences
     * Backend: GET /monitoring/preferences
     */
    async getLayoutPreferences(): Promise<LayoutPreferences> {
        try {
            return await apiClient.get("/monitoring/preferences")
        } catch {
            return {
                grid_size: "medium",
                auto_refresh: true,
                refresh_interval: 30,
                displayed_metrics: ["viewers", "health", "quota"],
            }
        }
    },

    /**
     * Update user's layout preferences
     * Backend: PUT /monitoring/preferences
     */
    async updateLayoutPreferences(prefs: Partial<LayoutPreferences>): Promise<LayoutPreferences> {
        return apiClient.put("/monitoring/preferences", prefs)
    },

    /**
     * Trigger a manual refresh for a channel (re-fetch from YouTube API)
     */
    async refreshChannel(accountId: string): Promise<ChannelStatus> {
        // This would trigger a backend job to refresh channel data
        return apiClient.get(`/monitoring/channels/${accountId}`)
    },
}

export default monitoringApi
