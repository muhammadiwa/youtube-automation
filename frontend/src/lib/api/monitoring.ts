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

export const monitoringApi = {
    /**
     * Get all channel statuses for monitoring grid
     */
    async getChannelStatuses(filters?: MonitoringFilters): Promise<ChannelStatus[]> {
        try {
            const params = filters ? { ...filters } as Record<string, string | number | boolean | undefined> : undefined
            const response = await apiClient.get<ChannelStatus[] | { items: ChannelStatus[] }>("/monitoring/channels", params)

            if (Array.isArray(response)) {
                return response
            }
            if (response && typeof response === 'object' && 'items' in response) {
                return response.items
            }
            return []
        } catch (error) {
            console.error("Failed to fetch channel statuses:", error)
            return []
        }
    },

    /**
     * Get monitoring statistics summary
     */
    async getStats(): Promise<MonitoringStats> {
        try {
            return await apiClient.get("/monitoring/stats")
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
     */
    async getChannelDetails(accountId: string): Promise<ChannelStatus> {
        return apiClient.get(`/monitoring/channels/${accountId}`)
    },

    /**
     * Trigger a manual refresh for a channel
     */
    async refreshChannel(accountId: string): Promise<ChannelStatus> {
        return apiClient.post(`/monitoring/channels/${accountId}/refresh`)
    },
}

export default monitoringApi
