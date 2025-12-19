"use client"

import { useState, useEffect, useCallback } from "react"
import {
    BarChart3,
    Clock,
    Repeat,
    Activity,
    HardDrive,
    TrendingUp,
    Calendar,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"

// Types
interface StreamAnalytics {
    totalStreams: number
    totalDurationHours: number
    totalLoopsCompleted: number
    avgStreamDurationMinutes: number
    avgBitrateKbps: number
    totalDataTransferredGb: number
    streamsByDay: { date: string; count: number }[]
    durationByDay: { date: string; hours: number }[]
}

// API function
async function getStreamAnalytics(days: number): Promise<StreamAnalytics> {
    const response = await fetch(`/api/v1/stream-jobs/analytics?days=${days}`, {
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to fetch analytics")
    }

    const data = await response.json()
    return {
        totalStreams: data.total_streams,
        totalDurationHours: data.total_duration_hours,
        totalLoopsCompleted: data.total_loops_completed,
        avgStreamDurationMinutes: data.avg_stream_duration_minutes,
        avgBitrateKbps: data.avg_bitrate_kbps,
        totalDataTransferredGb: data.total_data_transferred_gb,
        streamsByDay: data.streams_by_day,
        durationByDay: data.duration_by_day,
    }
}

function StatCard({
    title,
    value,
    icon: Icon,
    description,
}: {
    title: string
    value: string | number
    icon: React.ElementType
    description?: string
}) {
    return (
        <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{value}</p>
                        {description && (
                            <p className="text-xs text-muted-foreground mt-1">{description}</p>
                        )}
                    </div>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Icon className="h-6 w-6 text-primary" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function SimpleBarChart({
    data,
    valueKey,
    label,
}: {
    data: { date: string;[key: string]: string | number }[]
    valueKey: string
    label: string
}) {
    if (!data || data.length === 0) {
        return (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                No data available
            </div>
        )
    }

    const maxValue = Math.max(...data.map((d) => Number(d[valueKey]) || 0))

    return (
        <div className="space-y-2">
            <div className="flex items-end gap-1 h-[200px]">
                {data.map((item, index) => {
                    const value = Number(item[valueKey]) || 0
                    const height = maxValue > 0 ? (value / maxValue) * 100 : 0

                    return (
                        <div
                            key={index}
                            className="flex-1 flex flex-col items-center gap-1"
                        >
                            <div
                                className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
                                style={{ height: `${height}%`, minHeight: value > 0 ? "4px" : "0" }}
                                title={`${item.date}: ${value.toFixed(1)} ${label}`}
                            />
                        </div>
                    )
                })}
            </div>
            <div className="flex gap-1 text-xs text-muted-foreground">
                {data.map((item, index) => (
                    <div key={index} className="flex-1 text-center truncate">
                        {new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </div>
                ))}
            </div>
        </div>
    )
}

export default function StreamAnalyticsPage() {
    const { addToast } = useToast()

    const [loading, setLoading] = useState(true)
    const [analytics, setAnalytics] = useState<StreamAnalytics | null>(null)
    const [days, setDays] = useState(30)

    const loadAnalytics = useCallback(async () => {
        try {
            setLoading(true)
            const data = await getStreamAnalytics(days)
            setAnalytics(data)
        } catch (error) {
            console.error("Failed to load analytics:", error)
            addToast({
                title: "Error",
                description: "Failed to load analytics data",
                type: "error",
            })
        } finally {
            setLoading(false)
        }
    }, [days, addToast])

    useEffect(() => {
        loadAnalytics()
    }, [loadAnalytics])

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: "Analytics" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <BarChart3 className="h-8 w-8" />
                            Stream Analytics
                        </h1>
                        <p className="text-muted-foreground">
                            Insights and trends from your streaming activity
                        </p>
                    </div>
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
                </div>

                {loading ? (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            {[...Array(6)].map((_, i) => (
                                <Skeleton key={i} className="h-[100px]" />
                            ))}
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Skeleton className="h-[300px]" />
                            <Skeleton className="h-[300px]" />
                        </div>
                    </div>
                ) : analytics ? (
                    <>
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            <StatCard
                                title="Total Streams"
                                value={analytics.totalStreams}
                                icon={Activity}
                            />
                            <StatCard
                                title="Total Duration"
                                value={`${analytics.totalDurationHours.toFixed(1)}h`}
                                icon={Clock}
                            />
                            <StatCard
                                title="Loops Completed"
                                value={analytics.totalLoopsCompleted}
                                icon={Repeat}
                            />
                            <StatCard
                                title="Avg Duration"
                                value={`${analytics.avgStreamDurationMinutes.toFixed(0)}m`}
                                icon={TrendingUp}
                            />
                            <StatCard
                                title="Avg Bitrate"
                                value={`${analytics.avgBitrateKbps.toFixed(0)} kbps`}
                                icon={Activity}
                            />
                            <StatCard
                                title="Data Transferred"
                                value={`${analytics.totalDataTransferredGb.toFixed(2)} GB`}
                                icon={HardDrive}
                            />
                        </div>

                        {/* Charts */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <CardTitle>Streams per Day</CardTitle>
                                    <CardDescription>
                                        Number of streams started each day
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <SimpleBarChart
                                        data={analytics.streamsByDay}
                                        valueKey="count"
                                        label="streams"
                                    />
                                </CardContent>
                            </Card>

                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <CardTitle>Duration per Day</CardTitle>
                                    <CardDescription>
                                        Total streaming hours each day
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <SimpleBarChart
                                        data={analytics.durationByDay}
                                        valueKey="hours"
                                        label="hours"
                                    />
                                </CardContent>
                            </Card>
                        </div>

                        {/* Summary */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle>Summary</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Avg Streams/Day</p>
                                        <p className="text-xl font-semibold">
                                            {(analytics.totalStreams / days).toFixed(1)}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Avg Hours/Day</p>
                                        <p className="text-xl font-semibold">
                                            {(analytics.totalDurationHours / days).toFixed(1)}h
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Avg Loops/Stream</p>
                                        <p className="text-xl font-semibold">
                                            {analytics.totalStreams > 0
                                                ? (analytics.totalLoopsCompleted / analytics.totalStreams).toFixed(1)
                                                : "0"}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Data/Day</p>
                                        <p className="text-xl font-semibold">
                                            {(analytics.totalDataTransferredGb / days).toFixed(2)} GB
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                ) : (
                    <div className="text-center py-12 text-muted-foreground">
                        <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No analytics data available</p>
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}
