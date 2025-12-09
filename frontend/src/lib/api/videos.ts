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

export const videosApi = {
    /**
     * Get paginated list of videos
     */
    async getVideos(filters?: VideoFilters): Promise<PaginatedResponse<Video>> {
        return apiClient.get("/videos", filters)
    },

    /**
     * Get single video by ID
     */
    async getVideo(videoId: string): Promise<Video> {
        return apiClient.get(`/videos/${videoId}`)
    },

    /**
     * Upload a new video
     */
    async uploadVideo(data: UploadVideoData, file: File): Promise<{ jobId: string }> {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("data", JSON.stringify(data))

        const response = await fetch(`${apiClient["baseUrl"]}/videos/upload`, {
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
     * Update video metadata
     */
    async updateVideo(videoId: string, data: Partial<UploadVideoData>): Promise<Video> {
        return apiClient.put(`/videos/${videoId}`, data)
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
        return apiClient.post("/videos/bulk-update", data)
    },

    /**
     * Bulk delete videos
     */
    async bulkDelete(videoIds: string[]): Promise<BulkResult> {
        return apiClient.post("/videos/bulk-delete", { videoIds })
    },
}

export default videosApi
