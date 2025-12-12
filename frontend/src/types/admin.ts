// Admin related types

export type AdminRole = "admin" | "super_admin"

export interface AdminUser {
    id: string
    userId: string
    role: AdminRole
    permissions: string[]
    isActive: boolean
    lastLoginAt: string | null
    createdAt: string
}

export interface AdminAuthState {
    admin: AdminUser | null
    isAdmin: boolean
    isLoading: boolean
    is2FAVerified?: boolean
}

export interface AdminAccessVerification {
    isAdmin: boolean
    adminId: string
    role: AdminRole
    permissions: string[]
    requires2FA: boolean
}

export interface Admin2FAResponse {
    verified: boolean
    adminSessionToken: string
    expiresAt: string
}

export interface AdminLoginState {
    step: "credentials" | "2fa"
    isLoading: boolean
    error: string | null
    adminInfo: AdminAccessVerification | null
}

// Admin navigation item
export interface AdminNavItem {
    name: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string | number
}

// Admin sidebar section
export interface AdminNavSection {
    title: string
    items: AdminNavItem[]
}

// ==================== Analytics Types ====================

export interface PeriodComparison {
    previous_value: number
    change_percent: number
    trend: "up" | "down" | "stable"
}

export interface PlatformMetrics {
    total_users: number
    active_users: number
    new_users: number
    mrr: number
    arr: number
    total_streams: number
    total_videos: number
    active_streams: number
    active_subscriptions: number
    period_start: string
    period_end: string
    users_comparison: PeriodComparison | null
    mrr_comparison: PeriodComparison | null
    streams_comparison: PeriodComparison | null
}

export interface GrowthDataPoint {
    date: string
    value: number
}

export interface GrowthMetrics {
    user_growth: GrowthDataPoint[]
    user_growth_rate: number
    revenue_growth: GrowthDataPoint[]
    revenue_growth_rate: number
    churn_data: GrowthDataPoint[]
    current_churn_rate: number
    period_start: string
    period_end: string
    granularity: "daily" | "weekly" | "monthly"
}

export interface RealtimeMetrics {
    active_streams: number
    concurrent_users: number
    api_requests_per_minute: number
    active_jobs: number
    queue_depth: number
    avg_response_time_ms: number
    timestamp: string
}

export interface ExportRequest {
    format: "csv" | "pdf"
    metrics: string[]
    start_date?: string
    end_date?: string
    include_charts?: boolean
}

export interface ExportResponse {
    export_id: string
    status: "pending" | "processing" | "completed" | "failed"
    download_url: string | null
    format: string
    created_at: string
    completed_at: string | null
    file_size: number | null
}
