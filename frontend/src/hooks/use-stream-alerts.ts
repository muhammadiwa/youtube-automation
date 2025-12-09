"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { streamsApi, type StreamAlert, type StreamHealth } from "@/lib/api/streams"

interface UseStreamAlertsOptions {
    eventId: string
    enabled?: boolean
    pollInterval?: number
    onNewAlert?: (alert: StreamAlert) => void
    soundEnabled?: boolean
}

interface UseStreamAlertsReturn {
    alerts: StreamAlert[]
    health: StreamHealth | null
    loading: boolean
    error: Error | null
    acknowledgeAlert: (alertId: string) => Promise<void>
    refresh: () => Promise<void>
}

export function useStreamAlerts({
    eventId,
    enabled = true,
    pollInterval = 10000,
    onNewAlert,
    soundEnabled = false,
}: UseStreamAlertsOptions): UseStreamAlertsReturn {
    const [alerts, setAlerts] = useState<StreamAlert[]>([])
    const [health, setHealth] = useState<StreamHealth | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const previousAlertIds = useRef<Set<string>>(new Set())
    const audioRef = useRef<HTMLAudioElement | null>(null)

    // Initialize audio element
    useEffect(() => {
        if (typeof window !== "undefined") {
            audioRef.current = new Audio("/sounds/alert.mp3")
        }
    }, [])

    const fetchData = useCallback(async () => {
        if (!enabled) return

        try {
            const [healthData, alertsData] = await Promise.all([
                streamsApi.getHealth(eventId),
                streamsApi.getAlerts(eventId),
            ])

            setHealth(healthData)

            // Check for new alerts
            const newAlerts = alertsData.filter(
                (alert) => !previousAlertIds.current.has(alert.id)
            )

            if (newAlerts.length > 0) {
                // Play sound for new alerts
                if (soundEnabled && audioRef.current) {
                    audioRef.current.play().catch(() => { })
                }

                // Notify about new alerts
                newAlerts.forEach((alert) => {
                    onNewAlert?.(alert)
                    previousAlertIds.current.add(alert.id)
                })
            }

            setAlerts(alertsData)
            setError(null)
        } catch (err) {
            setError(err instanceof Error ? err : new Error("Failed to fetch alerts"))
        } finally {
            setLoading(false)
        }
    }, [eventId, enabled, soundEnabled, onNewAlert])

    // Initial fetch
    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Polling
    useEffect(() => {
        if (!enabled || pollInterval <= 0) return

        const interval = setInterval(fetchData, pollInterval)
        return () => clearInterval(interval)
    }, [enabled, pollInterval, fetchData])

    const acknowledgeAlert = useCallback(
        async (alertId: string) => {
            try {
                await streamsApi.acknowledgeAlert(eventId, alertId)
                setAlerts((prev) =>
                    prev.map((a) =>
                        a.id === alertId ? { ...a, acknowledged: true } : a
                    )
                )
            } catch (err) {
                console.error("Failed to acknowledge alert:", err)
                throw err
            }
        },
        [eventId]
    )

    return {
        alerts,
        health,
        loading,
        error,
        acknowledgeAlert,
        refresh: fetchData,
    }
}

// Helper function to get alert severity color
export function getAlertSeverityColor(severity: StreamAlert["severity"]): string {
    switch (severity) {
        case "error":
            return "text-red-500"
        case "warning":
            return "text-yellow-500"
        default:
            return "text-blue-500"
    }
}

// Helper function to get alert type label
export function getAlertTypeLabel(type: StreamAlert["type"]): string {
    switch (type) {
        case "health_warning":
            return "Health Warning"
        case "health_critical":
            return "Critical Health"
        case "reconnection":
            return "Reconnection"
        case "failover":
            return "Failover"
        case "disconnection":
            return "Disconnection"
        default:
            return "Alert"
    }
}
