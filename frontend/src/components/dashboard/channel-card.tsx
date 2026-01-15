"use client"

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import {
    Radio,
    Calendar,
    WifiOff,
    AlertTriangle,
    Activity,
    Users,
    RefreshCw,
    ExternalLink,
    Settings,
    Eye,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChannelStatusInfo, StreamStatus, HealthStatus } from "@/lib/api/monitoring"

interface ChannelCardProps {
    channel: ChannelStatusInfo
    onRefresh?: () => void
    onQuickAction?: (action: string) => void
}

const streamStatusConfig: Record<StreamStatus | "ended", { label: string; color: string; icon: typeof Radio; badgeClass: string }> = {
    live: {
        label: "Live",
        color: "bg-red-500",
        icon: Radio,
        badgeClass: "bg-red-500 text-white animate-pulse",
    },
    scheduled: {
        label: "Scheduled",
        color: "bg-blue-500",
        icon: Calendar,
        badgeClass: "bg-blue-500 text-white",
    },
    offline: {
        label: "Offline",
        color: "bg-gray-400",
        icon: WifiOff,
        badgeClass: "bg-gray-500/80 text-white",
    },
    ended: {
        label: "Ended",
        color: "bg-gray-600",
        icon: WifiOff,
        badgeClass: "bg-gray-600 text-white",
    },
}

const healthStatusConfig: Record<HealthStatus, { label: string; color: string; bgColor: string }> = {
    healthy: { label: "Healthy", color: "text-green-500", bgColor: "bg-green-500" },
    warning: { label: "Warning", color: "text-yellow-500", bgColor: "bg-yellow-500" },
    critical: { label: "Critical", color: "text-red-500", bgColor: "bg-red-500" },
}

export function ChannelCard({ channel, onRefresh, onQuickAction }: ChannelCardProps) {
    const [isRefreshing, setIsRefreshing] = useState(false)
    const streamStatus = streamStatusConfig[channel.stream_status] || streamStatusConfig.offline
    const healthStatus = healthStatusConfig[channel.health_status] || healthStatusConfig.healthy
    const StreamIcon = streamStatus.icon

    const handleRefresh = async () => {
        setIsRefreshing(true)
        onRefresh?.()
        setTimeout(() => setIsRefreshing(false), 1000)
    }

    const hasCriticalIssue = channel.health_status === "critical" || channel.is_token_expired
    const quotaPercentage = Math.round(channel.quota_percent)

    return (
        <Card
            className={cn(
                "transition-all hover:shadow-md h-full",
                hasCriticalIssue && "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20",
                channel.alert_count > 0 && !hasCriticalIssue && "ring-1 ring-yellow-500/50"
            )}
        >
            <CardContent className="p-4 flex flex-col h-full">
                {/* Header */}
                <div className="flex items-start gap-3 mb-3">
                    <div className="relative flex-shrink-0">
                        <Avatar className="h-10 w-10">
                            <AvatarImage src={channel.thumbnail_url} />
                            <AvatarFallback className="text-xs">
                                {channel.channel_title.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <div className={cn(
                            "absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background",
                            streamStatus.color
                        )} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm truncate">{channel.channel_title}</h3>
                        <Badge className={cn("text-xs mt-1", streamStatus.badgeClass)} variant="secondary">
                            <StreamIcon className="h-3 w-3 mr-1" />
                            {streamStatus.label}
                        </Badge>
                    </div>
                </div>

                {/* Stream Info (if live) */}
                {channel.stream_status === "live" && channel.current_stream && (
                    <p className="text-xs text-muted-foreground truncate mb-2">
                        {channel.current_stream.title}
                    </p>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Users className="h-3.5 w-3.5" />
                        <span>{channel.subscriber_count.toLocaleString()}</span>
                    </div>
                    {channel.stream_status === "live" && channel.current_stream && (
                        <div className="flex items-center gap-1.5 text-muted-foreground">
                            <Eye className="h-3.5 w-3.5" />
                            <span>{channel.current_stream.viewer_count?.toLocaleString() || 0}</span>
                        </div>
                    )}
                    <div className={cn("flex items-center gap-1.5", healthStatus.color)}>
                        <Activity className="h-3.5 w-3.5" />
                        <span>{healthStatus.label}</span>
                    </div>
                    {channel.alert_count > 0 && (
                        <div className="flex items-center gap-1.5 text-yellow-600">
                            <AlertTriangle className="h-3.5 w-3.5" />
                            <span>{channel.alert_count} alert{channel.alert_count > 1 ? "s" : ""}</span>
                        </div>
                    )}
                </div>

                {/* Quota Bar */}
                <div className="mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-muted-foreground">API Quota</span>
                        <span className={cn(
                            quotaPercentage >= 90 && "text-red-500",
                            quotaPercentage >= 75 && quotaPercentage < 90 && "text-yellow-500"
                        )}>
                            {quotaPercentage}%
                        </span>
                    </div>
                    <Progress
                        value={quotaPercentage}
                        className={cn(
                            "h-1.5",
                            quotaPercentage >= 90 && "[&>div]:bg-red-500",
                            quotaPercentage >= 75 && quotaPercentage < 90 && "[&>div]:bg-yellow-500"
                        )}
                    />
                </div>

                {/* Critical Alert */}
                {hasCriticalIssue && (
                    <div className="p-2 bg-red-100 dark:bg-red-950/30 rounded text-xs text-red-600 dark:text-red-400 mb-3">
                        <div className="flex items-center gap-1.5">
                            <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
                            <span>Requires attention</span>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1.5 mt-auto pt-2 border-t">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs flex-1"
                        onClick={() => onQuickAction?.("view")}
                    >
                        <ExternalLink className="h-3.5 w-3.5 mr-1" />
                        View
                    </Button>
                    <Link href={`/dashboard/accounts/${channel.account_id}`} className="flex-1">
                        <Button variant="ghost" size="sm" className="h-7 px-2 text-xs w-full">
                            <Settings className="h-3.5 w-3.5 mr-1" />
                            Manage
                        </Button>
                    </Link>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                    >
                        <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin")} />
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export default ChannelCard
