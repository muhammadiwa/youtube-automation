import apiClient from "./client"
import type { YouTubeAccount } from "@/types"

// ============ Monitoring Types ============
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
            const response = await apiClient.get<ChannelGridResponse>("/monitoring/channels", params)

            if (response && typeof response === 'object' && 'items' in response) {
                return response.items
            }
            if (Array.isArray(response)) {
                return response
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
