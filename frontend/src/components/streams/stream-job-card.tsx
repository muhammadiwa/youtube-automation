"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
    Play,
    Square,
    RotateCcw,
    MoreVertical,
    Trash2,
    Edit,
    Settings,
    Activity,
    Radio,
    Clock,
    RefreshCw,
    AlertTriangle,
    Repeat,
    Infinity,
    Video,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { useToast } from "@/components/ui/toast"
import {
    streamJobsApi,
    type StreamJob,
    type StreamJobStatus,
} from "@/lib/api/stream-jobs"

interface StreamJobCardProps {
    job: StreamJob
    onUpdate?: () => void
}

export function StreamJobCard({ job, onUpdate }: StreamJobCardProps) {
    const router = useRouter()
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [deleteConfirm, setDeleteConfirm] = useState(false)
    const [stopConfirm, setStopConfirm] = useState(false)

    const handleStart = async () => {
        try {
            setLoading(true)
            await streamJobsApi.startStreamJob(job.id)
            addToast({ type: "success", title: "Started", description: "Stream started successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            console.error("Failed to start stream:", error)
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
            await streamJobsApi.stopStreamJob(job.id)
            addToast({ type: "success", title: "Stopped", description: "Stream stopped successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            console.error("Failed to stop stream:", error)
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to stop stream",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleRestart = async () => {
        try {
            setLoading(true)
            await streamJobsApi.restartStreamJob(job.id)
            addToast({ type: "success", title: "Restarted", description: "Stream restarted successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            console.error("Failed to restart stream:", error)
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to restart stream",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        try {
            setLoading(true)
            await streamJobsApi.deleteStreamJob(job.id)
            addToast({ type: "success", title: "Deleted", description: "Stream job deleted successfully" })
            onUpdate?.()
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            console.error("Failed to delete stream:", error)
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to delete stream",
            })
        } finally {
            setLoading(false)
        }
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
                    <Badge variant="default" className="bg-blue-500 text-white">
                        <Clock className="mr-1 h-3 w-3" />
                        Scheduled
                    </Badge>
                )
            case "pending":
                return (
                    <Badge variant="secondary">
                        <Clock className="mr-1 h-3 w-3" />
                        Pending
                    </Badge>
                )
            case "stopped":
                return (
                    <Badge variant="secondary">
                        <Square className="mr-1 h-3 w-3" />
                        Stopped
                    </Badge>
                )
            case "completed":
                return (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                        Completed
                    </Badge>
                )
            case "failed":
                return (
                    <Badge variant="destructive">
                        <AlertTriangle className="mr-1 h-3 w-3" />
                        Failed
                    </Badge>
                )
            case "cancelled":
                return (
                    <Badge variant="outline" className="text-muted-foreground">
                        Cancelled
                    </Badge>
                )
            default:
                return <Badge variant="outline">{status}</Badge>
        }
    }

    const getLoopBadge = () => {
        if (job.loopMode === "infinite") {
            return (
                <Badge variant="outline" className="text-xs">
                    <Infinity className="mr-1 h-3 w-3" />
                    24/7
                </Badge>
            )
        }
        if (job.loopMode === "count" && job.loopCount) {
            return (
                <Badge variant="outline" className="text-xs">
                    <Repeat className="mr-1 h-3 w-3" />
                    {job.currentLoop}/{job.loopCount}
                </Badge>
            )
        }
        return null
    }

    const formatDuration = (seconds: number) => {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        const secs = seconds % 60
        if (hours > 0) {
            return `${hours}h ${minutes}m`
        }
        if (minutes > 0) {
            return `${minutes}m ${secs}s`
        }
        return `${secs}s`
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })
    }

    const canStart = ["pending", "scheduled", "stopped", "failed"].includes(job.status)
    const canStop = ["starting", "running"].includes(job.status)
    // Only starting and running are truly "active" - stopping can be deleted
    const isActive = ["starting", "running"].includes(job.status)

    return (
        <>
            <Card className="overflow-hidden border-0 shadow-lg hover:shadow-xl transition-shadow">
                <div className="relative">
                    {/* Thumbnail/Preview */}
                    <div
                        className="w-full aspect-video bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center cursor-pointer"
                        onClick={() => router.push(`/dashboard/streams/${job.id}/control`)}
                    >
                        <Video className="h-12 w-12 text-white/50" />
                    </div>

                    {/* Status Badge */}
                    <div className="absolute top-2 left-2 flex gap-1">
                        {getStatusBadge(job.status)}
                        <Badge variant="secondary" className="text-xs">
                            Video-to-Live
                        </Badge>
                    </div>

                    {/* Loop Badge */}
                    <div className="absolute top-2 right-2">
                        {getLoopBadge()}
                    </div>

                    {/* Metrics (when running) */}
                    {job.status === "running" && (
                        <div className="absolute bottom-2 right-2 flex gap-2">
                            {job.currentBitrateKbps && (
                                <div className="bg-black/70 text-white text-xs px-2 py-1 rounded">
                                    {job.currentBitrateKbps.toFixed(0)} kbps
                                </div>
                            )}
                            {job.currentFps && (
                                <div className="bg-black/70 text-white text-xs px-2 py-1 rounded">
                                    {job.currentFps.toFixed(0)} fps
                                </div>
                            )}
                            {job.currentSpeed && (
                                <div className="bg-black/70 text-white text-xs px-2 py-1 rounded">
                                    {job.currentSpeed}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                            <h3
                                className="font-semibold truncate cursor-pointer hover:text-primary"
                                onClick={() => router.push(`/dashboard/streams/${job.id}/control`)}
                            >
                                {job.title}
                            </h3>
                            {job.videoId && (
                                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                                    <Video className="h-3 w-3" />
                                    From Video Library
                                </p>
                            )}
                            <p className="text-sm text-muted-foreground">
                                {job.resolution} • {job.targetBitrate} kbps • {job.targetFps} fps
                            </p>
                            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                {job.status === "running" && job.currentDurationSeconds > 0 && (
                                    <span>Duration: {formatDuration(job.currentDurationSeconds)}</span>
                                )}
                                {job.status === "scheduled" && job.scheduledStartAt && (
                                    <span>Starts: {formatDate(job.scheduledStartAt)}</span>
                                )}
                                {job.lastError && (
                                    <span className="text-destructive truncate max-w-[150px]" title={job.lastError}>
                                        Error: {job.lastError}
                                    </span>
                                )}
                            </div>
                            {job.enableAutoRestart && job.restartCount > 0 && (
                                <p className="text-xs text-muted-foreground mt-1">
                                    Restarts: {job.restartCount}/{job.maxRestarts}
                                </p>
                            )}
                        </div>

                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" disabled={loading}>
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                {canStart && (
                                    <DropdownMenuItem onClick={handleStart} disabled={loading}>
                                        <Play className="mr-2 h-4 w-4" />
                                        Start Stream
                                    </DropdownMenuItem>
                                )}
                                {canStop && (
                                    <DropdownMenuItem onClick={() => setStopConfirm(true)} disabled={loading}>
                                        <Square className="mr-2 h-4 w-4" />
                                        Stop Stream
                                    </DropdownMenuItem>
                                )}
                                {(job.status === "running" || job.status === "failed") && (
                                    <DropdownMenuItem onClick={handleRestart} disabled={loading}>
                                        <RotateCcw className="mr-2 h-4 w-4" />
                                        Restart Stream
                                    </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                    onClick={() => router.push(`/dashboard/streams/${job.id}/control`)}
                                >
                                    <Settings className="mr-2 h-4 w-4" />
                                    Control Panel
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    onClick={() => router.push(`/dashboard/streams/${job.id}/health`)}
                                >
                                    <Activity className="mr-2 h-4 w-4" />
                                    Health Monitor
                                </DropdownMenuItem>
                                {!isActive && (
                                    <>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem
                                            onClick={() => router.push(`/dashboard/streams/${job.id}/edit`)}
                                        >
                                            <Edit className="mr-2 h-4 w-4" />
                                            Edit
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            className="text-destructive"
                                            onClick={() => setDeleteConfirm(true)}
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete
                                        </DropdownMenuItem>
                                    </>
                                )}
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </CardContent>
            </Card>

            {/* Delete Confirmation */}
            <ConfirmDialog
                open={deleteConfirm}
                onOpenChange={setDeleteConfirm}
                title="Delete Stream Job"
                description={`Are you sure you want to delete "${job.title}"? This action cannot be undone.`}
                confirmText="Delete"
                variant="destructive"
                onConfirm={handleDelete}
            />

            {/* Stop Confirmation */}
            <ConfirmDialog
                open={stopConfirm}
                onOpenChange={setStopConfirm}
                title="Stop Stream"
                description={`Are you sure you want to stop "${job.title}"? This will end the live broadcast.`}
                confirmText="Stop Stream"
                variant="destructive"
                onConfirm={handleStop}
            />
        </>
    )
}

export default StreamJobCard
