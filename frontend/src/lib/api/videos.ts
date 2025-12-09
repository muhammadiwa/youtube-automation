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
     * Upload a new video
     */
    async uploadVideo(data: UploadVideoData, file: File): Promise<{ jobId: string }> {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("data", JSON.stringify(data))

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/upload`, {
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
