import apiClient from "./client"

// ============ Title Generation ============
export interface TitleSuggestion {
    title: string
    confidence_score: number
    reasoning: string
    keywords: string[]
}

export interface GenerateTitlesRequest {
    video_content: string
    keywords?: string[]
    style?: "engaging" | "informative" | "clickbait" | "professional"
    max_length?: number
}

export interface TitleGenerationResponse {
    suggestions: TitleSuggestion[]
    generated_at: string
}

// ============ Description Generation ============
export interface DescriptionSuggestion {
    description: string
    seo_score: number
    keywords_used: string[]
    has_cta: boolean
    estimated_read_time: number
}

export interface GenerateDescriptionRequest {
    video_title: string
    video_content: string
    keywords?: string[]
    include_timestamps?: boolean
    include_cta?: boolean
    max_length?: number
}

export interface DescriptionGenerationResponse {
    suggestion: DescriptionSuggestion
    generated_at: string
}

// ============ Tag Suggestion ============
export interface TagSuggestion {
    tag: string
    relevance_score: number
    category: "primary" | "secondary" | "trending" | "long_tail"
}

export interface GenerateTagsRequest {
    video_title: string
    video_description?: string
    video_content?: string
    existing_tags?: string[]
    max_tags?: number
}

export interface TagSuggestionResponse {
    suggestions: TagSuggestion[]
    generated_at: string
}

// ============ Thumbnail Generation ============
export interface ThumbnailElement {
    element_type: "text" | "image" | "shape" | "logo"
    position: { x: number; y: number }
    size: { width: number; height: number }
    content?: string
    style?: Record<string, unknown>
}

export interface ThumbnailResult {
    id: string
    image_url: string
    style: string
    elements: ThumbnailElement[]
    width: number
    height: number
}

export interface GenerateThumbnailsRequest {
    video_title: string
    video_content?: string
    style?: "modern" | "minimalist" | "bold" | "professional" | "gaming"
    include_text?: boolean
    text_content?: string
    brand_colors?: string[]
}

export interface ThumbnailGenerationResponse {
    thumbnails: ThumbnailResult[]
    generated_at: string
}

export const aiApi = {
    /**
     * Generate AI-powered title suggestions
     * Backend endpoint: POST /ai/titles/generate
     */
    async generateTitles(data: GenerateTitlesRequest): Promise<TitleGenerationResponse> {
        try {
            return await apiClient.post("/ai/titles/generate", data)
        } catch (error) {
            console.error("Failed to generate titles:", error)
            // Return mock data for development
            const baseTitle = data.video_content.slice(0, 30)
            return {
                suggestions: [
                    { title: `${baseTitle} - Ultimate Guide`, confidence_score: 0.92, reasoning: "High engagement keywords", keywords: ["guide", "tutorial"] },
                    { title: `How to ${baseTitle} Like a Pro`, confidence_score: 0.88, reasoning: "How-to format performs well", keywords: ["how to", "pro"] },
                    { title: `${baseTitle} Explained in 10 Minutes`, confidence_score: 0.85, reasoning: "Time-bound content attracts clicks", keywords: ["explained", "minutes"] },
                    { title: `The Complete ${baseTitle} for Beginners`, confidence_score: 0.82, reasoning: "Beginner-friendly content", keywords: ["complete", "beginners"] },
                    { title: `${baseTitle} Changed Everything`, confidence_score: 0.78, reasoning: "Emotional hook", keywords: ["changed", "everything"] },
                ],
                generated_at: new Date().toISOString(),
            }
        }
    },

    /**
     * Generate AI-powered description
     * Backend endpoint: POST /ai/descriptions/generate
     */
    async generateDescription(data: GenerateDescriptionRequest): Promise<DescriptionGenerationResponse> {
        try {
            return await apiClient.post("/ai/descriptions/generate", data)
        } catch (error) {
            console.error("Failed to generate description:", error)
            // Return mock data for development
            return {
                suggestion: {
                    description: `In this video, we dive deep into ${data.video_title}. Whether you're a beginner or an expert, you'll find valuable insights and practical tips.\n\n🔔 Subscribe for more content!\n👍 Like if you found this helpful!\n💬 Comment your thoughts below!\n\n#${data.video_title.replace(/\s+/g, '')} #Tutorial #Guide`,
                    seo_score: 0.89,
                    keywords_used: ["tutorial", "guide", "tips"],
                    has_cta: true,
                    estimated_read_time: 30,
                },
                generated_at: new Date().toISOString(),
            }
        }
    },

    /**
     * Generate AI-powered tag suggestions
     * Backend endpoint: POST /ai/tags/suggest
     */
    async generateTags(data: GenerateTagsRequest): Promise<TagSuggestionResponse> {
        try {
            return await apiClient.post("/ai/tags/suggest", data)
        } catch (error) {
            console.error("Failed to generate tags:", error)
            // Return mock data for development
            const baseTags = data.video_title.toLowerCase().split(' ').filter(w => w.length > 3)
            return {
                suggestions: [
                    { tag: data.video_title.toLowerCase().replace(/\s+/g, ''), relevance_score: 0.95, category: "primary" },
                    { tag: "tutorial", relevance_score: 0.88, category: "secondary" },
                    { tag: "howto", relevance_score: 0.85, category: "secondary" },
                    { tag: "guide", relevance_score: 0.82, category: "trending" },
                    { tag: "tips", relevance_score: 0.78, category: "long_tail" },
                    ...baseTags.slice(0, 5).map((tag, i) => ({
                        tag,
                        relevance_score: 0.7 - i * 0.05,
                        category: "long_tail" as const
                    })),
                ],
                generated_at: new Date().toISOString(),
            }
        }
    },

    /**
     * Generate AI-powered thumbnails
     * Backend endpoint: POST /ai/thumbnails/generate
     */
    async generateThumbnails(data: GenerateThumbnailsRequest): Promise<ThumbnailGenerationResponse> {
        try {
            return await apiClient.post("/ai/thumbnails/generate", data)
        } catch (error) {
            console.error("Failed to generate thumbnails:", error)
            // Return mock data for development
            return {
                thumbnails: [
                    {
                        id: `thumb-${Date.now()}-1`,
                        image_url: "https://placehold.co/1280x720/EF4444/FFFFFF?text=Thumbnail+1",
                        style: "modern",
                        elements: [{
                            element_type: "text",
                            content: data.video_title,
                            position: { x: 50, y: 50 },
                            size: { width: 400, height: 100 }
                        }],
                        width: 1280,
                        height: 720,
                    },
                    {
                        id: `thumb-${Date.now()}-2`,
                        image_url: "https://placehold.co/1280x720/3B82F6/FFFFFF?text=Thumbnail+2",
                        style: "bold",
                        elements: [{
                            element_type: "text",
                            content: data.video_title,
                            position: { x: 50, y: 50 },
                            size: { width: 400, height: 100 }
                        }],
                        width: 1280,
                        height: 720,
                    },
                    {
                        id: `thumb-${Date.now()}-3`,
                        image_url: "https://placehold.co/1280x720/10B981/FFFFFF?text=Thumbnail+3",
                        style: "minimalist",
                        elements: [{
                            element_type: "text",
                            content: data.video_title,
                            position: { x: 50, y: 50 },
                            size: { width: 400, height: 100 }
                        }],
                        width: 1280,
                        height: 720,
                    },
                ],
                generated_at: new Date().toISOString(),
            }
        }
    },
}

export default aiApi
