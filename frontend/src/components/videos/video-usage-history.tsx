/**
 * Video Usage History Component
 * 
 * Displays timeline of video usage (YouTube uploads, streaming sessions).
 * Requirements: 4.2
 */

"use client"

import { useEffect, useState } from "react"
import { Youtube, Radio, Clock, Eye, Loader2, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
    onUpdate?: () => void
}

const ITEMS_PER_PAGE = 5

export function VideoUsageHistory({ videoId, onUpdate }: VideoUsageHistoryProps) {
    const [logs, setLogs] = useState<UsageLog[]>([])
    const [loading, setLoading] = useState(true)
    const [fixing, setFixing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [currentPage, setCurrentPage] = useState(1)

    useEffect(() => {
        loadUsageHistory()
    }, [videoId])

    // Reset to page 1 when logs change
    useEffect(() => {
        setCurrentPage(1)
    }, [logs.length])

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

    const handleFixLogs = async () => {
        try {
            setFixing(true)
            await videoLibraryApi.fixUsageLogs(videoId)
            await loadUsageHistory()
            onUpdate?.()
        } catch (err: any) {
            console.error("Failed to fix usage logs:", err)
            setError(err.message || "Failed to fix usage logs")
        } finally {
            setFixing(false)
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

    // Pagination calculations
    const totalPages = Math.ceil(logs.length / ITEMS_PER_PAGE)
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    const endIndex = startIndex + ITEMS_PER_PAGE
    const paginatedLogs = logs.slice(startIndex, endIndex)

    // Check if there are unclosed logs
    const hasUnclosedLogs = logs.some(log => log.usageType === "live_stream" && !log.endedAt)

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
                <div className="flex items-center justify-between">
                    <CardTitle>Usage History</CardTitle>
                    {hasUnclosedLogs && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleFixLogs}
                            disabled={fixing}
                        >
                            {fixing ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <RefreshCw className="mr-2 h-4 w-4" />
                            )}
                            Fix Logs
                        </Button>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {paginatedLogs.map((log) => (
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
                                            {log.endedAt && log.usageMetadata.stream_duration !== undefined && (
                                                <div className="flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    <span>
                                                        Duration: {formatDuration(log.usageMetadata.stream_duration)}
                                                    </span>
                                                </div>
                                            )}
                                            {log.usageMetadata.viewer_count !== undefined && log.usageMetadata.viewer_count > 0 && (
                                                <div className="flex items-center gap-1">
                                                    <Eye className="h-3 w-3" />
                                                    <span>Viewers: {log.usageMetadata.viewer_count}</span>
                                                </div>
                                            )}
                                            {!log.endedAt && (
                                                <Badge variant="destructive" className="text-xs">
                                                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                                                    Unclosed
                                                </Badge>
                                            )}
                                            {log.endedAt && (
                                                <Badge variant="outline" className="text-xs">
                                                    Completed
                                                </Badge>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between pt-2 border-t">
                            <span className="text-xs text-muted-foreground">
                                Showing {startIndex + 1}-{Math.min(endIndex, logs.length)} of {logs.length}
                            </span>
                            <div className="flex items-center gap-1">
                                <Button
                                    variant="outline"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={currentPage === 1}
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                </Button>
                                <span className="text-sm px-2">
                                    {currentPage} / {totalPages}
                                </span>
                                <Button
                                    variant="outline"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                    disabled={currentPage === totalPages}
                                >
                                    <ChevronRight className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
