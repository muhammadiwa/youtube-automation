import apiClient from "./client"

// ============ Moderation Rule Types ============
export interface ModerationRule {
    id: string
    account_id: string
    name: string
    type: "keyword" | "regex" | "spam" | "caps" | "links" | "emotes"
    pattern: string
    action: "delete" | "hide" | "timeout" | "ban" | "flag"
    timeout_duration?: number
    enabled: boolean
    created_at: string
    updated_at: string
}

export interface CreateModerationRuleRequest {
    account_id: string
    name: string
    type: ModerationRule["type"]
    pattern: string
    action: ModerationRule["action"]
    timeout_duration?: number
    enabled?: boolean
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

// ============ Comment Types ============
export interface Comment {
    id: string
    video_id: string
    account_id: string
    author_id: string
    author_name: string
    author_avatar?: string
    text: string
    like_count: number
    reply_count: number
    sentiment: "positive" | "neutral" | "negative"
    is_reply: boolean
    parent_id?: string
    status: "published" | "held" | "deleted" | "spam"
    created_at: string
}

export interface CommentReply {
    comment_id: string
    text: string
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

// ============ Custom Command Types ============
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
    response: string
    description?: string
    cooldown?: number
    user_level?: CustomCommand["user_level"]
    enabled?: boolean
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

// ============ Moderation Log Types ============
export interface ModerationLog {
    id: string
    account_id: string
    event_id?: string
    action: "delete" | "hide" | "timeout" | "ban" | "unban" | "approve" | "flag"
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

export interface ModerationLogsResponse {
    items: ModerationLog[]
    total: number
    page: number
    page_size: number
}

export interface CommentsResponse {
    items: Comment[]
    total: number
    page: number
    page_size: number
}

export const moderationApi = {
    // ============ Moderation Rules ============
    async getRules(accountId?: string): Promise<ModerationRule[]> {
        try {
            return await apiClient.get("/moderation/rules", { account_id: accountId })
        } catch (error) {
            return []
        }
    },

    async createRule(data: CreateModerationRuleRequest): Promise<ModerationRule> {
        return await apiClient.post("/moderation/rules", data)
    },

    async updateRule(ruleId: string, data: Partial<CreateModerationRuleRequest>): Promise<ModerationRule> {
        return await apiClient.patch(`/moderation/rules/${ruleId}`, data)
    },

    async deleteRule(ruleId: string): Promise<void> {
        return await apiClient.delete(`/moderation/rules/${ruleId}`)
    },

    async toggleRule(ruleId: string, enabled: boolean): Promise<ModerationRule> {
        return await apiClient.patch(`/moderation/rules/${ruleId}`, { enabled })
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

    // ============ Comments ============
    async getComments(params?: {
        account_id?: string
        video_id?: string
        sentiment?: string
        status?: string
        page?: number
        page_size?: number
    }): Promise<CommentsResponse> {
        try {
            return await apiClient.get("/moderation/comments", params)
        } catch (error) {
            return { items: [], total: 0, page: 1, page_size: 10 }
        }
    },

    async replyToComment(commentId: string, text: string): Promise<Comment> {
        return await apiClient.post(`/moderation/comments/${commentId}/reply`, { text })
    },

    async deleteComment(commentId: string): Promise<void> {
        return await apiClient.delete(`/moderation/comments/${commentId}`)
    },

    async markAsSpam(commentId: string): Promise<Comment> {
        return await apiClient.post(`/moderation/comments/${commentId}/spam`)
    },

    async approveComment(commentId: string): Promise<Comment> {
        return await apiClient.post(`/moderation/comments/${commentId}/approve`)
    },

    async bulkModerateComments(commentIds: string[], action: "delete" | "spam" | "approve"): Promise<{ success_count: number }> {
        return await apiClient.post("/moderation/comments/bulk", { comment_ids: commentIds, action })
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
    async getCustomCommands(accountId?: string): Promise<CustomCommand[]> {
        try {
            return await apiClient.get("/moderation/commands", { account_id: accountId })
        } catch (error) {
            return []
        }
    },

    async createCustomCommand(data: CreateCustomCommandRequest): Promise<CustomCommand> {
        return await apiClient.post("/moderation/commands", data)
    },

    async updateCustomCommand(commandId: string, data: Partial<CreateCustomCommandRequest>): Promise<CustomCommand> {
        return await apiClient.patch(`/moderation/commands/${commandId}`, data)
    },

    async deleteCustomCommand(commandId: string): Promise<void> {
        return await apiClient.delete(`/moderation/commands/${commandId}`)
    },

    async toggleCustomCommand(commandId: string, enabled: boolean): Promise<CustomCommand> {
        return await apiClient.patch(`/moderation/commands/${commandId}`, { enabled })
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
            return await apiClient.get("/moderation/logs", params)
        } catch (error) {
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
}

export default moderationApi
