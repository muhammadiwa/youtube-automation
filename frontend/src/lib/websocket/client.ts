/**
 * WebSocket Client for real-time features
 * Handles connection management, reconnection, and message routing
 */

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "reconnecting" | "error"

export interface WebSocketMessage<T = unknown> {
    type: string
    payload: T
    timestamp?: string
}

type MessageHandler<T = unknown> = (message: WebSocketMessage<T>) => void
type StatusHandler = (status: WebSocketStatus) => void

interface WebSocketConfig {
    url: string
    reconnectAttempts?: number
    reconnectDelay?: number
    heartbeatInterval?: number
    protocols?: string[]
}

const DEFAULT_CONFIG: Partial<WebSocketConfig> = {
    reconnectAttempts: 5,
    reconnectDelay: 3000,
    heartbeatInterval: 30000,
}

class WebSocketClient {
    private ws: WebSocket | null = null
    private config: WebSocketConfig
    private status: WebSocketStatus = "disconnected"
    private reconnectCount = 0
    private heartbeatTimer: NodeJS.Timeout | null = null
    private reconnectTimer: NodeJS.Timeout | null = null

    // Message handlers by type
    private messageHandlers: Map<string, Set<MessageHandler>> = new Map()
    private globalHandlers: Set<MessageHandler> = new Set()
    private statusHandlers: Set<StatusHandler> = new Set()

    // Pending messages queue (for messages sent while disconnected)
    private pendingMessages: WebSocketMessage[] = []

    // Authentication token
    private authToken: string | null = null

    constructor(config: WebSocketConfig) {
        this.config = { ...DEFAULT_CONFIG, ...config }
    }

    // Set authentication token
    setAuthToken(token: string | null) {
        this.authToken = token
    }

    // Get current status
    getStatus(): WebSocketStatus {
        return this.status
    }

    // Connect to WebSocket server
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            return
        }

        this.setStatus("connecting")

        try {
            // Build URL with auth token if available
            let url = this.config.url
            if (this.authToken) {
                const separator = url.includes("?") ? "&" : "?"
                url = `${url}${separator}token=${encodeURIComponent(this.authToken)}`
            }

            this.ws = new WebSocket(url, this.config.protocols)
            this.setupEventHandlers()
        } catch (error) {
            console.error("[WebSocket] Connection error:", error)
            this.setStatus("error")
            this.scheduleReconnect()
        }
    }

    // Disconnect from WebSocket server
    disconnect(): void {
        this.clearTimers()
        this.reconnectCount = 0

        if (this.ws) {
            this.ws.close(1000, "Client disconnect")
            this.ws = null
        }

        this.setStatus("disconnected")
    }

    // Send a message
    send<T>(type: string, payload: T): boolean {
        const message: WebSocketMessage<T> = {
            type,
            payload,
            timestamp: new Date().toISOString(),
        }

        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message))
            return true
        }

        // Queue message for later
        this.pendingMessages.push(message as WebSocketMessage)
        return false
    }

    // Subscribe to messages of a specific type
    subscribe<T = unknown>(type: string, handler: MessageHandler<T>): () => void {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, new Set())
        }
        this.messageHandlers.get(type)!.add(handler as MessageHandler)

        return () => {
            this.messageHandlers.get(type)?.delete(handler as MessageHandler)
        }
    }

    // Subscribe to all messages
    subscribeAll(handler: MessageHandler): () => void {
        this.globalHandlers.add(handler)
        return () => this.globalHandlers.delete(handler)
    }

    // Subscribe to status changes
    onStatusChange(handler: StatusHandler): () => void {
        this.statusHandlers.add(handler)
        // Immediately notify of current status
        handler(this.status)
        return () => this.statusHandlers.delete(handler)
    }

    // Private methods
    private setupEventHandlers(): void {
        if (!this.ws) return

        this.ws.onopen = () => {
            console.log("[WebSocket] Connected")
            this.setStatus("connected")
            this.reconnectCount = 0
            this.startHeartbeat()
            this.flushPendingMessages()
        }

        this.ws.onclose = (event) => {
            console.log("[WebSocket] Disconnected:", event.code, event.reason)
            this.stopHeartbeat()

            if (event.code !== 1000) {
                // Abnormal closure, attempt reconnect
                this.scheduleReconnect()
            } else {
                this.setStatus("disconnected")
            }
        }

        this.ws.onerror = (error) => {
            console.error("[WebSocket] Error:", error)
            this.setStatus("error")
        }

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data) as WebSocketMessage
                this.handleMessage(message)
            } catch (error) {
                console.error("[WebSocket] Failed to parse message:", error)
            }
        }
    }

    private handleMessage(message: WebSocketMessage): void {
        // Handle heartbeat response
        if (message.type === "pong") {
            return
        }

        // Notify type-specific handlers
        const handlers = this.messageHandlers.get(message.type)
        if (handlers) {
            handlers.forEach(handler => handler(message))
        }

        // Notify global handlers
        this.globalHandlers.forEach(handler => handler(message))
    }

    private setStatus(status: WebSocketStatus): void {
        if (this.status !== status) {
            this.status = status
            this.statusHandlers.forEach(handler => handler(status))
        }
    }

    private startHeartbeat(): void {
        if (!this.config.heartbeatInterval) return

        this.heartbeatTimer = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.send("ping", {})
            }
        }, this.config.heartbeatInterval)
    }

    private stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer)
            this.heartbeatTimer = null
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectCount >= (this.config.reconnectAttempts || 5)) {
            console.log("[WebSocket] Max reconnect attempts reached")
            this.setStatus("error")
            return
        }

        this.setStatus("reconnecting")
        this.reconnectCount++

        const delay = (this.config.reconnectDelay || 3000) * Math.pow(1.5, this.reconnectCount - 1)
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectCount})`)

        this.reconnectTimer = setTimeout(() => {
            this.connect()
        }, delay)
    }

    private clearTimers(): void {
        this.stopHeartbeat()
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer)
            this.reconnectTimer = null
        }
    }

    private flushPendingMessages(): void {
        while (this.pendingMessages.length > 0) {
            const message = this.pendingMessages.shift()
            if (message && this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message))
            }
        }
    }
}

// Create singleton instance
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws"

export const wsClient = new WebSocketClient({ url: WS_URL })
export default wsClient

// Export class for custom instances
export { WebSocketClient }
