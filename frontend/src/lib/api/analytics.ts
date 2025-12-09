import apiClient from "./client"

// ============ Analytics Types ============
export interface AnalyticsOverview {
    total_views: number
    total_subscribers: number
    total_watch_time: number
    total_revenue: number
    views_change: number
    subscribers_change: number
    watch_time_change: number
    revenue_change: number
    period: string
}

export interface ChannelMetrics {
    account_id: string
    channel_name: string
    views: number
    subscribers: number
    watch_time: number
    revenue: number
    engagement_rate: number
    top_videos: VideoMetrics[]
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

// ============ Revenue Types ============
export interface RevenueBreakdown {
    total: number
    ads: number
    memberships: number
    super_chat: number
    super_stickers: number
    merchandise: number
    youtube_premium: number
}

export interface RevenueGoal {
    id: string
    name: string
    target_amount: number
    current_amount: number
    start_date: string
    end_date: string
    progress_percentage: number
    forecast_amount?: number
    forecast_probability?: number
}

export interface RevenueTrend {
    date: string
    amount: number
    source: string
}

export interface TopEarningVideo {
    video_id: string
    title: string
    thumbnail_url: string
    revenue: number
    views: number
    cpm: number
    published_at: string
}

export interface TaxReport {
    year: number
    total_revenue: number
    total_ads: number
    total_memberships: number
    total_super_chat: number
    total_merchandise: number
    total_youtube_premium: number
    tax_withheld: number
    net_earnings: number
    currency: string
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
                total_revenue: 0,
                views_change: 0,
                subscribers_change: 0,
                watch_time_change: 0,
                revenue_change: 0,
                period: params?.period || "30d",
            }
        }
    },

    // ============ Channel Metrics ============
    async getChannelMetrics(accountId: string, params?: {
        start_date?: string
        end_date?: string
    }): Promise<ChannelMetrics> {
        return await apiClient.get(`/analytics/channels/${accountId}`, params)
    },

    async compareChannels(accountIds: string[], params?: {
        start_date?: string
        end_date?: string
    }): Promise<ChannelMetrics[]> {
        return await apiClient.post("/analytics/channels/compare", {
            account_ids: accountIds,
            ...params,
        })
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

    // ============ Reports ============
    async generateReport(data: {
        name: string
        type: "daily" | "weekly" | "monthly" | "custom"
        start_date?: string
        end_date?: string
        metrics: string[]
        format: "pdf" | "csv" | "json"
        account_ids?: string[]
    }): Promise<AnalyticsReport> {
        return await apiClient.post("/analytics/reports", data)
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

    // ============ Revenue ============
    async getRevenueOverview(params?: {
        account_id?: string
        period?: "7d" | "30d" | "90d" | "1y"
    }): Promise<RevenueBreakdown> {
        try {
            return await apiClient.get("/analytics/revenue/overview", params)
        } catch (error) {
            return {
                total: 0,
                ads: 0,
                memberships: 0,
                super_chat: 0,
                super_stickers: 0,
                merchandise: 0,
                youtube_premium: 0,
            }
        }
    },

    async getRevenueTrends(params?: {
        account_id?: string
        start_date?: string
        end_date?: string
    }): Promise<RevenueTrend[]> {
        try {
            return await apiClient.get("/analytics/revenue/trends", params)
        } catch (error) {
            return []
        }
    },

    async getRevenueGoals(): Promise<RevenueGoal[]> {
        try {
            return await apiClient.get("/analytics/revenue/goals")
        } catch (error) {
            return []
        }
    },

    async createRevenueGoal(data: {
        name: string
        target_amount: number
        start_date: string
        end_date: string
    }): Promise<RevenueGoal> {
        return await apiClient.post("/analytics/revenue/goals", data)
    },

    async updateRevenueGoal(goalId: string, data: Partial<{
        name: string
        target_amount: number
        start_date: string
        end_date: string
    }>): Promise<RevenueGoal> {
        return await apiClient.patch(`/analytics/revenue/goals/${goalId}`, data)
    },

    async deleteRevenueGoal(goalId: string): Promise<void> {
        return await apiClient.delete(`/analytics/revenue/goals/${goalId}`)
    },

    async getTopEarningVideos(params?: {
        account_id?: string
        period?: "7d" | "30d" | "90d" | "1y"
        limit?: number
    }): Promise<TopEarningVideo[]> {
        try {
            return await apiClient.get("/analytics/revenue/top-videos", params)
        } catch (error) {
            return []
        }
    },

    async getMonthlyRevenueTrends(params?: {
        account_id?: string
        year?: number
    }): Promise<RevenueTrend[]> {
        try {
            return await apiClient.get("/analytics/revenue/monthly-trends", params)
        } catch (error) {
            return []
        }
    },

    async getTaxReport(year: number): Promise<TaxReport | null> {
        try {
            return await apiClient.get(`/analytics/revenue/tax/${year}`)
        } catch (error) {
            return null
        }
    },

    async exportTaxReport(year: number, format: "pdf" | "csv"): Promise<{ download_url: string }> {
        return await apiClient.get(`/analytics/revenue/tax/${year}/export`, { format })
    },
}

// ============ AI Insights Types ============
export interface AIInsight {
    id: string
    type: "growth" | "optimization" | "warning" | "trend" | "recommendation"
    title: string
    description: string
    metric?: string
    change_percentage?: number
    action_url?: string
    action_label?: string
    priority: "high" | "medium" | "low"
    created_at: string
}

export const aiInsightsApi = {
    async getInsights(params?: {
        account_id?: string
        limit?: number
    }): Promise<AIInsight[]> {
        try {
            return await apiClient.get("/analytics/ai-insights", params)
        } catch (error) {
            // Return mock insights for demo
            return [
                {
                    id: "1",
                    type: "growth",
                    title: "Shorts Performing Well",
                    description: "Your shorts content is getting 40% more engagement than long-form videos. Consider increasing shorts production to capitalize on this trend.",
                    metric: "engagement",
                    change_percentage: 40,
                    action_url: "/dashboard/videos?type=shorts",
                    action_label: "View Shorts",
                    priority: "high",
                    created_at: new Date().toISOString(),
                },
                {
                    id: "2",
                    type: "optimization",
                    title: "Best Upload Time",
                    description: "Videos uploaded between 2-4 PM get 25% more views in the first 24 hours. Schedule your next uploads during this window.",
                    metric: "views",
                    change_percentage: 25,
                    action_url: "/dashboard/videos/upload",
                    action_label: "Schedule Upload",
                    priority: "medium",
                    created_at: new Date().toISOString(),
                },
                {
                    id: "3",
                    type: "trend",
                    title: "Weekend Audience Peak",
                    description: "Your audience is most active on Saturday mornings. Consider scheduling more content for this time slot.",
                    metric: "audience",
                    action_url: "/dashboard/streams/create",
                    action_label: "Schedule Stream",
                    priority: "medium",
                    created_at: new Date().toISOString(),
                },
                {
                    id: "4",
                    type: "warning",
                    title: "Declining CTR",
                    description: "Click-through rate has dropped 15% this month. Consider A/B testing new thumbnail styles to improve performance.",
                    metric: "ctr",
                    change_percentage: -15,
                    action_url: "/dashboard/videos",
                    action_label: "Update Thumbnails",
                    priority: "high",
                    created_at: new Date().toISOString(),
                },
                {
                    id: "5",
                    type: "recommendation",
                    title: "Trending Topic Opportunity",
                    description: "Topics related to 'AI tools' are trending in your niche. Creating content around this could boost discoverability.",
                    action_url: "/dashboard/videos/upload",
                    action_label: "Create Video",
                    priority: "low",
                    created_at: new Date().toISOString(),
                },
            ]
        }
    },

    async dismissInsight(insightId: string): Promise<void> {
        return await apiClient.post(`/analytics/ai-insights/${insightId}/dismiss`)
    },
}

export default analyticsApi
