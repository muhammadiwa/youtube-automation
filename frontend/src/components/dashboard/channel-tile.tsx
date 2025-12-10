"use client"

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
    Radio,
    Calendar,
    WifiOff,
    AlertTriangle,
    Activity,
    Users,
    Clock,
    RefreshCw,
    ChevronDown,
    ChevronUp,
    Play,
    Square,
    ExternalLink,
    Zap,
    Settings,
    BarChart3,
    MessageSquare,
    Video,
    Shield,
    Eye,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChannelStatus } from "@/lib/api/monitoring"

interface ChannelTileProps {
    channel: ChannelStatus
    size: "small" | "medium" | "large"
    expanded?: boolean
    onExpand?: () => void
    onRefresh?: () => void
    onQuickAction?: (action: string) => void
}

const streamStatusConfig = {
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
        badgeClass: "bg-gray-500 text-white",
    },
    error: {
        label: "Error",
        color: "bg-red-600",
        icon: AlertTriangle,
        badgeClass: "bg-red-600 text-white",
    },
}

const healthStatusConfig = {
    healthy: { label: "Healthy", color: "text-green-500", bgColor: "bg-green-500" },
    warning: { label: "Warning", color: "text-yellow-500", bgColor: "bg-yellow-500" },
    critical: { label: "Critical", color: "text-red-500", bgColor: "bg-red-500" },
    offline: { label: "Offline", color: "text-gray-400", bgColor: "bg-gray-400" },
}


// Expanded Detail Panel Component - Shows detailed metrics when a channel is expanded
function ExpandedDetailPanel({
    channel,
    onQuickAction,
    onRefresh,
    isRefreshing,
}: {
    channel: ChannelStatus
    onQuickAction?: (action: string) => void
    onRefresh?: () => void
    isRefreshing: boolean
}) {
    const healthStatus = healthStatusConfig[channel.healthStatus]

    const formatUptime = (seconds?: number) => {
        if (!seconds) return "N/A"
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return `${hours}h ${minutes}m`
    }

    const formatBitrate = (bitrate?: number) => {
        if (!bitrate) return "N/A"
        return `${(bitrate / 1000).toFixed(1)} Mbps`
    }

    const quotaPercentage = Math.round((channel.quotaUsage / channel.quotaLimit) * 100)

    return (
        <div className="space-y-4 animate-in slide-in-from-top-2 duration-200">
            {/* Critical Issues Alert */}
            {channel.healthStatus === "critical" && (
                <div className="p-3 bg-red-100 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg">
                    <div className="flex items-start gap-2">
                        <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="font-semibold text-red-700 dark:text-red-300">Critical Issue Detected</p>
                            <p className="text-sm text-red-600 dark:text-red-400">
                                This channel requires immediate attention. Check stream health and connection status.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Active Alerts */}
            {channel.alertCount > 0 && channel.healthStatus !== "critical" && (
                <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900 rounded-lg">
                    <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="font-medium">{channel.alertCount} active alert{channel.alertCount > 1 ? "s" : ""}</span>
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div>
                <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Quick Actions</h4>
                <div className="flex flex-wrap gap-2">
                    {channel.streamStatus === "live" ? (
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation()
                                onQuickAction?.("stop")
                            }}
                        >
                            <Square className="h-4 w-4 mr-1" />
                            Stop Stream
                        </Button>
                    ) : (
                        <Button
                            variant="default"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation()
                                onQuickAction?.("start")
                            }}
                        >
                            <Play className="h-4 w-4 mr-1" />
                            Start Stream
                        </Button>
                    )}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                            e.stopPropagation()
                            onQuickAction?.("view")
                        }}
                    >
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View Channel
                    </Button>
                    <Link href={`/dashboard/accounts/${channel.accountId}`} onClick={(e) => e.stopPropagation()}>
                        <Button variant="outline" size="sm">
                            <Settings className="h-4 w-4 mr-1" />
                            Manage
                        </Button>
                    </Link>
                    <Link href={`/dashboard/analytics/channel/${channel.accountId}`} onClick={(e) => e.stopPropagation()}>
                        <Button variant="outline" size="sm">
                            <BarChart3 className="h-4 w-4 mr-1" />
                            Analytics
                        </Button>
                    </Link>
                    <Link href={`/dashboard/videos?account=${channel.accountId}`} onClick={(e) => e.stopPropagation()}>
                        <Button variant="outline" size="sm">
                            <Video className="h-4 w-4 mr-1" />
                            Videos
                        </Button>
                    </Link>
                    <Link href={`/dashboard/comments?account=${channel.accountId}`} onClick={(e) => e.stopPropagation()}>
                        <Button variant="outline" size="sm">
                            <MessageSquare className="h-4 w-4 mr-1" />
                            Comments
                        </Button>
                    </Link>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                            e.stopPropagation()
                            onRefresh?.()
                        }}
                        disabled={isRefreshing}
                    >
                        <RefreshCw className={cn("h-4 w-4 mr-1", isRefreshing && "animate-spin")} />
                        Refresh
                    </Button>
                </div>
            </div>

            <Separator />

            {/* Detailed Metrics Grid */}
            <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground">Detailed Metrics</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    {/* Channel Stats */}
                    <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">Subscribers</span>
                        </div>
                        <p className="text-lg font-semibold">{channel.account.subscriberCount.toLocaleString()}</p>
                    </div>

                    <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <Video className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">Videos</span>
                        </div>
                        <p className="text-lg font-semibold">{channel.account.videoCount.toLocaleString()}</p>
                    </div>

                    {/* Stream Metrics (if live) */}
                    {channel.streamStatus === "live" && (
                        <>
                            <div className="p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center gap-2 mb-1">
                                    <Eye className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground">Current Viewers</span>
                                </div>
                                <p className="text-lg font-semibold">{channel.currentViewers?.toLocaleString() || 0}</p>
                            </div>

                            <div className="p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center gap-2 mb-1">
                                    <Clock className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground">Uptime</span>
                                </div>
                                <p className="text-lg font-semibold">{formatUptime(channel.uptime)}</p>
                            </div>

                            <div className="p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center gap-2 mb-1">
                                    <Zap className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground">Bitrate</span>
                                </div>
                                <p className="text-lg font-semibold">{formatBitrate(channel.bitrate)}</p>
                            </div>

                            {channel.droppedFrames !== undefined && (
                                <div className="p-3 bg-muted/50 rounded-lg">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Activity className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-xs text-muted-foreground">Dropped Frames</span>
                                    </div>
                                    <p className={cn("text-lg font-semibold", channel.droppedFrames > 100 && "text-yellow-500", channel.droppedFrames > 500 && "text-red-500")}>
                                        {channel.droppedFrames}
                                    </p>
                                </div>
                            )}
                        </>
                    )}

                    {/* Health Status */}
                    <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <Activity className={cn("h-4 w-4", healthStatus.color)} />
                            <span className="text-xs text-muted-foreground">Health Status</span>
                        </div>
                        <p className={cn("text-lg font-semibold", healthStatus.color)}>{healthStatus.label}</p>
                    </div>

                    {/* Token Status */}
                    <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <Shield className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">Token Status</span>
                        </div>
                        <Badge
                            variant={channel.tokenStatus === "valid" ? "default" : channel.tokenStatus === "expiring" ? "secondary" : "destructive"}
                            className="mt-1"
                        >
                            {channel.tokenStatus}
                        </Badge>
                    </div>

                    {/* Strikes */}
                    <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                            <AlertTriangle className={cn("h-4 w-4", channel.account.strikeCount > 0 ? "text-red-500" : "text-muted-foreground")} />
                            <span className="text-xs text-muted-foreground">Strikes</span>
                        </div>
                        <p className={cn("text-lg font-semibold", channel.account.strikeCount > 0 && "text-red-500")}>
                            {channel.account.strikeCount}
                        </p>
                    </div>

                    {/* Last Activity */}
                    {channel.lastActivity && (
                        <div className="p-3 bg-muted/50 rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                                <Clock className="h-4 w-4 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground">Last Activity</span>
                            </div>
                            <p className="text-sm font-medium">{new Date(channel.lastActivity).toLocaleString()}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* API Quota */}
            <div className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">API Quota Usage</span>
                    <span className={cn(
                        "text-sm font-semibold",
                        quotaPercentage >= 90 && "text-red-500",
                        quotaPercentage >= 75 && quotaPercentage < 90 && "text-yellow-500"
                    )}>
                        {quotaPercentage}%
                    </span>
                </div>
                <Progress
                    value={quotaPercentage}
                    className={cn(
                        "h-2",
                        quotaPercentage >= 90 && "[&>div]:bg-red-500",
                        quotaPercentage >= 75 && quotaPercentage < 90 && "[&>div]:bg-yellow-500"
                    )}
                />
                <p className="text-xs text-muted-foreground mt-1">
                    {channel.quotaUsage.toLocaleString()} / {channel.quotaLimit.toLocaleString()} units used
                </p>
            </div>
        </div>
    )
}


export function ChannelTile({
    channel,
    size,
    expanded = false,
    onExpand,
    onRefresh,
    onQuickAction,
}: ChannelTileProps) {
    const [isRefreshing, setIsRefreshing] = useState(false)
    const streamStatus = streamStatusConfig[channel.streamStatus]
    const healthStatus = healthStatusConfig[channel.healthStatus]
    const StreamIcon = streamStatus.icon

    const handleRefresh = async () => {
        setIsRefreshing(true)
        onRefresh?.()
        setTimeout(() => setIsRefreshing(false), 1000)
    }

    const formatUptime = (seconds?: number) => {
        if (!seconds) return "N/A"
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return `${hours}h ${minutes}m`
    }

    const formatBitrate = (bitrate?: number) => {
        if (!bitrate) return "N/A"
        return `${(bitrate / 1000).toFixed(1)} Mbps`
    }

    // Determine if channel has critical issues (Requirement 16.3)
    const hasCriticalIssue = channel.healthStatus === "critical" ||
        channel.tokenStatus === "expired" ||
        channel.account.strikeCount >= 2

    // Small tile - minimal info with click to expand
    if (size === "small") {
        return (
            <div className="space-y-0">
                <Card
                    className={cn(
                        "cursor-pointer transition-all hover:shadow-md",
                        hasCriticalIssue && "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20",
                        channel.hasActiveAlerts && !hasCriticalIssue && "ring-2 ring-yellow-500",
                        expanded && "ring-2 ring-primary"
                    )}
                    onClick={onExpand}
                >
                    <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <Avatar className="h-8 w-8">
                                    <AvatarImage src={channel.account.thumbnailUrl} />
                                    <AvatarFallback className="text-xs">
                                        {channel.account.channelTitle.substring(0, 2).toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className={cn("absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background", streamStatus.color)} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{channel.account.channelTitle}</p>
                                <div className="flex items-center gap-1">
                                    <StreamIcon className="h-3 w-3" />
                                    <span className="text-xs text-muted-foreground">{streamStatus.label}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-1">
                                {hasCriticalIssue && (
                                    <AlertTriangle className="h-4 w-4 text-red-500" />
                                )}
                                {channel.alertCount > 0 && (
                                    <Badge variant="destructive" className="h-5 px-1.5 text-xs">
                                        {channel.alertCount}
                                    </Badge>
                                )}
                                {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                            </div>
                        </div>
                    </CardContent>
                </Card>
                {/* Expanded Detail Panel for Small Tile */}
                {expanded && (
                    <Card className="mt-2 border-primary/50">
                        <CardContent className="p-4">
                            <ExpandedDetailPanel
                                channel={channel}
                                onQuickAction={onQuickAction}
                                onRefresh={handleRefresh}
                                isRefreshing={isRefreshing}
                            />
                        </CardContent>
                    </Card>
                )}
            </div>
        )
    }

    // Medium tile - standard info with click to expand
    if (size === "medium") {
        return (
            <div className="space-y-0">
                <Card
                    className={cn(
                        "cursor-pointer transition-all hover:shadow-md",
                        hasCriticalIssue && "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20",
                        channel.hasActiveAlerts && !hasCriticalIssue && "ring-2 ring-yellow-500",
                        expanded && "ring-2 ring-primary"
                    )}
                    onClick={onExpand}
                >
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <div className="relative">
                                <Avatar className="h-12 w-12">
                                    <AvatarImage src={channel.account.thumbnailUrl} />
                                    <AvatarFallback>
                                        {channel.account.channelTitle.substring(0, 2).toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className={cn("absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-background", streamStatus.color)} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-1">
                                    <h3 className="font-semibold truncate">{channel.account.channelTitle}</h3>
                                    <div className="flex items-center gap-2">
                                        <Badge className={streamStatus.badgeClass}>
                                            <StreamIcon className="h-3 w-3 mr-1" />
                                            {streamStatus.label}
                                        </Badge>
                                        {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                                    </div>
                                </div>
                                {channel.streamStatus === "live" && (
                                    <p className="text-sm text-muted-foreground truncate mb-2">
                                        {channel.currentStreamTitle || "Live Stream"}
                                    </p>
                                )}
                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                    {channel.streamStatus === "live" && (
                                        <>
                                            <div className="flex items-center gap-1">
                                                <Users className="h-3.5 w-3.5" />
                                                <span>{channel.currentViewers?.toLocaleString() || 0}</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Clock className="h-3.5 w-3.5" />
                                                <span>{formatUptime(channel.uptime)}</span>
                                            </div>
                                        </>
                                    )}
                                    <div className={cn("flex items-center gap-1", healthStatus.color)}>
                                        <Activity className="h-3.5 w-3.5" />
                                        <span>{healthStatus.label}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {/* Critical Issue Indicator */}
                        {hasCriticalIssue && (
                            <div className="mt-3 flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                                <AlertTriangle className="h-4 w-4" />
                                <span className="font-medium">Critical issue - click to view details</span>
                            </div>
                        )}
                        {channel.alertCount > 0 && !hasCriticalIssue && (
                            <div className="mt-3 flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
                                <AlertTriangle className="h-4 w-4" />
                                <span>{channel.alertCount} active alert{channel.alertCount > 1 ? "s" : ""}</span>
                            </div>
                        )}
                    </CardContent>
                </Card>
                {/* Expanded Detail Panel for Medium Tile */}
                {expanded && (
                    <Card className="mt-2 border-primary/50">
                        <CardContent className="p-4">
                            <ExpandedDetailPanel
                                channel={channel}
                                onQuickAction={onQuickAction}
                                onRefresh={handleRefresh}
                                isRefreshing={isRefreshing}
                            />
                        </CardContent>
                    </Card>
                )}
            </div>
        )
    }

    // Large tile - full info with inline expansion
    return (
        <Card
            className={cn(
                "transition-all",
                hasCriticalIssue && "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20",
                channel.hasActiveAlerts && !hasCriticalIssue && "ring-2 ring-yellow-500",
                expanded && "ring-2 ring-primary"
            )}
        >
            <CardContent className="p-4">
                <div className="flex items-start gap-4">
                    <div className="relative">
                        <Avatar className="h-16 w-16">
                            <AvatarImage src={channel.account.thumbnailUrl} />
                            <AvatarFallback>
                                {channel.account.channelTitle.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <div className={cn("absolute -bottom-1 -right-1 h-5 w-5 rounded-full border-2 border-background", streamStatus.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                            <h3 className="text-lg font-semibold truncate">{channel.account.channelTitle}</h3>
                            <div className="flex items-center gap-2">
                                <Badge className={streamStatus.badgeClass}>
                                    <StreamIcon className="h-3 w-3 mr-1" />
                                    {streamStatus.label}
                                </Badge>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        handleRefresh()
                                    }}
                                >
                                    <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
                                </Button>
                            </div>
                        </div>
                        {channel.streamStatus === "live" && channel.currentStreamTitle && (
                            <p className="text-sm text-muted-foreground truncate mb-2">
                                {channel.currentStreamTitle}
                            </p>
                        )}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                            {channel.streamStatus === "live" && (
                                <>
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <p className="text-sm font-medium">{channel.currentViewers?.toLocaleString() || 0}</p>
                                            <p className="text-xs text-muted-foreground">Viewers</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <p className="text-sm font-medium">{formatUptime(channel.uptime)}</p>
                                            <p className="text-xs text-muted-foreground">Uptime</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Zap className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <p className="text-sm font-medium">{formatBitrate(channel.bitrate)}</p>
                                            <p className="text-xs text-muted-foreground">Bitrate</p>
                                        </div>
                                    </div>
                                </>
                            )}
                            <div className="flex items-center gap-2">
                                <Activity className={cn("h-4 w-4", healthStatus.color)} />
                                <div>
                                    <p className={cn("text-sm font-medium", healthStatus.color)}>{healthStatus.label}</p>
                                    <p className="text-xs text-muted-foreground">Health</p>
                                </div>
                            </div>
                        </div>
                        {/* Quota usage */}
                        <div className="mt-3">
                            <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-muted-foreground">API Quota</span>
                                <span>{Math.round((channel.quotaUsage / channel.quotaLimit) * 100)}%</span>
                            </div>
                            <Progress value={(channel.quotaUsage / channel.quotaLimit) * 100} className="h-1.5" />
                        </div>
                    </div>
                </div>

                {/* Critical Issue Alert */}
                {hasCriticalIssue && (
                    <div className="mt-4 p-3 bg-red-100 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                            <AlertTriangle className="h-4 w-4" />
                            <span className="font-medium">Critical issue detected - immediate attention required</span>
                        </div>
                    </div>
                )}

                {/* Alerts section */}
                {channel.alertCount > 0 && !hasCriticalIssue && (
                    <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
                            <AlertTriangle className="h-4 w-4" />
                            <span className="font-medium">{channel.alertCount} active alert{channel.alertCount > 1 ? "s" : ""}</span>
                        </div>
                    </div>
                )}

                {/* Expandable section */}
                <div className="mt-4 pt-4 border-t">
                    <Button
                        variant="ghost"
                        className="w-full justify-between"
                        onClick={onExpand}
                    >
                        <span>{expanded ? "Hide Details" : "Show Details"}</span>
                        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                </div>

                {/* Expanded content */}
                {expanded && (
                    <div className="mt-4">
                        <ExpandedDetailPanel
                            channel={channel}
                            onQuickAction={onQuickAction}
                            onRefresh={handleRefresh}
                            isRefreshing={isRefreshing}
                        />
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
