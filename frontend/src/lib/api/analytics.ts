import apiClient from "./client"

// ============ Analytics Types ============
export interface AnalyticsOverview {
    total_views: number
    total_subscribers: number
    total_watch_time: number
    views_change: number
    subscribers_change: number
    watch_time_change: number
    period: string
}

export interface ChannelMetrics {
    account_id: string
    channel_name: string
    views: number
    subscribers: number
    watch_time: number
    engagement_rate: number
    top_videos: VideoMetrics[]
}

export interface ChannelDetailedMetrics {
    account_id: string
    period: string
    start_date: string
    end_date: string
    subscribers: number
    subscriber_change: number
    views: number
    views_change: number
    watch_time: number
    engagement_rate: number
    traffic_sources: Record<string, { views: number; watch_time_minutes: number }>
    demographics: {
        age_groups: Record<string, { male: number; female: number }>
        gender: { male: number; female: number }
    }
    top_videos: TopVideoData[]
    last_sync_at?: string | null
    has_analytics_data?: boolean
}

export interface TopVideoData {
    video_id: string
    title: string
    thumbnail_url?: string
    published_at?: string
    views: number
    watch_time_minutes: number
    average_view_duration: number
    duration_seconds?: number
    likes: number
    comments: number
}

export interface TopVideosResponse {
    account_id: string
    channel_title: string
    videos: TopVideoData[]
    total: number
}

export interface VideoMetrics {
    video_id: string
    title: string
    views: number
    likes: number
    comments: number
    watch_time: number
    average_view_duration: number
    click_through_rate: number
}

export interface TimeSeriesData {
    date: string
    value: number
}

export interface AnalyticsReport {
    id: string
    name: string
    type: "daily" | "weekly" | "monthly" | "custom"
    start_date: string
    end_date: string
    metrics: string[]
    format: "pdf" | "csv" | "json"
    status: "pending" | "generating" | "completed" | "failed"
    download_url?: string
    created_at: string
}

export interface SyncResponse {
    status: string
    message: string
}

export const analyticsApi = {
    // ============ Overview ============
    async getOverview(params?: {
        account_id?: string
        period?: "7d" | "30d" | "90d" | "1y"
    }): Promise<AnalyticsOverview> {
        try {
            return await apiClient.get("/analytics/overview", params)
        } catch (error) {
            console.error("Failed to fetch analytics overview:", error)
            return {
                total_views: 0,
                total_subscribers: 0,
                total_watch_time: 0,
                views_change: 0,
                subscribers_change: 0,
                watch_time_change: 0,
                period: params?.period || "30d",
            }
        }
    },

    // ============ Channel Metrics ============
    async getChannelMetrics(accountId: string, params?: {
        start_date?: string
        end_date?: string
    }): Promise<ChannelMetrics> {
        try {
            // Use the accounts endpoint
            const response = await apiClient.get<{
                account_id: string
                subscriber_count: number
                total_views: number
                total_videos: number
                subscriber_change: number
                views_change: number
                engagement_rate: number
                watch_time_minutes: number
            }>(`/analytics/accounts/${accountId}`, params);

            return {
                account_id: response.account_id || accountId,
                channel_name: "",
                views: response.total_views || 0,
                subscribers: response.subscriber_count || 0,
                watch_time: response.watch_time_minutes || 0,
                engagement_rate: response.engagement_rate || 0,
                top_videos: [],
            };
        } catch (error) {
            console.error("Failed to get channel metrics:", error);
            return {
                account_id: accountId,
                channel_name: "",
                views: 0,
                subscribers: 0,
                watch_time: 0,
                engagement_rate: 0,
                top_videos: [],
            };
        }
    },

    async getChannelDetailedMetrics(accountId: string, params?: {
        period?: "7d" | "30d" | "90d" | "1y"
    }): Promise<ChannelDetailedMetrics> {
        return await apiClient.get(`/analytics/channel/${accountId}/metrics`, params)
    },

    async getChannelTopVideos(accountId: string, params?: {
        limit?: number
    }): Promise<TopVideosResponse> {
        try {
            return await apiClient.get(`/analytics/channel/${accountId}/top-videos`, params)
        } catch (error) {
            console.error("Failed to fetch top videos:", error)
            return {
                account_id: accountId,
                channel_title: "",
                videos: [],
                total: 0,
            }
        }
    },

    async compareChannels(accountIds: string[], params?: {
        start_date?: string
        end_date?: string
    }): Promise<ChannelMetrics[]> {
        // Ensure dates are provided
        const today = new Date();
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(today.getDate() - 30);

        const requestData = {
            account_ids: accountIds,
            start_date: params?.start_date || thirtyDaysAgo.toISOString().split('T')[0],
            end_date: params?.end_date || today.toISOString().split('T')[0],
        };

        try {
            const response = await apiClient.post<{
                channels: Array<{
                    account_id: string
                    channel_title?: string
                    total_views: number
                    subscriber_count: number
                    watch_time_minutes: number
                    engagement_rate: number
                }>
            }>("/analytics/compare", requestData);

            // Transform response to ChannelMetrics format
            if (response && response.channels) {
                return response.channels.map((ch) => ({
                    account_id: ch.account_id,
                    channel_name: ch.channel_title || "Unknown",
                    views: ch.total_views || 0,
                    subscribers: ch.subscriber_count || 0,
                    watch_time: ch.watch_time_minutes || 0,
                    engagement_rate: ch.engagement_rate || 0,
                    top_videos: [],
                }));
            }
            return [];
        } catch (error) {
            console.error("Failed to compare channels:", error);
            return [];
        }
    },

    // ============ Time Series ============
    async getViewsTimeSeries(params?: {
        account_id?: string
        start_date?: string
        end_date?: string
        granularity?: "hour" | "day" | "week" | "month"
    }): Promise<TimeSeriesData[]> {
        try {
            return await apiClient.get("/analytics/views/timeseries", params)
        } catch (error) {
            return []
        }
    },

    async getSubscribersTimeSeries(params?: {
        account_id?: string
        start_date?: string
        end_date?: string
        granularity?: "hour" | "day" | "week" | "month"
    }): Promise<TimeSeriesData[]> {
        try {
            return await apiClient.get("/analytics/subscribers/timeseries", params)
        } catch (error) {
            return []
        }
    },

    // ============ Sync ============
    async syncAccount(accountId: string): Promise<SyncResponse> {
        return await apiClient.post(`/analytics/sync/${accountId}`)
    },

    async syncAllAccounts(): Promise<SyncResponse> {
        return await apiClient.post("/analytics/sync")
    },

    // ============ Reports ============
    async generateReport(data: {
        name: string
        type?: "daily" | "weekly" | "monthly" | "custom"
        start_date?: string
        end_date?: string
        metrics?: string[]
        format: "pdf" | "csv" | "json"
        account_ids?: string[]
        include_ai_insights?: boolean
    }): Promise<AnalyticsReport> {
        // Transform to backend format (supports both field names)
        return await apiClient.post("/analytics/reports", {
            name: data.name,
            title: data.name,  // Send both for compatibility
            format: data.format,
            report_type: data.format,  // Send both for compatibility
            type: data.type,
            start_date: data.start_date,
            end_date: data.end_date,
            account_ids: data.account_ids,
            metrics: data.metrics,
            include_ai_insights: data.include_ai_insights ?? true,
        })
    },

    async getReports(): Promise<AnalyticsReport[]> {
        try {
            return await apiClient.get("/analytics/reports")
        } catch (error) {
            return []
        }
    },

    async getReport(reportId: string): Promise<AnalyticsReport> {
        return await apiClient.get(`/analytics/reports/${reportId}`)
    },
}

// ============ AI Insights Types ============
export interface AIInsight {
    id: string
    type: "growth" | "optimization" | "warning" | "trend" | "recommendation"
    title: string
    description: string
    recommendation?: string
    metric?: string
    change_percentage?: number
    action_url?: string
    action_label?: string
    priority: "high" | "medium" | "low"
    created_at?: string
    // Backward compatibility fields
    category?: string
    confidence?: number
    metric_change?: number
    metric_name?: string
}

export const aiInsightsApi = {
    async getInsights(params?: {
        account_id?: string
        start_date?: string
        end_date?: string
        limit?: number
    }): Promise<AIInsight[]> {
        try {
            return await apiClient.get("/analytics/ai-insights", params)
        } catch (error) {
            // Return empty array - no mock data
            console.error("Failed to fetch AI insights:", error)
            return []
        }
    },

    async dismissInsight(insightId: string): Promise<void> {
        return await apiClient.post(`/analytics/ai-insights/${insightId}/dismiss`)
    },
}

export default analyticsApi
