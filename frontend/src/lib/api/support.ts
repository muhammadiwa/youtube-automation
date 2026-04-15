/**
 * Support API client for user support ticket management.
 * Handles ticket creation, viewing, and messaging.
 */

import apiClient from "./client"

// ============ Types ============

export interface SupportTicket {
    id: string
    subject: string
    description: string
    category: string | null
    status: TicketStatus
    priority: TicketPriority
    message_count: number
    created_at: string
    updated_at: string
    resolved_at: string | null
}

export interface SupportTicketDetail {
    id: string
    subject: string
    description: string
    category: string | null
    status: TicketStatus
    priority: TicketPriority
    messages: TicketMessage[]
    created_at: string
    updated_at: string
    resolved_at: string | null
}

export interface TicketMessage {
    id: string
    ticket_id: string
    sender_id: string
    sender_type: "user" | "admin"
    sender_name: string | null
    content: string
    attachments: string[] | null
    created_at: string
}

export interface TicketListResponse {
    items: SupportTicket[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface TicketStats {
    total: number
    open: number
    in_progress: number
    waiting_user: number
    resolved: number
    closed: number
}

export interface CreateTicketRequest {
    subject: string
    description: string
    category?: string
    priority?: TicketPriority
}

export interface CreateMessageRequest {
    content: string
    attachments?: string[]
}

export type TicketStatus = "open" | "in_progress" | "waiting_user" | "resolved" | "closed"
export type TicketPriority = "low" | "medium" | "high" | "urgent"

// ============ API Functions ============

export const supportApi = {
    /**
     * Create a new support ticket
     */
    async createTicket(data: CreateTicketRequest): Promise<SupportTicket> {
        return apiClient.post("/support/tickets", data)
    },

    /**
     * Get list of user's support tickets
     */
    async getTickets(params?: {
        page?: number
        page_size?: number
        status?: TicketStatus | string
    }): Promise<TicketListResponse> {
        return apiClient.get("/support/tickets", params)
    },

    /**
     * Get ticket statistics
     */
    async getStats(): Promise<TicketStats> {
        return apiClient.get("/support/tickets/stats")
    },

    /**
     * Get detailed ticket information with messages
     */
    async getTicketDetail(ticketId: string): Promise<SupportTicketDetail> {
        return apiClient.get(`/support/tickets/${ticketId}`)
    },

    /**
     * Add a message to a ticket
     */
    async addMessage(ticketId: string, data: CreateMessageRequest): Promise<TicketMessage> {
        return apiClient.post(`/support/tickets/${ticketId}/messages`, data)
    },
}

export default supportApi
