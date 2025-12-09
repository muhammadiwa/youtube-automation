import { ApiError } from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

interface RequestOptions extends RequestInit {
    params?: Record<string, string | number | boolean | undefined>
}

class ApiClient {
    private baseUrl: string
    private accessToken: string | null = null

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl
    }

    setAccessToken(token: string | null) {
        this.accessToken = token
    }

    getAccessToken(): string | null {
        return this.accessToken
    }

    private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
        const url = new URL(`${this.baseUrl}${endpoint}`)
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined) {
                    url.searchParams.append(key, String(value))
                }
            })
        }
        return url.toString()
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error: ApiError = await response.json().catch(() => ({
                message: response.statusText,
                code: `HTTP_${response.status}`,
            }))
            throw error
        }

        if (response.status === 204) {
            return undefined as T
        }

        return response.json()
    }

    async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { params, ...fetchOptions } = options
        const url = this.buildUrl(endpoint, params)

        const headers: HeadersInit = {
            "Content-Type": "application/json",
            ...options.headers,
        }

        if (this.accessToken) {
            (headers as Record<string, string>)["Authorization"] = `Bearer ${this.accessToken}`
        }

        const response = await fetch(url, {
            ...fetchOptions,
            headers,
        })

        return this.handleResponse<T>(response)
    }

    async get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
        return this.request<T>(endpoint, { method: "GET", params })
    }

    async post<T>(endpoint: string, data?: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: "POST",
            body: data ? JSON.stringify(data) : undefined,
        })
    }

    async put<T>(endpoint: string, data?: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: "PUT",
            body: data ? JSON.stringify(data) : undefined,
        })
    }

    async patch<T>(endpoint: string, data?: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: "PATCH",
            body: data ? JSON.stringify(data) : undefined,
        })
    }

    async delete<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: "DELETE" })
    }
}

export const apiClient = new ApiClient(API_BASE_URL)
export default apiClient
