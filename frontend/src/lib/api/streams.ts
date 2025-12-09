import apiClient from "./client"

// ============ Live Event Types ============
export interface LiveEvent {
    id: string
    account_id: string
    title: string
    description?: string
    scheduled_start: string
    scheduled_end?: string
    status: "scheduled" | "live" | "ended" | "cancelled"
    broadcast_id?: string
    stream_id?: string
    rtmp_url?: string
    stream_key?: string
    privacy_status: "public" | "unlisted" | "private"
    enable_dvr: boolean
    enable_auto_start: boolean
    enable_auto_stop: boolean
    thumbnail_url?: string
    viewer_count?: number
    created_at: string
    updated_at: string
}

export interface CreateLiveEventRequest {
    account_id: string
    title: string
    description?: string
    scheduled_start: string
    scheduled_end?: string
    privacy_status?: "public" | "unlisted" | "private"
    enable_dvr?: boolean
    enable_auto_start?: boolean
    enable_auto_stop?: boolean
    thumbnail_url?: string
}

export interface UpdateLiveEventRequest {
    title?: string
    description?: string
    scheduled_start?: string
    scheduled_end?: string
    privacy_status?: "public" | "unlisted" | "private"
    enable_dvr?: boolean
    enable_auto_start?: boolean
    enable_auto_stop?: boolean
}

// ============ Stream Health Types ============
export interface StreamHealth {
    event_id: string
    status: "healthy" | "warning" | "critical" | "offline"
    bitrate: number
    dropped_frames: number
    fps: number
    resolution: string
    connection_quality: number
    last_updated: string
}

export interface StreamHealthHistory {
    timestamp: string
    bitrate: number
    dropped_frames: number
    fps: number
    connection_quality: number
    viewer_count: number
}

export interface StreamAlert {
    id: string
    event_id: string
    type: "health_warning" | "health_critical" | "reconnection" | "failover" | "disconnection"
    message: string
    severity: "info" | "warning" | "error"
    acknowledged: boolean
    created_at: string
}

// ============ Playlist Types ============
export interface PlaylistItem {
    id: string
    event_id: string
    video_url: string
    title: string
    duration: number
    order: number
    status: "pending" | "playing" | "completed" | "skipped"
}

export interface CreatePlaylistItemRequest {
    video_url: string
    title: string
    duration?: number
    order?: number
}

// ============ Simulcast Types ============
export interface SimulcastTarget {
    id: string
    event_id: string
    platform: string
    rtmp_url: string
    stream_key: string
    status: "active" | "inactive" | "error"
    health?: StreamHealth
}

export interface CreateSimulcastTargetRequest {
    platform: string
    rtmp_url: string
    stream_key: string
}

export interface LiveEventsResponse {
    items: LiveEvent[]
    total: number
    page: number
    page_size: number
}

export const streamsApi = {
    // ============ Live Events ============
    async getEvents(params?: {
        account_id?: string
        status?: string
        page?: number
        page_size?: number
    }): Promise<LiveEventsResponse> {
        try {
            return await apiClient.get("/streams/events", params)
        } catch (error) {
            console.error("Failed to fetch events:", error)
            return { items: [], total: 0, page: 1, page_size: 10 }
        }
    },

    async getEvent(eventId: string): Promise<LiveEvent> {
        return await apiClient.get(`/streams/events/${eventId}`)
    },

    async createEvent(data: CreateLiveEventRequest): Promise<LiveEvent> {
        return await apiClient.post("/streams/events", data)
    },

    async updateEvent(eventId: string, data: UpdateLiveEventRequest): Promise<LiveEvent> {
        return await apiClient.patch(`/streams/events/${eventId}`, data)
    },

    async deleteEvent(eventId: string): Promise<void> {
        return await apiClient.delete(`/streams/events/${eventId}`)
    },

    async startEvent(eventId: string): Promise<LiveEvent> {
        return await apiClient.post(`/streams/events/${eventId}/start`)
    },

    async stopEvent(eventId: string): Promise<LiveEvent> {
        return await apiClient.post(`/streams/events/${eventId}/stop`)
    },

    // ============ Stream Health ============
    async getHealth(eventId: string): Promise<StreamHealth> {
        try {
            return await apiClient.get(`/streams/events/${eventId}/health`)
        } catch (error) {
            return {
                event_id: eventId,
                status: "offline",
                bitrate: 0,
                dropped_frames: 0,
                fps: 0,
                resolution: "0x0",
                connection_quality: 0,
                last_updated: new Date().toISOString(),
            }
        }
    },

    async getHealthHistory(eventId: string, duration?: string): Promise<StreamHealthHistory[]> {
        try {
            return await apiClient.get(`/streams/events/${eventId}/health/history`, { duration })
        } catch (error) {
            // Return mock data for demo purposes
            const now = Date.now()
            return Array.from({ length: 30 }, (_, i) => ({
                timestamp: new Date(now - (29 - i) * 60000).toISOString(),
                bitrate: 4500 + Math.random() * 1000 - 500,
                dropped_frames: Math.floor(Math.random() * 5),
                fps: 29 + Math.random() * 2,
                connection_quality: 85 + Math.random() * 15,
                viewer_count: Math.floor(100 + Math.random() * 50),
            }))
        }
    },

    async getAlerts(eventId: string): Promise<StreamAlert[]> {
        try {
            return await apiClient.get(`/streams/events/${eventId}/alerts`)
        } catch (error) {
            return []
        }
    },

    async acknowledgeAlert(eventId: string, alertId: string): Promise<void> {
        return await apiClient.post(`/streams/events/${eventId}/alerts/${alertId}/acknowledge`)
    },

    // ============ Playlist ============
    async getPlaylist(eventId: string): Promise<PlaylistItem[]> {
        try {
            return await apiClient.get(`/streams/events/${eventId}/playlist`)
        } catch (error) {
            return []
        }
    },

    async addPlaylistItem(eventId: string, data: CreatePlaylistItemRequest): Promise<PlaylistItem> {
        return await apiClient.post(`/streams/events/${eventId}/playlist`, data)
    },

    async removePlaylistItem(eventId: string, itemId: string): Promise<void> {
        return await apiClient.delete(`/streams/events/${eventId}/playlist/${itemId}`)
    },

    async reorderPlaylist(eventId: string, itemIds: string[]): Promise<PlaylistItem[]> {
        return await apiClient.post(`/streams/events/${eventId}/playlist/reorder`, { item_ids: itemIds })
    },

    // ============ Simulcast ============
    async getSimulcastTargets(eventId: string): Promise<SimulcastTarget[]> {
        try {
            return await apiClient.get(`/streams/events/${eventId}/simulcast`)
        } catch (error) {
            return []
        }
    },

    async addSimulcastTarget(eventId: string, data: CreateSimulcastTargetRequest): Promise<SimulcastTarget> {
        return await apiClient.post(`/streams/events/${eventId}/simulcast`, data)
    },

    async removeSimulcastTarget(eventId: string, targetId: string): Promise<void> {
        return await apiClient.delete(`/streams/events/${eventId}/simulcast/${targetId}`)
    },
}

export default streamsApi
