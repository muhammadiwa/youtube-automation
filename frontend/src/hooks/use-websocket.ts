"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import wsClient, { WebSocketStatus, WebSocketMessage } from "@/lib/websocket/client"
import { useAuth } from "@/hooks/use-auth"
import apiClient from "@/lib/api/client"

/**
 * Hook to manage WebSocket connection and status
 */
export function useWebSocket() {
    const { isAuthenticated } = useAuth()
    const [status, setStatus] = useState<WebSocketStatus>("disconnected")
    const [isConnected, setIsConnected] = useState(false)

    useEffect(() => {
        // Subscribe to status changes
        const unsubscribe = wsClient.onStatusChange((newStatus) => {
            setStatus(newStatus)
            setIsConnected(newStatus === "connected")
        })

        return unsubscribe
    }, [])

    useEffect(() => {
        // Connect when authenticated
        if (isAuthenticated) {
            const token = apiClient.getAccessToken()
            wsClient.setAuthToken(token)
            wsClient.connect()
        } else {
            wsClient.disconnect()
        }

        return () => {
            // Don't disconnect on unmount if still authenticated
            // This allows the connection to persist across page navigations
        }
    }, [isAuthenticated])

    const connect = useCallback(() => {
        const token = apiClient.getAccessToken()
        wsClient.setAuthToken(token)
        wsClient.connect()
    }, [])

    const disconnect = useCallback(() => {
        wsClient.disconnect()
    }, [])

    const send = useCallback(<T>(type: string, payload: T) => {
        return wsClient.send(type, payload)
    }, [])

    return {
        status,
        isConnected,
        connect,
        disconnect,
        send,
    }
}

/**
 * Hook to subscribe to specific WebSocket message types
 */
export function useWebSocketSubscription<T = unknown>(
    type: string,
    handler: (message: WebSocketMessage<T>) => void,
    deps: React.DependencyList = []
) {
    const handlerRef = useRef(handler)
    handlerRef.current = handler

    useEffect(() => {
        const unsubscribe = wsClient.subscribe<T>(type, (message) => {
            handlerRef.current(message)
        })

        return unsubscribe
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [type, ...deps])
}

/**
 * Hook to subscribe to all WebSocket messages
 */
export function useWebSocketMessages(
    handler: (message: WebSocketMessage) => void,
    deps: React.DependencyList = []
) {
    const handlerRef = useRef(handler)
    handlerRef.current = handler

    useEffect(() => {
        const unsubscribe = wsClient.subscribeAll((message) => {
            handlerRef.current(message)
        })

        return unsubscribe
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, deps)
}

export default useWebSocket
