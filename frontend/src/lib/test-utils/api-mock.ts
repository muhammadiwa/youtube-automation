/**
 * API Mock Utilities for Testing
 * 
 * These utilities help with testing API interactions without hitting the real backend.
 * Can be used for unit tests, integration tests, and development.
 */

import type { ApiError } from "@/types"

export interface MockResponse<T> {
    data?: T
    error?: ApiError
    delay?: number
    status?: number
}

export interface MockEndpoint {
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
    path: string | RegExp
    response: MockResponse<unknown> | ((params: Record<string, string>) => MockResponse<unknown>)
}

class ApiMocker {
    private mocks: MockEndpoint[] = []
    private originalFetch: typeof fetch | null = null
    private isActive = false

    /**
     * Add a mock endpoint
     */
    mock<T>(
        method: MockEndpoint["method"],
        path: string | RegExp,
        response: MockResponse<T> | ((params: Record<string, string>) => MockResponse<T>)
    ): () => void {
        const endpoint: MockEndpoint = { method, path, response }
        this.mocks.push(endpoint)

        return () => {
            const index = this.mocks.indexOf(endpoint)
            if (index > -1) this.mocks.splice(index, 1)
        }
    }

    /**
     * Start intercepting fetch requests
     */
    start(): void {
        if (this.isActive) return

        this.originalFetch = globalThis.fetch
        this.isActive = true

        globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
            const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url
            const method = init?.method?.toUpperCase() || "GET"

            // Find matching mock
            const mock = this.findMock(method, url)

            if (mock) {
                const params = this.extractParams(mock.path, url)
                const response = typeof mock.response === "function"
                    ? mock.response(params)
                    : mock.response

                // Simulate network delay
                if (response.delay) {
                    await new Promise(resolve => setTimeout(resolve, response.delay))
                }

                const status = response.error ? (response.error.status || 400) : (response.status || 200)
                const body = response.error || response.data

                return new Response(JSON.stringify(body), {
                    status,
                    headers: { "Content-Type": "application/json" },
                })
            }

            // Fall through to original fetch if no mock found
            if (this.originalFetch) {
                return this.originalFetch(input, init)
            }

            throw new Error(`No mock found for ${method} ${url}`)
        }
    }

    /**
     * Stop intercepting fetch requests
     */
    stop(): void {
        if (!this.isActive) return

        if (this.originalFetch) {
            globalThis.fetch = this.originalFetch
            this.originalFetch = null
        }
        this.isActive = false
    }

    /**
     * Clear all mocks
     */
    clear(): void {
        this.mocks = []
    }

    /**
     * Reset (stop and clear)
     */
    reset(): void {
        this.stop()
        this.clear()
    }

    private findMock(method: string, url: string): MockEndpoint | undefined {
        return this.mocks.find(mock => {
            if (mock.method !== method) return false

            if (typeof mock.path === "string") {
                return url.includes(mock.path)
            }

            return mock.path.test(url)
        })
    }

    private extractParams(path: string | RegExp, url: string): Record<string, string> {
        if (typeof path === "string") {
            return {}
        }

        const match = url.match(path)
        if (!match?.groups) return {}

        return match.groups
    }
}

export const apiMocker = new ApiMocker()
export default apiMocker

// Convenience functions for common mock scenarios
export const mockSuccess = <T>(data: T, delay = 0): MockResponse<T> => ({
    data,
    delay,
    status: 200,
})

export const mockError = (message: string, code: string, status = 400): MockResponse<never> => ({
    error: { message, code, status },
    status,
})

export const mock401 = (): MockResponse<never> => mockError(
    "Unauthorized",
    "UNAUTHORIZED",
    401
)

export const mock404 = (): MockResponse<never> => mockError(
    "Not found",
    "NOT_FOUND",
    404
)

export const mock500 = (): MockResponse<never> => mockError(
    "Internal server error",
    "INTERNAL_ERROR",
    500
)
