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

// ============ Revenue Types (matching backend schemas) ============
export interface RevenueBreakdown {
    total: number
    ads: number
    memberships: number
    super_chat: number
    super_stickers: number
    merchandise: number
    youtube_premium: number
}

// Backend response format for dashboard
export interface RevenueDashboardResponse {
    total_revenue: number
    ad_revenue: number
    membership_revenue: number
    super_chat_revenue: number
    super_sticker_revenue: number
    merchandise_revenue: number
    youtube_premium_revenue: number
    revenue_change: number
    revenue_change_percent: number
    breakdown: {
        ad: number
        membership: number
        super_chat: number
        super_sticker: number
        merchandise: number
        youtube_premium: number
        total: number
    }
    accounts: AccountRevenue[]
    start_date: string
    end_date: string
    currency: string
}

export interface AccountRevenue {
    account_id: string
    channel_title?: string
    total_revenue: number
    ad_revenue: number
    membership_revenue: number
    super_chat_revenue: number
    super_sticker_revenue: number
    merchandise_revenue: number
    youtube_premium_revenue: number
    revenue_change: number
    revenue_change_percent: number
}

export interface RevenueGoal {
    id: string
    user_id: string
    account_id?: string
    name: string
    description?: string
    target_amount: number
    currency: string
    period_type: string
    start_date: string
    end_date: string
    current_amount: number
    progress_percentage: number
    forecast_amount?: number
    forecast_probability?: number
    status: string
    achieved_at?: string
    notify_at_percentage?: number[]
    last_notification_percentage?: number
    created_at: string
    updated_at: string
}

export interface RevenueTrend {
    date: string
    amount: number
    source: string
}

export interface MonthlyRevenueSummary {
    month: number
    year: number
    total_revenue: number
    ad_revenue: number
    membership_revenue: number
    super_chat_revenue: number
    super_sticker_revenue: number
    merchandise_revenue: number
    youtube_premium_revenue: number
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

export interface TaxReportResponse {
    year: number
    total_revenue: number
    accounts: TaxReportSummary[]
    generated_at: string
    file_path?: string
    currency: string
}

export interface TaxReportSummary {
    account_id: string
    channel_title?: string
    total_revenue: number
    ad_revenue: number
    membership_revenue: number
    super_chat_revenue: number
    super_sticker_revenue: number
    merchandise_revenue: number
    youtube_premium_revenue: number
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

    // ============ Revenue (using backend /revenue endpoints) ============
    async getRevenueDashboard(params: {
        start_date: string
        end_date: string
        account_ids?: string[]
        user_id: string
    }): Promise<RevenueDashboardResponse> {
        return await apiClient.post("/revenue/dashboard", {
            start_date: params.start_date,
            end_date: params.end_date,
            account_ids: params.account_ids,
        })
    },

    // Helper to convert dashboard response to simple breakdown
    async getRevenueOverview(params?: {
        account_id?: string
        period?: "7d" | "30d" | "90d" | "1y"
        user_id?: string
    }): Promise<RevenueBreakdown> {
        try {
            // Calculate date range based on period
            const endDate = new Date()
            const startDate = new Date()
            switch (params?.period) {
                case "7d":
                    startDate.setDate(startDate.getDate() - 7)
                    break
                case "30d":
                    startDate.setDate(startDate.getDate() - 30)
                    break
                case "90d":
                    startDate.setDate(startDate.getDate() - 90)
                    break
                case "1y":
                    startDate.setFullYear(startDate.getFullYear() - 1)
                    break
                default:
                    startDate.setDate(startDate.getDate() - 30)
            }

            const response = await apiClient.post<RevenueDashboardResponse>("/revenue/dashboard", {
                start_date: startDate.toISOString().split("T")[0],
                end_date: endDate.toISOString().split("T")[0],
                account_ids: params?.account_id ? [params.account_id] : undefined,
            })

            return {
                total: response.total_revenue || 0,
                ads: response.ad_revenue || 0,
                memberships: response.membership_revenue || 0,
                super_chat: response.super_chat_revenue || 0,
                super_stickers: response.super_sticker_revenue || 0,
                merchandise: response.merchandise_revenue || 0,
                youtube_premium: response.youtube_premium_revenue || 0,
            }
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

    async getMonthlyBreakdown(params: {
        year: number
        account_ids?: string[]
    }): Promise<MonthlyRevenueSummary[]> {
        try {
            return await apiClient.get("/revenue/monthly-breakdown", {
                year: params.year,
            })
        } catch (error) {
            return []
        }
    },

    async getRevenueGoals(userId: string, activeOnly: boolean = false): Promise<RevenueGoal[]> {
        try {
            return await apiClient.get("/revenue/goals", {
                user_id: userId,
                active_only: activeOnly,
            })
        } catch (error) {
            return []
        }
    },

    async createRevenueGoal(_userId: string, data: {
        name: string
        description?: string
        target_amount: number
        currency?: string
        period_type: "daily" | "weekly" | "monthly" | "yearly" | "custom"
        start_date: string
        end_date: string
        account_id?: string
        notify_at_percentage?: number[]
    }): Promise<RevenueGoal> {
        return await apiClient.post("/revenue/goals", data)
    },

    async updateRevenueGoal(goalId: string, data: Partial<{
        name: string
        description: string
        target_amount: number
        end_date: string
        status: string
        notify_at_percentage: number[]
    }>): Promise<RevenueGoal> {
        return await apiClient.patch(`/revenue/goals/${goalId}`, data)
    },

    async deleteRevenueGoal(goalId: string): Promise<void> {
        return await apiClient.delete(`/revenue/goals/${goalId}`)
    },

    async refreshGoalProgress(goalId: string): Promise<RevenueGoal> {
        return await apiClient.post(`/revenue/goals/${goalId}/refresh`)
    },

    async getTopEarningVideos(params?: {
        account_id?: string
        period?: "7d" | "30d" | "90d" | "1y"
        limit?: number
    }): Promise<TopEarningVideo[]> {
        try {
            // This would need a separate endpoint - for now return empty
            // Backend doesn't have this specific endpoint yet
            return await apiClient.get("/analytics/revenue/top-videos", params)
        } catch (error) {
            return []
        }
    },

    async getMonthlyRevenueTrends(params?: {
        account_id?: string
        year?: number
    }): Promise<MonthlyRevenueSummary[]> {
        try {
            return await apiClient.get("/revenue/monthly-breakdown", {
                year: params?.year || new Date().getFullYear(),
            })
        } catch (error) {
            return []
        }
    },

    async generateTaxReport(_userId: string, params: {
        year: number
        account_ids?: string[]
        format?: "csv" | "pdf"
    }): Promise<TaxReportResponse> {
        return await apiClient.post("/revenue/tax-report", {
            year: params.year,
            account_ids: params.account_ids,
            format: params.format || "csv",
        })
    },

    async exportTaxReport(_userId: string, params: {
        year: number
        account_ids?: string[]
    }): Promise<Blob> {
        return await apiClient.post("/revenue/tax-report/export", {
            year: params.year,
            account_ids: params.account_ids,
        })
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
