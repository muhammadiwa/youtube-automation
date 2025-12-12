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

// ==================== Subscription Management Types ====================

export interface AdminSubscriptionFilters {
    plan?: string
    status?: string
    user_search?: string
}

export interface AdminSubscription {
    id: string
    user_id: string
    user_email: string | null
    user_name: string | null
    plan_tier: string
    status: string
    billing_cycle: string
    current_period_start: string
    current_period_end: string
    cancel_at_period_end: boolean
    canceled_at: string | null
    created_at: string
    updated_at: string
}

export interface AdminSubscriptionListResponse {
    items: AdminSubscription[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface SubscriptionUpgradeRequest {
    new_plan: string
    reason?: string
}

export interface SubscriptionDowngradeRequest {
    new_plan: string
    reason?: string
}

export interface SubscriptionExtendRequest {
    days: number
    reason?: string
}

export interface RefundRequest {
    amount?: number
    reason: string
}

export interface RefundResponse {
    refund_id: string
    payment_id: string
    amount: number
    currency: string
    status: string
    gateway: string
    processed_at: string
}

export interface RevenueByPlan {
    plan: string
    revenue: number
    transaction_count: number
}

export interface RevenueByGateway {
    gateway: string
    revenue: number
    transaction_count: number
}

export interface RevenueAnalytics {
    mrr: number
    arr: number
    total_revenue: number
    total_refunds: number
    refund_rate: number
    refund_count: number
    growth_rate: number
    revenue_by_plan: RevenueByPlan[]
    revenue_by_gateway: RevenueByGateway[]
    period_start: string
    period_end: string
}


// ==================== Promotional Types ====================

export type DiscountType = "percentage" | "fixed"

export interface DiscountCode {
    id: string
    code: string
    discount_type: DiscountType
    discount_value: number
    valid_from: string
    valid_until: string
    usage_limit: number | null
    usage_count: number
    applicable_plans: string[]
    is_active: boolean
    is_valid: boolean
    created_by: string
    created_at: string
    updated_at: string
}

export interface DiscountCodeListResponse {
    items: DiscountCode[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface DiscountCodeCreateRequest {
    code: string
    discount_type: DiscountType
    discount_value: number
    valid_from: string
    valid_until: string
    usage_limit?: number | null
    applicable_plans?: string[]
}

export interface DiscountCodeUpdateRequest {
    discount_type?: DiscountType
    discount_value?: number
    valid_from?: string
    valid_until?: string
    usage_limit?: number | null
    applicable_plans?: string[]
    is_active?: boolean
}

export interface DiscountCodeValidationResponse {
    is_valid: boolean
    code: string
    discount_type: DiscountType | null
    discount_value: number | null
    reason: string | null
}

export interface DiscountCodeFilters {
    is_active?: boolean
    search?: string
}


// ==================== Content Moderation Types ====================

export type ReportSeverity = "low" | "medium" | "high" | "critical"
export type ReportStatus = "pending" | "reviewed" | "approved" | "removed"
export type ContentType = "video" | "comment" | "stream" | "thumbnail"

export interface ModerationFilters {
    status?: ReportStatus
    severity?: ReportSeverity
    content_type?: ContentType
    search?: string
}

export interface ReporterInfo {
    id: string | null
    email: string | null
    name: string | null
}

export interface ContentOwnerInfo {
    id: string
    email: string | null
    name: string | null
}

export interface ContentReportSummary {
    id: string
    content_type: ContentType
    content_id: string
    content_preview: string | null
    reason: string
    reason_category: string | null
    severity: ReportSeverity
    report_count: number
    status: ReportStatus
    created_at: string
    content_owner_email: string | null
}

export interface ContentReportDetail {
    id: string
    content_type: ContentType
    content_id: string
    content_preview: string | null
    content_owner: ContentOwnerInfo
    reporter: ReporterInfo | null
    reason: string
    reason_category: string | null
    additional_info: Record<string, unknown> | null
    severity: ReportSeverity
    report_count: number
    status: ReportStatus
    reviewed_by: string | null
    reviewed_at: string | null
    review_notes: string | null
    created_at: string
    updated_at: string
}

export interface ContentReportListResponse {
    items: ContentReportSummary[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface ContentApproveRequest {
    notes?: string
}

export interface ContentApproveResponse {
    report_id: string
    status: string
    reviewed_at: string
    message: string
}

export interface ContentRemoveRequest {
    reason: string
    notify_user?: boolean
}

export interface ContentRemoveResponse {
    report_id: string
    content_id: string
    content_type: string
    status: string
    content_deleted: boolean
    user_notified: boolean
    audit_log_id: string
    removed_at: string
    message: string
}

export interface UserWarnRequest {
    reason: string
    related_report_id?: string
}

export interface UserWarnResponse {
    warning_id: string
    user_id: string
    warning_number: number
    reason: string
    notification_sent: boolean
    created_at: string
    message: string
}


// ==================== System Monitoring Types ====================

export type HealthStatus = "healthy" | "degraded" | "critical"
export type ComponentStatusType = "healthy" | "degraded" | "down"
export type WorkerStatusType = "active" | "idle" | "unhealthy" | "offline"
export type AlertSeverity = "info" | "warning" | "critical"

export interface ComponentHealth {
    name: string
    status: ComponentStatusType
    message: string | null
    latency_ms: number | null
    error_rate: number | null
    last_check: string
    details: Record<string, unknown> | null
    suggested_action: string | null
}

export interface SystemHealthResponse {
    overall_status: HealthStatus
    timestamp: string
    version: string
    uptime_seconds: number
    components: ComponentHealth[]
}

export interface JobQueueStatus {
    queue_name: string
    depth: number
    processing: number
    processing_rate: number
    failed_jobs: number
    dlq_count: number
    oldest_job_age_seconds: number | null
}

export interface JobQueueResponse {
    timestamp: string
    total_depth: number
    total_processing: number
    total_failed: number
    total_dlq: number
    queues: JobQueueStatus[]
}

export interface WorkerInfo {
    id: string
    name: string
    status: WorkerStatusType
    load: number
    current_jobs: number
    completed_jobs: number
    failed_jobs: number
    last_heartbeat: string | null
    started_at: string | null
    hostname: string | null
}

export interface WorkerStatusResponse {
    timestamp: string
    total_workers: number
    active_workers: number
    idle_workers: number
    unhealthy_workers: number
    total_capacity: number
    current_load: number
    utilization_percent: number
    workers: WorkerInfo[]
}

export interface WorkerRestartRequest {
    reason?: string
    graceful?: boolean
}

export interface WorkerRestartResponse {
    worker_id: string
    status: string
    message: string
    jobs_reassigned: number
    restarted_at: string
}

export interface SystemErrorAlert {
    id: string
    severity: AlertSeverity
    message: string
    component: string
    correlation_id: string | null
    occurred_at: string
    notified_at: string | null
    details: Record<string, unknown> | null
}

export interface ErrorAlertsResponse {
    alerts: SystemErrorAlert[]
    total: number
    critical_count: number
    warning_count: number
}

// ==================== Quota Management Types ====================

export interface AccountQuotaInfo {
    account_id: string
    channel_title: string
    daily_quota_used: number
    daily_quota_limit: number
    usage_percent: number
    quota_reset_at: string | null
}

export interface UserQuotaUsage {
    user_id: string
    user_email: string
    user_name: string | null
    total_quota_used: number
    account_count: number
    highest_usage_percent: number
    accounts: AccountQuotaInfo[]
}

export interface QuotaDashboardResponse {
    timestamp: string
    total_daily_quota_used: number
    total_daily_quota_limit: number
    platform_usage_percent: number
    total_accounts: number
    accounts_over_80_percent: number
    accounts_over_90_percent: number
    total_users_with_accounts: number
    high_usage_users: UserQuotaUsage[]
    alert_threshold_percent: number
    alerts_triggered: number
}

export interface QuotaAlertInfo {
    id: string
    user_id: string
    user_email: string
    account_id: string
    channel_title: string
    usage_percent: number
    quota_used: number
    quota_limit: number
    triggered_at: string
    notified: boolean
}

export interface QuotaAlertsResponse {
    timestamp: string
    alerts: QuotaAlertInfo[]
    total_alerts: number
    critical_count: number
    warning_count: number
}
