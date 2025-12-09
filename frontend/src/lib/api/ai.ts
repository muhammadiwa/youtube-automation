import apiClient from "./client"

export interface TitleSuggestion {
    title: string
    confidenceScore: number
    reasoning: string
    keywords: string[]
}

export interface DescriptionSuggestion {
    description: string
    confidenceScore: number
    reasoning: string
}

export interface TagSuggestion {
    tag: string
    relevance: number
    category: string
}

export interface ThumbnailResult {
    id: string
    imageUrl: string
    style: string
}

export interface GenerateTitlesRequest {
    videoTitle?: string
    videoDescription?: string
    targetAudience?: string
    keywords?: string[]
}

export interface GenerateDescriptionRequest {
    videoTitle: string
    videoContent?: string
    keywords?: string[]
    includeHashtags?: boolean
}

export interface GenerateTagsRequest {
    videoTitle: string
    videoDescription?: string
    category?: string
}

export interface GenerateThumbnailsRequest {
    videoId: string
    style?: "modern" | "classic" | "bold" | "minimal"
    includeText?: boolean
    text?: string
}

export const aiApi = {
    /**
     * Generate AI-powered title suggestions
     */
    async generateTitles(data: GenerateTitlesRequest): Promise<TitleSuggestion[]> {
        return apiClient.post("/ai/generate-titles", data)
    },

    /**
     * Generate AI-powered description
     */
    async generateDescription(data: GenerateDescriptionRequest): Promise<DescriptionSuggestion> {
        return apiClient.post("/ai/generate-description", data)
    },

    /**
     * Generate AI-powered tag suggestions
     */
    async generateTags(data: GenerateTagsRequest): Promise<TagSuggestion[]> {
        return apiClient.post("/ai/generate-tags", data)
    },

    /**
     * Generate AI-powered thumbnails
     */
    async generateThumbnails(data: GenerateThumbnailsRequest): Promise<ThumbnailResult[]> {
        return apiClient.post("/ai/generate-thumbnails", data)
    },
}

export default aiApi
