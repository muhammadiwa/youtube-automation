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
    // Analytics endpoints - handled gracefully with fallback data
    "/analytics/overview",
    "/analytics/ai-insights",
    "/analytics/insights",
    "/analytics/views/timeseries",
    "/analytics/subscribers/timeseries",
    "/analytics/reports",
    "/analytics/revenue/top-videos",
    // Moderation endpoints - handled gracefully with empty arrays
    "/moderation/rules",
    "/moderation/comments",
    "/moderation/auto-reply",
    "/moderation/commands",
    "/moderation/chatbot",
    "/moderation/logs",
    // Monitoring endpoints - handled gracefully with empty arrays
    "/monitoring/channels",
    "/monitoring/preferences",
    // Stream job endpoints - handled gracefully with fallback data
    "/stream-jobs/history",
    "/stream-jobs/analytics",
    "/stream-jobs/export",
    // Notifications endpoints - handled gracefully
    "/notifications",
    // Account OAuth endpoints - 401 here means YouTube token expired, not app session
    "/accounts/", // Covers /accounts/{id}/refresh-token, /accounts/{id}/sync, etc.
    // Billing endpoints - handled gracefully with fallback data
    "/billing/subscriptions",
    "/billing/plans",
    "/billing/usage",
    "/billing/invoices",
    "/billing/payment-methods",
    "/billing/dashboard",
    "/payments/gateways",
    "/payments/history",
]

// Endpoints where 401 should NOT trigger logout (YouTube OAuth errors)
const NO_LOGOUT_ON_401_ENDPOINTS = [
    "/accounts/", // YouTube account operations - 401 means YouTube token expired
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
                // Check if this is a YouTube OAuth error (not app session expired)
                const isYouTubeOAuthError = NO_LOGOUT_ON_401_ENDPOINTS.some(endpoint =>
                    config.url?.includes(endpoint)
                )

                if (isYouTubeOAuthError) {
                    // Don't logout - this is a YouTube token error, not app session
                    // Show a more helpful message
                    addToast({
                        type: "error",
                        title: "YouTube Token Expired",
                        description: "Please reconnect your YouTube account to continue.",
                    })
                    return
                }

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

        // Set up response interceptor (no logging in production)
        const removeResponseInterceptor = apiClient.addResponseInterceptor((response) => {
            return response
        })

        // Set up error interceptor for additional processing
        const removeErrorInterceptor = apiClient.addErrorInterceptor((error) => {
            return error
        })

        return () => {
            apiClient.setGlobalErrorHandler(null)
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
