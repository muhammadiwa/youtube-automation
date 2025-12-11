"use client"

import { useState, useEffect, useCallback } from "react"
import apiClient from "@/lib/api/client"

/**
 * Hook to track loading state for specific API endpoints
 * @param endpoints - Optional array of endpoints to track. If not provided, tracks all requests.
 */
export function useApiLoading(endpoints?: string[]) {
    const [isLoading, setIsLoading] = useState(false)
    const [loadingEndpoints, setLoadingEndpoints] = useState<Set<string>>(new Set())

    useEffect(() => {
        const handleLoadingChange = (loading: boolean, endpoint: string) => {
            // If specific endpoints are provided, only track those
            if (endpoints && !endpoints.some(e => endpoint.includes(e))) {
                return
            }

            setLoadingEndpoints(prev => {
                const next = new Set(prev)
                if (loading) {
                    next.add(endpoint)
                } else {
                    next.delete(endpoint)
                }
                return next
            })
        }

        const unsubscribe = apiClient.addLoadingListener(handleLoadingChange)
        return unsubscribe
    }, [endpoints])

    useEffect(() => {
        setIsLoading(loadingEndpoints.size > 0)
    }, [loadingEndpoints])

    return {
        isLoading,
        loadingEndpoints: Array.from(loadingEndpoints),
        isEndpointLoading: useCallback(
            (endpoint: string) => loadingEndpoints.has(endpoint),
            [loadingEndpoints]
        ),
    }
}

export default useApiLoading
