import { ApiError } from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

// Retry configuration
const DEFAULT_RETRY_CONFIG = {
    maxRetries: 3,
    retryDelay: 1000, // Base delay in ms
    retryableStatuses: [408, 429, 500, 502, 503, 504],
    retryableMethods: ["GET", "HEAD", "OPTIONS", "PUT", "DELETE"],
}

// Request interceptor type
type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>

// Response interceptor type
type ResponseInterceptor = (response: Response, config: RequestConfig) => Response | Promise<Response>

// Error interceptor type
type ErrorInterceptor = (error: ApiError, config: RequestConfig) => ApiError | Promise<ApiError>

// Global error handler type
type GlobalErrorHandler = (error: ApiError, config: RequestConfig) => void

interface RequestConfig extends RequestInit {
    params?: Record<string, string | number | boolean | undefined>
    includeUserId?: boolean
    skipRetry?: boolean
    retryCount?: number
    url?: string
}

interface RetryConfig {
    maxRetries: number
    retryDelay: number
    retryableStatuses: number[]
    retryableMethods: string[]
}

// Loading state management
type LoadingStateListener = (isLoading: boolean, endpoint: string) => void

class ApiClient {
    private baseUrl: string
    private accessToken: string | null = null
    private userId: string | null = null
    private retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG

    // Interceptors
    private requestInterceptors: RequestInterceptor[] = []
    private responseInterceptors: ResponseInterceptor[] = []
    private errorInterceptors: ErrorInterceptor[] = []

    // Global error handler
    private globalErrorHandler: GlobalErrorHandler | null = null

    // Loading state
    private activeRequests: Map<string, number> = new Map()
    private loadingListeners: Set<LoadingStateListener> = new Set()

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl
    }

    // Configuration methods
    setAccessToken(token: string | null) {
        this.accessToken = token
    }

    getAccessToken(): string | null {
        return this.accessToken
    }

    setUserId(userId: string | null) {
        this.userId = userId
        if (typeof window !== "undefined") {
            if (userId) {
                localStorage.setItem("user_id", userId)
            } else {
                localStorage.removeItem("user_id")
            }
        }
    }

    getUserId(): string | null {
        if (this.userId) return this.userId
        if (typeof window !== "undefined") {
            return localStorage.getItem("user_id")
        }
        return null
    }

    getBaseUrl(): string {
        return this.baseUrl
    }

    // Retry configuration
    setRetryConfig(config: Partial<RetryConfig>) {
        this.retryConfig = { ...this.retryConfig, ...config }
    }

    // Interceptor registration
    addRequestInterceptor(interceptor: RequestInterceptor): () => void {
        this.requestInterceptors.push(interceptor)
        return () => {
            const index = this.requestInterceptors.indexOf(interceptor)
            if (index > -1) this.requestInterceptors.splice(index, 1)
        }
    }

    addResponseInterceptor(interceptor: ResponseInterceptor): () => void {
        this.responseInterceptors.push(interceptor)
        return () => {
            const index = this.responseInterceptors.indexOf(interceptor)
            if (index > -1) this.responseInterceptors.splice(index, 1)
        }
    }

    addErrorInterceptor(interceptor: ErrorInterceptor): () => void {
        this.errorInterceptors.push(interceptor)
        return () => {
            const index = this.errorInterceptors.indexOf(interceptor)
            if (index > -1) this.errorInterceptors.splice(index, 1)
        }
    }

    // Global error handler
    setGlobalErrorHandler(handler: GlobalErrorHandler | null) {
        this.globalErrorHandler = handler
    }

    // Loading state management
    addLoadingListener(listener: LoadingStateListener): () => void {
        this.loadingListeners.add(listener)
        return () => this.loadingListeners.delete(listener)
    }

    private notifyLoadingState(endpoint: string, isLoading: boolean) {
        this.loadingListeners.forEach(listener => listener(isLoading, endpoint))
    }

    private incrementActiveRequests(endpoint: string) {
        const count = this.activeRequests.get(endpoint) || 0
        this.activeRequests.set(endpoint, count + 1)
        if (count === 0) {
            this.notifyLoadingState(endpoint, true)
        }
    }

    private decrementActiveRequests(endpoint: string) {
        const count = this.activeRequests.get(endpoint) || 0
        if (count <= 1) {
            this.activeRequests.delete(endpoint)
            this.notifyLoadingState(endpoint, false)
        } else {
            this.activeRequests.set(endpoint, count - 1)
        }
    }

    isLoading(endpoint?: string): boolean {
        if (endpoint) {
            return (this.activeRequests.get(endpoint) || 0) > 0
        }
        return this.activeRequests.size > 0
    }

    // URL building
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

    // Response handling
    private async handleResponse<T>(response: Response, config: RequestConfig): Promise<T> {
        // Run response interceptors
        let processedResponse = response
        for (const interceptor of this.responseInterceptors) {
            processedResponse = await interceptor(processedResponse, config)
        }

        if (!processedResponse.ok) {
            let error: ApiError
            try {
                error = await processedResponse.json()
            } catch {
                error = {
                    message: processedResponse.statusText || "An error occurred",
                    code: `HTTP_${processedResponse.status}`,
                    status: processedResponse.status,
                }
            }

            // Add status to error if not present
            if (!error.status) {
                error.status = processedResponse.status
            }

            // Run error interceptors
            let processedError = error
            for (const interceptor of this.errorInterceptors) {
                processedError = await interceptor(processedError, config)
            }

            // Call global error handler
            if (this.globalErrorHandler) {
                this.globalErrorHandler(processedError, config)
            }

            throw processedError
        }

        if (processedResponse.status === 204) {
            return undefined as T
        }

        return processedResponse.json()
    }

    // Retry logic with exponential backoff
    private async executeWithRetry<T>(
        endpoint: string,
        config: RequestConfig,
        attempt: number = 0
    ): Promise<T> {
        const url = this.buildUrl(endpoint, config.params)
        config.url = url

        try {
            const response = await fetch(url, config)
            return await this.handleResponse<T>(response, config)
        } catch (error) {
            const apiError = error as ApiError
            const method = config.method || "GET"

            // Check if we should retry
            const shouldRetry =
                !config.skipRetry &&
                attempt < this.retryConfig.maxRetries &&
                this.retryConfig.retryableMethods.includes(method.toUpperCase()) &&
                apiError.status !== undefined &&
                this.retryConfig.retryableStatuses.includes(apiError.status)

            if (shouldRetry) {
                // Exponential backoff with jitter
                const delay = this.retryConfig.retryDelay * Math.pow(2, attempt) + Math.random() * 100
                await new Promise(resolve => setTimeout(resolve, delay))
                return this.executeWithRetry<T>(endpoint, { ...config, retryCount: attempt + 1 }, attempt + 1)
            }

            throw error
        }
    }

    // Main request method
    async request<T>(endpoint: string, options: RequestConfig = {}): Promise<T> {
        const { params, includeUserId, skipRetry, ...fetchOptions } = options

        // Build headers
        const headers: HeadersInit = {
            "Content-Type": "application/json",
            ...options.headers,
        }

        if (this.accessToken) {
            (headers as Record<string, string>)["Authorization"] = `Bearer ${this.accessToken}`
        }

        // Add X-User-ID header if requested
        if (includeUserId !== false) {
            const userId = this.getUserId()
            if (userId) {
                (headers as Record<string, string>)["X-User-ID"] = userId
            }
        }

        let config: RequestConfig = {
            ...fetchOptions,
            headers,
            params,
            skipRetry,
        }

        // Run request interceptors
        for (const interceptor of this.requestInterceptors) {
            config = await interceptor(config)
        }

        // Track loading state
        this.incrementActiveRequests(endpoint)

        try {
            return await this.executeWithRetry<T>(endpoint, config)
        } finally {
            this.decrementActiveRequests(endpoint)
        }
    }

    // HTTP method shortcuts
    async get<T>(
        endpoint: string,
        options?: Record<string, string | number | boolean | undefined> | {
            params?: Record<string, string | number | boolean | undefined>
            includeUserId?: boolean
            skipRetry?: boolean
        }
    ): Promise<T> {
        if (options && ("params" in options || "includeUserId" in options || "skipRetry" in options)) {
            const { params, includeUserId, skipRetry } = options as {
                params?: Record<string, string | number | boolean | undefined>
                includeUserId?: boolean
                skipRetry?: boolean
            }
            return this.request<T>(endpoint, { method: "GET", params, includeUserId, skipRetry })
        }
        return this.request<T>(endpoint, {
            method: "GET",
            params: options as Record<string, string | number | boolean | undefined>
        })
    }

    async post<T>(
        endpoint: string,
        data?: unknown,
        options?: { includeUserId?: boolean; skipRetry?: boolean }
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: "POST",
            body: data ? JSON.stringify(data) : undefined,
            ...options,
        })
    }

    async put<T>(
        endpoint: string,
        data?: unknown,
        options?: { skipRetry?: boolean }
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: "PUT",
            body: data ? JSON.stringify(data) : undefined,
            ...options,
        })
    }

    async patch<T>(
        endpoint: string,
        data?: unknown,
        options?: { skipRetry?: boolean }
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: "PATCH",
            body: data ? JSON.stringify(data) : undefined,
            ...options,
        })
    }

    async delete<T>(
        endpoint: string,
        options?: { skipRetry?: boolean }
    ): Promise<T> {
        return this.request<T>(endpoint, { method: "DELETE", ...options })
    }
}

export const apiClient = new ApiClient(API_BASE_URL)
export default apiClient

// Export types for external use
export type { RequestConfig, RetryConfig, RequestInterceptor, ResponseInterceptor, ErrorInterceptor, GlobalErrorHandler, LoadingStateListener }
