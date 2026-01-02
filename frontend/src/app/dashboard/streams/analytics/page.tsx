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
    Zap,
    Timer,
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
import apiClient from "@/lib/api/client"
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    ComposedChart,
    Line,
} from "recharts"

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
    const data = await apiClient.get<Record<string, unknown>>("/stream-jobs/analytics", { days })

    return {
        totalStreams: data.total_streams as number,
        totalDurationHours: data.total_duration_hours as number,
        totalLoopsCompleted: data.total_loops_completed as number,
        avgStreamDurationMinutes: data.avg_stream_duration_minutes as number,
        avgBitrateKbps: data.avg_bitrate_kbps as number,
        totalDataTransferredGb: data.total_data_transferred_gb as number,
        streamsByDay: data.streams_by_day as { date: string; count: number }[],
        durationByDay: data.duration_by_day as { date: string; hours: number }[],
    }
}

// Custom tooltip for charts
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color: string }>; label?: string }) {
    if (active && payload && payload.length) {
        return (
            <div className="bg-background border rounded-lg shadow-lg p-3">
                <p className="font-medium text-sm mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} className="text-sm" style={{ color: entry.color }}>
                        {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
                    </p>
                ))}
            </div>
        )
    }
    return null
}

function StatCard({
    title,
    value,
    icon: Icon,
    description,
    trend,
    color = "primary",
}: {
    title: string
    value: string | number
    icon: React.ElementType
    description?: string
    trend?: string
    color?: "primary" | "green" | "blue" | "orange" | "purple" | "pink"
}) {
    const colorClasses = {
        primary: "bg-primary/10 text-primary",
        green: "bg-green-500/10 text-green-500",
        blue: "bg-blue-500/10 text-blue-500",
        orange: "bg-orange-500/10 text-orange-500",
        purple: "bg-purple-500/10 text-purple-500",
        pink: "bg-pink-500/10 text-pink-500",
    }

    return (
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold">{value}</p>
                        {description && (
                            <p className="text-xs text-muted-foreground">{description}</p>
                        )}
                        {trend && (
                            <p className="text-xs text-green-500 flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" />
                                {trend}
                            </p>
                        )}
                    </div>
                    <div className={`h-12 w-12 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
                        <Icon className="h-6 w-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
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

    // Format chart data with proper date labels
    const formatChartData = (streamsByDay: { date: string; count: number }[], durationByDay: { date: string; hours: number }[]) => {
        const dateMap = new Map<string, { date: string; streams: number; hours: number }>()

        streamsByDay.forEach(item => {
            const formattedDate = new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
            dateMap.set(item.date, { date: formattedDate, streams: item.count, hours: 0 })
        })

        durationByDay.forEach(item => {
            const existing = dateMap.get(item.date)
            if (existing) {
                existing.hours = item.hours
            } else {
                const formattedDate = new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                dateMap.set(item.date, { date: formattedDate, streams: 0, hours: item.hours })
            }
        })

        return Array.from(dateMap.values()).sort((a, b) => {
            const dateA = new Date(a.date)
            const dateB = new Date(b.date)
            return dateA.getTime() - dateB.getTime()
        })
    }

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
                                <Skeleton key={i} className="h-[120px]" />
                            ))}
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Skeleton className="h-[400px]" />
                            <Skeleton className="h-[400px]" />
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
                                color="primary"
                                description={`${(analytics.totalStreams / days).toFixed(1)} per day`}
                            />
                            <StatCard
                                title="Total Duration"
                                value={`${analytics.totalDurationHours.toFixed(1)}h`}
                                icon={Clock}
                                color="blue"
                                description={`${(analytics.totalDurationHours / days).toFixed(1)}h per day`}
                            />
                            <StatCard
                                title="Loops Completed"
                                value={analytics.totalLoopsCompleted.toLocaleString()}
                                icon={Repeat}
                                color="green"
                            />
                            <StatCard
                                title="Avg Duration"
                                value={`${analytics.avgStreamDurationMinutes.toFixed(0)}m`}
                                icon={Timer}
                                color="orange"
                            />
                            <StatCard
                                title="Avg Bitrate"
                                value={`${analytics.avgBitrateKbps.toFixed(0)} kbps`}
                                icon={Zap}
                                color="purple"
                            />
                            <StatCard
                                title="Data Transferred"
                                value={`${analytics.totalDataTransferredGb.toFixed(2)} GB`}
                                icon={HardDrive}
                                color="pink"
                            />
                        </div>

                        {/* Combined Chart */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle>Streaming Activity Overview</CardTitle>
                                <CardDescription>
                                    Streams started and hours streamed per day
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {analytics.streamsByDay.length > 0 || analytics.durationByDay.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={350}>
                                        <ComposedChart data={formatChartData(analytics.streamsByDay, analytics.durationByDay)}>
                                            <defs>
                                                <linearGradient id="colorStreams" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.1} />
                                                </linearGradient>
                                                <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                            <XAxis
                                                dataKey="date"
                                                tick={{ fontSize: 12 }}
                                                tickLine={false}
                                                axisLine={false}
                                            />
                                            <YAxis
                                                yAxisId="left"
                                                tick={{ fontSize: 12 }}
                                                tickLine={false}
                                                axisLine={false}
                                                label={{ value: 'Streams', angle: -90, position: 'insideLeft', fontSize: 12 }}
                                            />
                                            <YAxis
                                                yAxisId="right"
                                                orientation="right"
                                                tick={{ fontSize: 12 }}
                                                tickLine={false}
                                                axisLine={false}
                                                label={{ value: 'Hours', angle: 90, position: 'insideRight', fontSize: 12 }}
                                            />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Legend />
                                            <Bar
                                                yAxisId="left"
                                                dataKey="streams"
                                                name="Streams"
                                                fill="url(#colorStreams)"
                                                radius={[4, 4, 0, 0]}
                                            />
                                            <Line
                                                yAxisId="right"
                                                type="monotone"
                                                dataKey="hours"
                                                name="Hours"
                                                stroke="#3b82f6"
                                                strokeWidth={3}
                                                dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                                                activeDot={{ r: 6, strokeWidth: 2 }}
                                            />
                                        </ComposedChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-[350px] flex items-center justify-center text-muted-foreground">
                                        <div className="text-center">
                                            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No streaming data available for this period</p>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Individual Charts */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Streams per Day */}
                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Activity className="h-5 w-5 text-primary" />
                                        Streams per Day
                                    </CardTitle>
                                    <CardDescription>
                                        Number of streams started each day
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {analytics.streamsByDay.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={250}>
                                            <AreaChart data={analytics.streamsByDay.map(item => ({
                                                date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                                                count: item.count
                                            }))}>
                                                <defs>
                                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8} />
                                                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.1} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                                <XAxis
                                                    dataKey="date"
                                                    tick={{ fontSize: 11 }}
                                                    tickLine={false}
                                                    axisLine={false}
                                                />
                                                <YAxis
                                                    tick={{ fontSize: 11 }}
                                                    tickLine={false}
                                                    axisLine={false}
                                                    allowDecimals={false}
                                                />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Area
                                                    type="monotone"
                                                    dataKey="count"
                                                    name="Streams"
                                                    stroke="hsl(var(--primary))"
                                                    strokeWidth={2}
                                                    fill="url(#colorCount)"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                                            No data available
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Duration per Day */}
                            <Card className="border-0 shadow-lg">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Clock className="h-5 w-5 text-blue-500" />
                                        Duration per Day
                                    </CardTitle>
                                    <CardDescription>
                                        Total streaming hours each day
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {analytics.durationByDay.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={250}>
                                            <BarChart data={analytics.durationByDay.map(item => ({
                                                date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                                                hours: parseFloat(item.hours.toFixed(2))
                                            }))}>
                                                <defs>
                                                    <linearGradient id="colorDuration" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                                <XAxis
                                                    dataKey="date"
                                                    tick={{ fontSize: 11 }}
                                                    tickLine={false}
                                                    axisLine={false}
                                                />
                                                <YAxis
                                                    tick={{ fontSize: 11 }}
                                                    tickLine={false}
                                                    axisLine={false}
                                                />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Bar
                                                    dataKey="hours"
                                                    name="Hours"
                                                    fill="url(#colorDuration)"
                                                    radius={[4, 4, 0, 0]}
                                                />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                                            No data available
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Summary */}
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-background to-muted/30">
                            <CardHeader>
                                <CardTitle>Performance Summary</CardTitle>
                                <CardDescription>
                                    Key metrics for the selected period
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                    <div className="text-center p-4 rounded-lg bg-background/50">
                                        <p className="text-sm text-muted-foreground mb-1">Avg Streams/Day</p>
                                        <p className="text-3xl font-bold text-primary">
                                            {(analytics.totalStreams / days).toFixed(1)}
                                        </p>
                                    </div>
                                    <div className="text-center p-4 rounded-lg bg-background/50">
                                        <p className="text-sm text-muted-foreground mb-1">Avg Hours/Day</p>
                                        <p className="text-3xl font-bold text-blue-500">
                                            {(analytics.totalDurationHours / days).toFixed(1)}h
                                        </p>
                                    </div>
                                    <div className="text-center p-4 rounded-lg bg-background/50">
                                        <p className="text-sm text-muted-foreground mb-1">Avg Loops/Stream</p>
                                        <p className="text-3xl font-bold text-green-500">
                                            {analytics.totalStreams > 0
                                                ? (analytics.totalLoopsCompleted / analytics.totalStreams).toFixed(1)
                                                : "0"}
                                        </p>
                                    </div>
                                    <div className="text-center p-4 rounded-lg bg-background/50">
                                        <p className="text-sm text-muted-foreground mb-1">Data/Day</p>
                                        <p className="text-3xl font-bold text-purple-500">
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
                        <p className="text-sm mt-2">Start streaming to see your analytics</p>
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}
