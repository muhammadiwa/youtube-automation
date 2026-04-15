"use client"

import { useState, useEffect, useCallback } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { LiveStreamCard } from "@/components/dashboard/live-stream-card"
import { ScheduleTimeline } from "@/components/dashboard/schedule-timeline"
import { AlertCenter } from "@/components/dashboard/alert-center"
import { monitoringApi } from "@/lib/api"
import type {
    MonitoringDashboard,
    ChannelStatusInfo,
    HealthStatus,
    StreamStatus,
} from "@/lib/api/monitoring"
import {
    Monitor,
    Radio,
    Calendar,
    WifiOff,
    AlertTriangle,
    CheckCircle,
    RefreshCw,
    Users,
    Eye,
    Activity,
    Gauge,
} from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"

const REFRESH_INTERVAL = 30000 // 30 seconds

export default function MonitoringPage() {
    const [dashboard, setDashboard] = useState<MonitoringDashboard | null>(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

    const fetchDashboard = useCallback(async (showRefreshing = false) => {
        if (showRefreshing) setRefreshing(true)
        try {
            const data = await monitoringApi.getDashboard()
            setDashboard(data)
            setLastUpdated(new Date())
        } catch (error) {
            console.error("Failed to fetch monitoring data:", error)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }, [])

    useEffect(() => {
        fetchDashboard()

        // Auto-refresh
        const interval = setInterval(() => {
            fetchDashboard()
        }, REFRESH_INTERVAL)

        return () => clearInterval(interval)
    }, [fetchDashboard])

    const handleRefresh = () => {
        fetchDashboard(true)
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Monitoring" },
                ]}
            >
                <div className="space-y-6">
                    <Skeleton className="h-10 w-64" />
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        {[...Array(6)].map((_, i) => (
                            <Skeleton key={i} className="h-24" />
                        ))}
                    </div>
                    <div className="grid lg:grid-cols-3 gap-6">
                        <Skeleton className="h-96 lg:col-span-2" />
                        <Skeleton className="h-96" />
                    </div>
                </div>
            </DashboardLayout>
        )
    }

    const overview = dashboard?.overview

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Monitoring" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Monitor className="h-6 w-6" />
                            Live Control Center
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Real-time monitoring of your YouTube channels
                            {lastUpdated && (
                                <span className="ml-2">
                                    • Updated {lastUpdated.toLocaleTimeString()}
                                </span>
                            )}
                        </p>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
                        Refresh
                    </Button>
                </div>

                {/* Overview Stats */}
                {overview && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        {/* Total Channels */}
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                                        <Monitor className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{overview.total_channels}</p>
                                        <p className="text-xs text-muted-foreground">Channels</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Live Now */}
                        <Card className={cn(overview.live_channels > 0 && "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900")}>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "p-2 rounded-lg",
                                        overview.live_channels > 0
                                            ? "bg-red-100 dark:bg-red-900"
                                            : "bg-slate-100 dark:bg-slate-800"
                                    )}>
                                        <Radio className={cn(
                                            "h-5 w-5",
                                            overview.live_channels > 0
                                                ? "text-red-600 dark:text-red-400"
                                                : "text-slate-400"
                                        )} />
                                    </div>
                                    <div>
                                        <p className={cn(
                                            "text-2xl font-bold",
                                            overview.live_channels > 0 && "text-red-600 dark:text-red-400"
                                        )}>
                                            {overview.live_channels}
                                        </p>
                                        <p className="text-xs text-muted-foreground">Live Now</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Total Viewers */}
                        <Card className={cn(overview.total_viewers > 0 && "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900")}>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "p-2 rounded-lg",
                                        overview.total_viewers > 0
                                            ? "bg-blue-100 dark:bg-blue-900"
                                            : "bg-slate-100 dark:bg-slate-800"
                                    )}>
                                        <Eye className={cn(
                                            "h-5 w-5",
                                            overview.total_viewers > 0
                                                ? "text-blue-600 dark:text-blue-400"
                                                : "text-slate-400"
                                        )} />
                                    </div>
                                    <div>
                                        <p className={cn(
                                            "text-2xl font-bold",
                                            overview.total_viewers > 0 && "text-blue-600 dark:text-blue-400"
                                        )}>
                                            {overview.total_viewers.toLocaleString()}
                                        </p>
                                        <p className="text-xs text-muted-foreground">Viewers</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Scheduled */}
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                                        <Calendar className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                                            {overview.scheduled_channels}
                                        </p>
                                        <p className="text-xs text-muted-foreground">Scheduled</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Healthy */}
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                                        <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                                            {overview.healthy_channels}
                                        </p>
                                        <p className="text-xs text-muted-foreground">Healthy</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Alerts */}
                        <Card className={cn(overview.critical_alerts > 0 && "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900")}>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "p-2 rounded-lg",
                                        overview.critical_alerts > 0
                                            ? "bg-red-100 dark:bg-red-900"
                                            : "bg-yellow-100 dark:bg-yellow-900"
                                    )}>
                                        <AlertTriangle className={cn(
                                            "h-5 w-5",
                                            overview.critical_alerts > 0
                                                ? "text-red-600 dark:text-red-400"
                                                : "text-yellow-600 dark:text-yellow-400"
                                        )} />
                                    </div>
                                    <div>
                                        <p className={cn(
                                            "text-2xl font-bold",
                                            overview.critical_alerts > 0
                                                ? "text-red-600 dark:text-red-400"
                                                : overview.active_alerts > 0
                                                    ? "text-yellow-600 dark:text-yellow-400"
                                                    : ""
                                        )}>
                                            {overview.active_alerts}
                                        </p>
                                        <p className="text-xs text-muted-foreground">Alerts</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Main Content Grid */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left Column - Live Streams & Channels */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Live Streams Section */}
                        {dashboard && dashboard.live_streams.length > 0 && (
                            <div>
                                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Radio className="h-5 w-5 text-red-500" />
                                    Live Now
                                    <Badge className="bg-red-500 text-white animate-pulse">
                                        {dashboard.live_streams.length}
                                    </Badge>
                                </h2>
                                <div className="grid sm:grid-cols-2 gap-4">
                                    {dashboard.live_streams.map((stream) => (
                                        <LiveStreamCard key={stream.stream_id} stream={stream} />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* All Channels Grid */}
                        <div>
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Activity className="h-5 w-5 text-blue-500" />
                                Channel Status
                            </h2>
                            {dashboard && dashboard.channels.length > 0 ? (
                                <div className="grid sm:grid-cols-2 gap-4">
                                    {dashboard.channels.map((channel) => (
                                        <ChannelStatusCard key={channel.account_id} channel={channel} />
                                    ))}
                                </div>
                            ) : (
                                <Card>
                                    <CardContent className="py-12 text-center">
                                        <Monitor className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                        <h3 className="text-lg font-semibold mb-2">No Channels Connected</h3>
                                        <p className="text-muted-foreground mb-4">
                                            Connect your YouTube accounts to start monitoring
                                        </p>
                                        <Link href="/dashboard/accounts">
                                            <Button>Connect Account</Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>

                    {/* Right Column - Schedule & Alerts */}
                    <div className="space-y-6">
                        {/* Schedule Timeline */}
                        <ScheduleTimeline streams={dashboard?.scheduled_streams || []} />

                        {/* Alert Center */}
                        <AlertCenter alerts={dashboard?.alerts || []} />
                    </div>
                </div>
            </div>
        </DashboardLayout>
    )
}

// ============================================================================
// Channel Status Card Component
// ============================================================================

interface ChannelStatusCardProps {
    channel: ChannelStatusInfo
}

const streamStatusConfig: Record<StreamStatus, { label: string; color: string; icon: typeof Radio }> = {
    live: { label: "Live", color: "bg-red-500", icon: Radio },
    scheduled: { label: "Scheduled", color: "bg-blue-500", icon: Calendar },
    offline: { label: "Offline", color: "bg-gray-400", icon: WifiOff },
    ended: { label: "Ended", color: "bg-gray-400", icon: WifiOff },
}

const healthStatusConfig: Record<HealthStatus, { label: string; color: string }> = {
    healthy: { label: "Healthy", color: "text-green-500" },
    warning: { label: "Warning", color: "text-yellow-500" },
    critical: { label: "Critical", color: "text-red-500" },
}

function ChannelStatusCard({ channel }: ChannelStatusCardProps) {
    const streamStatus = streamStatusConfig[channel.stream_status]
    const healthStatus = healthStatusConfig[channel.health_status]
    const StatusIcon = streamStatus.icon

    const hasCriticalIssue = channel.health_status === "critical"

    return (
        <Card className={cn(
            "transition-all hover:shadow-md",
            hasCriticalIssue && "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20"
        )}>
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start gap-3 mb-3">
                    <div className="relative">
                        <Avatar className="h-10 w-10">
                            <AvatarImage src={channel.thumbnail_url || ""} />
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
                        <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {streamStatus.label}
                            </Badge>
                            <span className={cn("text-xs", healthStatus.color)}>
                                {healthStatus.label}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Users className="h-3.5 w-3.5" />
                        <span>{channel.subscriber_count.toLocaleString()}</span>
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
                        <span className="text-muted-foreground flex items-center gap-1">
                            <Gauge className="h-3 w-3" />
                            API Quota
                        </span>
                        <span className={cn(
                            channel.quota_percent >= 90 && "text-red-500",
                            channel.quota_percent >= 75 && channel.quota_percent < 90 && "text-yellow-500"
                        )}>
                            {channel.quota_percent.toFixed(0)}%
                        </span>
                    </div>
                    <Progress
                        value={channel.quota_percent}
                        className={cn(
                            "h-1.5",
                            channel.quota_percent >= 90 && "[&>div]:bg-red-500",
                            channel.quota_percent >= 75 && channel.quota_percent < 90 && "[&>div]:bg-yellow-500"
                        )}
                    />
                </div>

                {/* Next scheduled */}
                {channel.next_scheduled && (
                    <div className="text-xs text-muted-foreground border-t pt-2">
                        <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            Next: {channel.next_scheduled.title}
                        </span>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-3 pt-2 border-t">
                    <Link href={`/dashboard/accounts/${channel.account_id}`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full text-xs h-7">
                            Manage
                        </Button>
                    </Link>
                    <Link href={`/dashboard/analytics/channel/${channel.account_id}`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full text-xs h-7">
                            Analytics
                        </Button>
                    </Link>
                </div>
            </CardContent>
        </Card>
    )
}
