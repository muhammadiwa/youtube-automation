"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts"
import { format, parseISO } from "date-fns"
import type { GrowthMetrics } from "@/types/admin"

interface GrowthChartsProps {
    data: GrowthMetrics | null
    isLoading?: boolean
}

function formatDate(dateStr: string, granularity: string): string {
    try {
        const date = parseISO(dateStr)
        switch (granularity) {
            case "daily":
                return format(date, "MMM d")
            case "weekly":
                return format(date, "MMM d")
            case "monthly":
                return format(date, "MMM yyyy")
            default:
                return format(date, "MMM d")
        }
    } catch {
        return dateStr
    }
}

function formatCurrency(value: number): string {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value)
}

function ChartSkeleton() {
    return (
        <Card className="border-0 shadow-md">
            <CardHeader className="pb-2">
                <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
                <Skeleton className="h-[250px] w-full" />
            </CardContent>
        </Card>
    )
}

export function GrowthCharts({ data, isLoading }: GrowthChartsProps) {
    if (isLoading || !data) {
        return (
            <div className="grid gap-6 lg:grid-cols-2">
                <ChartSkeleton />
                <ChartSkeleton />
                <ChartSkeleton />
            </div>
        )
    }

    const granularity = data.granularity

    // Transform user growth data
    const userGrowthData = data.user_growth.map((point) => ({
        date: formatDate(point.date, granularity),
        users: point.value,
    }))

    // Transform revenue growth data
    const revenueGrowthData = data.revenue_growth.map((point) => ({
        date: formatDate(point.date, granularity),
        revenue: point.value,
    }))

    // Transform churn data
    const churnData = data.churn_data.map((point) => ({
        date: formatDate(point.date, granularity),
        churn: point.value,
    }))

    return (
        <div className="grid gap-6 lg:grid-cols-2">
            {/* User Growth Chart */}
            <Card className="border-0 shadow-md">
                <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-semibold">User Growth</CardTitle>
                        <span className="text-sm text-muted-foreground">
                            {data.user_growth_rate >= 0 ? "+" : ""}{data.user_growth_rate.toFixed(1)}% growth
                        </span>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={userGrowthData}>
                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => value.toLocaleString()}
                                />
                                <Tooltip
                                    formatter={(value: number) => [value.toLocaleString(), "Users"]}
                                    contentStyle={{
                                        backgroundColor: "hsl(var(--background))",
                                        border: "1px solid hsl(var(--border))",
                                        borderRadius: "8px",
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="users"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Revenue Growth Chart */}
            <Card className="border-0 shadow-md">
                <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-semibold">Revenue Growth</CardTitle>
                        <span className="text-sm text-muted-foreground">
                            {data.revenue_growth_rate >= 0 ? "+" : ""}{data.revenue_growth_rate.toFixed(1)}% growth
                        </span>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={revenueGrowthData}>
                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => formatCurrency(value)}
                                />
                                <Tooltip
                                    formatter={(value: number) => [formatCurrency(value), "Revenue"]}
                                    contentStyle={{
                                        backgroundColor: "hsl(var(--background))",
                                        border: "1px solid hsl(var(--border))",
                                        borderRadius: "8px",
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="revenue"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Churn Rate Chart */}
            <Card className="border-0 shadow-md lg:col-span-2">
                <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-semibold">Churn Rate</CardTitle>
                        <span className="text-sm text-muted-foreground">
                            Current: {data.current_churn_rate.toFixed(2)}%
                        </span>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={churnData}>
                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    tick={{ fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `${value}%`}
                                />
                                <Tooltip
                                    formatter={(value: number) => [`${value.toFixed(2)}%`, "Churn Rate"]}
                                    contentStyle={{
                                        backgroundColor: "hsl(var(--background))",
                                        border: "1px solid hsl(var(--border))",
                                        borderRadius: "8px",
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="churn"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
