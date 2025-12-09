import apiClient from "./client"

// ============ Competitor Types ============
export interface Competitor {
    id: string
    user_id: string
    channel_id: string
    channel_name: string
    channel_url: string
    thumbnail_url?: string
    subscriber_count: number
    video_count: number
    view_count: number
    created_at: string
    updated_at: string
    last_synced_at?: string
}

export interface CompetitorMetrics {
    competitor_id: string
    date: string
    subscribers: number
    views: number
    videos: number
    engagement_rate: number
    avg_views_per_video: number
}

export interface CompetitorVideo {
    id: string
    competitor_id: string
    video_id: string
    title: string
    thumbnail_url?: string
    view_count: number
    like_count: number
    comment_count: number
    published_at: string
    duration: string
}

export interface CompetitorComparison {
    your_channel: ChannelStats
    competitors: CompetitorStats[]
}

export interface ChannelStats {
    name: string
    subscribers: number
    views: number
    videos: number
    engagement_rate: number
    growth_rate: number
}

export interface CompetitorStats extends ChannelStats {
    competitor_id: string
    variance: {
        subscribers: number
        views: number
        engagement: number
    }
}

export interface CompetitorRecommendation {
    id: string
    competitor_id: string
    type: "content" | "timing" | "tags" | "thumbnail" | "engagement"
    title: string
    description: string
    priority: "low" | "medium" | "high"
    created_at: string
}

export interface CompetitorAlert {
    id: string
    competitor_id: string
    competitor_name: string
    type: "new_video" | "milestone" | "trending" | "upload_frequency"
    title: string
    message: string
    video_id?: string
    video_title?: string
    video_thumbnail?: string
    read: boolean
    created_at: string
}

export interface CompetitorAlertPreference {
    competitor_id: string
    competitor_name: string
    new_video_enabled: boolean
    milestone_enabled: boolean
    trending_enabled: boolean
    upload_frequency_enabled: boolean
}

export interface CompetitorAlertsResponse {
    items: CompetitorAlert[]
    total: number
    unread_count: number
}

export interface CompetitorsResponse {
    items: Competitor[]
    total: number
}

export const competitorsApi = {
    // ============ Competitors ============
    async getCompetitors(): Promise<CompetitorsResponse> {
        try {
            return await apiClient.get("/competitors")
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async getCompetitor(competitorId: string): Promise<Competitor> {
        return await apiClient.get(`/competitors/${competitorId}`)
    },

    async addCompetitor(channelUrl: string): Promise<Competitor> {
        return await apiClient.post("/competitors", { channel_url: channelUrl })
    },

    async removeCompetitor(competitorId: string): Promise<void> {
        return await apiClient.delete(`/competitors/${competitorId}`)
    },

    async syncCompetitor(competitorId: string): Promise<Competitor> {
        return await apiClient.post(`/competitors/${competitorId}/sync`)
    },

    // ============ Metrics ============
    async getMetrics(competitorId: string, params?: {
        start_date?: string
        end_date?: string
    }): Promise<CompetitorMetrics[]> {
        try {
            return await apiClient.get(`/competitors/${competitorId}/metrics`, params)
        } catch (error) {
            return []
        }
    },

    async getComparison(competitorIds?: string[]): Promise<CompetitorComparison> {
        try {
            return await apiClient.post("/competitors/compare", { competitor_ids: competitorIds })
        } catch (error) {
            return {
                your_channel: {
                    name: "Your Channel",
                    subscribers: 0,
                    views: 0,
                    videos: 0,
                    engagement_rate: 0,
                    growth_rate: 0,
                },
                competitors: [],
            }
        }
    },

    // ============ Videos ============
    async getCompetitorVideos(competitorId: string, params?: {
        page?: number
        page_size?: number
        sort_by?: "views" | "likes" | "comments" | "published_at"
    }): Promise<{ items: CompetitorVideo[]; total: number }> {
        try {
            return await apiClient.get(`/competitors/${competitorId}/videos`, params)
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async getLatestVideos(params?: {
        page?: number
        page_size?: number
    }): Promise<{ items: CompetitorVideo[]; total: number }> {
        try {
            return await apiClient.get("/competitors/videos/latest", params)
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    // ============ Recommendations ============
    async getRecommendations(competitorId?: string): Promise<CompetitorRecommendation[]> {
        try {
            return await apiClient.get("/competitors/recommendations", { competitor_id: competitorId })
        } catch (error) {
            return []
        }
    },

    async dismissRecommendation(recommendationId: string): Promise<void> {
        return await apiClient.delete(`/competitors/recommendations/${recommendationId}`)
    },

    // ============ Export ============
    async exportAnalysis(competitorIds?: string[], format: "pdf" | "csv" = "pdf"): Promise<{ download_url: string }> {
        return await apiClient.post("/competitors/export", { competitor_ids: competitorIds, format })
    },

    // ============ Alerts ============
    async getAlerts(params?: {
        page?: number
        page_size?: number
        unread_only?: boolean
        competitor_id?: string
    }): Promise<CompetitorAlertsResponse> {
        try {
            return await apiClient.get("/competitors/alerts", params)
        } catch (error) {
            return { items: [], total: 0, unread_count: 0 }
        }
    },

    async markAlertAsRead(alertId: string): Promise<CompetitorAlert> {
        return await apiClient.post(`/competitors/alerts/${alertId}/read`)
    },

    async markAllAlertsAsRead(): Promise<void> {
        return await apiClient.post("/competitors/alerts/read-all")
    },

    async deleteAlert(alertId: string): Promise<void> {
        return await apiClient.delete(`/competitors/alerts/${alertId}`)
    },

    // ============ Alert Preferences ============
    async getAlertPreferences(): Promise<CompetitorAlertPreference[]> {
        try {
            return await apiClient.get("/competitors/alerts/preferences")
        } catch (error) {
            return []
        }
    },

    async updateAlertPreference(
        competitorId: string,
        data: Partial<{
            new_video_enabled: boolean
            milestone_enabled: boolean
            trending_enabled: boolean
            upload_frequency_enabled: boolean
        }>
    ): Promise<CompetitorAlertPreference> {
        return await apiClient.patch(`/competitors/alerts/preferences/${competitorId}`, data)
    },
}

export default competitorsApi
