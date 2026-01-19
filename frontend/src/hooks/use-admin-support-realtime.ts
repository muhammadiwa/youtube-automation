/**
 * Real-time support hook for Admin WebSocket-based ticket updates.
 * Provides automatic reconnection and message handling for admin users.
 */

import { useEffect, useRef, useCallback, useState } from "react"

export type AdminSupportEventType = "new_message" | "status_change" | "new_ticket" | "subscribed" | "unsubscribed" | "pong"

export interface AdminSupportWebSocketMessage {
    type: AdminSupportEventType
    ticket_id?: string
    payload?: Record<string, unknown>
    timestamp?: string
}

export type AdminSupportMessageHandler = (message: AdminSupportWebSocketMessage) => void

interface UseAdminSupportRealtimeOptions {
    adminId?: string
    onMessage?: AdminSupportMessageHandler
    onNewMessage?: (ticketId: string, payload: Record<string, unknown>) => void
    onStatusChange?: (ticketId: string, oldStatus: string, newStatus: string) => void
    onNewTicket?: (ticketData: Record<string, unknown>) => void
    onConnect?: () => void
    onDisconnect?: () => void
    autoConnect?: boolean
}

export function useAdminSupportRealtime(options: UseAdminSupportRealtimeOptions = {}) {
    const { adminId, autoConnect = true } = options

    const wsRef = useRef<WebSocket | null>(null)
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
    const reconnectAttemptsRef = useRef(0)
    const isConnectingRef = useRef(false)
    const adminIdRef = useRef(adminId)

    // Store callbacks in refs to avoid recreating connect function
    const callbacksRef = useRef(options)
    callbacksRef.current = options

    const [isConnected, setIsConnected] = useState(false)
    const [subscribedTickets, setSubscribedTickets] = useState<Set<string>>(new Set())

    // Keep adminIdRef in sync
    useEffect(() => {
        adminIdRef.current = adminId
    }, [adminId])

    const connect = useCallback(() => {
        const currentAdminId = adminIdRef.current

        // Prevent multiple simultaneous connection attempts
        if (!currentAdminId || isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
            console.log("[AdminSupportWS] Connect skipped:", {
                adminId: currentAdminId,
                isConnecting: isConnectingRef.current,
                wsState: wsRef.current?.readyState
            })
            return
        }

        isConnectingRef.current = true

        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"
        const ws = new WebSocket(`${wsUrl}/api/v1/admin/support/ws/${currentAdminId}`)
        console.log(`[AdminSupportWS] Connecting to /admin/support/ws with user_id: ${currentAdminId}`)

        ws.onopen = () => {
            console.log("[AdminSupportWS] Connected successfully")
            setIsConnected(true)
            isConnectingRef.current = false
            reconnectAttemptsRef.current = 0
            callbacksRef.current.onConnect?.()

            // Re-subscribe to previously subscribed tickets
            setSubscribedTickets(prev => {
                prev.forEach(ticketId => {
                    console.log("[AdminSupportWS] Re-subscribing to ticket:", ticketId)
                    ws.send(JSON.stringify({ type: "subscribe", ticket_id: ticketId }))
                })
                return prev
            })
        }

        ws.onmessage = (event) => {
            try {
                const message: AdminSupportWebSocketMessage = JSON.parse(event.data)
                console.log("[AdminSupportWS] Message received:", message.type, message)

                // Call generic handler
                callbacksRef.current.onMessage?.(message)

                // Call specific handlers
                if (message.type === "new_message" && message.ticket_id && message.payload) {
                    console.log("[AdminSupportWS] New message for ticket:", message.ticket_id)
                    callbacksRef.current.onNewMessage?.(message.ticket_id, message.payload)
                }

                if (message.type === "status_change" && message.ticket_id && message.payload) {
                    const { old_status, new_status } = message.payload as { old_status: string; new_status: string }
                    console.log("[AdminSupportWS] Status change:", old_status, "→", new_status)
                    callbacksRef.current.onStatusChange?.(message.ticket_id, old_status, new_status)
                }

                if (message.type === "new_ticket" && message.payload) {
                    console.log("[AdminSupportWS] New ticket created:", message.payload)
                    callbacksRef.current.onNewTicket?.(message.payload)
                }
            } catch (error) {
                console.error("[AdminSupportWS] Failed to parse message:", error)
            }
        }

        ws.onclose = (event) => {
            console.log("[AdminSupportWS] Disconnected", event.code, event.reason)
            setIsConnected(false)
            isConnectingRef.current = false
            callbacksRef.current.onDisconnect?.()

            // Only attempt reconnection if it wasn't a clean close and we haven't exceeded max attempts
            if (event.code !== 1000 && reconnectAttemptsRef.current < 10) {
                const delay = Math.min(3000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
                reconnectAttemptsRef.current += 1

                console.log(`[AdminSupportWS] Reconnecting in ${delay / 1000}s (attempt ${reconnectAttemptsRef.current}/10)`)

                reconnectTimeoutRef.current = setTimeout(() => {
                    if (adminIdRef.current) {
                        connect()
                    }
                }, delay)
            } else if (reconnectAttemptsRef.current >= 10) {
                console.error("[AdminSupportWS] Max reconnection attempts reached. Please refresh the page.")
            }
        }

        ws.onerror = (error) => {
            console.error("[AdminSupportWS] WebSocket error:", error)
            isConnectingRef.current = false
        }

        wsRef.current = ws
    }, []) // No dependencies - uses refs

    const disconnect = useCallback(() => {
        console.log("[AdminSupportWS] Manually disconnecting")

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
            reconnectTimeoutRef.current = null
        }

        if (wsRef.current) {
            wsRef.current.close(1000, "Manual disconnect")
            wsRef.current = null
        }

        isConnectingRef.current = false
        reconnectAttemptsRef.current = 0
        setIsConnected(false)
    }, [])

    const subscribeToTicket = useCallback((ticketId: string) => {
        console.log("[AdminSupportWS] Subscribing to ticket:", ticketId)
        setSubscribedTickets(prev => new Set(prev).add(ticketId))

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "subscribe", ticket_id: ticketId }))
            console.log("[AdminSupportWS] Subscription message sent")
        } else {
            console.log("[AdminSupportWS] WebSocket not ready, will subscribe on connect")
        }
    }, [])

    const unsubscribeFromTicket = useCallback((ticketId: string) => {
        setSubscribedTickets(prev => {
            const next = new Set(prev)
            next.delete(ticketId)
            return next
        })

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "unsubscribe", ticket_id: ticketId }))
        }
    }, [])

    const sendPing = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "ping" }))
        }
    }, [])

    // Auto-connect when adminId becomes available
    useEffect(() => {
        if (autoConnect && adminId) {
            console.log("[AdminSupportWS] Auto-connect triggered with adminId:", adminId)
            connect()
        }

        // Cleanup on unmount
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current)
            }
            if (wsRef.current) {
                wsRef.current.close(1000, "Component unmounted")
            }
        }
    }, [autoConnect, adminId, connect])

    // Heartbeat to keep connection alive
    useEffect(() => {
        if (!isConnected) return

        const interval = setInterval(sendPing, 30000)
        return () => clearInterval(interval)
    }, [isConnected, sendPing])

    return {
        isConnected,
        connect,
        disconnect,
        subscribeToTicket,
        unsubscribeFromTicket,
        subscribedTickets: Array.from(subscribedTickets),
    }
}

export default useAdminSupportRealtime
