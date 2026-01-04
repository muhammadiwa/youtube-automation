import apiClient from "./client"

// ============ Moderation Rule Types (matching backend schemas) ============
export type RuleType = "keyword" | "regex" | "spam" | "caps" | "links"
export type ActionType = "hide" | "delete" | "timeout" | "warn" | "ban"
export type SeverityLevel = "low" | "medium" | "high" | "critical"

// Backend response format
export interface ModerationRuleBackend {
    id: string
    account_id: string
    name: string
    description?: string
    rule_type: RuleType
    pattern?: string
    keywords?: string[]
    settings?: Record<string, unknown>
    caps_threshold_percent?: number
    min_message_length?: number
    action_type: ActionType
    severity: SeverityLevel
    timeout_duration_seconds?: number
    is_enabled: boolean
    priority: number
    trigger_count: number
    last_triggered_at?: string
    created_at: string
    updated_at: string
}

// Frontend-friendly format (mapped from backend)
export interface ModerationRule {
    id: string
    account_id: string
    name: string
    description?: string
    type: RuleType
    pattern: string
    keywords?: string[]
    action: ActionType
    severity: SeverityLevel
    timeout_duration?: number
    enabled: boolean
    priority: number
    trigger_count: number
    last_triggered_at?: string
    created_at: string
    updated_at: string
}

export interface CreateModerationRuleRequest {
    account_id: string
    name: string
    description?: string
    rule_type: RuleType
    pattern?: string
    keywords?: string[]
    action_type: ActionType
    severity?: SeverityLevel
    timeout_duration_seconds?: number
    is_enabled?: boolean
    priority?: number
}

// Helper to map backend response to frontend format
function mapRuleFromBackend(rule: ModerationRuleBackend): ModerationRule {
    return {
        id: rule.id,
        account_id: rule.account_id,
        name: rule.name,
        description: rule.description,
        type: rule.rule_type,
        pattern: rule.pattern || (rule.keywords ? rule.keywords.join(", ") : ""),
        keywords: rule.keywords,
        action: rule.action_type,
        severity: rule.severity,
        timeout_duration: rule.timeout_duration_seconds,
        enabled: rule.is_enabled,
        priority: rule.priority,
        trigger_count: rule.trigger_count,
        last_triggered_at: rule.last_triggered_at,
        created_at: rule.created_at,
        updated_at: rule.updated_at,
    }
}

// ============ Chat Message Types ============
export interface ChatMessage {
    id: string
    event_id: string
    author_id: string
    author_name: string
    author_avatar?: string
    message: string
    is_moderator: boolean
    is_owner: boolean
    is_member: boolean
    timestamp: string
    moderation_status?: "approved" | "flagged" | "deleted" | "hidden"
    moderation_reason?: string
}

// ============ Auto Reply Rule Types ============
export interface AutoReplyRule {
    id: string
    account_id: string
    name: string
    trigger_pattern: string
    reply_template: string
    enabled: boolean
    match_count: number
    created_at: string
}

// ============ Custom Command Types (matching backend schemas) ============
export interface CustomCommandBackend {
    id: string
    account_id: string
    trigger: string
    description?: string
    response_type: string
    response_text?: string
    action_type?: string
    webhook_url?: string
    is_enabled: boolean
    moderator_only: boolean
    member_only: boolean
    cooldown_seconds: number
    usage_count: number
    last_used_at?: string
    created_at: string
    updated_at: string
}

// Frontend-friendly format
export interface CustomCommand {
    id: string
    account_id: string
    trigger: string
    response: string
    description?: string
    cooldown: number
    user_level: "everyone" | "subscriber" | "moderator" | "owner"
    enabled: boolean
    use_count: number
    created_at: string
    updated_at: string
}

export interface CreateCustomCommandRequest {
    account_id: string
    trigger: string
    response_text: string
    description?: string
    response_type?: string
    cooldown_seconds?: number
    moderator_only?: boolean
    member_only?: boolean
    is_enabled?: boolean
}

// Helper to map backend response to frontend format
function mapCommandFromBackend(cmd: CustomCommandBackend): CustomCommand {
    let userLevel: CustomCommand["user_level"] = "everyone"
    if (cmd.moderator_only) userLevel = "moderator"
    else if (cmd.member_only) userLevel = "subscriber"

    return {
        id: cmd.id,
        account_id: cmd.account_id,
        trigger: cmd.trigger,
        response: cmd.response_text || "",
        description: cmd.description,
        cooldown: cmd.cooldown_seconds,
        user_level: userLevel,
        enabled: cmd.is_enabled,
        use_count: cmd.usage_count,
        created_at: cmd.created_at,
        updated_at: cmd.updated_at,
    }
}

// ============ Chatbot Config Types ============
export interface ChatbotConfig {
    id: string
    account_id: string
    enabled: boolean
    personality: "friendly" | "professional" | "funny" | "custom"
    custom_personality?: string
    response_style: "brief" | "detailed" | "conversational"
    triggers: string[]
    greeting_enabled: boolean
    greeting_message?: string
    farewell_enabled: boolean
    farewell_message?: string
    created_at: string
    updated_at: string
}

// ============ Moderation Log Types (matching backend schemas) ============
export interface ModerationLogBackend {
    id: string
    rule_id?: string
    account_id: string
    session_id?: string
    action_type: string
    severity: string
    user_channel_id: string
    user_display_name?: string
    message_id?: string
    message_content?: string
    reason: string
    was_successful: boolean
    error_message?: string
    timeout_duration_seconds?: number
    timeout_expires_at?: string
    processing_time_ms: number
    created_at: string
}

// Frontend-friendly format
export interface ModerationLog {
    id: string
    account_id: string
    event_id?: string
    action: "delete" | "hide" | "timeout" | "ban" | "unban" | "approve" | "flag" | "warn"
    target_type: "message" | "comment" | "user"
    target_id: string
    target_user_id?: string
    target_user_name?: string
    reason?: string
    moderator_id: string
    moderator_name: string
    details?: Record<string, unknown>
    created_at: string
}

// Helper to map backend response to frontend format
function mapLogFromBackend(log: ModerationLogBackend): ModerationLog {
    return {
        id: log.id,
        account_id: log.account_id,
        event_id: log.session_id,
        action: log.action_type as ModerationLog["action"],
        target_type: log.message_id ? "message" : "user",
        target_id: log.message_id || log.user_channel_id,
        target_user_id: log.user_channel_id,
        target_user_name: log.user_display_name,
        reason: log.reason,
        moderator_id: "system",
        moderator_name: "Auto-moderation",
        details: {
            severity: log.severity,
            processing_time_ms: log.processing_time_ms,
            was_successful: log.was_successful,
            error_message: log.error_message,
            timeout_duration_seconds: log.timeout_duration_seconds,
            message_content: log.message_content,
        },
        created_at: log.created_at,
    }
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface ModerationLogsResponse {
    items: ModerationLog[]
    total: number
    page: number
    page_size: number
}

export const moderationApi = {
    // ============ Moderation Rules ============
    async getRules(params?: {
        accountId?: string
        page?: number
        pageSize?: number
    }): Promise<PaginatedResponse<ModerationRule>> {
        try {
            const response = await apiClient.get<{
                items: ModerationRuleBackend[]
                total: number
                page: number
                page_size: number
                total_pages: number
            }>("/moderation/rules", {
                account_id: params?.accountId,
                enabled_only: false,
                page: params?.page || 1,
                page_size: params?.pageSize || 10,
            })
            return {
                items: response.items.map(mapRuleFromBackend),
                total: response.total,
                page: response.page,
                page_size: response.page_size,
                total_pages: response.total_pages,
            }
        } catch {
            return { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }
        }
    },

    async createRule(data: CreateModerationRuleRequest): Promise<ModerationRule> {
        const response = await apiClient.post<ModerationRuleBackend>("/moderation/rules", data)
        return mapRuleFromBackend(response)
    },

    async updateRule(ruleId: string, data: Partial<CreateModerationRuleRequest>): Promise<ModerationRule> {
        const response = await apiClient.patch<ModerationRuleBackend>(`/moderation/rules/${ruleId}`, data)
        return mapRuleFromBackend(response)
    },

    async deleteRule(ruleId: string): Promise<void> {
        return await apiClient.delete(`/moderation/rules/${ruleId}`)
    },

    async toggleRule(ruleId: string, enabled: boolean): Promise<ModerationRule> {
        const response = await apiClient.patch<ModerationRuleBackend>(`/moderation/rules/${ruleId}`, { is_enabled: enabled })
        return mapRuleFromBackend(response)
    },

    // ============ Chat Moderation ============
    async getChatMessages(eventId: string, params?: {
        page?: number
        page_size?: number
        status?: string
    }): Promise<{ items: ChatMessage[]; total: number }> {
        try {
            return await apiClient.get(`/moderation/chat/${eventId}/messages`, params)
        } catch (error) {
            return { items: [], total: 0 }
        }
    },

    async moderateMessage(eventId: string, messageId: string, action: "delete" | "hide" | "approve"): Promise<ChatMessage> {
        return await apiClient.post(`/moderation/chat/${eventId}/messages/${messageId}/${action}`)
    },

    async timeoutUser(eventId: string, userId: string, duration: number): Promise<void> {
        return await apiClient.post(`/moderation/chat/${eventId}/timeout`, { user_id: userId, duration })
    },

    async banUser(eventId: string, userId: string): Promise<void> {
        return await apiClient.post(`/moderation/chat/${eventId}/ban`, { user_id: userId })
    },

    async unbanUser(eventId: string, userId: string): Promise<void> {
        return await apiClient.post(`/moderation/chat/${eventId}/unban`, { user_id: userId })
    },

    async enableSlowMode(eventId: string, delay: number): Promise<void> {
        return await apiClient.post(`/moderation/chat/${eventId}/slow-mode`, { delay })
    },

    async disableSlowMode(eventId: string): Promise<void> {
        return await apiClient.delete(`/moderation/chat/${eventId}/slow-mode`)
    },

    // ============ Auto Reply Rules ============
    async getAutoReplyRules(accountId?: string): Promise<AutoReplyRule[]> {
        try {
            return await apiClient.get("/moderation/auto-reply", { account_id: accountId })
        } catch (error) {
            return []
        }
    },

    async createAutoReplyRule(data: {
        account_id: string
        name: string
        trigger_pattern: string
        reply_template: string
        enabled?: boolean
    }): Promise<AutoReplyRule> {
        return await apiClient.post("/moderation/auto-reply", data)
    },

    async updateAutoReplyRule(ruleId: string, data: Partial<{
        name: string
        trigger_pattern: string
        reply_template: string
        enabled: boolean
    }>): Promise<AutoReplyRule> {
        return await apiClient.patch(`/moderation/auto-reply/${ruleId}`, data)
    },

    async deleteAutoReplyRule(ruleId: string): Promise<void> {
        return await apiClient.delete(`/moderation/auto-reply/${ruleId}`)
    },

    // ============ Custom Commands ============
    async getCustomCommands(params?: {
        accountId?: string
        page?: number
        pageSize?: number
    }): Promise<PaginatedResponse<CustomCommand>> {
        try {
            const response = await apiClient.get<{
                items: CustomCommandBackend[]
                total: number
                page: number
                page_size: number
                total_pages: number
            }>("/moderation/commands", {
                account_id: params?.accountId,
                enabled_only: false,
                page: params?.page || 1,
                page_size: params?.pageSize || 10,
            })
            return {
                items: response.items.map(mapCommandFromBackend),
                total: response.total,
                page: response.page,
                page_size: response.page_size,
                total_pages: response.total_pages,
            }
        } catch {
            return { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 }
        }
    },

    async createCustomCommand(data: CreateCustomCommandRequest): Promise<CustomCommand> {
        const response = await apiClient.post<CustomCommandBackend>("/moderation/commands", data)
        return mapCommandFromBackend(response)
    },

    async updateCustomCommand(commandId: string, data: Partial<CreateCustomCommandRequest>): Promise<CustomCommand> {
        const response = await apiClient.patch<CustomCommandBackend>(`/moderation/commands/${commandId}`, data)
        return mapCommandFromBackend(response)
    },

    async deleteCustomCommand(commandId: string): Promise<void> {
        return await apiClient.delete(`/moderation/commands/${commandId}`)
    },

    async toggleCustomCommand(commandId: string, enabled: boolean): Promise<CustomCommand> {
        const response = await apiClient.patch<CustomCommandBackend>(`/moderation/commands/${commandId}`, { is_enabled: enabled })
        return mapCommandFromBackend(response)
    },

    // ============ Chatbot Configuration ============
    async getChatbotConfig(accountId: string): Promise<ChatbotConfig | null> {
        try {
            return await apiClient.get(`/moderation/chatbot/${accountId}`)
        } catch (error) {
            return null
        }
    },

    async updateChatbotConfig(accountId: string, data: Partial<ChatbotConfig>): Promise<ChatbotConfig> {
        return await apiClient.patch(`/moderation/chatbot/${accountId}`, data)
    },

    async testChatbot(accountId: string, message: string): Promise<{ response: string }> {
        return await apiClient.post(`/moderation/chatbot/${accountId}/test`, { message })
    },

    // ============ Moderation Logs ============
    async getModerationLogs(params?: {
        account_id?: string
        event_id?: string
        action?: string
        target_type?: string
        start_date?: string
        end_date?: string
        page?: number
        page_size?: number
    }): Promise<ModerationLogsResponse> {
        try {
            const response = await apiClient.get<{
                items: ModerationLogBackend[]
                total: number
                page: number
                page_size: number
            }>("/moderation/logs", params)
            return {
                items: response.items.map(mapLogFromBackend),
                total: response.total,
                page: response.page,
                page_size: response.page_size,
            }
        } catch {
            return { items: [], total: 0, page: 1, page_size: 20 }
        }
    },

    async exportModerationLogs(params?: {
        account_id?: string
        start_date?: string
        end_date?: string
        format?: "csv" | "json"
    }): Promise<Blob> {
        // Build URL with params for blob download
        const queryParams = new URLSearchParams()
        if (params?.account_id) queryParams.append("account_id", params.account_id)
        if (params?.start_date) queryParams.append("start_date", params.start_date)
        if (params?.end_date) queryParams.append("end_date", params.end_date)
        if (params?.format) queryParams.append("format", params.format)

        const response = await fetch(`/api/v1/moderation/logs/export?${queryParams.toString()}`)
        return response.blob()
    },

    // ============ Live Chat Moderation Control ============
    async startLiveModeration(data: {
        account_id: string
        broadcast_id: string
        session_id?: string
    }): Promise<{ is_active: boolean; broadcast_id: string; message: string }> {
        return await apiClient.post("/moderation/live/start", data)
    },

    async stopLiveModeration(accountId: string, broadcastId: string): Promise<{ is_active: boolean; broadcast_id: string; message: string }> {
        return await apiClient.post("/moderation/live/stop", undefined, {
            params: { account_id: accountId, broadcast_id: broadcastId }
        } as never)
    },

    async getLiveModerationStatus(accountId?: string): Promise<{
        active_count: number
        sessions: Array<{
            account_id: string
            broadcast_id: string
            session_id: string | null
            is_running: boolean
            live_chat_id: string | null
            polling_interval_ms: number
            processed_messages: number
        }>
    }> {
        try {
            return await apiClient.get("/moderation/live/status", { account_id: accountId })
        } catch {
            return { active_count: 0, sessions: [] }
        }
    },
}

export default moderationApi
