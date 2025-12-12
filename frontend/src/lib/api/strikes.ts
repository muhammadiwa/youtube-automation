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
    alert_type: string  // Backend uses alert_type
    title: string
    message: string
    severity: string
    channels_sent?: string[]
    delivery_status: string
    delivered_at?: string
    delivery_error?: string
    acknowledged: boolean  // Backend uses acknowledged, not read
    acknowledged_at?: string
    acknowledged_by?: string
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
    // Backend requires account_id - GET /strikes/account/{account_id}
    async getStrikes(params?: {
        account_id?: string
        status?: StrikeStatus
        type?: StrikeType
        page?: number
        page_size?: number
        include_expired?: boolean
    }): Promise<StrikesResponse> {
        try {
            if (!params?.account_id) {
                // No account_id provided, return empty
                return { items: [], total: 0 }
            }
            const response = await apiClient.get<{ strikes: Strike[]; total: number; active_count: number }>(`/strikes/account/${params.account_id}`, {
                include_expired: params.include_expired || false,
            })
            // Backend returns { strikes: [], total: number, active_count: number }
            return {
                items: response.strikes || [],
                total: response.total || 0,
            }
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async getStrike(strikeId: string): Promise<Strike> {
        return await apiClient.get(`/strikes/${strikeId}`)
    },

    // Backend uses /strikes/{strike_id}/timeline instead of /history
    async getStrikeHistory(strikeId: string): Promise<StrikeHistory[]> {
        try {
            const response = await apiClient.get<{ events: StrikeHistory[] }>(`/strikes/${strikeId}/timeline`)
            // Backend returns StrikeTimeline with events array
            return response.events || []
        } catch (error) {
            return []
        }
    },

    // ============ Summaries ============
    // Backend requires account_id - GET /strikes/account/{account_id}/summary
    async getStrikeSummaries(): Promise<StrikeSummariesResponse> {
        // This endpoint doesn't exist in backend - would need to fetch per account
        // For now return empty
        return { items: [], total: 0 }
    },

    async getAccountStrikeSummary(accountId: string): Promise<StrikeSummary> {
        return await apiClient.get(`/strikes/account/${accountId}/summary`)
    },

    // ============ Appeals ============
    // Backend expects appeal_reason as query param, not body
    async submitAppeal(strikeId: string, data: {
        reason: string
        evidence?: string
    }): Promise<Strike> {
        return await apiClient.post(`/strikes/${strikeId}/appeal?appeal_reason=${encodeURIComponent(data.reason)}`)
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
    // Backend requires account_id - GET /strikes/account/{account_id}/paused-streams
    async getPausedStreams(accountId?: string): Promise<PausedStreamsResponse> {
        try {
            if (!accountId) {
                return { items: [], total: 0 }
            }
            const response = await apiClient.get<{ paused_streams: PausedStream[]; total: number }>(`/strikes/account/${accountId}/paused-streams`)
            return {
                items: response.paused_streams || [],
                total: response.total || 0,
            }
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    // Backend expects user_id and confirmation in body
    async resumeStream(streamId: string, userId?: string): Promise<void> {
        return await apiClient.post(`/strikes/paused-streams/${streamId}/resume`, {
            user_id: userId,
            confirmation: true,
        })
    },

    // ============ Sync ============
    // Backend endpoint is POST /strikes/account/{account_id}/sync
    async syncStrikes(accountId: string): Promise<{ new_strikes: number; updated_strikes: number; errors: string[] }> {
        return await apiClient.post(`/strikes/account/${accountId}/sync`)
    },
}

export default strikesApi
