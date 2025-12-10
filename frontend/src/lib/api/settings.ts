import apiClient from "./client"

// ============ Profile Types ============
export interface UserProfile {
    id: string
    email: string
    name: string
    avatar_url?: string
    is_2fa_enabled: boolean
    created_at: string
    last_login_at: string
}

export interface UpdateProfileRequest {
    name?: string
    avatar_url?: string
}

export interface ChangePasswordRequest {
    current_password: string
    new_password: string
}

export interface TwoFactorSetupResponse {
    secret: string
    qr_code_url: string
    backup_codes: string[]
}

// ============ API Key Types ============
export interface ApiKey {
    id: string
    name: string
    key_prefix: string
    scopes: ApiKeyScope[]
    last_used_at?: string
    expires_at?: string
    created_at: string
}

export type ApiKeyScope =
    | "read:accounts"
    | "write:accounts"
    | "read:videos"
    | "write:videos"
    | "read:streams"
    | "write:streams"
    | "read:analytics"
    | "read:billing"

export interface CreateApiKeyRequest {
    name: string
    scopes: ApiKeyScope[]
    expires_in_days?: number
}

export interface CreateApiKeyResponse {
    id: string
    name: string
    key: string // Full key, only shown once
    key_prefix: string
    scopes: ApiKeyScope[]
    expires_at?: string
    created_at: string
}

// ============ Webhook Types ============
export interface Webhook {
    id: string
    name: string
    url: string
    events: WebhookEvent[]
    secret: string
    is_active: boolean
    last_triggered_at?: string
    failure_count: number
    created_at: string
}

export type WebhookEvent =
    | "video.uploaded"
    | "video.published"
    | "video.deleted"
    | "stream.started"
    | "stream.ended"
    | "stream.error"
    | "account.connected"
    | "account.disconnected"
    | "subscription.created"
    | "subscription.cancelled"
    | "payment.completed"
    | "payment.failed"

export interface CreateWebhookRequest {
    name: string
    url: string
    events: WebhookEvent[]
}

export interface UpdateWebhookRequest {
    name?: string
    url?: string
    events?: WebhookEvent[]
    is_active?: boolean
}

export interface WebhookDelivery {
    id: string
    webhook_id: string
    event: WebhookEvent
    payload: Record<string, unknown>
    response_status?: number
    response_body?: string
    success: boolean
    delivered_at: string
    duration_ms: number
}

export interface TestWebhookResponse {
    success: boolean
    status_code?: number
    response_time_ms?: number
    error?: string
}

export const settingsApi = {
    // ============ Profile ============
    async getProfile(): Promise<UserProfile> {
        try {
            return await apiClient.get("/users/me")
        } catch (error) {
            // Return mock data for development
            return {
                id: "user-1",
                email: "user@example.com",
                name: "John Doe",
                is_2fa_enabled: false,
                created_at: new Date().toISOString(),
                last_login_at: new Date().toISOString(),
            }
        }
    },

    async updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
        return await apiClient.patch("/users/me", data)
    },

    async changePassword(data: ChangePasswordRequest): Promise<void> {
        return await apiClient.post("/auth/password/change", data)
    },

    // ============ 2FA ============
    async enable2FA(): Promise<TwoFactorSetupResponse> {
        return await apiClient.post("/auth/2fa/enable")
    },

    async verify2FASetup(code: string): Promise<{ backup_codes: string[] }> {
        return await apiClient.post("/auth/2fa/verify-setup", { code })
    },

    async disable2FA(code: string): Promise<void> {
        return await apiClient.post("/auth/2fa/disable", { code })
    },

    async regenerateBackupCodes(code: string): Promise<{ backup_codes: string[] }> {
        return await apiClient.post("/auth/2fa/regenerate-backup-codes", { code })
    },

    // ============ API Keys ============
    async getApiKeys(): Promise<ApiKey[]> {
        try {
            return await apiClient.get("/api-keys")
        } catch (error) {
            return []
        }
    },

    async createApiKey(data: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
        return await apiClient.post("/api-keys", data)
    },

    async revokeApiKey(keyId: string): Promise<void> {
        return await apiClient.delete(`/api-keys/${keyId}`)
    },

    // ============ Webhooks ============
    async getWebhooks(): Promise<Webhook[]> {
        try {
            return await apiClient.get("/webhooks")
        } catch (error) {
            return []
        }
    },

    async createWebhook(data: CreateWebhookRequest): Promise<Webhook> {
        return await apiClient.post("/webhooks", data)
    },

    async updateWebhook(webhookId: string, data: UpdateWebhookRequest): Promise<Webhook> {
        return await apiClient.patch(`/webhooks/${webhookId}`, data)
    },

    async deleteWebhook(webhookId: string): Promise<void> {
        return await apiClient.delete(`/webhooks/${webhookId}`)
    },

    async testWebhook(webhookId: string): Promise<TestWebhookResponse> {
        return await apiClient.post(`/webhooks/${webhookId}/test`)
    },

    async getWebhookDeliveries(webhookId: string, params?: {
        page?: number
        page_size?: number
    }): Promise<{ items: WebhookDelivery[]; total: number }> {
        try {
            return await apiClient.get(`/webhooks/${webhookId}/deliveries`, params)
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async retryWebhookDelivery(webhookId: string, deliveryId: string): Promise<WebhookDelivery> {
        return await apiClient.post(`/webhooks/${webhookId}/deliveries/${deliveryId}/retry`)
    },
}

export default settingsApi
