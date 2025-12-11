"use client"

import { useState, useEffect, useCallback } from "react"
import { useWebSocketSubscription } from "./use-websocket"
import wsClient from "@/lib/websocket/client"

export interface StreamHealthData {
    sessionId: string
    eventId: string
    bitrate: number
    frameRate: number
    droppedFrames: number
    connectionStatus: "excellent" | "good" | "fair" | "poor"
    viewerCount: number
    chatRate: number
    uptime: number
    timestamp: string
}

export interface StreamHealthAlert {
    eventId: string
    alertType: "bitrate_low" | "frames_dropping" | "connection_poor" | "disconnected"
    severity: "warning" | "critical"
    message: string
    timestamp: string
}

/**
 * Hook for real-time stream health updates
 * Validates: Requirements 8.1 - Stream health metrics every 10 seconds
 */
export function useRealtimeStreamHealth(eventId: string | null) {
    const [health, setHealth] = useState<StreamHealthData | null>(null)
    const [alerts, setAlerts] = useState<StreamHealthAlert[]>([])
    const [isSubscribed, setIsSubscribed] = useState(false)

    // Subscribe to health updates for this stream
    useWebSocketSubscription<StreamHealthData>(
        "stream.health.update",
        (message) => {
            if (message.payload.eventId === eventId) {
                setHealth(message.payload)
            }
        },
        [eventId]
    )

    // Subscribe to health alerts
    useWebSocketSubscription<StreamHealthAlert>(
        "stream.health.alert",
        (message) => {
            if (message.payload.eventId === eventId) {
                setAlerts(prev => [...prev.slice(-9), message.payload]) // Keep last 10 alerts
            }
        },
        [eventId]
    )

    // Subscribe to this stream's health updates
    useEffect(() => {
        if (!eventId) {
            setIsSubscribed(false)
            return
        }

        // Send subscription request
        wsClient.send("stream.health.subscribe", { eventId })
        setIsSubscribed(true)

        return () => {
            // Unsubscribe when component unmounts or eventId changes
            wsClient.send("stream.health.unsubscribe", { eventId })
            setIsSubscribed(false)
        }
    }, [eventId])

    const clearAlerts = useCallback(() => {
        setAlerts([])
    }, [])

    return {
        health,
        alerts,
        isSubscribed,
        clearAlerts,
    }
}

/**
 * Hook for monitoring multiple streams' health
 */
export function useRealtimeMultiStreamHealth(eventIds: string[]) {
    const [healthMap, setHealthMap] = useState<Map<string, StreamHealthData>>(new Map())

    // Subscribe to health updates for all streams
    useWebSocketSubscription<StreamHealthData>(
        "stream.health.update",
        (message) => {
            if (eventIds.includes(message.payload.eventId)) {
                setHealthMap(prev => {
                    const next = new Map(prev)
                    next.set(message.payload.eventId, message.payload)
                    return next
                })
            }
        },
        [eventIds.join(",")]
    )

    // Subscribe to all streams
    useEffect(() => {
        if (eventIds.length === 0) return

        eventIds.forEach(eventId => {
            wsClient.send("stream.health.subscribe", { eventId })
        })

        return () => {
            eventIds.forEach(eventId => {
                wsClient.send("stream.health.unsubscribe", { eventId })
            })
        }
    }, [eventIds])

    return {
        healthMap,
        getHealth: (eventId: string) => healthMap.get(eventId) || null,
    }
}

export default useRealtimeStreamHealth
