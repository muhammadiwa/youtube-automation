import apiClient from "./client"

// ============ Notification Types ============
export interface Notification {
    id: string
    user_id: string
    type: NotificationType
    title: string
    message: string
    priority: "low" | "medium" | "high" | "critical"
    read: boolean
    action_url?: string
    metadata?: Record<string, unknown>
    created_at: string
}

export type NotificationType =
    | "stream_started"
    | "stream_ended"
    | "stream_error"
    | "upload_complete"
    | "upload_failed"
    | "quota_warning"
    | "token_expiring"
    | "strike_detected"
    | "revenue_alert"
    | "competitor_update"
    | "system_alert"
    | "comment_received"
    | "subscriber_milestone"

export interface NotificationPreference {
    id: string
    user_id: string
    event_type: NotificationType
    email_enabled: boolean
    telegram_enabled: boolean
}

export interface NotificationChannel {
    type: "email" | "telegram"
    enabled: boolean
    config?: Record<string, string>
}

export interface NotificationsResponse {
    items: Notification[]
    total: number
    unread_count: number
}

export const notificationsApi = {
    // ============ Notifications ============
    async getNotifications(params?: {
        page?: number
        page_size?: number
        unread_only?: boolean
        type?: NotificationType
    }): Promise<NotificationsResponse> {
        try {
            return await apiClient.get("/notifications", params)
        } catch (error) {
            return { items: [], total: 0, unread_count: 0 }
        }
    },

    async getUnreadCount(): Promise<number> {
        try {
            const response = await apiClient.get<{ count: number }>("/notifications/unread/count")
            return response.count
        } catch (error) {
            return 0
        }
    },

    async markAsRead(notificationId: string): Promise<Notification> {
        return await apiClient.post(`/notifications/${notificationId}/read`)
    },

    async markAllAsRead(): Promise<void> {
        return await apiClient.post("/notifications/read-all")
    },

    async deleteNotification(notificationId: string): Promise<void> {
        return await apiClient.delete(`/notifications/${notificationId}`)
    },

    async clearAll(): Promise<void> {
        return await apiClient.delete("/notifications/clear")
    },

    // ============ Preferences ============
    async getPreferences(): Promise<NotificationPreference[]> {
        try {
            return await apiClient.get("/notifications/preferences")
        } catch (error) {
            // Return default preferences
            const defaultTypes: NotificationType[] = [
                "stream_started",
                "stream_ended",
                "stream_error",
                "upload_complete",
                "upload_failed",
                "quota_warning",
                "token_expiring",
                "strike_detected",
                "revenue_alert",
                "competitor_update",
                "system_alert",
                "comment_received",
                "subscriber_milestone",
            ]
            return defaultTypes.map((type, index) => ({
                id: `pref-${index}`,
                user_id: "",
                event_type: type,
                email_enabled: true,
                telegram_enabled: false,
            }))
        }
    },

    async updatePreference(
        eventType: NotificationType,
        data: Partial<{
            email_enabled: boolean
            telegram_enabled: boolean
        }>
    ): Promise<NotificationPreference> {
        return await apiClient.patch(`/notifications/preferences/${eventType}`, data)
    },

    async updateAllPreferences(
        data: Partial<{
            email_enabled: boolean
            telegram_enabled: boolean
        }>
    ): Promise<NotificationPreference[]> {
        return await apiClient.patch("/notifications/preferences", data)
    },

    // ============ Channels ============
    async getChannels(): Promise<NotificationChannel[]> {
        try {
            const channels = await apiClient.get<NotificationChannel[]>("/notifications/channels")
            // Filter to only return email and telegram
            return channels.filter(c => c.type === "email" || c.type === "telegram")
        } catch {
            return [
                { type: "email", enabled: true },
                { type: "telegram", enabled: false },
            ]
        }
    },

    async configureChannel(
        channelType: "email" | "telegram",
        config: Record<string, string>
    ): Promise<NotificationChannel> {
        return await apiClient.post(`/notifications/channels/${channelType}`, config)
    },

    async testChannel(channelType: "email" | "telegram"): Promise<{ success: boolean; message: string }> {
        return await apiClient.post(`/notifications/channels/${channelType}/test`)
    },

    async disableChannel(channelType: "email" | "telegram"): Promise<void> {
        return await apiClient.delete(`/notifications/channels/${channelType}`)
    },
}

export default notificationsApi
