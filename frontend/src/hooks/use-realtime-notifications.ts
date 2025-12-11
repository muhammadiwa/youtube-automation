"use client"

import { useState, useEffect, useCallback } from "react"
import { useWebSocketSubscription } from "./use-websocket"
import wsClient from "@/lib/websocket/client"
import { useToast } from "@/components/ui/toast"

export interface RealtimeNotification {
    id: string
    type: "info" | "success" | "warning" | "error"
    title: string
    message: string
    category: string
    priority: "low" | "normal" | "high" | "critical"
    timestamp: string
    isRead: boolean
    actionUrl?: string
    metadata?: Record<string, unknown>
}

/**
 * Hook for real-time notification delivery
 * Validates: Requirements 23.1 - Notification delivery within 60 seconds
 */
export function useRealtimeNotifications() {
    const [notifications, setNotifications] = useState<RealtimeNotification[]>([])
    const [unreadCount, setUnreadCount] = useState(0)
    const { addToast } = useToast()

    // Subscribe to new notifications
    useWebSocketSubscription<RealtimeNotification>(
        "notification.new",
        (message) => {
            const notification = message.payload

            // Add to notifications list
            setNotifications(prev => [notification, ...prev.slice(0, 49)]) // Keep last 50

            // Update unread count
            if (!notification.isRead) {
                setUnreadCount(prev => prev + 1)
            }

            // Show toast for high priority notifications
            if (notification.priority === "high" || notification.priority === "critical") {
                addToast({
                    type: notification.type === "error" ? "error" :
                        notification.type === "warning" ? "warning" :
                            notification.type === "success" ? "success" : "info",
                    title: notification.title,
                    description: notification.message,
                    duration: notification.priority === "critical" ? 10000 : 5000,
                })
            }
        },
        [addToast]
    )

    // Subscribe to notification updates (read status, etc.)
    useWebSocketSubscription<{ id: string; isRead: boolean }>(
        "notification.update",
        (message) => {
            const { id, isRead } = message.payload

            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, isRead } : n)
            )

            if (isRead) {
                setUnreadCount(prev => Math.max(0, prev - 1))
            }
        },
        []
    )

    // Subscribe to bulk read updates
    useWebSocketSubscription<{ ids: string[] }>(
        "notification.bulk_read",
        (message) => {
            const { ids } = message.payload

            setNotifications(prev =>
                prev.map(n => ids.includes(n.id) ? { ...n, isRead: true } : n)
            )

            setUnreadCount(prev => Math.max(0, prev - ids.length))
        },
        []
    )

    // Connect to notification channel on mount
    useEffect(() => {
        wsClient.send("notification.subscribe", {})

        return () => {
            wsClient.send("notification.unsubscribe", {})
        }
    }, [])

    // Mark a notification as read
    const markAsRead = useCallback((id: string) => {
        wsClient.send("notification.read", { id })

        // Optimistic update
        setNotifications(prev =>
            prev.map(n => n.id === id ? { ...n, isRead: true } : n)
        )
        setUnreadCount(prev => Math.max(0, prev - 1))
    }, [])

    // Mark all notifications as read
    const markAllAsRead = useCallback(() => {
        const unreadIds = notifications.filter(n => !n.isRead).map(n => n.id)
        if (unreadIds.length === 0) return

        wsClient.send("notification.read_all", { ids: unreadIds })

        // Optimistic update
        setNotifications(prev => prev.map(n => ({ ...n, isRead: true })))
        setUnreadCount(0)
    }, [notifications])

    // Clear all notifications
    const clearAll = useCallback(() => {
        setNotifications([])
        setUnreadCount(0)
    }, [])

    return {
        notifications,
        unreadCount,
        markAsRead,
        markAllAsRead,
        clearAll,
    }
}

export default useRealtimeNotifications
