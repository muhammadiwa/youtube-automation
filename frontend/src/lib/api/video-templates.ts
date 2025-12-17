import apiClient from "./client"

export interface VideoTemplate {
    id: string
    userId?: string
    user_id?: string
    name: string
    description?: string
    titleTemplate?: string
    title_template?: string
    descriptionTemplate?: string
    description_template?: string
    tags?: string[]
    categoryId?: string
    category_id?: string
    visibility?: "public" | "unlisted" | "private"
    isDefault?: boolean
    is_default?: boolean
    createdAt?: string
    created_at?: string
    updatedAt?: string
    updated_at?: string
}

export interface CreateTemplateData {
    name: string
    description?: string
    titleTemplate?: string
    descriptionTemplate?: string
    tags?: string[]
    categoryId?: string
    visibility?: "public" | "unlisted" | "private"
    isDefault?: boolean
}

export interface UpdateTemplateData extends Partial<CreateTemplateData> { }

// Helper to normalize template from backend snake_case to frontend camelCase
function normalizeTemplate(t: any): VideoTemplate {
    return {
        id: t.id,
        userId: t.user_id || t.userId,
        name: t.name,
        description: t.description,
        titleTemplate: t.title_template || t.titleTemplate,
        descriptionTemplate: t.description_template || t.descriptionTemplate,
        tags: t.tags,
        categoryId: t.category_id || t.categoryId,
        visibility: t.visibility,
        isDefault: t.is_default || t.isDefault || false,
        createdAt: t.created_at || t.createdAt,
        updatedAt: t.updated_at || t.updatedAt,
    }
}

export const videoTemplatesApi = {
    /**
     * Get all templates for current user
     */
    async getTemplates(): Promise<VideoTemplate[]> {
        try {
            const response = await apiClient.get<VideoTemplate[] | { templates: VideoTemplate[] }>("/videos/templates")
            let templates: any[] = []
            if (Array.isArray(response)) {
                templates = response
            } else if (response && typeof response === "object" && "templates" in response) {
                templates = response.templates
            }
            return templates.map(normalizeTemplate)
        } catch (error) {
            console.error("Failed to fetch templates:", error)
            return []
        }
    },

    /**
     * Get single template by ID
     */
    async getTemplate(templateId: string): Promise<VideoTemplate> {
        const response = await apiClient.get(`/videos/templates/${templateId}`)
        return normalizeTemplate(response)
    },

    /**
     * Create new template
     */
    async createTemplate(data: CreateTemplateData): Promise<VideoTemplate> {
        // Map to backend field names
        const backendData = {
            name: data.name,
            description: data.description,
            title_template: data.titleTemplate,
            description_template: data.descriptionTemplate,
            tags: data.tags,
            category_id: data.categoryId,
            visibility: data.visibility,
            is_default: data.isDefault,
        }
        return apiClient.post("/videos/templates", backendData)
    },

    /**
     * Update template
     */
    async updateTemplate(templateId: string, data: UpdateTemplateData): Promise<VideoTemplate> {
        const backendData: Record<string, unknown> = {}
        if (data.name !== undefined) backendData.name = data.name
        if (data.description !== undefined) backendData.description = data.description
        if (data.titleTemplate !== undefined) backendData.title_template = data.titleTemplate
        if (data.descriptionTemplate !== undefined) backendData.description_template = data.descriptionTemplate
        if (data.tags !== undefined) backendData.tags = data.tags
        if (data.categoryId !== undefined) backendData.category_id = data.categoryId
        if (data.visibility !== undefined) backendData.visibility = data.visibility
        if (data.isDefault !== undefined) backendData.is_default = data.isDefault

        const response = await apiClient.put(`/videos/templates/${templateId}`, backendData)
        return normalizeTemplate(response)
    },

    /**
     * Delete template
     */
    async deleteTemplate(templateId: string): Promise<void> {
        return apiClient.delete(`/videos/templates/${templateId}`)
    },

    /**
     * Apply template to video
     */
    async applyTemplate(videoId: string, templateId: string): Promise<void> {
        return apiClient.post(`/videos/${videoId}/apply-template`, { template_id: templateId })
    },

    /**
     * Get default template
     */
    async getDefaultTemplate(): Promise<VideoTemplate | null> {
        try {
            const templates = await this.getTemplates()
            return templates.find((t) => t.isDefault) || null
        } catch {
            return null
        }
    },
}

export default videoTemplatesApi
