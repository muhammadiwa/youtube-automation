"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import {
    Play,
    Square,
    Radio,
    Users,
    Clock,
    Activity,
    Settings,
    RefreshCw,
    Copy,
    ExternalLink,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Wifi,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { streamsApi, type LiveEvent, type StreamHealth } from "@/lib/api/streams"
import { LiveChatPanel } from "@/components/dashboard/live-chat-panel"

function formatDuration(seconds: number): string {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }
    return `${mins}:${secs.toString().padStart(2, "0")}`
}

function HealthIndicator({ status }: { status: StreamHealth["status"] }) {
    const config = {
        healthy: { color: "bg-green-500", icon: CheckCircle, label: "Healthy" },
        warning: { color: "bg-yellow-500", icon: AlertTriangle, label: "Warning" },
        critical: { color: "bg-red-500", icon: XCircle, label: "Critical" },
        offline: { color: "bg-gray-500", icon: Wifi, label: "Offline" },
    }
    const { color, icon: Icon, label } = config[status]
    return (
        <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${color} ${status === "healthy" ? "animate-pulse" : ""}`} />
            <Icon className="h-4 w-4" />
            <span className="text-sm font-medium">{label}</span>
        </div>
    )
}

// ChatPanel is now replaced by LiveChatPanel component

export default function StreamControlPage() {
    const params = useParams()
    const router = useRouter()
    const eventId = params.id as string

    const [event, setEvent] = useState<LiveEvent | null>(null)
    const [health, setHealth] = useState<StreamHealth | null>(null)
    const [loading, setLoading] = useState(true)
    const [actionLoading, setActionLoading] = useState(false)
    const [duration, setDuration] = useState(0)
    const [copied, setCopied] = useState<string | null>(null)

    const loadEvent = useCallback(async () => {
        try {
            const data = await streamsApi.getEvent(eventId)
            setEvent(data)
        } catch (error) {
            console.error("Failed to load event:", error)
        } finally {
            setLoading(false)
        }
    }, [eventId])

    const loadHealth = useCallback(async () => {
        try {
            const data = await streamsApi.getHealth(eventId)
            setHealth(data)
        } catch (error) {
            console.error("Failed to load health:", error)
        }
    }, [eventId])

    useEffect(() => {
        loadEvent()
        loadHealth()
        // Poll health every 10 seconds
        const healthInterval = setInterval(loadHealth, 10000)
        return () => clearInterval(healthInterval)
    }, [loadEvent, loadHealth])

    // Duration timer
    useEffect(() => {
        if (event?.status !== "live") return
        const startTime = event.scheduled_start ? new Date(event.scheduled_start).getTime() : Date.now()
        const updateDuration = () => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000)
            setDuration(elapsed)
        }
        updateDuration()
        const interval = setInterval(updateDuration, 1000)
        return () => clearInterval(interval)
    }, [event?.status, event?.scheduled_start])

    const handleStartStream = async () => {
        try {
            setActionLoading(true)
            await streamsApi.startEvent(eventId)
            await loadEvent()
        } catch (error) {
            console.error("Failed to start stream:", error)
            alert("Failed to start stream")
        } finally {
            setActionLoading(false)
        }
    }

    const handleStopStream = async () => {
        if (!confirm("Are you sure you want to stop the stream?")) return
        try {
            setActionLoading(true)
            await streamsApi.stopEvent(eventId)
            await loadEvent()
        } catch (error) {
            console.error("Failed to stop stream:", error)
            alert("Failed to stop stream")
        } finally {
            setActionLoading(false)
        }
    }

    const copyToClipboard = (text: string, field: string) => {
        navigator.clipboard.writeText(text)
        setCopied(field)
        setTimeout(() => setCopied(null), 2000)
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Streams", href: "/dashboard/streams" },
                    { label: "Control Panel" },
                ]}
            >
                <div className="space-y-6">
                    <Skeleton className="h-10 w-64" />
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2">
                            <Skeleton className="aspect-video w-full" />
                        </div>
                        <Skeleton className="h-[400px]" />
                    </div>
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
                    { label: "Control Panel" },
                ]}
            >
                <div className="text-center py-12">
                    <h2 className="text-xl font-semibold mb-2">Stream not found</h2>
                    <p className="text-muted-foreground mb-4">
                        The stream you&apos;re looking for doesn&apos;t exist or has been deleted.
                    </p>
                    <Button onClick={() => router.push("/dashboard/streams")}>Back to Streams</Button>
                </div>
            </DashboardLayout>
        )
    }

    const isLive = event.status === "live"
    const isScheduled = event.status === "scheduled"

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: event.title },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-3">
                                {event.title}
                                {isLive && (
                                    <Badge className="bg-red-500 text-white animate-pulse">
                                        <Radio className="mr-1 h-3 w-3" />
                                        LIVE
                                    </Badge>
                                )}
                            </h1>
                            <p className="text-muted-foreground">
                                {isLive ? `Live for ${formatDuration(duration)}` : event.status}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {isScheduled && (
                            <Button
                                onClick={handleStartStream}
                                disabled={actionLoading}
                                className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                            >
                                <Play className="mr-2 h-4 w-4" />
                                {actionLoading ? "Starting..." : "Go Live"}
                            </Button>
                        )}
                        {isLive && (
                            <Button
                                variant="destructive"
                                onClick={handleStopStream}
                                disabled={actionLoading}
                            >
                                <Square className="mr-2 h-4 w-4" />
                                {actionLoading ? "Stopping..." : "End Stream"}
                            </Button>
                        )}
                        <Button
                            variant="outline"
                            onClick={() => router.push(`/dashboard/streams/${eventId}/health`)}
                        >
                            <Activity className="mr-2 h-4 w-4" />
                            Health
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => router.push(`/dashboard/streams/${eventId}/simulcast`)}
                        >
                            <Settings className="mr-2 h-4 w-4" />
                            Simulcast
                        </Button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Video Preview & Controls */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Video Preview */}
                        <Card className="border-0 shadow-lg overflow-hidden">
                            <div className="aspect-video bg-black relative">
                                {event.broadcast_id ? (
                                    <iframe
                                        src={`https://www.youtube.com/embed/${event.broadcast_id}?autoplay=0`}
                                        className="w-full h-full"
                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                        allowFullScreen
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-white">
                                        <div className="text-center">
                                            <Radio className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                            <p>Preview not available</p>
                                        </div>
                                    </div>
                                )}
                                {isLive && (
                                    <div className="absolute top-4 left-4 flex items-center gap-4">
                                        <Badge className="bg-red-500 text-white">
                                            <Radio className="mr-1 h-3 w-3 animate-pulse" />
                                            LIVE
                                        </Badge>
                                        <Badge variant="secondary" className="bg-black/70 text-white">
                                            <Users className="mr-1 h-3 w-3" />
                                            {event.viewer_count?.toLocaleString() || 0}
                                        </Badge>
                                        <Badge variant="secondary" className="bg-black/70 text-white">
                                            <Clock className="mr-1 h-3 w-3" />
                                            {formatDuration(duration)}
                                        </Badge>
                                    </div>
                                )}
                            </div>
                        </Card>

                        {/* Stream Info Tabs */}
                        <Tabs defaultValue="health" className="w-full">
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="health">Stream Health</TabsTrigger>
                                <TabsTrigger value="settings">Stream Settings</TabsTrigger>
                            </TabsList>
                            <TabsContent value="health">
                                <Card className="border-0 shadow-lg">
                                    <CardHeader className="pb-2">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <Activity className="h-5 w-5" />
                                                Health Metrics
                                            </CardTitle>
                                            <Button variant="ghost" size="sm" onClick={loadHealth}>
                                                <RefreshCw className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {health ? (
                                            <div className="space-y-4">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm text-muted-foreground">Status</span>
                                                    <HealthIndicator status={health.status} />
                                                </div>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div className="p-3 bg-muted rounded-lg">
                                                        <p className="text-xs text-muted-foreground">Bitrate</p>
                                                        <p className="text-lg font-semibold">
                                                            {(health.bitrate / 1000).toFixed(1)} Kbps
                                                        </p>
                                                    </div>
                                                    <div className="p-3 bg-muted rounded-lg">
                                                        <p className="text-xs text-muted-foreground">Frame Rate</p>
                                                        <p className="text-lg font-semibold">{health.fps} fps</p>
                                                    </div>
                                                    <div className="p-3 bg-muted rounded-lg">
                                                        <p className="text-xs text-muted-foreground">Resolution</p>
                                                        <p className="text-lg font-semibold">{health.resolution}</p>
                                                    </div>
                                                    <div className="p-3 bg-muted rounded-lg">
                                                        <p className="text-xs text-muted-foreground">Dropped Frames</p>
                                                        <p className="text-lg font-semibold">{health.dropped_frames}</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex items-center justify-between text-sm">
                                                        <span className="text-muted-foreground">Connection Quality</span>
                                                        <span>{health.connection_quality}%</span>
                                                    </div>
                                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full transition-all ${health.connection_quality > 80
                                                                ? "bg-green-500"
                                                                : health.connection_quality > 50
                                                                    ? "bg-yellow-500"
                                                                    : "bg-red-500"
                                                                }`}
                                                            style={{ width: `${health.connection_quality}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-muted-foreground text-center py-4">
                                                Health data not available
                                            </p>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="settings">
                                <Card className="border-0 shadow-lg">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg">Stream Settings</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        {event.rtmp_url && (
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">RTMP URL</label>
                                                <div className="flex gap-2">
                                                    <Input value={event.rtmp_url} readOnly className="font-mono text-sm" />
                                                    <Button
                                                        variant="outline"
                                                        size="icon"
                                                        onClick={() => copyToClipboard(event.rtmp_url!, "rtmp")}
                                                    >
                                                        {copied === "rtmp" ? (
                                                            <CheckCircle className="h-4 w-4 text-green-500" />
                                                        ) : (
                                                            <Copy className="h-4 w-4" />
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>
                                        )}
                                        {event.stream_key && (
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">Stream Key</label>
                                                <div className="flex gap-2">
                                                    <Input
                                                        type="password"
                                                        value={event.stream_key}
                                                        readOnly
                                                        className="font-mono text-sm"
                                                    />
                                                    <Button
                                                        variant="outline"
                                                        size="icon"
                                                        onClick={() => copyToClipboard(event.stream_key!, "key")}
                                                    >
                                                        {copied === "key" ? (
                                                            <CheckCircle className="h-4 w-4 text-green-500" />
                                                        ) : (
                                                            <Copy className="h-4 w-4" />
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>
                                        )}
                                        <div className="grid grid-cols-2 gap-4 pt-2">
                                            <div>
                                                <p className="text-sm text-muted-foreground">Privacy</p>
                                                <p className="font-medium capitalize">{event.privacy_status}</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-muted-foreground">DVR</p>
                                                <p className="font-medium">{event.enable_dvr ? "Enabled" : "Disabled"}</p>
                                            </div>
                                        </div>
                                        {event.broadcast_id && (
                                            <Button
                                                variant="outline"
                                                className="w-full"
                                                onClick={() =>
                                                    window.open(
                                                        `https://www.youtube.com/watch?v=${event.broadcast_id}`,
                                                        "_blank"
                                                    )
                                                }
                                            >
                                                <ExternalLink className="mr-2 h-4 w-4" />
                                                View on YouTube
                                            </Button>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </div>

                    {/* Chat Panel */}
                    <div className="lg:col-span-1">
                        <LiveChatPanel eventId={eventId} isLive={isLive} />
                    </div>
                </div>
            </div>
        </DashboardLayout>
    )
}
