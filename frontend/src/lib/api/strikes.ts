import apiClient from "./client"

// ============ Strike Types ============
export type StrikeType = "copyright" | "community_guidelines" | "trademark" | "other"
export type StrikeStatus = "active" | "appealed" | "resolved" | "expired"
export type AppealStatus = "pending" | "under_review" | "approved" | "rejected" | "not_appealed"

export interface Strike {
    id: string
    account_id: string
    channel_id: string
    channel_name: string
    type: StrikeType
    reason: string
    description: string
    video_id?: string
    video_title?: string
    status: StrikeStatus
    appeal_status: AppealStatus
    appeal_deadline?: string
    issued_at: string
    expires_at?: string
    resolved_at?: string
    created_at: string
    updated_at: string
}

export interface StrikeHistory {
    id: string
    strike_id: string
    action: "issued" | "appealed" | "appeal_reviewed" | "resolved" | "expired"
    description: string
    timestamp: string
}

export interface StrikeSummary {
    account_id: string
    channel_name: string
    channel_thumbnail?: string
    total_strikes: number
    active_strikes: number
    appealed_strikes: number
    resolved_strikes: number
    has_paused_streams: boolean
    risk_level: "low" | "medium" | "high" | "critical"
}

export interface StrikeAlert {
    id: string
    strike_id: string
    account_id: string
    channel_name: string
    type: "new_strike" | "appeal_deadline" | "appeal_result" | "strike_resolved" | "risk_warning"
    title: string
    message: string
    severity: "info" | "warning" | "error" | "critical"
    read: boolean
    created_at: string
}

export interface PausedStream {
    id: string
    account_id: string
    channel_name: string
    stream_title: string
    scheduled_start_at: string
    paused_at: string
    pause_reason: string
    strike_id: string
}

export interface StrikesResponse {
    items: Strike[]
    total: number
}

export interface StrikeSummariesResponse {
    items: StrikeSummary[]
    total: number
}

export interface StrikeAlertsResponse {
    items: StrikeAlert[]
    total: number
    unread_count: number
}

export interface PausedStreamsResponse {
    items: PausedStream[]
    total: number
}

export const strikesApi = {
    // ============ Strikes ============
    async getStrikes(params?: {
        account_id?: string
        status?: StrikeStatus
        type?: StrikeType
        page?: number
        page_size?: number
    }): Promise<StrikesResponse> {
        try {
            return await apiClient.get("/strikes", params)
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async getStrike(strikeId: string): Promise<Strike> {
        return await apiClient.get(`/strikes/${strikeId}`)
    },

    async getStrikeHistory(strikeId: string): Promise<StrikeHistory[]> {
        try {
            return await apiClient.get(`/strikes/${strikeId}/history`)
        } catch (error) {
            return []
        }
    },

    // ============ Summaries ============
    async getStrikeSummaries(): Promise<StrikeSummariesResponse> {
        try {
            return await apiClient.get("/strikes/summaries")
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async getAccountStrikeSummary(accountId: string): Promise<StrikeSummary> {
        return await apiClient.get(`/strikes/summaries/${accountId}`)
    },

    // ============ Appeals ============
    async submitAppeal(strikeId: string, data: {
        reason: string
        evidence?: string
    }): Promise<Strike> {
        return await apiClient.post(`/strikes/${strikeId}/appeal`, data)
    },

    // ============ Alerts ============
    async getAlerts(params?: {
        page?: number
        page_size?: number
        unread_only?: boolean
    }): Promise<StrikeAlertsResponse> {
        try {
            return await apiClient.get("/strikes/alerts", params)
        } catch (error) {
            return { items: [], total: 0, unread_count: 0 }
        }
    },

    async markAlertAsRead(alertId: string): Promise<StrikeAlert> {
        return await apiClient.post(`/strikes/alerts/${alertId}/read`)
    },

    async markAllAlertsAsRead(): Promise<void> {
        return await apiClient.post("/strikes/alerts/read-all")
    },

    async dismissAlert(alertId: string): Promise<void> {
        return await apiClient.delete(`/strikes/alerts/${alertId}`)
    },

    // ============ Paused Streams ============
    async getPausedStreams(): Promise<PausedStreamsResponse> {
        try {
            return await apiClient.get("/strikes/paused-streams")
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async resumeStream(streamId: string): Promise<void> {
        return await apiClient.post(`/strikes/paused-streams/${streamId}/resume`)
    },

    // ============ Sync ============
    async syncStrikes(accountId?: string): Promise<void> {
        return await apiClient.post("/strikes/sync", { account_id: accountId })
    },
}

export default strikesApi
