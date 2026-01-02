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

// Backend response format
interface BackendLiveEventsResponse {
    events: LiveEvent[]
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
            const response = await apiClient.get<BackendLiveEventsResponse | LiveEventsResponse>("/streams/events", params)

            // Handle backend response format (events) vs frontend format (items)
            if ('events' in response && Array.isArray(response.events)) {
                return {
                    items: response.events,
                    total: response.total || 0,
                    page: response.page || 1,
                    page_size: response.page_size || 10,
                }
            }
            if ('items' in response && Array.isArray(response.items)) {
                return response as LiveEventsResponse
            }
            return { items: [], total: 0, page: 1, page_size: 10 }
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
