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
    Calendar,
    Play,
    ExternalLink,
    Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
import apiClient from "@/lib/api/client"

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
    const params: Record<string, number> = {
        days,
        page,
        page_size: pageSize,
    }

    const data = await apiClient.get<Record<string, unknown>>("/stream-jobs/history", params)

    return {
        items: ((data.items as Record<string, unknown>[]) || []).map((item: Record<string, unknown>) => ({
            id: item.id as string,
            title: item.title as string,
            status: item.status as string,
            loopMode: item.loop_mode as string,
            resolution: item.resolution as string,
            targetBitrate: item.target_bitrate as number,
            actualStartAt: item.actual_start_at as string | null,
            actualEndAt: item.actual_end_at as string | null,
            totalDurationSeconds: item.total_duration_seconds as number,
            totalLoops: item.total_loops as number,
            avgBitrateKbps: item.avg_bitrate_kbps as number | null,
            totalDroppedFrames: item.total_dropped_frames as number,
            createdAt: item.created_at as string,
        })),
        total: data.total as number,
        page: data.page as number,
        pageSize: data.page_size as number,
    }
}

async function exportStreamData(days: number): Promise<void> {
    const token = localStorage.getItem("auth_access_token")
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

    const response = await fetch(`${baseUrl}/stream-jobs/export?days=${days}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
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
    if (!seconds || seconds === 0) return "0m"
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
                <Badge className="bg-green-500/10 text-green-600 border-green-500/20 hover:bg-green-500/20">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Completed
                </Badge>
            )
        case "stopped":
            return (
                <Badge variant="secondary" className="bg-gray-500/10 text-gray-600 border-gray-500/20">
                    <XCircle className="mr-1 h-3 w-3" />
                    Stopped
                </Badge>
            )
        case "failed":
            return (
                <Badge className="bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20">
                    <AlertTriangle className="mr-1 h-3 w-3" />
                    Failed
                </Badge>
            )
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

function StatCard({
    title,
    value,
    icon: Icon,
    color = "primary",
}: {
    title: string
    value: string | number
    icon: React.ElementType
    color?: "primary" | "green" | "blue" | "orange"
}) {
    const colorClasses = {
        primary: "bg-primary/10 text-primary",
        green: "bg-green-500/10 text-green-500",
        blue: "bg-blue-500/10 text-blue-500",
        orange: "bg-orange-500/10 text-orange-500",
    }

    return (
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{value}</p>
                    </div>
                    <div className={`h-12 w-12 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
                        <Icon className="h-6 w-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
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
    const totalDuration = history.reduce((sum, h) => sum + h.totalDurationSeconds, 0)
    const totalLoops = history.reduce((sum, h) => sum + h.totalLoops, 0)
    const totalDroppedFrames = history.reduce((sum, h) => sum + h.totalDroppedFrames, 0)

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
                        <Select value={days.toString()} onValueChange={(v) => { setDays(parseInt(v)); setPage(1); }}>
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
                            {exporting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <Download className="mr-2 h-4 w-4" />
                            )}
                            {exporting ? "Exporting..." : "Export CSV"}
                        </Button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <StatCard
                        title="Total Streams"
                        value={total}
                        icon={Activity}
                        color="primary"
                    />
                    <StatCard
                        title="Total Duration"
                        value={formatDuration(totalDuration)}
                        icon={Clock}
                        color="blue"
                    />
                    <StatCard
                        title="Total Loops"
                        value={totalLoops.toLocaleString()}
                        icon={Repeat}
                        color="green"
                    />
                    <StatCard
                        title="Dropped Frames"
                        value={totalDroppedFrames.toLocaleString()}
                        icon={AlertTriangle}
                        color="orange"
                    />
                </div>

                {/* History Table */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Stream Sessions</CardTitle>
                        <CardDescription>
                            Click on a row to view stream details
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="space-y-4">
                                {[...Array(5)].map((_, i) => (
                                    <Skeleton key={i} className="h-14 w-full" />
                                ))}
                            </div>
                        ) : history.length === 0 ? (
                            <div className="text-center py-16 text-muted-foreground">
                                <History className="h-16 w-16 mx-auto mb-4 opacity-30" />
                                <p className="text-lg font-medium">No stream history found</p>
                                <p className="text-sm mt-2">
                                    Start streaming to see your history here
                                </p>
                                <Button
                                    className="mt-4"
                                    onClick={() => router.push("/dashboard/streams/create-video-live")}
                                >
                                    <Play className="mr-2 h-4 w-4" />
                                    Create Stream
                                </Button>
                            </div>
                        ) : (
                            <>
                                <div className="rounded-lg border overflow-hidden">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-muted/50">
                                                <TableHead className="font-semibold">Title</TableHead>
                                                <TableHead className="font-semibold">Status</TableHead>
                                                <TableHead className="font-semibold">Duration</TableHead>
                                                <TableHead className="font-semibold">Loops</TableHead>
                                                <TableHead className="font-semibold">Resolution</TableHead>
                                                <TableHead className="font-semibold">Avg Bitrate</TableHead>
                                                <TableHead className="font-semibold">Started</TableHead>
                                                <TableHead className="font-semibold w-[50px]"></TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {history.map((item) => (
                                                <TableRow
                                                    key={item.id}
                                                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                                                    onClick={() => router.push(`/dashboard/streams/${item.id}/control`)}
                                                >
                                                    <TableCell className="font-medium max-w-[200px] truncate">
                                                        {item.title}
                                                    </TableCell>
                                                    <TableCell>
                                                        <StatusBadge status={item.status} />
                                                    </TableCell>
                                                    <TableCell className="font-mono text-sm">
                                                        {formatDuration(item.totalDurationSeconds)}
                                                    </TableCell>
                                                    <TableCell>
                                                        <span className="inline-flex items-center gap-1">
                                                            <Repeat className="h-3 w-3 text-muted-foreground" />
                                                            {item.totalLoops}
                                                        </span>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" className="font-mono">
                                                            {item.resolution}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="font-mono text-sm">
                                                        {item.avgBitrateKbps
                                                            ? `${item.avgBitrateKbps.toFixed(0)} kbps`
                                                            : "—"}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {item.actualStartAt ? formatDate(item.actualStartAt) : "—"}
                                                    </TableCell>
                                                    <TableCell>
                                                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>

                                {/* Pagination */}
                                {totalPages > 1 && (
                                    <div className="flex items-center justify-between mt-6">
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
                                            <div className="flex items-center gap-1">
                                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                    let pageNum: number
                                                    if (totalPages <= 5) {
                                                        pageNum = i + 1
                                                    } else if (page <= 3) {
                                                        pageNum = i + 1
                                                    } else if (page >= totalPages - 2) {
                                                        pageNum = totalPages - 4 + i
                                                    } else {
                                                        pageNum = page - 2 + i
                                                    }
                                                    return (
                                                        <Button
                                                            key={pageNum}
                                                            variant={page === pageNum ? "default" : "outline"}
                                                            size="sm"
                                                            className="w-8 h-8 p-0"
                                                            onClick={() => setPage(pageNum)}
                                                        >
                                                            {pageNum}
                                                        </Button>
                                                    )
                                                })}
                                            </div>
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
