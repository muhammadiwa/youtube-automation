"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
    History,
    Download,
    Clock,
    Repeat,
    Activity,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Filter,
    Calendar,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { useToast } from "@/hooks/use-toast"

// Types
interface StreamHistoryItem {
    id: string
    title: string
    status: string
    loopMode: string
    resolution: string
    targetBitrate: number
    actualStartAt: string | null
    actualEndAt: string | null
    totalDurationSeconds: number
    totalLoops: number
    avgBitrateKbps: number | null
    totalDroppedFrames: number
    createdAt: string
}

interface StreamHistoryResponse {
    items: StreamHistoryItem[]
    total: number
    page: number
    pageSize: number
}

// API functions
async function getStreamHistory(days: number, page: number, pageSize: number): Promise<StreamHistoryResponse> {
    const params = new URLSearchParams({
        days: days.toString(),
        page: page.toString(),
        page_size: pageSize.toString(),
    })

    const response = await fetch(`/api/v1/stream-jobs/history?${params}`, {
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to fetch history")
    }

    const data = await response.json()
    return {
        items: data.items.map((item: Record<string, unknown>) => ({
            id: item.id,
            title: item.title,
            status: item.status,
            loopMode: item.loop_mode,
            resolution: item.resolution,
            targetBitrate: item.target_bitrate,
            actualStartAt: item.actual_start_at,
            actualEndAt: item.actual_end_at,
            totalDurationSeconds: item.total_duration_seconds,
            totalLoops: item.total_loops,
            avgBitrateKbps: item.avg_bitrate_kbps,
            totalDroppedFrames: item.total_dropped_frames,
            createdAt: item.created_at,
        })),
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
    }
}

async function exportStreamData(days: number): Promise<void> {
    const response = await fetch(`/api/v1/stream-jobs/export?days=${days}`, {
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to export data")
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `stream_jobs_export_${days}days.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
}

function formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
        return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
}

function formatDate(dateString: string): string {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    })
}

function StatusBadge({ status }: { status: string }) {
    switch (status) {
        case "completed":
            return (
                <Badge variant="outline" className="text-green-600 border-green-600">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Completed
                </Badge>
            )
        case "stopped":
            return (
                <Badge variant="secondary">
                    Stopped
                </Badge>
            )
        case "failed":
            return (
                <Badge variant="destructive">
                    <XCircle className="mr-1 h-3 w-3" />
                    Failed
                </Badge>
            )
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

export default function StreamHistoryPage() {
    const router = useRouter()
    const { addToast } = useToast()

    const [loading, setLoading] = useState(true)
    const [exporting, setExporting] = useState(false)
    const [history, setHistory] = useState<StreamHistoryItem[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(20)
    const [days, setDays] = useState(30)

    const loadHistory = useCallback(async () => {
        try {
            setLoading(true)
            const data = await getStreamHistory(days, page, pageSize)
            setHistory(data.items)
            setTotal(data.total)
        } catch (error) {
            console.error("Failed to load history:", error)
            addToast({
                title: "Error",
                description: "Failed to load stream history",
                type: "error",
            })
        } finally {
            setLoading(false)
        }
    }, [days, page, pageSize, addToast])

    useEffect(() => {
        loadHistory()
    }, [loadHistory])

    const handleExport = async () => {
        try {
            setExporting(true)
            await exportStreamData(days)
            addToast({
                title: "Export Complete",
                description: "Stream data has been exported to CSV",
                type: "success",
            })
        } catch (error) {
            console.error("Failed to export:", error)
            addToast({
                title: "Export Failed",
                description: "Failed to export stream data",
                type: "error",
            })
        } finally {
            setExporting(false)
        }
    }

    const totalPages = Math.ceil(total / pageSize)

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: "History" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <History className="h-8 w-8" />
                            Stream History
                        </h1>
                        <p className="text-muted-foreground">
                            View past streams and their performance metrics
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v))}>
                            <SelectTrigger className="w-[150px]">
                                <Calendar className="mr-2 h-4 w-4" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="7">Last 7 days</SelectItem>
                                <SelectItem value="30">Last 30 days</SelectItem>
                                <SelectItem value="90">Last 90 days</SelectItem>
                                <SelectItem value="365">Last year</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button onClick={handleExport} disabled={exporting} variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            {exporting ? "Exporting..." : "Export CSV"}
                        </Button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card className="border-0 shadow-lg">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                <Activity className="h-4 w-4" />
                                Total Streams
                            </div>
                            <p className="text-2xl font-bold">{total}</p>
                        </CardContent>
                    </Card>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                <Clock className="h-4 w-4" />
                                Total Duration
                            </div>
                            <p className="text-2xl font-bold">
                                {formatDuration(history.reduce((sum, h) => sum + h.totalDurationSeconds, 0))}
                            </p>
                        </CardContent>
                    </Card>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                <Repeat className="h-4 w-4" />
                                Total Loops
                            </div>
                            <p className="text-2xl font-bold">
                                {history.reduce((sum, h) => sum + h.totalLoops, 0)}
                            </p>
                        </CardContent>
                    </Card>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                <AlertTriangle className="h-4 w-4" />
                                Dropped Frames
                            </div>
                            <p className="text-2xl font-bold">
                                {history.reduce((sum, h) => sum + h.totalDroppedFrames, 0).toLocaleString()}
                            </p>
                        </CardContent>
                    </Card>
                </div>

                {/* History Table */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Stream Sessions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="space-y-4">
                                {[...Array(5)].map((_, i) => (
                                    <Skeleton key={i} className="h-12 w-full" />
                                ))}
                            </div>
                        ) : history.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>No stream history found</p>
                            </div>
                        ) : (
                            <>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Title</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Duration</TableHead>
                                            <TableHead>Loops</TableHead>
                                            <TableHead>Resolution</TableHead>
                                            <TableHead>Avg Bitrate</TableHead>
                                            <TableHead>Started</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {history.map((item) => (
                                            <TableRow
                                                key={item.id}
                                                className="cursor-pointer hover:bg-muted/50"
                                                onClick={() => router.push(`/dashboard/streams/${item.id}/control`)}
                                            >
                                                <TableCell className="font-medium">{item.title}</TableCell>
                                                <TableCell>
                                                    <StatusBadge status={item.status} />
                                                </TableCell>
                                                <TableCell>{formatDuration(item.totalDurationSeconds)}</TableCell>
                                                <TableCell>{item.totalLoops}</TableCell>
                                                <TableCell>{item.resolution}</TableCell>
                                                <TableCell>
                                                    {item.avgBitrateKbps
                                                        ? `${item.avgBitrateKbps.toFixed(0)} kbps`
                                                        : "—"}
                                                </TableCell>
                                                <TableCell>
                                                    {item.actualStartAt ? formatDate(item.actualStartAt) : "—"}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>

                                {/* Pagination */}
                                {totalPages > 1 && (
                                    <div className="flex items-center justify-between mt-4">
                                        <p className="text-sm text-muted-foreground">
                                            Showing {(page - 1) * pageSize + 1} to{" "}
                                            {Math.min(page * pageSize, total)} of {total} streams
                                        </p>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(page - 1)}
                                                disabled={page === 1}
                                            >
                                                Previous
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(page + 1)}
                                                disabled={page >= totalPages}
                                            >
                                                Next
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
