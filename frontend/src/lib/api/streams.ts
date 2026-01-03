import apiClient from "./client"

// ============ Live Event Types ============
export interface LiveEvent {
    id: string
    account_id: string
    title: string
    description?: string
    scheduled_start: string  // mapped from scheduled_start_at
    scheduled_end?: string   // mapped from scheduled_end_at
    status: "scheduled" | "live" | "ended" | "cancelled" | "created"
    broadcast_id?: string    // mapped from youtube_broadcast_id
    stream_id?: string       // mapped from youtube_stream_id
    rtmp_url?: string
    stream_key?: string      // mapped from rtmp_key
    privacy_status: "public" | "unlisted" | "private"
    enable_dvr: boolean
    enable_auto_start: boolean
    enable_auto_stop: boolean
    thumbnail_url?: string
    viewer_count?: number    // mapped from peak_viewers
    created_at: string
    updated_at: string
}

// Backend response format (raw from API)
interface BackendLiveEvent {
    id: string
    account_id: string
    title: string
    description?: string
    scheduled_start_at?: string
    scheduled_end_at?: string
    actual_start_at?: string
    actual_end_at?: string
    status: string
    youtube_broadcast_id?: string
    youtube_stream_id?: string
    rtmp_url?: string
    rtmp_key?: string
    privacy_status: string
    enable_dvr: boolean
    enable_auto_start: boolean
    enable_auto_stop: boolean
    thumbnail_url?: string
    peak_viewers?: number
    total_chat_messages?: number
    created_at: string
    updated_at: string
}

// Transform backend response to frontend format
function transformLiveEvent(event: BackendLiveEvent): LiveEvent {
    return {
        id: event.id,
        account_id: event.account_id,
        title: event.title,
        description: event.description,
        scheduled_start: event.scheduled_start_at || event.actual_start_at || "",
        scheduled_end: event.scheduled_end_at || event.actual_end_at,
        status: event.status as LiveEvent["status"],
        broadcast_id: event.youtube_broadcast_id,
        stream_id: event.youtube_stream_id,
        rtmp_url: event.rtmp_url,
        stream_key: event.rtmp_key,
        privacy_status: event.privacy_status as LiveEvent["privacy_status"],
        enable_dvr: event.enable_dvr,
        enable_auto_start: event.enable_auto_start,
        enable_auto_stop: event.enable_auto_stop,
        thumbnail_url: event.thumbnail_url,
        viewer_count: event.peak_viewers,
        created_at: event.created_at,
        updated_at: event.updated_at,
    }
}

export interface CreateLiveEventRequest {
    account_id: string
    title: string
    description?: string
    scheduled_start_at: string  // Use backend field name
    scheduled_end_at?: string   // Use backend field name
    privacy_status?: "public" | "unlisted" | "private"
    enable_dvr?: boolean
    enable_auto_start?: boolean
    enable_auto_stop?: boolean
    thumbnail_url?: string
}

export interface UpdateLiveEventRequest {
    title?: string
    description?: string
    scheduled_start_at?: string  // Use backend field name
    scheduled_end_at?: string    // Use backend field name
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

// Backend response format for list
interface BackendLiveEventsResponse {
    events: BackendLiveEvent[]
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
            const response = await apiClient.get<BackendLiveEventsResponse>("/streams/events", params)

            // Transform backend events to frontend format
            if ('events' in response && Array.isArray(response.events)) {
                return {
                    items: response.events.map(transformLiveEvent),
                    total: response.total || 0,
                    page: response.page || 1,
                    page_size: response.page_size || 10,
                }
            }
            return { items: [], total: 0, page: 1, page_size: 10 }
        } catch (error) {
            console.error("Failed to fetch events:", error)
            return { items: [], total: 0, page: 1, page_size: 10 }
        }
    },

    async getEvent(eventId: string): Promise<LiveEvent> {
        const response = await apiClient.get<BackendLiveEvent>(`/streams/events/${eventId}`)
        return transformLiveEvent(response)
    },

    async createEvent(data: CreateLiveEventRequest): Promise<LiveEvent> {
        const response = await apiClient.post<BackendLiveEvent>("/streams/events", data)
        return transformLiveEvent(response)
    },

    async updateEvent(eventId: string, data: UpdateLiveEventRequest): Promise<LiveEvent> {
        const response = await apiClient.put<BackendLiveEvent>(`/streams/events/${eventId}`, data)
        return transformLiveEvent(response)
    },

    async deleteEvent(eventId: string): Promise<void> {
        return await apiClient.delete(`/streams/events/${eventId}`)
    },

    async startEvent(eventId: string): Promise<LiveEvent> {
        const response = await apiClient.post<BackendLiveEvent>(`/streams/events/${eventId}/start`)
        return transformLiveEvent(response)
    },

    async stopEvent(eventId: string): Promise<LiveEvent> {
        const response = await apiClient.post<BackendLiveEvent>(`/streams/events/${eventId}/stop`)
        return transformLiveEvent(response)
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
