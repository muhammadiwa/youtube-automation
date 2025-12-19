/**
 * Stream Jobs API Client for Video-to-Live Streaming
 * 
 * Provides API methods for managing FFmpeg-based video streaming jobs.
 * Requirements: 1.1, 1.2, 1.3, 1.5, 4.6, 4.7, 6.4, 9.1
 */

import apiClient from "./client"

// ============================================
// Types & Interfaces
// ============================================

export type StreamJobStatus =
    | "pending"
    | "scheduled"
    | "starting"
    | "running"
    | "stopping"
    | "stopped"
    | "completed"
    | "failed"
    | "cancelled"

export type LoopMode = "none" | "count" | "infinite"

export type EncodingMode = "cbr" | "vbr"

export type Resolution = "720p" | "1080p" | "1440p" | "4k"

export interface StreamJob {
    id: string
    userId: string
    accountId: string
    videoId: string | null
    videoPath: string
    playlistId: string | null

    // RTMP settings
    rtmpUrl: string
    streamKeyMasked: string | null
    isStreamKeyLocked: boolean

    // Metadata
    title: string
    description: string | null

    // Loop configuration
    loopMode: LoopMode
    loopCount: number | null
    currentLoop: number

    // Output settings
    resolution: Resolution
    targetBitrate: number
    encodingMode: EncodingMode
    targetFps: number

    // Scheduling
    scheduledStartAt: string | null
    scheduledEndAt: string | null
    timeUntilStart: number | null

    // Process tracking
    pid: number | null
    status: StreamJobStatus

    // Timing
    actualStartAt: string | null
    actualEndAt: string | null
    totalDurationSeconds: number
    currentDurationSeconds: number

    // Error handling
    lastError: string | null
    restartCount: number
    maxRestarts: number
    enableAutoRestart: boolean

    // Current metrics
    currentBitrate: number | null
    currentBitrateKbps: number | null
    currentFps: number | null
    currentSpeed: string | null
    droppedFrames: number
    frameCount: number

    // Playlist tracking
    currentPlaylistIndex: number
    totalPlaylistItems: number
    playlistProgress: number

    // Timestamps
    createdAt: string
    updatedAt: string
}

export interface StreamJobHealth {
    id: string
    streamJobId: string

    // FFmpeg metrics
    bitrate: number
    bitrateKbps: number
    fps: number | null
    speed: string | null
    droppedFrames: number
    droppedFramesDelta: number
    frameCount: number

    // System resources
    cpuPercent: number | null
    memoryMb: number | null

    // Alert info
    alertType: "warning" | "critical" | null
    alertMessage: string | null
    isAlertAcknowledged: boolean
    isHealthy: boolean

    // Timestamp
    collectedAt: string
}

export interface CreateStreamJobRequest {
    accountId: string
    videoId?: string
    videoPath: string
    playlistId?: string

    // RTMP settings
    rtmpUrl?: string
    streamKey: string

    // Metadata
    title: string
    description?: string

    // Loop configuration
    loopMode?: LoopMode
    loopCount?: number

    // Output settings
    resolution?: Resolution
    targetBitrate?: number
    encodingMode?: EncodingMode
    targetFps?: number

    // Scheduling
    scheduledStartAt?: string
    scheduledEndAt?: string

    // Auto-restart
    enableAutoRestart?: boolean
    maxRestarts?: number
}

export interface UpdateStreamJobRequest {
    title?: string
    description?: string
    loopMode?: LoopMode
    loopCount?: number
    resolution?: Resolution
    targetBitrate?: number
    encodingMode?: EncodingMode
    targetFps?: number
    scheduledStartAt?: string
    scheduledEndAt?: string
    enableAutoRestart?: boolean
    maxRestarts?: number
}

export interface StreamJobListResponse {
    jobs: StreamJob[]
    total: number
    page: number
    pageSize: number
}

export interface StreamJobHealthListResponse {
    records: StreamJobHealth[]
    total: number
    page: number
    pageSize: number
}

export interface SlotStatus {
    usedSlots: number
    totalSlots: number
    availableSlots: number
    plan: string
}

export interface ResourceUsage {
    totalCpuPercent: number
    totalMemoryMb: number
    totalBandwidthKbps: number
    activeStreams: number
    estimatedRemainingSlots: number
    isWarning: boolean
}

export interface StreamResource {
    streamJobId: string
    title: string
    status: StreamJobStatus
    cpuPercent: number | null
    memoryMb: number | null
    bitrateKbps: number | null
}

export interface ResourceDashboard {
    aggregate: ResourceUsage
    streams: StreamResource[]
}

export interface StreamJobFilters {
    status?: StreamJobStatus
    accountId?: string
    page?: number
    pageSize?: number
}

// ============================================
// API Response Transformers
// ============================================

function transformStreamJob(data: Record<string, unknown>): StreamJob {
    return {
        id: data.id as string,
        userId: data.user_id as string,
        accountId: data.account_id as string,
        videoId: data.video_id as string | null,
        videoPath: data.video_path as string,
        playlistId: data.playlist_id as string | null,
        rtmpUrl: data.rtmp_url as string,
        streamKeyMasked: data.stream_key_masked as string | null,
        isStreamKeyLocked: data.is_stream_key_locked as boolean,
        title: data.title as string,
        description: data.description as string | null,
        loopMode: data.loop_mode as LoopMode,
        loopCount: data.loop_count as number | null,
        currentLoop: data.current_loop as number,
        resolution: data.resolution as Resolution,
        targetBitrate: data.target_bitrate as number,
        encodingMode: data.encoding_mode as EncodingMode,
        targetFps: data.target_fps as number,
        scheduledStartAt: data.scheduled_start_at as string | null,
        scheduledEndAt: data.scheduled_end_at as string | null,
        timeUntilStart: data.time_until_start as number | null,
        pid: data.pid as number | null,
        status: data.status as StreamJobStatus,
        actualStartAt: data.actual_start_at as string | null,
        actualEndAt: data.actual_end_at as string | null,
        totalDurationSeconds: data.total_duration_seconds as number,
        currentDurationSeconds: data.current_duration_seconds as number,
        lastError: data.last_error as string | null,
        restartCount: data.restart_count as number,
        maxRestarts: data.max_restarts as number,
        enableAutoRestart: data.enable_auto_restart as boolean,
        currentBitrate: data.current_bitrate as number | null,
        currentBitrateKbps: data.current_bitrate_kbps as number | null,
        currentFps: data.current_fps as number | null,
        currentSpeed: data.current_speed as string | null,
        droppedFrames: data.dropped_frames as number,
        frameCount: data.frame_count as number,
        currentPlaylistIndex: data.current_playlist_index as number || 0,
        totalPlaylistItems: data.total_playlist_items as number || 0,
        playlistProgress: data.playlist_progress as number || 0,
        createdAt: data.created_at as string,
        updatedAt: data.updated_at as string,
    }
}

function transformStreamJobHealth(data: Record<string, unknown>): StreamJobHealth {
    return {
        id: data.id as string,
        streamJobId: data.stream_job_id as string,
        bitrate: data.bitrate as number,
        bitrateKbps: data.bitrate_kbps as number,
        fps: data.fps as number | null,
        speed: data.speed as string | null,
        droppedFrames: data.dropped_frames as number,
        droppedFramesDelta: data.dropped_frames_delta as number,
        frameCount: data.frame_count as number,
        cpuPercent: data.cpu_percent as number | null,
        memoryMb: data.memory_mb as number | null,
        alertType: data.alert_type as "warning" | "critical" | null,
        alertMessage: data.alert_message as string | null,
        isAlertAcknowledged: data.is_alert_acknowledged as boolean,
        isHealthy: data.is_healthy as boolean,
        collectedAt: data.collected_at as string,
    }
}

function transformSlotStatus(data: Record<string, unknown>): SlotStatus {
    return {
        usedSlots: data.used_slots as number,
        totalSlots: data.total_slots as number,
        availableSlots: data.available_slots as number,
        plan: data.plan as string,
    }
}

function transformResourceDashboard(data: Record<string, unknown>): ResourceDashboard {
    const aggregate = data.aggregate as Record<string, unknown>
    const streams = data.streams as Record<string, unknown>[]

    return {
        aggregate: {
            totalCpuPercent: aggregate.total_cpu_percent as number,
            totalMemoryMb: aggregate.total_memory_mb as number,
            totalBandwidthKbps: aggregate.total_bandwidth_kbps as number,
            activeStreams: aggregate.active_streams as number,
            estimatedRemainingSlots: aggregate.estimated_remaining_slots as number,
            isWarning: aggregate.is_warning as boolean,
        },
        streams: streams.map((s) => ({
            streamJobId: s.stream_job_id as string,
            title: s.title as string,
            status: s.status as StreamJobStatus,
            cpuPercent: s.cpu_percent as number | null,
            memoryMb: s.memory_mb as number | null,
            bitrateKbps: s.bitrate_kbps as number | null,
        })),
    }
}

// ============================================
// API Client
// ============================================

export const streamJobsApi = {
    /**
     * Create a new stream job
     * Requirements: 1.1
     */
    async createStreamJob(request: CreateStreamJobRequest): Promise<StreamJob> {
        const backendData = {
            account_id: request.accountId,
            video_id: request.videoId,
            video_path: request.videoPath,
            playlist_id: request.playlistId,
            rtmp_url: request.rtmpUrl || "rtmp://a.rtmp.youtube.com/live2",
            stream_key: request.streamKey,
            title: request.title,
            description: request.description,
            loop_mode: request.loopMode || "none",
            loop_count: request.loopCount,
            resolution: request.resolution || "1080p",
            target_bitrate: request.targetBitrate || 6000,
            encoding_mode: request.encodingMode || "cbr",
            target_fps: request.targetFps || 30,
            scheduled_start_at: request.scheduledStartAt,
            scheduled_end_at: request.scheduledEndAt,
            enable_auto_restart: request.enableAutoRestart ?? true,
            max_restarts: request.maxRestarts ?? 5,
        }

        const response = await apiClient.post<Record<string, unknown>>("/stream-jobs", backendData)
        return transformStreamJob(response)
    },

    /**
     * Get paginated list of stream jobs
     * Requirements: 1.5
     */
    async getStreamJobs(filters?: StreamJobFilters): Promise<StreamJobListResponse> {
        const params: Record<string, string | number | undefined> = {}
        if (filters?.status) params.status = filters.status
        if (filters?.accountId) params.account_id = filters.accountId
        if (filters?.page) params.page = filters.page
        if (filters?.pageSize) params.page_size = filters.pageSize

        const response = await apiClient.get<Record<string, unknown>>("/stream-jobs", params)

        return {
            jobs: ((response.jobs as Record<string, unknown>[]) || []).map(transformStreamJob),
            total: response.total as number,
            page: response.page as number,
            pageSize: response.page_size as number,
        }
    },

    /**
     * Get single stream job by ID
     * Requirements: 1.5
     */
    async getStreamJob(jobId: string): Promise<StreamJob> {
        const response = await apiClient.get<Record<string, unknown>>(`/stream-jobs/${jobId}`)
        return transformStreamJob(response)
    },

    /**
     * Update a stream job
     */
    async updateStreamJob(jobId: string, request: UpdateStreamJobRequest): Promise<StreamJob> {
        const backendData: Record<string, unknown> = {}
        if (request.title !== undefined) backendData.title = request.title
        if (request.description !== undefined) backendData.description = request.description
        if (request.loopMode !== undefined) backendData.loop_mode = request.loopMode
        if (request.loopCount !== undefined) backendData.loop_count = request.loopCount
        if (request.resolution !== undefined) backendData.resolution = request.resolution
        if (request.targetBitrate !== undefined) backendData.target_bitrate = request.targetBitrate
        if (request.encodingMode !== undefined) backendData.encoding_mode = request.encodingMode
        if (request.targetFps !== undefined) backendData.target_fps = request.targetFps
        if (request.scheduledStartAt !== undefined) backendData.scheduled_start_at = request.scheduledStartAt
        if (request.scheduledEndAt !== undefined) backendData.scheduled_end_at = request.scheduledEndAt
        if (request.enableAutoRestart !== undefined) backendData.enable_auto_restart = request.enableAutoRestart
        if (request.maxRestarts !== undefined) backendData.max_restarts = request.maxRestarts

        const response = await apiClient.put<Record<string, unknown>>(`/stream-jobs/${jobId}`, backendData)
        return transformStreamJob(response)
    },

    /**
     * Delete a stream job
     */
    async deleteStreamJob(jobId: string): Promise<void> {
        await apiClient.delete(`/stream-jobs/${jobId}`)
    },

    /**
     * Start a stream job
     * Requirements: 1.2
     */
    async startStreamJob(jobId: string): Promise<StreamJob> {
        const response = await apiClient.post<Record<string, unknown>>(`/stream-jobs/${jobId}/start`, {})
        return transformStreamJob(response)
    },

    /**
     * Stop a stream job
     * Requirements: 1.3
     */
    async stopStreamJob(jobId: string): Promise<StreamJob> {
        const response = await apiClient.post<Record<string, unknown>>(`/stream-jobs/${jobId}/stop`, {})
        return transformStreamJob(response)
    },

    /**
     * Restart a stream job
     */
    async restartStreamJob(jobId: string): Promise<StreamJob> {
        const response = await apiClient.post<Record<string, unknown>>(`/stream-jobs/${jobId}/restart`, {})
        return transformStreamJob(response)
    },

    /**
     * Get health history for a stream job
     * Requirements: 4.7
     */
    async getHealthHistory(
        jobId: string,
        options?: { hours?: number; page?: number; pageSize?: number }
    ): Promise<StreamJobHealthListResponse> {
        const params: Record<string, number | undefined> = {}
        if (options?.hours) params.hours = options.hours
        if (options?.page) params.page = options.page
        if (options?.pageSize) params.page_size = options.pageSize

        const response = await apiClient.get<Record<string, unknown>>(`/stream-jobs/${jobId}/health`, params)

        return {
            records: ((response.records as Record<string, unknown>[]) || []).map(transformStreamJobHealth),
            total: response.total as number,
            page: response.page as number,
            pageSize: response.page_size as number,
        }
    },

    /**
     * Get latest health for a stream job
     * Requirements: 4.7
     */
    async getHealthLatest(jobId: string): Promise<StreamJobHealth> {
        const response = await apiClient.get<Record<string, unknown>>(`/stream-jobs/${jobId}/health/latest`)
        return transformStreamJobHealth(response)
    },

    /**
     * Acknowledge a health alert
     */
    async acknowledgeAlert(healthId: string): Promise<StreamJobHealth> {
        const response = await apiClient.post<Record<string, unknown>>(`/stream-jobs/health/${healthId}/acknowledge`, {})
        return transformStreamJobHealth(response)
    },

    /**
     * Get slot status for current user
     * Requirements: 6.4
     */
    async getSlotStatus(): Promise<SlotStatus> {
        const response = await apiClient.get<Record<string, unknown>>("/stream-jobs/slots")
        return transformSlotStatus(response)
    },

    /**
     * Get resource usage dashboard
     * Requirements: 9.1
     */
    async getResourceUsage(): Promise<ResourceDashboard> {
        const response = await apiClient.get<Record<string, unknown>>("/stream-jobs/resources")
        return transformResourceDashboard(response)
    },

    /**
     * Connect to WebSocket for real-time health updates
     * Requirements: 4.6
     */
    connectToHealthWebSocket(
        jobId: string,
        callbacks: {
            onMessage: (health: StreamJobHealth) => void
            onStreamEnded?: (status: string) => void
            onError?: (error: Event) => void
            onClose?: () => void
        }
    ): WebSocket {
        const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1")
            .replace("http://", "ws://")
            .replace("https://", "wss://")

        const ws = new WebSocket(`${wsUrl}/stream-jobs/${jobId}/health/ws`)

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === "stream_ended") {
                    callbacks.onStreamEnded?.(data.status)
                } else {
                    callbacks.onMessage(transformStreamJobHealth(data))
                }
            } catch (error) {
                console.error("Failed to parse WebSocket message:", error)
            }
        }

        ws.onerror = (error) => {
            callbacks.onError?.(error)
        }

        ws.onclose = () => {
            callbacks.onClose?.()
        }

        return ws
    },
}

export default streamJobsApi
