import apiClient from "./client"
import type { Video, PaginatedResponse } from "@/types"

export interface VideoFilters {
    accountId?: string
    status?: "draft" | "uploading" | "processing" | "published" | "scheduled"
    visibility?: "public" | "unlisted" | "private"
    search?: string
    sortBy?: "date" | "views" | "status"
    sortOrder?: "asc" | "desc"
    page?: number
    pageSize?: number
}

export interface UploadVideoData {
    accountId: string
    title: string
    description?: string
    tags?: string[]
    categoryId?: string
    visibility?: "public" | "unlisted" | "private"
    scheduledPublishAt?: string
}

export interface BulkUpdateData {
    videoIds: string[]
    updates: {
        title?: string
        description?: string
        tags?: string[]
        categoryId?: string
        visibility?: "public" | "unlisted" | "private"
        scheduledPublishAt?: string
    }
}

export interface BulkResult {
    success: number
    failed: number
    results: Array<{
        videoId: string
        success: boolean
        error?: string
    }>
}

const defaultPaginatedResponse: PaginatedResponse<Video> = {
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    totalPages: 0,
}

export const videosApi = {
    /**
     * Get paginated list of videos
     */
    async getVideos(filters?: VideoFilters): Promise<PaginatedResponse<Video>> {
        try {
            const params = filters ? { ...filters } as Record<string, string | number | boolean | undefined> : undefined
            const response = await apiClient.get<PaginatedResponse<Video> | Video[] | { videos: Video[] }>("/videos", params)

            // Handle different response formats
            if (Array.isArray(response)) {
                return {
                    items: response,
                    total: response.length,
                    page: 1,
                    pageSize: response.length,
                    totalPages: 1,
                }
            }
            if (response && typeof response === 'object') {
                if ('items' in response && Array.isArray(response.items)) {
                    return response as PaginatedResponse<Video>
                }
                if ('videos' in response && Array.isArray(response.videos)) {
                    return {
                        items: response.videos,
                        total: response.videos.length,
                        page: 1,
                        pageSize: response.videos.length,
                        totalPages: 1,
                    }
                }
            }
            return defaultPaginatedResponse
        } catch (error) {
            console.error("Failed to fetch videos:", error)
            return defaultPaginatedResponse
        }
    },

    /**
     * Get single video by ID
     */
    async getVideo(videoId: string): Promise<Video> {
        return apiClient.get(`/videos/${videoId}`)
    },

    /**
     * Upload a new video with optional thumbnail
     */
    async uploadVideo(data: UploadVideoData, file: File, thumbnail?: File): Promise<{ jobId: string; videoId: string }> {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("account_id", data.accountId)
        formData.append("title", data.title)
        if (data.description) formData.append("description", data.description)
        if (data.tags && data.tags.length > 0) formData.append("tags", data.tags.join(","))
        if (data.categoryId) formData.append("category_id", data.categoryId)
        formData.append("visibility", data.visibility || "private")
        if (data.scheduledPublishAt) formData.append("scheduled_publish_at", data.scheduledPublishAt)
        if (thumbnail) formData.append("thumbnail", thumbnail)

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${apiClient.getAccessToken()}`,
            },
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json()
            throw error
        }

        const result = await response.json()
        return { jobId: result.job_id, videoId: result.video_id }
    },

    /**
     * Update video metadata
     */
    async updateVideo(videoId: string, data: Partial<UploadVideoData>): Promise<Video> {
        // Map frontend field names to backend field names
        const backendData: Record<string, unknown> = {}
        if (data.title !== undefined) backendData.title = data.title
        if (data.description !== undefined) backendData.description = data.description
        if (data.tags !== undefined) backendData.tags = data.tags
        if (data.categoryId !== undefined) backendData.category_id = data.categoryId
        if (data.visibility !== undefined) backendData.visibility = data.visibility

        return apiClient.patch(`/videos/${videoId}/metadata`, backendData)
    },

    /**
     * Delete video
     */
    async deleteVideo(videoId: string): Promise<void> {
        return apiClient.delete(`/videos/${videoId}`)
    },

    /**
     * Bulk update videos
     */
    async bulkUpdate(data: BulkUpdateData): Promise<BulkResult> {
        // Map frontend format to backend format
        const backendData: Record<string, unknown> = {
            video_ids: data.videoIds,
        }
        if (data.updates.title) backendData.title = data.updates.title
        if (data.updates.description) backendData.description = data.updates.description
        if (data.updates.tags) backendData.tags = data.updates.tags
        if (data.updates.categoryId) backendData.category_id = data.updates.categoryId
        if (data.updates.visibility) backendData.visibility = data.updates.visibility

        return apiClient.post("/videos/bulk-update", backendData)
    },

    /**
     * Bulk delete videos
     */
    async bulkDelete(videoIds: string[]): Promise<BulkResult> {
        return apiClient.post("/videos/bulk-delete", { videoIds })
    },

    /**
     * Get upload progress for a video
     */
    async getUploadProgress(videoId: string): Promise<{
        videoId: string
        jobId: string | null
        status: string
        progress: number
        error: string | null
    }> {
        return apiClient.get(`/videos/${videoId}/progress`)
    },

    /**
     * Upload custom thumbnail for a video
     */
    async uploadThumbnail(videoId: string, file: File): Promise<{ status: string; taskId: string }> {
        const formData = new FormData()
        formData.append("thumbnail", file)

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/${videoId}/thumbnail`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${apiClient.getAccessToken()}`,
            },
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json()
            throw error
        }

        return response.json()
    },

    /**
     * Sync video stats from YouTube
     */
    async syncVideoStats(videoId: string): Promise<Video> {
        return apiClient.post(`/videos/${videoId}/sync-stats`, {})
    },
}

export default videosApi
