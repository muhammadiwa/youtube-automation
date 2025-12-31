// Common types used across the application

export interface User {
    id: string
    email: string
    name: string
    is2FAEnabled: boolean
    createdAt: string
    lastLoginAt: string
}

export interface YouTubeAccount {
    id: string
    userId: string
    channelId: string
    channelTitle: string
    thumbnailUrl: string
    subscriberCount: number
    videoCount: number
    isMonetized: boolean
    hasLiveStreamingEnabled: boolean
    strikeCount: number
    tokenExpiresAt: string
    lastSyncAt: string
    status: "active" | "expired" | "error"
    // Stream key info
    hasStreamKey: boolean
    streamKeyMasked: string | null
    rtmpUrl: string | null
}

export interface Video {
    id: string
    youtubeId?: string
    accountId: string
    userId?: string
    title: string
    description?: string
    tags?: string[]
    categoryId?: string
    thumbnailUrl?: string
    visibility: "public" | "unlisted" | "private"
    scheduledPublishAt?: string
    publishedAt?: string
    viewCount: number
    likeCount: number
    commentCount: number
    status: "draft" | "uploading" | "processing" | "published" | "scheduled" | "failed" | "in_library" | "uploaded"
    uploadProgress?: number
    filePath?: string  // Local file path for Video-to-Live streaming
    fileSize?: number
    duration?: number  // Duration in seconds
    format?: string  // Video format (mp4, mov, etc)
    resolution?: string  // Video resolution (1080p, 720p, etc)
    // Library-specific fields
    folderId?: string | null
    isFavorite?: boolean
    customTags?: string[]
    notes?: string
    isUsedForStreaming?: boolean
    streamingCount?: number
    totalStreamingDuration?: number  // Total streaming duration in seconds
    createdAt?: string
    updatedAt?: string
}

export interface LiveEvent {
    id: string
    accountId: string
    youtubeBroadcastId: string
    youtubeStreamId: string
    title: string
    description: string
    thumbnailUrl: string
    scheduledStartAt?: string
    scheduledEndAt?: string
    actualStartAt?: string
    actualEndAt?: string
    latencyMode: "normal" | "low" | "ultraLow"
    enableDvr: boolean
    isRecurring: boolean
    status: "created" | "scheduled" | "live" | "ended" | "failed"
}

export interface ApiError {
    message: string
    code: string
    status?: number
    details?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    pageSize: number
    totalPages: number
}
