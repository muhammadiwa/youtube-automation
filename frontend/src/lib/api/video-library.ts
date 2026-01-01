/**
 * Video Library API Client
 * 
 * Handles all API calls for video library management (library-first approach).
 * Requirements: 1.1, 1.2, 1.3, 2.1, 3.1
 */

import apiClient from "./client"
import type { Video, PaginatedResponse } from "@/types"

// ============================================
// Types
// ============================================

export interface VideoFolder {
    id: string
    userId: string
    name: string
    parentId: string | null
    description: string | null
    color: string | null
    icon: string | null
    position: number
    createdAt: string
    updatedAt: string
}

export interface LibraryVideoFilters {
    folderId?: string | null
    status?: "in_library" | "uploading" | "uploaded" | "failed"
    search?: string
    tags?: string[]
    isFavorite?: boolean
    sortBy?: "created_at" | "title" | "duration" | "file_size"
    sortOrder?: "asc" | "desc"
    page?: number
    limit?: number
}

export interface UploadToLibraryData {
    title: string
    description?: string
    tags?: string[]
    folderId?: string | null
}

export interface VideoMetadataUpdate {
    title?: string
    description?: string
    tags?: string[]
    notes?: string
}

export interface CreateFolderData {
    name: string
    parentId?: string | null
    description?: string
    color?: string
    icon?: string
}

export interface UpdateFolderData {
    name?: string
    description?: string
    color?: string
    icon?: string
}

export interface YouTubeUploadRequest {
    accountId: string
    title?: string
    description?: string
    tags?: string[]
    categoryId?: string
    visibility?: "public" | "unlisted" | "private"
    scheduledPublishAt?: string
}

export interface BulkUploadToYouTubeRequest {
    videoIds: string[]
    accountId: string
}

export interface CreateStreamRequest {
    accountId: string
    title?: string
    loopMode?: "none" | "count" | "infinite"
    loopCount?: number
    resolution?: "720p" | "1080p" | "1440p" | "4k"
    targetBitrate?: number
    targetFps?: number
    scheduledStartAt?: string
}

export interface VideoUsageStats {
    youtubeUploads: number
    streamingSessions: number
    totalStreamingDuration: number
    lastUsedAt: string | null
}

export interface UsageLog {
    id: string
    usageType: "youtube_upload" | "live_stream"
    startedAt: string
    endedAt: string | null
    usageMetadata: {
        youtube_id?: string
        stream_job_id?: string
        stream_duration?: number
        viewer_count?: number
        upload_duration?: number
    }
}

// ============================================
// Video Library API
// ============================================

export const videoLibraryApi = {
    /**
     * Upload video to library (not YouTube)
     */
    async uploadToLibrary(
        file: File,
        data: UploadToLibraryData
    ): Promise<Video> {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("title", data.title)
        if (data.description) formData.append("description", data.description)
        if (data.tags && data.tags.length > 0) formData.append("tags", data.tags.join(","))
        if (data.folderId) formData.append("folder_id", data.folderId)

        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/library/upload`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${apiClient.getAccessToken()}`,
                },
                body: formData,
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || "Failed to upload video")
        }

        return response.json()
    },

    /**
     * Get library videos with filters and pagination
     */
    async getLibraryVideos(
        filters?: LibraryVideoFilters
    ): Promise<PaginatedResponse<Video>> {
        const params: Record<string, string | number | boolean> = {
            page: filters?.page || 1,
            limit: filters?.limit || 20,
        }

        // Only send folder_id if it's a valid non-empty string (not null/undefined/"")
        if (filters?.folderId) params.folder_id = filters.folderId
        if (filters?.status) params.status = filters.status
        if (filters?.search) params.search = filters.search
        if (filters?.tags && filters.tags.length > 0) params.tags = filters.tags.join(",")
        if (filters?.isFavorite !== undefined) params.is_favorite = filters.isFavorite
        if (filters?.sortBy) params.sort_by = filters.sortBy
        if (filters?.sortOrder) params.sort_order = filters.sortOrder

        return apiClient.get<PaginatedResponse<Video>>("/videos/library", params)
    },

    /**
     * Get single video from library
     */
    async getLibraryVideo(videoId: string): Promise<Video> {
        return apiClient.get(`/videos/library/${videoId}`)
    },

    /**
     * Update video metadata in library
     */
    async updateMetadata(
        videoId: string,
        data: VideoMetadataUpdate
    ): Promise<Video> {
        return apiClient.patch(`/videos/library/${videoId}`, data)
    },

    /**
     * Delete video from library
     */
    async deleteFromLibrary(videoId: string): Promise<void> {
        return apiClient.delete(`/videos/library/${videoId}`)
    },

    /**
     * Toggle video favorite status
     */
    async toggleFavorite(videoId: string): Promise<Video> {
        return apiClient.post(`/videos/library/${videoId}/favorite`, {})
    },

    /**
     * Move video to folder (or root if folderId is null)
     */
    async moveToFolder(videoId: string, folderId: string | null): Promise<Video> {
        // Build URL with query param if folderId is provided
        const url = folderId
            ? `/videos/library/${videoId}/move?folder_id=${folderId}`
            : `/videos/library/${videoId}/move`
        return apiClient.post(url, {})
    },

    /**
     * Get video stream URL for preview
     */
    async getStreamUrl(videoId: string): Promise<{ streamUrl: string }> {
        const response = await apiClient.get<{ stream_url: string }>(`/videos/library/${videoId}/stream`)
        return { streamUrl: response.stream_url }
    },

    // ============================================
    // Folder Management
    // ============================================

    /**
     * Get all folders (tree structure)
     */
    async getAllFolders(): Promise<VideoFolder[]> {
        return apiClient.get("/videos/library/folders/all")
    },

    /**
     * Create new folder
     */
    async createFolder(data: CreateFolderData): Promise<VideoFolder> {
        return apiClient.post("/videos/library/folders", data)
    },

    /**
     * Update folder
     */
    async updateFolder(
        folderId: string,
        data: UpdateFolderData
    ): Promise<VideoFolder> {
        return apiClient.patch(`/videos/library/folders/${folderId}`, data)
    },

    /**
     * Delete folder (must be empty)
     */
    async deleteFolder(folderId: string): Promise<void> {
        return apiClient.delete(`/videos/library/folders/${folderId}`)
    },

    // ============================================
    // YouTube Upload
    // ============================================

    /**
     * Upload library video to YouTube
     */
    async uploadToYouTube(
        videoId: string,
        data: YouTubeUploadRequest
    ): Promise<{ jobId: string; status: string; message: string }> {
        return apiClient.post(`/videos/library/${videoId}/upload-to-youtube`, {
            account_id: data.accountId,
            title: data.title,
            description: data.description,
            tags: data.tags,
            category_id: data.categoryId,
            visibility: data.visibility,
            scheduled_publish_at: data.scheduledPublishAt,
        })
    },

    /**
     * Bulk upload multiple videos to YouTube
     */
    async bulkUploadToYouTube(
        data: BulkUploadToYouTubeRequest
    ): Promise<{
        totalVideos: number
        jobsCreated: number
        jobs: Array<{ jobId: string; videoId: string; status: string }>
        errors: string[]
    }> {
        return apiClient.post("/videos/library/bulk-upload-to-youtube", {
            video_ids: data.videoIds,
            account_id: data.accountId,
        })
    },

    /**
     * Get YouTube upload progress
     */
    async getUploadProgress(videoId: string): Promise<{
        videoId: string
        jobId: string | null
        status: string
        progress: number
        youtubeId: string | null
        uploadAttempts: number
        lastError: string | null
    }> {
        return apiClient.get(`/videos/library/${videoId}/upload-progress`)
    },

    /**
     * Retry failed YouTube upload
     */
    async retryUpload(videoId: string): Promise<{ jobId: string; status: string }> {
        return apiClient.post(`/videos/library/${videoId}/retry-upload`, {})
    },

    /**
     * Cancel ongoing YouTube upload
     */
    async cancelUpload(videoId: string): Promise<{ status: string; message: string }> {
        return apiClient.post(`/videos/library/${videoId}/cancel-upload`, {})
    },

    /**
     * Get YouTube video info and stats
     */
    async getYouTubeInfo(videoId: string): Promise<{
        youtubeId: string
        title: string
        viewCount: number
        likeCount: number
        commentCount: number
        publishedAt: string
    }> {
        return apiClient.get(`/videos/library/${videoId}/youtube-info`)
    },

    // ============================================
    // Streaming Integration
    // ============================================

    /**
     * Create stream job from library video
     */
    async createStream(
        videoId: string,
        data: CreateStreamRequest
    ): Promise<{
        streamJobId: string
        videoId: string
        status: string
        title: string
        message: string
    }> {
        const response = await apiClient.post<{
            stream_job_id: string
            video_id: string
            status: string
            title: string
            message: string
        }>(`/videos/library/${videoId}/create-stream`, {
            account_id: data.accountId,
            title: data.title,
            loop_mode: data.loopMode || "infinite",
            loop_count: data.loopCount,
            resolution: data.resolution || "1080p",
            target_bitrate: data.targetBitrate || 6000,
            target_fps: data.targetFps || 30,
            scheduled_start_at: data.scheduledStartAt,
        })

        // Transform snake_case to camelCase
        return {
            streamJobId: response.stream_job_id,
            videoId: response.video_id,
            status: response.status,
            title: response.title,
            message: response.message,
        }
    },

    /**
     * Get streaming history for video
     */
    async getStreamingHistory(
        videoId: string,
        page: number = 1,
        limit: number = 20
    ): Promise<{
        videoId: string
        history: Array<{
            id: string
            streamJobId: string
            startedAt: string
            endedAt: string | null
            duration: number
            metadata: Record<string, unknown>
        }>
        page: number
        limit: number
    }> {
        return apiClient.get(`/videos/library/${videoId}/streaming-history`, {
            page,
            limit,
        })
    },

    /**
     * Get video usage statistics
     */
    async getUsageStats(videoId: string): Promise<{
        videoId: string
        title: string
        usageStats: VideoUsageStats
        usageLogs: UsageLog[]
        isCurrentlyInUse: boolean
        youtubeId: string | null
        isUsedForStreaming: boolean
        streamingCount: number
        totalStreamingDuration: number
    }> {
        return apiClient.get(`/videos/library/${videoId}/usage`)
    },
}

export default videoLibraryApi
