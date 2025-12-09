"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import {
    Activity,
    Wifi,
    WifiOff,
    AlertTriangle,
    CheckCircle,
    XCircle,
    RefreshCw,
    ArrowLeft,
    Users,
    Clock,
    TrendingUp,
    TrendingDown,
    Volume2,
    VolumeX,
    Radio,
    Zap,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    Line,
    LineChart,
} from "recharts"
import { useTheme } from "next-themes"
import {
    streamsApi,
    type LiveEvent,
    type StreamHealth,
    type StreamHealthHistory,
    type StreamAlert,
} from "@/lib/api/streams"
import { useToast } from "@/components/ui/toast"
import { getAlertTypeLabel } from "@/hooks/use-stream-alerts"

// ============ Helper Functions ============
function formatBitrate(bitrate: number): string {
    if (bitrate >= 1000) {
        return `${(bitrate / 1000).toFixed(1)} Mbps`
    }
    return `${bitrate.toFixed(0)} Kbps`
}

function formatTime(dateString: string): string {
    const date = new Date(dateString)
    return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
    })
}

function getStatusConfig(status: StreamHealth["status"]) {
    const configs = {
        healthy: {
            color: "bg-green-500",
            textColor: "text-green-500",
            icon: CheckCircle,
            label: "Healthy",
            description: "Stream is running optimally",
        },
        warning: {
            color: "bg-yellow-500",
            textColor: "text-yellow-500",
            icon: AlertTriangle,
            label: "Warning",
            description: "Some metrics need attention",
        },
        critical: {
            color: "bg-red-500",
            textColor: "text-red-500",
            icon: XCircle,
            label: "Critical",
            description: "Immediate action required",
        },
        offline: {
            color: "bg-gray-500",
            textColor: "text-gray-500",
            icon: WifiOff,
            label: "Offline",
            description: "Stream is not active",
        },
    }
    return configs[status]
}

// ============ Components ============
function HealthStatusCard({ health }: { health: StreamHealth }) {
    const config = getStatusConfig(health.status)
    const Icon = config.icon

    return (
        <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-full ${config.color}/10`}>
                            <Icon className={`h-8 w-8 ${config.textColor}`} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold">{config.label}</h3>
                            <p className="text-muted-foreground">{config.description}</p>
                        </div>
                    </div>
                    <div className={`w-4 h-4 rounded-full ${config.color} ${health.status === "healthy" ? "animate-pulse" : ""}`} />
                </div>
            </CardContent>
        </Card>
    )
}

function MetricCard({
    title,
    value,
    unit,
    icon: Icon,
    trend,
    status,
}: {
    title: string
    value: string | number
    unit?: string
    icon: React.ElementType
    trend?: "up" | "down" | "stable"
    status?: "good" | "warning" | "critical"
}) {
    const statusColors = {
        good: "text-green-500",
        warning: "text-yellow-500",
        critical: "text-red-500",
    }

    return (
        <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">{title}</span>
                    <Icon className={`h-4 w-4 ${status ? statusColors[status] : "text-muted-foreground"}`} />
                </div>
                <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold">{value}</span>
                    {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
                    {trend && (
                        <span className={trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-muted-foreground"}>
                            {trend === "up" ? <TrendingUp className="h-4 w-4" /> : trend === "down" ? <TrendingDown className="h-4 w-4" /> : null}
                        </span>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}


function ConnectionQualityMeter({ quality }: { quality: number }) {
    const getQualityColor = (q: number) => {
        if (q >= 80) return "bg-green-500"
        if (q >= 50) return "bg-yellow-500"
        return "bg-red-500"
    }

    const getQualityLabel = (q: number) => {
        if (q >= 80) return "Excellent"
        if (q >= 60) return "Good"
        if (q >= 40) return "Fair"
        return "Poor"
    }

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Wifi className="h-5 w-5" />
                    Connection Quality
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-3xl font-bold">{quality.toFixed(0)}%</span>
                        <Badge variant={quality >= 80 ? "default" : quality >= 50 ? "secondary" : "destructive"}>
                            {getQualityLabel(quality)}
                        </Badge>
                    </div>
                    <div className="h-4 bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${getQualityColor(quality)}`}
                            style={{ width: `${quality}%` }}
                        />
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Poor</span>
                        <span>Fair</span>
                        <span>Good</span>
                        <span>Excellent</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function DroppedFramesIndicator({ current, history }: { current: number; history: StreamHealthHistory[] }) {
    const { theme } = useTheme()
    const isDark = theme === "dark"

    const recentDrops = history.slice(-10).reduce((sum, h) => sum + h.dropped_frames, 0)
    const status = recentDrops > 20 ? "critical" : recentDrops > 10 ? "warning" : "good"

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Dropped Frames
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <span className="text-3xl font-bold">{current}</span>
                        <span className="text-sm text-muted-foreground ml-2">current</span>
                    </div>
                    <Badge variant={status === "good" ? "default" : status === "warning" ? "secondary" : "destructive"}>
                        {recentDrops} in last 10 min
                    </Badge>
                </div>
                <ResponsiveContainer width="100%" height={80}>
                    <AreaChart data={history.slice(-20)}>
                        <defs>
                            <linearGradient id="droppedGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <Area
                            type="monotone"
                            dataKey="dropped_frames"
                            stroke="#ef4444"
                            strokeWidth={2}
                            fill="url(#droppedGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}


function BitrateChart({ history, timeRange }: { history: StreamHealthHistory[]; timeRange: string }) {
    const { theme } = useTheme()
    const isDark = theme === "dark"

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border rounded-xl p-3 shadow-xl">
                    <p className="font-semibold text-sm mb-2">{formatTime(label)}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                            <div
                                className="h-2.5 w-2.5 rounded-full"
                                style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-muted-foreground capitalize">{entry.name}:</span>
                            <span className="font-medium">
                                {entry.name === "bitrate" ? formatBitrate(entry.value) : entry.value}
                            </span>
                        </div>
                    ))}
                </div>
            )
        }
        return null
    }

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Bitrate Over Time
                    </CardTitle>
                    <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full bg-blue-500" />
                            <span className="text-muted-foreground">Bitrate</span>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={history}>
                        <defs>
                            <linearGradient id="bitrateGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke={isDark ? "#374151" : "#e5e7eb"}
                            vertical={false}
                        />
                        <XAxis
                            dataKey="timestamp"
                            stroke={isDark ? "#6b7280" : "#9ca3af"}
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={formatTime}
                        />
                        <YAxis
                            stroke={isDark ? "#6b7280" : "#9ca3af"}
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${(value / 1000).toFixed(1)}M`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="bitrate"
                            stroke="#3b82f6"
                            strokeWidth={2.5}
                            fill="url(#bitrateGradient)"
                            dot={false}
                            activeDot={{ r: 6, strokeWidth: 0 }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}

function ViewerCountChart({ history }: { history: StreamHealthHistory[] }) {
    const { theme } = useTheme()
    const isDark = theme === "dark"

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border rounded-xl p-3 shadow-xl">
                    <p className="font-semibold text-sm mb-2">{formatTime(label)}</p>
                    <div className="flex items-center gap-2 text-sm">
                        <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
                        <span className="text-muted-foreground">Viewers:</span>
                        <span className="font-medium">{payload[0].value.toLocaleString()}</span>
                    </div>
                </div>
            )
        }
        return null
    }

    const currentViewers = history.length > 0 ? history[history.length - 1].viewer_count : 0
    const peakViewers = Math.max(...history.map((h) => h.viewer_count), 0)

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Viewer Count
                    </CardTitle>
                    <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Current:</span>
                            <span className="font-semibold">{currentViewers.toLocaleString()}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Peak:</span>
                            <span className="font-semibold">{peakViewers.toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={history}>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke={isDark ? "#374151" : "#e5e7eb"}
                            vertical={false}
                        />
                        <XAxis
                            dataKey="timestamp"
                            stroke={isDark ? "#6b7280" : "#9ca3af"}
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={formatTime}
                        />
                        <YAxis
                            stroke={isDark ? "#6b7280" : "#9ca3af"}
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Line
                            type="monotone"
                            dataKey="viewer_count"
                            stroke="#10b981"
                            strokeWidth={2.5}
                            dot={false}
                            activeDot={{ r: 6, strokeWidth: 0, fill: "#10b981" }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}


function AlertsPanel({
    alerts,
    onAcknowledge,
    soundEnabled,
    onSoundToggle,
}: {
    alerts: StreamAlert[]
    onAcknowledge: (alertId: string) => void
    soundEnabled: boolean
    onSoundToggle: (enabled: boolean) => void
}) {
    const getAlertIcon = (type: StreamAlert["type"]) => {
        switch (type) {
            case "health_warning":
                return <AlertTriangle className="h-4 w-4 text-yellow-500" />
            case "health_critical":
                return <XCircle className="h-4 w-4 text-red-500" />
            case "reconnection":
                return <RefreshCw className="h-4 w-4 text-blue-500" />
            case "failover":
                return <Zap className="h-4 w-4 text-orange-500" />
            case "disconnection":
                return <WifiOff className="h-4 w-4 text-red-500" />
            default:
                return <Activity className="h-4 w-4" />
        }
    }

    const getSeverityBadge = (severity: StreamAlert["severity"]) => {
        switch (severity) {
            case "error":
                return <Badge variant="destructive">Error</Badge>
            case "warning":
                return <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-500">Warning</Badge>
            default:
                return <Badge variant="outline">Info</Badge>
        }
    }

    const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged)

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5" />
                        Alerts
                        {unacknowledgedAlerts.length > 0 && (
                            <Badge variant="destructive" className="ml-2">
                                {unacknowledgedAlerts.length}
                            </Badge>
                        )}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                        <Label htmlFor="sound-toggle" className="text-sm text-muted-foreground">
                            Sound
                        </Label>
                        <Switch
                            id="sound-toggle"
                            checked={soundEnabled}
                            onCheckedChange={onSoundToggle}
                        />
                        {soundEnabled ? (
                            <Volume2 className="h-4 w-4 text-muted-foreground" />
                        ) : (
                            <VolumeX className="h-4 w-4 text-muted-foreground" />
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {alerts.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                        <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                        <p>No alerts - stream is healthy</p>
                    </div>
                ) : (
                    <div className="space-y-3 max-h-[300px] overflow-y-auto">
                        {alerts.map((alert) => (
                            <div
                                key={alert.id}
                                className={`p-3 rounded-lg border ${alert.acknowledged ? "bg-muted/50 opacity-60" : "bg-muted"
                                    }`}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex items-start gap-3">
                                        {getAlertIcon(alert.type)}
                                        <div className="flex-1">
                                            <p className="text-sm font-medium">{alert.message}</p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {new Date(alert.created_at).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {getSeverityBadge(alert.severity)}
                                        {!alert.acknowledged && (
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onAcknowledge(alert.id)}
                                            >
                                                Dismiss
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function ReconnectionBanner({ health, alerts }: { health: StreamHealth; alerts: StreamAlert[] }) {
    const reconnectionAlert = alerts.find(
        (a) => a.type === "reconnection" && !a.acknowledged
    )
    const failoverAlert = alerts.find(
        (a) => a.type === "failover" && !a.acknowledged
    )

    if (!reconnectionAlert && !failoverAlert && health.status !== "critical") {
        return null
    }

    if (failoverAlert) {
        return (
            <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4 flex items-center gap-3">
                <Zap className="h-5 w-5 text-orange-500 animate-pulse" />
                <div className="flex-1">
                    <p className="font-medium text-orange-500">Failover Active</p>
                    <p className="text-sm text-muted-foreground">
                        Stream has switched to backup source
                    </p>
                </div>
            </div>
        )
    }

    if (reconnectionAlert) {
        return (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex items-center gap-3">
                <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
                <div className="flex-1">
                    <p className="font-medium text-blue-500">Reconnecting...</p>
                    <p className="text-sm text-muted-foreground">
                        Attempting to restore stream connection
                    </p>
                </div>
            </div>
        )
    }

    if (health.status === "critical") {
        return (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3">
                <XCircle className="h-5 w-5 text-red-500" />
                <div className="flex-1">
                    <p className="font-medium text-red-500">Critical Health Issue</p>
                    <p className="text-sm text-muted-foreground">
                        Stream health is critical - immediate attention required
                    </p>
                </div>
            </div>
        )
    }

    return null
}


// ============ Main Component ============
export default function StreamHealthPage() {
    const params = useParams()
    const router = useRouter()
    const eventId = params.id as string
    const { addToast } = useToast()

    const [event, setEvent] = useState<LiveEvent | null>(null)
    const [health, setHealth] = useState<StreamHealth | null>(null)
    const [healthHistory, setHealthHistory] = useState<StreamHealthHistory[]>([])
    const [alerts, setAlerts] = useState<StreamAlert[]>([])
    const [loading, setLoading] = useState(true)
    const [timeRange, setTimeRange] = useState("30m")
    const [soundEnabled, setSoundEnabled] = useState(false)
    const [autoRefresh, setAutoRefresh] = useState(true)

    const audioRef = useRef<HTMLAudioElement | null>(null)
    const previousAlertIds = useRef<Set<string>>(new Set())

    // Load event data
    const loadEvent = useCallback(async () => {
        try {
            const data = await streamsApi.getEvent(eventId)
            setEvent(data)
        } catch (error) {
            console.error("Failed to load event:", error)
        }
    }, [eventId])

    // Load health data
    const loadHealth = useCallback(async () => {
        try {
            const [healthData, historyData, alertsData] = await Promise.all([
                streamsApi.getHealth(eventId),
                streamsApi.getHealthHistory(eventId, timeRange),
                streamsApi.getAlerts(eventId),
            ])
            setHealth(healthData)
            setHealthHistory(historyData)

            // Check for new alerts and show toast notifications
            const newAlerts = alertsData.filter(
                (a) => !a.acknowledged && !previousAlertIds.current.has(a.id)
            )

            newAlerts.forEach((alert) => {
                // Show toast notification for new alerts
                addToast({
                    type: alert.severity === "error" ? "error" : alert.severity === "warning" ? "warning" : "info",
                    title: getAlertTypeLabel(alert.type),
                    description: alert.message,
                    duration: 8000,
                })

                // Play sound if enabled
                if (soundEnabled && audioRef.current) {
                    audioRef.current.play().catch(() => { })
                }

                // Track this alert as seen
                previousAlertIds.current.add(alert.id)
            })

            setAlerts(alertsData)
        } catch (error) {
            console.error("Failed to load health:", error)
        } finally {
            setLoading(false)
        }
    }, [eventId, timeRange, soundEnabled, addToast])

    // Initial load
    useEffect(() => {
        loadEvent()
        loadHealth()
    }, [loadEvent, loadHealth])

    // Auto-refresh every 10 seconds
    useEffect(() => {
        if (!autoRefresh) return
        const interval = setInterval(loadHealth, 10000)
        return () => clearInterval(interval)
    }, [autoRefresh, loadHealth])

    // Handle alert acknowledgment
    const handleAcknowledgeAlert = async (alertId: string) => {
        try {
            await streamsApi.acknowledgeAlert(eventId, alertId)
            setAlerts((prev) =>
                prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
            )
        } catch (error) {
            console.error("Failed to acknowledge alert:", error)
        }
    }

    // Get metric status
    const getBitrateStatus = (bitrate: number): "good" | "warning" | "critical" => {
        if (bitrate >= 4000) return "good"
        if (bitrate >= 2000) return "warning"
        return "critical"
    }

    const getFpsStatus = (fps: number): "good" | "warning" | "critical" => {
        if (fps >= 28) return "good"
        if (fps >= 24) return "warning"
        return "critical"
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Streams", href: "/dashboard/streams" },
                    { label: "Health Monitoring" },
                ]}
            >
                <div className="space-y-6">
                    <Skeleton className="h-10 w-64" />
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                    <Skeleton className="h-[300px]" />
                </div>
            </DashboardLayout>
        )
    }

    if (!event) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Streams", href: "/dashboard/streams" },
                    { label: "Health Monitoring" },
                ]}
            >
                <div className="text-center py-12">
                    <h2 className="text-xl font-semibold mb-2">Stream not found</h2>
                    <p className="text-muted-foreground mb-4">
                        The stream you&apos;re looking for doesn&apos;t exist.
                    </p>
                    <Button onClick={() => router.push("/dashboard/streams")}>
                        Back to Streams
                    </Button>
                </div>
            </DashboardLayout>
        )
    }

    const isLive = event.status === "live"

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: event.title, href: `/dashboard/streams/${eventId}/control` },
                { label: "Health" },
            ]}
        >
            {/* Hidden audio element for alert sounds */}
            <audio ref={audioRef} src="/sounds/alert.mp3" preload="auto" />

            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push(`/dashboard/streams/${eventId}/control`)}
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-3">
                                Health Monitoring
                                {isLive && (
                                    <Badge className="bg-red-500 text-white animate-pulse">
                                        <Radio className="mr-1 h-3 w-3" />
                                        LIVE
                                    </Badge>
                                )}
                            </h1>
                            <p className="text-muted-foreground">{event.title}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Label htmlFor="auto-refresh" className="text-sm">
                                Auto-refresh
                            </Label>
                            <Switch
                                id="auto-refresh"
                                checked={autoRefresh}
                                onCheckedChange={setAutoRefresh}
                            />
                        </div>
                        <Select value={timeRange} onValueChange={setTimeRange}>
                            <SelectTrigger className="w-[120px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="15m">Last 15 min</SelectItem>
                                <SelectItem value="30m">Last 30 min</SelectItem>
                                <SelectItem value="1h">Last 1 hour</SelectItem>
                                <SelectItem value="3h">Last 3 hours</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button variant="outline" onClick={loadHealth}>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Refresh
                        </Button>
                    </div>
                </div>

                {/* Reconnection/Failover Banner */}
                {health && <ReconnectionBanner health={health} alerts={alerts} />}

                {/* Status Overview */}
                {health && <HealthStatusCard health={health} />}

                {/* Metrics Grid */}
                {health && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <MetricCard
                            title="Bitrate"
                            value={formatBitrate(health.bitrate)}
                            icon={Activity}
                            status={getBitrateStatus(health.bitrate)}
                        />
                        <MetricCard
                            title="Frame Rate"
                            value={health.fps.toFixed(1)}
                            unit="fps"
                            icon={Clock}
                            status={getFpsStatus(health.fps)}
                        />
                        <MetricCard
                            title="Resolution"
                            value={health.resolution}
                            icon={TrendingUp}
                        />
                        <MetricCard
                            title="Dropped Frames"
                            value={health.dropped_frames}
                            icon={Zap}
                            status={health.dropped_frames > 10 ? "critical" : health.dropped_frames > 5 ? "warning" : "good"}
                        />
                    </div>
                )}

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <BitrateChart history={healthHistory} timeRange={timeRange} />
                    {health && (
                        <ConnectionQualityMeter quality={health.connection_quality} />
                    )}
                </div>

                {/* Second Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ViewerCountChart history={healthHistory} />
                    {health && (
                        <DroppedFramesIndicator
                            current={health.dropped_frames}
                            history={healthHistory}
                        />
                    )}
                </div>

                {/* Alerts Panel */}
                <AlertsPanel
                    alerts={alerts}
                    onAcknowledge={handleAcknowledgeAlert}
                    soundEnabled={soundEnabled}
                    onSoundToggle={setSoundEnabled}
                />
            </div>
        </DashboardLayout>
    )
}
