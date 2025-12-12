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

// ==================== User Management Types ====================

export type UserStatus = "active" | "suspended" | "pending"

export interface UserFilters {
    status?: UserStatus
    plan?: string
    search?: string
    registered_after?: string
    registered_before?: string
}

export interface UserSummary {
    id: string
    email: string
    name: string
    status: UserStatus
    is_active: boolean
    plan_name: string | null
    created_at: string
    last_login_at: string | null
    warning_count: number
}

export interface UserListResponse {
    items: UserSummary[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface SubscriptionInfo {
    id: string | null
    plan_name: string | null
    status: string | null
    start_date: string | null
    end_date: string | null
    next_billing_date: string | null
}

export interface YouTubeAccountSummary {
    id: string
    channel_id: string
    channel_name: string
    subscriber_count: number | null
    is_active: boolean
}

export interface UsageStats {
    total_videos: number
    total_streams: number
    storage_used_gb: number
    bandwidth_used_gb: number
    ai_generations_used: number
}

export interface ActivityLog {
    id: string
    action: string
    details: Record<string, unknown> | null
    ip_address: string | null
    created_at: string
}

export interface UserDetail {
    id: string
    email: string
    name: string
    status: UserStatus
    is_active: boolean
    is_2fa_enabled: boolean
    subscription: SubscriptionInfo | null
    connected_accounts: YouTubeAccountSummary[]
    usage_stats: UsageStats
    activity_history: ActivityLog[]
    created_at: string
    updated_at: string
    last_login_at: string | null
    warning_count: number
}

export interface UserSuspendRequest {
    reason: string
}

export interface UserSuspendResponse {
    user_id: string
    status: string
    suspended_at: string
    reason: string
    jobs_paused: number
    notification_sent: boolean
}

export interface UserActivateResponse {
    user_id: string
    status: string
    activated_at: string
    jobs_resumed: number
}

export interface ImpersonationSession {
    session_id: string
    admin_id: string
    user_id: string
    access_token: string
    expires_at: string
    audit_log_id: string
}

export interface ImpersonateRequest {
    reason?: string
}

export interface ImpersonateResponse {
    session: ImpersonationSession
    message: string
}

export interface PasswordResetResponse {
    user_id: string
    email: string
    reset_link_sent: boolean
    expires_at: string
}

export interface UserStatsResponse {
    total: number
    active: number
    suspended: number
    new_this_month: number
}
