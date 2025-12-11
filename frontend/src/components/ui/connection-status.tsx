"use client"

import { useWebSocket } from "@/hooks/use-websocket"
import { cn } from "@/lib/utils"
import { Wifi, WifiOff, Loader2 } from "lucide-react"

interface ConnectionStatusProps {
    className?: string
    showLabel?: boolean
    size?: "sm" | "md" | "lg"
}

const statusConfig = {
    connected: {
        color: "bg-green-500",
        pulseColor: "bg-green-400",
        icon: Wifi,
        label: "Connected",
        description: "Real-time updates active",
    },
    connecting: {
        color: "bg-yellow-500",
        pulseColor: "bg-yellow-400",
        icon: Loader2,
        label: "Connecting",
        description: "Establishing connection...",
    },
    reconnecting: {
        color: "bg-yellow-500",
        pulseColor: "bg-yellow-400",
        icon: Loader2,
        label: "Reconnecting",
        description: "Connection lost, reconnecting...",
    },
    disconnected: {
        color: "bg-gray-400",
        pulseColor: "bg-gray-300",
        icon: WifiOff,
        label: "Disconnected",
        description: "Real-time updates unavailable",
    },
    error: {
        color: "bg-red-500",
        pulseColor: "bg-red-400",
        icon: WifiOff,
        label: "Error",
        description: "Connection error occurred",
    },
}

const sizeConfig = {
    sm: {
        dot: "h-2 w-2",
        icon: "h-3 w-3",
        text: "text-xs",
    },
    md: {
        dot: "h-2.5 w-2.5",
        icon: "h-4 w-4",
        text: "text-sm",
    },
    lg: {
        dot: "h-3 w-3",
        icon: "h-5 w-5",
        text: "text-base",
    },
}

export function ConnectionStatus({
    className,
    showLabel = false,
    size = "md"
}: ConnectionStatusProps) {
    const { status } = useWebSocket()
    const config = statusConfig[status]
    const sizes = sizeConfig[size]
    const Icon = config.icon
    const isAnimating = status === "connecting" || status === "reconnecting"

    return (
        <div
            className={cn("flex items-center gap-2 cursor-default", className)}
            title={`${config.label}: ${config.description}`}
        >
            <div className="relative">
                {/* Pulse animation for connected state */}
                {status === "connected" && (
                    <span
                        className={cn(
                            "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                            config.pulseColor,
                            sizes.dot
                        )}
                    />
                )}
                {/* Status dot */}
                <span
                    className={cn(
                        "relative inline-flex rounded-full",
                        config.color,
                        sizes.dot
                    )}
                />
            </div>

            {showLabel && (
                <div className="flex items-center gap-1.5">
                    <Icon
                        className={cn(
                            sizes.icon,
                            isAnimating && "animate-spin"
                        )}
                    />
                    <span className={cn("font-medium", sizes.text)}>
                        {config.label}
                    </span>
                </div>
            )}
        </div>
    )
}

/**
 * Inline connection status for use in headers/footers
 */
export function ConnectionStatusInline({ className }: { className?: string }) {
    const { status, isConnected } = useWebSocket()

    if (isConnected) {
        return null // Don't show when connected
    }

    const config = statusConfig[status]
    const Icon = config.icon
    const isAnimating = status === "connecting" || status === "reconnecting"

    return (
        <div
            className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
                status === "error" ? "bg-red-500/10 text-red-500" : "bg-yellow-500/10 text-yellow-600",
                className
            )}
        >
            <Icon className={cn("h-3 w-3", isAnimating && "animate-spin")} />
            <span>{config.label}</span>
        </div>
    )
}

export default ConnectionStatus
