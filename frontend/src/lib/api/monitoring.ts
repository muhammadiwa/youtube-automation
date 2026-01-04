/**
 * Monitoring API Client - Live Control Center
 * 
 * All data is fetched from backend - no mock data.
 */

import apiClient from "./client"

// ============================================================================
// Types - Match backend schemas exactly
// ============================================================================

export type StreamStatus = "live" | "scheduled" | "offline" | "ended"
export type HealthStatus = "healthy" | "warning" | "critical"
export type AlertSeverity = "critical" | "warning" | "info"
export type AlertType =
    | "token_expired"
    | "token_expiring"
    | "quota_high"
    | "quota_critical"
    | "stream_dropped"
    | "strike_detected"
    | "account_error"
    | "viewer_drop"
    | "peak_viewers"

export interface Alert {
    id: string
    type: AlertType
    severity: AlertSeverity
    channel_id: string
    channel_title: string
    message: string
    details?: string
    created_at: string
    acknowledged: boolean
}

export interface LiveStreamInfo {
    stream_id: string
    account_id: string
    channel_id: string
    channel_title: string
    channel_thumbnail?: string
    title: string
    description?: string
    youtube_broadcast_id?: string
    viewer_count: number
    peak_viewers: number
    chat_messages: number
    likes: number
    started_at: string
    duration_seconds: number
    health_status: HealthStatus
}

export interface ScheduledStreamInfo {
    stream_id: string
    account_id: string
    channel_id: string
    channel_title: string
    channel_thumbnail?: string
    title: string
    description?: string
    scheduled_start_at: string
    scheduled_end_at?: string
    starts_in_seconds: number
}

export interface ChannelStatusInfo {
    account_id: string
    channel_id: string
    channel_title: string
    thumbnail_url?: string
    subscriber_count: number
    video_count: number
    view_count: number
    stream_status: StreamStatus
    health_status: HealthStatus
    token_expires_at?: string
    is_token_expired: boolean
    is_token_expiring_soon: boolean
    quota_used: number
    quota_limit: number
    quota_percent: number
    strike_count: number
    has_error: boolean
    last_error?: string
    alert_count: number
    current_stream?: LiveStreamInfo
    next_scheduled?: ScheduledStreamInfo
    last_sync_at?: string
}

export interface MonitoringOverview {
    total_channels: number
    live_channels: number
    scheduled_channels: number
    offline_channels: number
    healthy_channels: number
    warning_channels: number
    critical_channels: number
    total_viewers: number
    total_scheduled_today: number
    active_alerts: number
    critical_alerts: number
}

export interface MonitoringDashboard {
    overview: MonitoringOverview
    live_streams: LiveStreamInfo[]
    scheduled_streams: ScheduledStreamInfo[]
    channels: ChannelStatusInfo[]
    alerts: Alert[]
}

export interface LiveStreamsResponse {
    streams: LiveStreamInfo[]
    total_live: number
    total_viewers: number
}

export interface ScheduledStreamsResponse {
    streams: ScheduledStreamInfo[]
    total_scheduled: number
}

// ============================================================================
// API Functions
// ============================================================================

export const monitoringApi = {
    /**
     * Get complete monitoring dashboard data
     * Backend: GET /monitoring/dashboard
     */
    async getDashboard(): Promise<MonitoringDashboard> {
        return apiClient.get<MonitoringDashboard>("/monitoring/dashboard")
    },

    /**
     * Get monitoring overview stats only (lightweight)
     * Backend: GET /monitoring/overview
     */
    async getOverview(): Promise<MonitoringOverview> {
        return apiClient.get<MonitoringOverview>("/monitoring/overview")
    },

    /**
     * Get all currently live streams
     * Backend: GET /monitoring/live
     */
    async getLiveStreams(): Promise<LiveStreamsResponse> {
        return apiClient.get<LiveStreamsResponse>("/monitoring/live")
    },

    /**
     * Get scheduled streams
     * Backend: GET /monitoring/scheduled
     */
    async getScheduledStreams(daysAhead: number = 7): Promise<ScheduledStreamsResponse> {
        return apiClient.get<ScheduledStreamsResponse>("/monitoring/scheduled", {
            days_ahead: daysAhead,
        })
    },

    /**
     * Get status for a specific channel
     * Backend: GET /monitoring/channels/{account_id}
     */
    async getChannelStatus(accountId: string): Promise<ChannelStatusInfo> {
        return apiClient.get<ChannelStatusInfo>(`/monitoring/channels/${accountId}`)
    },

    /**
     * Get all active alerts
     * Backend: GET /monitoring/alerts
     */
    async getAlerts(): Promise<Alert[]> {
        return apiClient.get<Alert[]>("/monitoring/alerts")
    },
}

export default monitoringApi
