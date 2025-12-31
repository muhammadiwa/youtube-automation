/**
 * Video Usage History Component
 * 
 * Displays timeline of video usage (YouTube uploads, streaming sessions).
 * Requirements: 4.2
 */

"use client"

import { useEffect, useState } from "react"
import { Youtube, Radio, Clock, Eye, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { videoLibraryApi } from "@/lib/api/video-library"

interface UsageLog {
    id: string
    usageType: "youtube_upload" | "live_stream"
    startedAt: string
    endedAt: string | null
    usageMetadata: {
        youtube_id?: string
        stream_job_id?: string
        stream_duration?: number
        viewer_count?: number
        upload_duration?: number
    }
}

interface VideoUsageHistoryProps {
    videoId: string
}

export function VideoUsageHistory({ videoId }: VideoUsageHistoryProps) {
    const [logs, setLogs] = useState<UsageLog[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadUsageHistory()
    }, [videoId])

    const loadUsageHistory = async () => {
        try {
            setLoading(true)
            setError(null)
            const data = await videoLibraryApi.getUsageStats(videoId)
            setLogs(data.usageLogs || [])
        } catch (err: any) {
            console.error("Failed to load usage history:", err)
            setError(err.message || "Failed to load usage history")
        } finally {
            setLoading(false)
        }
    }

    const formatDate = (date: string) => {
        return new Date(date).toLocaleString()
    }

    const formatDuration = (seconds: number) => {
        const hours = Math.floor(seconds / 3600)
        const mins = Math.floor((seconds % 3600) / 60)
        const secs = seconds % 60
        if (hours > 0) {
            return `${hours}h ${mins}m ${secs}s`
        }
        if (mins > 0) {
            return `${mins}m ${secs}s`
        }
        return `${secs}s`
    }

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Usage History</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <Skeleton className="h-16 w-full" />
                        <Skeleton className="h-16 w-full" />
                        <Skeleton className="h-16 w-full" />
                    </div>
                </CardContent>
            </Card>
        )
    }

    if (error) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Usage History</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">{error}</p>
                </CardContent>
            </Card>
        )
    }

    if (logs.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Usage History</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">
                        No usage history yet. Upload to YouTube or create a stream to see usage logs.
                    </p>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Usage History</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {logs.map((log) => (
                        <div
                            key={log.id}
                            className="flex items-start gap-3 rounded-lg border p-3"
                        >
                            {/* Icon */}
                            <div className="mt-1">
                                {log.usageType === "youtube_upload" ? (
                                    <Youtube className="h-5 w-5 text-red-600" />
                                ) : (
                                    <Radio className="h-5 w-5 text-red-600" />
                                )}
                            </div>

                            {/* Content */}
                            <div className="flex-1 space-y-1">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">
                                            {log.usageType === "youtube_upload"
                                                ? "YouTube Upload"
                                                : "Live Stream"}
                                        </span>
                                        <Badge variant="secondary" className="text-xs">
                                            {log.usageType === "youtube_upload" ? "VOD" : "Live"}
                                        </Badge>
                                    </div>
                                    <span className="text-xs text-muted-foreground">
                                        {formatDate(log.startedAt)}
                                    </span>
                                </div>

                                {/* Metadata */}
                                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                                    {log.usageType === "youtube_upload" && log.usageMetadata.youtube_id && (
                                        <div className="flex items-center gap-1">
                                            <Youtube className="h-3 w-3" />
                                            <span>ID: {log.usageMetadata.youtube_id}</span>
                                        </div>
                                    )}

                                    {log.usageType === "live_stream" && (
                                        <>
                                            {log.usageMetadata.stream_duration !== undefined && (
                                                <div className="flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    <span>
                                                        Duration: {formatDuration(log.usageMetadata.stream_duration)}
                                                    </span>
                                                </div>
                                            )}
                                            {log.usageMetadata.viewer_count !== undefined && (
                                                <div className="flex items-center gap-1">
                                                    <Eye className="h-3 w-3" />
                                                    <span>Viewers: {log.usageMetadata.viewer_count}</span>
                                                </div>
                                            )}
                                            {!log.endedAt && (
                                                <Badge variant="default" className="text-xs">
                                                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                                                    Streaming
                                                </Badge>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
