import apiClient from "./client"

// ============ Strike Types ============
export type StrikeType = "copyright" | "community_guidelines" | "trademark" | "other"
export type StrikeStatus = "active" | "appealed" | "resolved" | "expired"
export type AppealStatus = "pending" | "under_review" | "approved" | "rejected" | "not_appealed"
export type RiskLevel = "low" | "medium" | "high" | "critical"

export interface Strike {
    id: string
    account_id: string
    youtube_strike_id?: string
    strike_type: string
    severity: string
    reason: string
    reason_details?: string
    affected_video_id?: string
    affected_video_title?: string
    affected_content_url?: string
    status: StrikeStatus
    appeal_status: AppealStatus
    appeal_submitted_at?: string
    appeal_reason?: string
    appeal_response?: string
    appeal_resolved_at?: string
    issued_at: string
    expires_at?: string
    resolved_at?: string
    notification_sent: boolean
    streams_paused: boolean
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
    channel_id?: string
    channel_name?: string
    channel_thumbnail?: string
    total_strikes: number
    active_strikes: number
    appealed_strikes: number
    resolved_strikes: number
    expired_strikes: number
    has_high_risk: boolean
    risk_level: RiskLevel
    latest_strike?: Strike
}

export interface AllAccountsSummary {
    total_accounts: number
    accounts_with_strikes: number
    clean_accounts: number
    total_active_strikes: number
    total_appealed_strikes: number
    summaries: StrikeSummary[]
}

export interface SyncAllResult {
    total_accounts: number
    synced_accounts: number
    failed_accounts: number
    new_strikes: number
    updated_strikes: number
    resolved_strikes: number
    errors: string[]
}

export interface StrikeAlert {
    id: string
    strike_id: string
    account_id: string
    alert_type: string
    title: string
    message: string
    severity: string
    channels_sent?: string[]
    delivery_status: string
    delivered_at?: string
    delivery_error?: string
    acknowledged: boolean
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
    strikes: Strike[]
    total: number
    active_count: number
}

export interface StrikeAlertsResponse {
    items: StrikeAlert[]
    total: number
    unread_count: number
}

export interface PausedStreamsResponse {
    paused_streams: PausedStream[]
    total: number
}

export interface StrikeTimelineEvent {
    event_type: string
    timestamp: string
    description: string
    details?: Record<string, unknown>
}

export interface StrikeTimeline {
    strike_id: string
    events: StrikeTimelineEvent[]
}

export const strikesApi = {
    // ============ All Accounts ============
    async getAllSummaries(): Promise<AllAccountsSummary> {
        try {
            return await apiClient.get<AllAccountsSummary>("/strikes/summaries")
        } catch (error) {
            return {
                total_accounts: 0,
                accounts_with_strikes: 0,
                clean_accounts: 0,
                total_active_strikes: 0,
                total_appealed_strikes: 0,
                summaries: [],
            }
        }
    },

    async syncAllAccounts(): Promise<SyncAllResult> {
        return await apiClient.post<SyncAllResult>("/strikes/sync-all")
    },

    // ============ Strikes ============
    async getStrikes(params?: {
        account_id?: string
        status?: StrikeStatus
        type?: StrikeType
        include_expired?: boolean
    }): Promise<StrikesResponse> {
        try {
            if (!params?.account_id) {
                return { strikes: [], total: 0, active_count: 0 }
            }
            return await apiClient.get<StrikesResponse>(`/strikes/account/${params.account_id}`, {
                include_expired: params.include_expired || false,
            })
        } catch (error) {
            return { strikes: [], total: 0, active_count: 0 }
        }
    },

    async getStrike(strikeId: string): Promise<Strike> {
        return await apiClient.get(`/strikes/${strikeId}`)
    },

    async getStrikeTimeline(strikeId: string): Promise<StrikeTimeline> {
        try {
            return await apiClient.get<StrikeTimeline>(`/strikes/${strikeId}/timeline`)
        } catch (error) {
            return { strike_id: strikeId, events: [] }
        }
    },

    // ============ Summaries ============
    async getAccountStrikeSummary(accountId: string): Promise<StrikeSummary> {
        return await apiClient.get(`/strikes/account/${accountId}/summary`)
    },

    // ============ Appeals ============
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
    async getPausedStreams(accountId?: string): Promise<PausedStreamsResponse> {
        try {
            if (!accountId) {
                return { paused_streams: [], total: 0 }
            }
            return await apiClient.get<PausedStreamsResponse>(`/strikes/account/${accountId}/paused-streams`)
        } catch (error) {
            return { paused_streams: [], total: 0 }
        }
    },

    async resumeStream(streamId: string, userId?: string): Promise<void> {
        return await apiClient.post(`/strikes/paused-streams/${streamId}/resume`, {
            user_id: userId,
            confirmation: true,
        })
    },

    // ============ Sync ============
    async syncStrikes(accountId: string): Promise<{ new_strikes: number; updated_strikes: number; errors: string[] }> {
        return await apiClient.post(`/strikes/account/${accountId}/sync`)
    },
}

export default strikesApi
