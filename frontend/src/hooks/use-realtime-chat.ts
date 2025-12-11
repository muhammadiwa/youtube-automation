"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useWebSocketSubscription } from "./use-websocket"
import wsClient from "@/lib/websocket/client"

export interface ChatMessage {
    id: string
    eventId: string
    authorId: string
    authorName: string
    authorImageUrl?: string
    message: string
    timestamp: string
    isModerator: boolean
    isOwner: boolean
    badges: string[]
    isDeleted?: boolean
    deletedBy?: string
}

export interface ChatModerationAction {
    eventId: string
    messageId: string
    action: "delete" | "timeout" | "ban"
    moderatorId: string
    reason?: string
    duration?: number
    timestamp: string
}

export interface ChatStatus {
    eventId: string
    isSlowMode: boolean
    slowModeDelay?: number
    isMembersOnly: boolean
    isSubscribersOnly: boolean
}

/**
 * Hook for real-time chat synchronization
 * Validates: Requirements 12.1 - Chat moderation within 2 seconds
 */
export function useRealtimeChat(eventId: string | null) {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [chatStatus, setChatStatus] = useState<ChatStatus | null>(null)
    const [isConnected, setIsConnected] = useState(false)
    const messagesRef = useRef<ChatMessage[]>([])

    // Keep ref in sync with state
    messagesRef.current = messages

    // Subscribe to new chat messages
    useWebSocketSubscription<ChatMessage>(
        "chat.message",
        (wsMessage) => {
            if (wsMessage.payload.eventId === eventId) {
                setMessages(prev => {
                    // Limit to last 200 messages for performance
                    const updated = [...prev, wsMessage.payload]
                    return updated.slice(-200)
                })
            }
        },
        [eventId]
    )

    // Subscribe to moderation actions
    useWebSocketSubscription<ChatModerationAction>(
        "chat.moderation",
        (wsMessage) => {
            if (wsMessage.payload.eventId === eventId) {
                const { messageId, action } = wsMessage.payload

                if (action === "delete") {
                    setMessages(prev =>
                        prev.map(msg =>
                            msg.id === messageId
                                ? { ...msg, isDeleted: true, deletedBy: wsMessage.payload.moderatorId }
                                : msg
                        )
                    )
                }
            }
        },
        [eventId]
    )

    // Subscribe to chat status changes
    useWebSocketSubscription<ChatStatus>(
        "chat.status",
        (wsMessage) => {
            if (wsMessage.payload.eventId === eventId) {
                setChatStatus(wsMessage.payload)
            }
        },
        [eventId]
    )

    // Subscribe to chat room
    useEffect(() => {
        if (!eventId) {
            setIsConnected(false)
            setMessages([])
            return
        }

        // Join chat room
        wsClient.send("chat.join", { eventId })
        setIsConnected(true)

        return () => {
            // Leave chat room
            wsClient.send("chat.leave", { eventId })
            setIsConnected(false)
        }
    }, [eventId])

    // Send a chat message
    const sendMessage = useCallback((message: string) => {
        if (!eventId) return false
        return wsClient.send("chat.send", { eventId, message })
    }, [eventId])

    // Delete a message (moderator action)
    const deleteMessage = useCallback((messageId: string, reason?: string) => {
        if (!eventId) return false
        return wsClient.send("chat.moderate", {
            eventId,
            messageId,
            action: "delete",
            reason
        })
    }, [eventId])

    // Timeout a user
    const timeoutUser = useCallback((userId: string, duration: number, reason?: string) => {
        if (!eventId) return false
        return wsClient.send("chat.moderate", {
            eventId,
            userId,
            action: "timeout",
            duration,
            reason
        })
    }, [eventId])

    // Ban a user
    const banUser = useCallback((userId: string, reason?: string) => {
        if (!eventId) return false
        return wsClient.send("chat.moderate", {
            eventId,
            userId,
            action: "ban",
            reason
        })
    }, [eventId])

    // Clear local messages
    const clearMessages = useCallback(() => {
        setMessages([])
    }, [])

    return {
        messages,
        chatStatus,
        isConnected,
        sendMessage,
        deleteMessage,
        timeoutUser,
        banUser,
        clearMessages,
    }
}

export default useRealtimeChat
