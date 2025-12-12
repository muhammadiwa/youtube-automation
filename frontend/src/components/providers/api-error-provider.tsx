"use client"

import React, { createContext, useContext, useEffect, useCallback, useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/components/ui/toast"
import apiClient from "@/lib/api/client"
import type { ApiError } from "@/types"

interface ApiErrorContextType {
    lastError: ApiError | null
    clearError: () => void
}

const ApiErrorContext = createContext<ApiErrorContextType | undefined>(undefined)

// Error messages for common HTTP status codes
const ERROR_MESSAGES: Record<number, string> = {
    400: "Invalid request. Please check your input.",
    401: "Your session has expired. Please log in again.",
    403: "You don't have permission to perform this action.",
    404: "The requested resource was not found.",
    408: "Request timed out. Please try again.",
    409: "A conflict occurred. The resource may have been modified.",
    422: "Validation error. Please check your input.",
    429: "Too many requests. Please wait a moment and try again.",
    500: "An internal server error occurred. Please try again later.",
    502: "Service temporarily unavailable. Please try again later.",
    503: "Service temporarily unavailable. Please try again later.",
    504: "Request timed out. Please try again later.",
}

// Endpoints that should not show toast notifications
const SILENT_ENDPOINTS = [
    "/auth/me", // Don't show error when checking auth status
    "/auth/refresh", // Don't show error when refreshing token
    "/admin/me", // Don't show error when checking admin status (may not be admin)
    "/strikes/alerts", // Don't show error for strike alerts (handled gracefully in component)
    "/strikes/summaries", // Don't show error for strike summaries
]

export function ApiErrorProvider({ children }: { children: React.ReactNode }) {
    const router = useRouter()
    const { addToast } = useToast()
    const [lastError, setLastError] = useState<ApiError | null>(null)

    const clearError = useCallback(() => {
        setLastError(null)
    }, [])

    useEffect(() => {
        // Set up global error handler
        const handleGlobalError = (error: ApiError, config: { url?: string }) => {
            setLastError(error)

            // Check if this endpoint should be silent
            const isSilent = SILENT_ENDPOINTS.some(endpoint =>
                config.url?.includes(endpoint)
            )

            if (isSilent) {
                return
            }

            // Handle authentication errors
            if (error.status === 401) {
                // Clear tokens and redirect to login
                localStorage.removeItem("auth_access_token")
                localStorage.removeItem("auth_refresh_token")
                localStorage.removeItem("user_id")
                apiClient.setAccessToken(null)
                apiClient.setUserId(null)

                addToast({
                    type: "error",
                    title: "Session Expired",
                    description: "Please log in again to continue.",
                })

                router.push("/login")
                return
            }

            // Get appropriate error message
            const message = error.message ||
                (error.status ? ERROR_MESSAGES[error.status] : null) ||
                "An unexpected error occurred."

            // Show toast notification
            addToast({
                type: "error",
                title: "Error",
                description: message,
            })
        }

        apiClient.setGlobalErrorHandler(handleGlobalError)

        // Set up request interceptor for logging
        const removeRequestInterceptor = apiClient.addRequestInterceptor((config) => {
            // Add request timestamp for debugging
            if (process.env.NODE_ENV === "development") {
                console.log(`[API Request] ${config.method || "GET"} ${config.url}`)
            }
            return config
        })

        // Set up response interceptor for logging
        const removeResponseInterceptor = apiClient.addResponseInterceptor((response, config) => {
            if (process.env.NODE_ENV === "development") {
                console.log(`[API Response] ${config.method || "GET"} ${config.url} - ${response.status}`)
            }
            return response
        })

        // Set up error interceptor for additional processing
        const removeErrorInterceptor = apiClient.addErrorInterceptor((error, config) => {
            if (process.env.NODE_ENV === "development") {
                console.error(`[API Error] ${config.method || "GET"} ${config.url}`, error)
            }
            return error
        })

        return () => {
            apiClient.setGlobalErrorHandler(null)
            removeRequestInterceptor()
            removeResponseInterceptor()
            removeErrorInterceptor()
        }
    }, [router, addToast])

    return (
        <ApiErrorContext.Provider value={{ lastError, clearError }}>
            {children}
        </ApiErrorContext.Provider>
    )
}

export function useApiError() {
    const context = useContext(ApiErrorContext)
    if (context === undefined) {
        throw new Error("useApiError must be used within an ApiErrorProvider")
    }
    return context
}

export default ApiErrorProvider
