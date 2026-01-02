"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import {
    Play,
    Square,
    RotateCcw,
    Activity,
    Radio,
    Clock,
    RefreshCw,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Wifi,
    WifiOff,
    Repeat,
    Infinity,
    Cpu,
    HardDrive,
    Gauge,
    Film,
    Settings,
    Copy,
    Eye,
    EyeOff,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { useToast } from "@/components/ui/toast"
import {
    streamJobsApi,
    type StreamJob,
    type StreamJobHealth,
    type StreamJobStatus,
} from "@/lib/api/stream-jobs"

interface StreamJobControlPanelProps {
    job: StreamJob
    onUpdate?: () => void
}

function formatDuration(seconds: number): string {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }
    return `${mins}:${secs.toString().padStart(2, "0")}`
}

function HealthIndicator({ health }: { health: StreamJobHealth | null }) {
    if (!health) {
        return (
            <div className="flex items-center gap-2 text-muted-foreground">
                <div className="w-3 h-3 rounded-full bg-gray-400" />
                <span className="text-sm">No data</span>
            </div>
        )
    }

    const isHealthy = health.isHealthy
    const hasAlert = health.alertType !== null

    if (!isHealthy || health.alertType === "critical") {
        return (
            <div className="flex items-center gap-2 text-red-500">
                <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                <XCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Critical</span>
            </div>
        )
    }

    if (hasAlert && health.alertType === "warning") {
        return (
            <div className="flex items-center gap-2 text-yellow-500">
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">Warning</span>
            </div>
        )
    }

    return (
        <div className="flex items-center gap-2 text-green-500">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Healthy</span>
        </div>
    )
}

function ConnectionStatus({ connected }: { connected: boolean }) {
    return (
        <div className={`flex items-center gap-1 text-xs ${connected ? "text-green-500" : "text-red-500"}`}>
            {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            <span>{connected ? "Live" : "Disconnected"}</span>
        </div>
    )
}

export function StreamJobControlPanel({ job, onUpdate }: StreamJobControlPanelProps) {
    const { addToast } = useToast()
    const wsRef = useRef<WebSocket | null>(null)
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

    const [currentJob, setCurrentJob] = useState<StreamJob>(job)
    const [health, setHealth] = useState<StreamJobHealth | null>(null)
    const [healthHistory, setHealthHistory] = useState<StreamJobHealth[]>([])
    const [wsConnected, setWsConnected] = useState(false)
    const [loading, setLoading] = useState(false)
    const [duration, setDuration] = useState(0)
    const [showStreamKey, setShowStreamKey] = useState(false)
    const [copied, setCopied] = useState<string | null>(null)

    // Dialogs
    const [stopConfirm, setStopConfirm] = useState(false)
    const [restartConfirm, setRestartConfirm] = useState(false)

    // Update job when prop changes
    useEffect(() => {
        setCurrentJob(job)
    }, [job])

    // Duration timer
    useEffect(() => {
        if (currentJob.status !== "running") {
            setDuration(currentJob.currentDurationSeconds)
            return
        }

        const startTime = currentJob.actualStartAt
            ? new Date(currentJob.actualStartAt).getTime()
            : Date.now()

        const updateDuration = () => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000)
            setDuration(elapsed)
        }

        updateDuration()
        const interval = setInterval(updateDuration, 1000)
        return () => clearInterval(interval)
    }, [currentJob.status, currentJob.actualStartAt, currentJob.currentDurationSeconds])

    // WebSocket connection for real-time health
    const connectWebSocket = useCallback(() => {
        if (currentJob.status !== "running" && currentJob.status !== "starting") {
            return
        }

        // Don't reconnect if already connected
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            return
        }

        // Clean up existing connection
        if (wsRef.current) {
            wsRef.current.close()
        }

        const ws = streamJobsApi.connectToHealthWebSocket(currentJob.id, {
            onMessage: (healthData) => {
                setHealth(healthData)
                setHealthHistory((prev) => [healthData, ...prev.slice(0, 19)])
            },
            onStreamEnded: (status) => {
                addToast({
                    type: "info",
                    title: "Stream Ended",
                    description: `Stream status: ${status}`,
                })
                onUpdate?.()
            },
            onError: () => {
                setWsConnected(false)
            },
            onClose: () => {
                setWsConnected(false)
                // Attempt reconnect after 5 seconds if still running
                reconnectTimeoutRef.current = setTimeout(() => {
                    if (currentJob.status === "running") {
                        connectWebSocket()
                    }
                }, 5000)
            },
        })

        ws.onopen = () => {
            setWsConnected(true)
        }

        wsRef.current = ws
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentJob.id, addToast, onUpdate])

    // Connect WebSocket when job starts running
    useEffect(() => {
        if (currentJob.status === "running" || currentJob.status === "starting") {
            connectWebSocket()
        } else {
            // Close WebSocket when not running
            if (wsRef.current) {
                wsRef.current.close()
                wsRef.current = null
            }
            setWsConnected(false)
        }

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current)
            }
        }
    }, [currentJob.status, connectWebSocket])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close()
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current)
            }
        }
    }, [])

    // Fallback: Poll health data only if WebSocket is not connected
    useEffect(() => {
        if (currentJob.status !== "running") return

        // If WebSocket is connected, no need to poll
        if (wsConnected) return

        const loadHealth = async () => {
            try {
                const latestHealth = await streamJobsApi.getHealthLatest(currentJob.id)
                setHealth(latestHealth)
            } catch {
                // Health data may not exist yet
            }
        }

        // Load immediately as fallback
        loadHealth()

        // Poll every 30 seconds as fallback (WebSocket should handle realtime)
        const interval = setInterval(loadHealth, 30000)

        return () => clearInterval(interval)
    }, [currentJob.id, currentJob.status, wsConnected])

    // Poll for status updates when stopping or starting
    useEffect(() => {
        if (currentJob.status !== "stopping" && currentJob.status !== "starting") {
            return
        }

        const pollStatus = async () => {
            try {
                const updated = await streamJobsApi.getStreamJob(currentJob.id)
                if (updated.status !== currentJob.status) {
                    setCurrentJob(updated)
                    setLoading(false)

                    // Show toast based on new status
                    if (updated.status === "stopped") {
                        addToast({ type: "success", title: "Stopped", description: "Stream stopped successfully" })
                    } else if (updated.status === "running") {
                        addToast({ type: "success", title: "Started", description: "Stream is now live" })
                    } else if (updated.status === "failed") {
                        addToast({ type: "error", title: "Failed", description: updated.lastError || "Stream failed to start" })
                    }

                    onUpdate?.()
                }
            } catch {
                // Ignore errors during polling
            }
        }

        // Poll every 1 second for faster feedback
        const interval = setInterval(pollStatus, 1000)
        return () => clearInterval(interval)
    }, [currentJob.id, currentJob.status, onUpdate, addToast])

    // Actions
    const handleStart = async () => {
        try {
            setLoading(true)
            const updated = await streamJobsApi.startStreamJob(currentJob.id)
            setCurrentJob(updated)
            addToast({ type: "success", title: "Started", description: "Stream started successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to start stream",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleStop = async () => {
        try {
            setLoading(true)
            const updated = await streamJobsApi.stopStreamJob(currentJob.id)
            setCurrentJob(updated)
            // Don't show success toast yet - wait for polling to confirm stopped status
            // Toast will be shown when status changes from "stopping" to "stopped"
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to stop stream",
            })
            setLoading(false)
        }
        // Don't set loading to false here - let polling handle it
    }

    const handleRestart = async () => {
        try {
            setLoading(true)
            const updated = await streamJobsApi.restartStreamJob(currentJob.id)
            setCurrentJob(updated)
            addToast({ type: "success", title: "Restarted", description: "Stream restarted successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to restart stream",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleAcknowledgeAlert = async () => {
        if (!health?.id || health.isAlertAcknowledged) return
        try {
            const updated = await streamJobsApi.acknowledgeAlert(health.id)
            setHealth(updated)
            addToast({ type: "success", title: "Alert Acknowledged" })
        } catch {
            addToast({ type: "error", title: "Failed to acknowledge alert" })
        }
    }

    const copyToClipboard = (text: string, field: string) => {
        navigator.clipboard.writeText(text)
        setCopied(field)
        setTimeout(() => setCopied(null), 2000)
    }

    const getStatusBadge = (status: StreamJobStatus) => {
        switch (status) {
            case "running":
                return (
                    <Badge className="bg-red-500 text-white animate-pulse">
                        <Radio className="mr-1 h-3 w-3" />
                        LIVE
                    </Badge>
                )
            case "starting":
                return (
                    <Badge className="bg-yellow-500 text-white">
                        <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                        Starting
                    </Badge>
                )
            case "stopping":
                return (
                    <Badge className="bg-orange-500 text-white">
                        <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                        Stopping
                    </Badge>
                )
            case "scheduled":
                return (
                    <Badge className="bg-blue-500 text-white">
                        <Clock className="mr-1 h-3 w-3" />
                        Scheduled
                    </Badge>
                )
            case "pending":
                return <Badge variant="secondary"><Clock className="mr-1 h-3 w-3" />Pending</Badge>
            case "stopped":
                return <Badge variant="secondary"><Square className="mr-1 h-3 w-3" />Stopped</Badge>
            case "completed":
                return <Badge variant="outline" className="text-green-600 border-green-600">Completed</Badge>
            case "failed":
                return <Badge variant="destructive"><AlertTriangle className="mr-1 h-3 w-3" />Failed</Badge>
            case "cancelled":
                return <Badge variant="outline" className="text-muted-foreground">Cancelled</Badge>
            default:
                return <Badge variant="outline">{status}</Badge>
        }
    }

    const canStart = ["pending", "scheduled", "stopped", "failed"].includes(currentJob.status)
    const canStop = ["starting", "running"].includes(currentJob.status)
    const isRunning = currentJob.status === "running"

    return (
        <div className="space-y-6">
            {/* Header with Status and Controls */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-3">
                            {currentJob.title}
                            {getStatusBadge(currentJob.status)}
                            <Badge variant="secondary" className="text-xs">Video-to-Live</Badge>
                        </h2>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                            {isRunning && (
                                <>
                                    <span className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {formatDuration(duration)}
                                    </span>
                                    <ConnectionStatus connected={wsConnected} />
                                </>
                            )}
                            {currentJob.status === "scheduled" && currentJob.timeUntilStart && (
                                <span>Starts in {formatDuration(currentJob.timeUntilStart)}</span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex gap-2">
                    {canStart && (
                        <Button
                            onClick={handleStart}
                            disabled={loading}
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                        >
                            <Play className="mr-2 h-4 w-4" />
                            {loading ? "Starting..." : "Start Stream"}
                        </Button>
                    )}
                    {canStop && (
                        <Button
                            variant="destructive"
                            onClick={() => setStopConfirm(true)}
                            disabled={loading}
                        >
                            <Square className="mr-2 h-4 w-4" />
                            {loading ? "Stopping..." : "Stop Stream"}
                        </Button>
                    )}
                    {(isRunning || currentJob.status === "failed") && (
                        <Button
                            variant="outline"
                            onClick={() => setRestartConfirm(true)}
                            disabled={loading}
                        >
                            <RotateCcw className="mr-2 h-4 w-4" />
                            Restart
                        </Button>
                    )}
                </div>
            </div>

            {/* Playlist Progress */}
            {currentJob.totalPlaylistItems > 1 && (
                <Card className="border-0 shadow-lg">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Film className="h-5 w-5" />
                            Playlist Progress
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Current Video</span>
                                <span className="font-semibold">
                                    {currentJob.currentPlaylistIndex + 1} / {currentJob.totalPlaylistItems}
                                </span>
                            </div>
                            <Progress
                                value={currentJob.playlistProgress}
                                className="h-2"
                            />
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Loop Progress */}
            {(currentJob.loopMode === "count" || currentJob.loopMode === "infinite") && (
                <Card className="border-0 shadow-lg">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg flex items-center gap-2">
                            {currentJob.loopMode === "infinite" ? (
                                <Infinity className="h-5 w-5" />
                            ) : (
                                <Repeat className="h-5 w-5" />
                            )}
                            Loop Progress
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Current Loop</span>
                                <span className="font-semibold">
                                    {currentJob.currentLoop}
                                    {currentJob.loopMode === "count" && currentJob.loopCount && (
                                        <span className="text-muted-foreground"> / {currentJob.loopCount}</span>
                                    )}
                                    {currentJob.loopMode === "infinite" && (
                                        <span className="text-muted-foreground"> (24/7)</span>
                                    )}
                                </span>
                            </div>
                            {currentJob.loopMode === "count" && currentJob.loopCount && (
                                <Progress
                                    value={(currentJob.currentLoop / currentJob.loopCount) * 100}
                                    className="h-2"
                                />
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Auto-Restart Status */}
            {currentJob.enableAutoRestart && (
                <Card className="border-0 shadow-lg">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <RefreshCw className="h-5 w-5" />
                            Auto-Restart
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Restart Attempts</span>
                            <span className="font-semibold">
                                {currentJob.restartCount} / {currentJob.maxRestarts}
                            </span>
                        </div>
                        <Progress
                            value={(currentJob.restartCount / currentJob.maxRestarts) * 100}
                            className="h-2 mt-2"
                        />
                        {currentJob.restartCount >= currentJob.maxRestarts && (
                            <p className="text-xs text-destructive mt-2">
                                Max restart attempts reached. Manual intervention required.
                            </p>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Health Alerts */}
            {health?.alertType && !health.isAlertAcknowledged && (
                <Card className={`border-0 shadow-lg ${health.alertType === "critical" ? "bg-red-50 dark:bg-red-950" : "bg-yellow-50 dark:bg-yellow-950"
                    }`}>
                    <CardContent className="pt-4">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-3">
                                {health.alertType === "critical" ? (
                                    <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                                ) : (
                                    <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                                )}
                                <div>
                                    <p className={`font-semibold ${health.alertType === "critical" ? "text-red-700 dark:text-red-300" : "text-yellow-700 dark:text-yellow-300"
                                        }`}>
                                        {health.alertType === "critical" ? "Critical Alert" : "Warning"}
                                    </p>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {health.alertMessage}
                                    </p>
                                </div>
                            </div>
                            <Button variant="outline" size="sm" onClick={handleAcknowledgeAlert}>
                                Acknowledge
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Main Content Tabs */}
            <Tabs defaultValue="health" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="health">Health Metrics</TabsTrigger>
                    <TabsTrigger value="output">Output Settings</TabsTrigger>
                    <TabsTrigger value="stream">Stream Settings</TabsTrigger>
                </TabsList>

                {/* Health Metrics Tab */}
                <TabsContent value="health">
                    <Card className="border-0 shadow-lg">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Activity className="h-5 w-5" />
                                    Real-time Metrics
                                </CardTitle>
                                <HealthIndicator health={health} />
                            </div>
                        </CardHeader>
                        <CardContent>
                            {isRunning && health ? (
                                <div className="space-y-4">
                                    {/* FFmpeg Metrics */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <Gauge className="h-3 w-3" />
                                                Bitrate
                                            </div>
                                            <p className="text-lg font-semibold">
                                                {health.bitrateKbps?.toFixed(0) || "—"} kbps
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Target: {currentJob.targetBitrate} kbps
                                            </p>
                                        </div>
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <Film className="h-3 w-3" />
                                                Frame Rate
                                            </div>
                                            <p className="text-lg font-semibold">
                                                {health.fps?.toFixed(1) || "—"} fps
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Target: {currentJob.targetFps} fps
                                            </p>
                                        </div>
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <Activity className="h-3 w-3" />
                                                Speed
                                            </div>
                                            <p className="text-lg font-semibold">
                                                {health.speed || "—"}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Encoding speed
                                            </p>
                                        </div>
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <AlertTriangle className="h-3 w-3" />
                                                Dropped Frames
                                            </div>
                                            <p className={`text-lg font-semibold ${health.droppedFrames > 100 ? "text-red-500" :
                                                health.droppedFrames > 50 ? "text-yellow-500" : ""
                                                }`}>
                                                {health.droppedFrames}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                +{health.droppedFramesDelta} since last
                                            </p>
                                        </div>
                                    </div>

                                    {/* System Resources */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <Cpu className="h-3 w-3" />
                                                CPU Usage
                                            </div>
                                            <p className="text-lg font-semibold">
                                                {health.cpuPercent?.toFixed(1) || "—"}%
                                            </p>
                                            <Progress
                                                value={health.cpuPercent || 0}
                                                className="h-1 mt-2"
                                            />
                                        </div>
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                                <HardDrive className="h-3 w-3" />
                                                Memory
                                            </div>
                                            <p className="text-lg font-semibold">
                                                {health.memoryMb?.toFixed(0) || "—"} MB
                                            </p>
                                        </div>
                                    </div>

                                    {/* Frame Count */}
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Total Frames Processed</span>
                                        <span className="font-mono">{health.frameCount.toLocaleString()}</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground">
                                    <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                    <p>Health metrics available when stream is running</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Output Settings Tab */}
                <TabsContent value="output">
                    <Card className="border-0 shadow-lg">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                Output Configuration
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-3 bg-muted rounded-lg">
                                    <p className="text-xs text-muted-foreground">Resolution</p>
                                    <p className="text-lg font-semibold">{currentJob.resolution}</p>
                                </div>
                                <div className="p-3 bg-muted rounded-lg">
                                    <p className="text-xs text-muted-foreground">Target Bitrate</p>
                                    <p className="text-lg font-semibold">{currentJob.targetBitrate} kbps</p>
                                </div>
                                <div className="p-3 bg-muted rounded-lg">
                                    <p className="text-xs text-muted-foreground">Frame Rate</p>
                                    <p className="text-lg font-semibold">{currentJob.targetFps} fps</p>
                                </div>
                                <div className="p-3 bg-muted rounded-lg">
                                    <p className="text-xs text-muted-foreground">Encoding Mode</p>
                                    <p className="text-lg font-semibold uppercase">{currentJob.encodingMode}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Stream Settings Tab */}
                <TabsContent value="stream">
                    <Card className="border-0 shadow-lg">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg">Stream Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">RTMP URL</label>
                                <div className="flex gap-2">
                                    <Input
                                        value={currentJob.rtmpUrl}
                                        readOnly
                                        className="font-mono text-sm"
                                    />
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={() => copyToClipboard(currentJob.rtmpUrl, "rtmp")}
                                    >
                                        {copied === "rtmp" ? (
                                            <CheckCircle className="h-4 w-4 text-green-500" />
                                        ) : (
                                            <Copy className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                            </div>

                            {currentJob.streamKeyMasked && (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Stream Key</label>
                                    <div className="flex gap-2">
                                        <Input
                                            type={showStreamKey ? "text" : "password"}
                                            value={currentJob.streamKeyMasked}
                                            readOnly
                                            className="font-mono text-sm"
                                        />
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            onClick={() => setShowStreamKey(!showStreamKey)}
                                        >
                                            {showStreamKey ? (
                                                <EyeOff className="h-4 w-4" />
                                            ) : (
                                                <Eye className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </div>
                                    {currentJob.isStreamKeyLocked && (
                                        <p className="text-xs text-muted-foreground">
                                            Stream key is locked while stream is active
                                        </p>
                                    )}
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4 pt-2">
                                <div>
                                    <p className="text-sm text-muted-foreground">Loop Mode</p>
                                    <p className="font-medium capitalize">{currentJob.loopMode}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Auto-Restart</p>
                                    <p className="font-medium">
                                        {currentJob.enableAutoRestart ? "Enabled" : "Disabled"}
                                    </p>
                                </div>
                            </div>

                            {currentJob.lastError && (
                                <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                                    <p className="text-sm font-medium text-red-700 dark:text-red-300">Last Error</p>
                                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                                        {currentJob.lastError}
                                    </p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Confirmation Dialogs */}
            <ConfirmDialog
                open={stopConfirm}
                onOpenChange={setStopConfirm}
                title="Stop Stream"
                description={`Are you sure you want to stop "${currentJob.title}"? This will end the live broadcast immediately.`}
                confirmText="Stop Stream"
                variant="destructive"
                onConfirm={handleStop}
            />

            <ConfirmDialog
                open={restartConfirm}
                onOpenChange={setRestartConfirm}
                title="Restart Stream"
                description={`Are you sure you want to restart "${currentJob.title}"? The stream will briefly go offline during restart.`}
                confirmText="Restart"
                variant="default"
                onConfirm={handleRestart}
            />
        </div>
    )
}

export default StreamJobControlPanel
