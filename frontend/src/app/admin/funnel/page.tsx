"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    TrendingDown,
    Users,
    Target,
    ArrowDown,
    RefreshCcw,
    Calendar,
    AlertCircle,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar as CalendarComponent } from "@/components/ui/calendar"
import { cn } from "@/lib/utils"
import { format, subDays } from "date-fns"
import adminApi from "@/lib/api/admin"
import type { FunnelAnalysisResponse } from "@/types/admin"

const stageColors = [
    "bg-blue-500",
    "bg-indigo-500",
    "bg-violet-500",
    "bg-purple-500",
    "bg-fuchsia-500",
    "bg-pink-500",
]

function getStageColor(index: number): string {
    return stageColors[index % stageColors.length]
}

export default function FunnelAnalysisPage() {
    const [data, setData] = useState<FunnelAnalysisResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [refreshing, setRefreshing] = useState(false)
    const [dateRange, setDateRange] = useState<{ from: Date; to: Date }>({
        from: subDays(new Date(), 30),
        to: new Date(),
    })

    const fetchFunnelData = useCallback(async () => {
        try {
            setError(null)
            const response = await adminApi.getFunnelAnalysis({
                start_date: dateRange.from.toISOString(),
                end_date: dateRange.to.toISOString(),
            })
            setData(response)
        } catch (err) {
            setError("Failed to load funnel analysis data")
            console.error("Funnel analysis error:", err)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }, [dateRange])

    useEffect(() => {
        setLoading(true)
        fetchFunnelData()
    }, [fetchFunnelData])

    const handleRefresh = () => {
        setRefreshing(true)
        fetchFunnelData()
    }

    const maxCount = data?.stages.reduce((max, stage) => Math.max(max, stage.count), 0) || 1

    return (
        <AdminLayout breadcrumbs={[{ label: "Funnel Analysis" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Funnel Analysis
                        </h1>
                        <p className="text-muted-foreground">
                            User conversion rates through the signup and activation funnel
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button variant="outline" className="w-[240px] justify-start text-left font-normal">
                                    <Calendar className="mr-2 h-4 w-4" />
                                    {format(dateRange.from, "MMM d")} - {format(dateRange.to, "MMM d, yyyy")}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="end">
                                <CalendarComponent
                                    mode="range"
                                    selected={{ from: dateRange.from, to: dateRange.to }}
                                    onSelect={(range) => {
                                        if (range?.from && range?.to) {
                                            setDateRange({ from: range.from, to: range.to })
                                        }
                                    }}
                                    numberOfMonths={2}
                                />
                            </PopoverContent>
                        </Popover>
                        <Button variant="outline" size="icon" onClick={handleRefresh} disabled={refreshing}>
                            <RefreshCcw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                        </Button>
                    </div>
                </motion.div>

                {loading ? (
                    <div className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-3">
                            {[1, 2, 3].map((i) => (
                                <Card key={i}>
                                    <CardHeader className="pb-2">
                                        <Skeleton className="h-4 w-24" />
                                    </CardHeader>
                                    <CardContent>
                                        <Skeleton className="h-8 w-20" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                        <Card>
                            <CardHeader>
                                <Skeleton className="h-6 w-40" />
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <Skeleton key={i} className="h-16 w-full" />
                                ))}
                            </CardContent>
                        </Card>
                    </div>
                ) : error ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                            <AlertCircle className="h-8 w-8 text-red-500" />
                        </div>
                        <p className="text-lg font-medium text-red-500 mb-2">Failed to load funnel data</p>
                        <p className="text-muted-foreground mb-4">{error}</p>
                        <Button onClick={handleRefresh} className="rounded-xl">
                            Try Again
                        </Button>
                    </div>
                ) : data ? (
                    <>
                        {/* Summary Cards */}
                        <div className="grid gap-4 md:grid-cols-3">
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">Overall Conversion</CardTitle>
                                        <Target className="h-4 w-4 text-muted-foreground" />
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold text-emerald-600">
                                            {data.overall_conversion.toFixed(1)}%
                                        </div>
                                        <p className="text-xs text-muted-foreground">From signup to paid conversion</p>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">Total Signups</CardTitle>
                                        <Users className="h-4 w-4 text-muted-foreground" />
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">{data.stages[0]?.count.toLocaleString() || 0}</div>
                                        <p className="text-xs text-muted-foreground">Users entering the funnel</p>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">Biggest Drop-off</CardTitle>
                                        <TrendingDown className="h-4 w-4 text-muted-foreground" />
                                    </CardHeader>
                                    <CardContent>
                                        {data.stages.length > 0 ? (
                                            <>
                                                <div className="text-2xl font-bold text-red-600">
                                                    {Math.max(...data.stages.map(s => s.drop_off_rate)).toFixed(1)}%
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    {data.stages.find(s => s.drop_off_rate === Math.max(...data.stages.map(st => st.drop_off_rate)))?.stage || "N/A"}
                                                </p>
                                            </>
                                        ) : (
                                            <div className="text-2xl font-bold">-</div>
                                        )}
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Funnel Visualization */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                            <Card>
                                <CardHeader>
                                    <CardTitle>Conversion Funnel</CardTitle>
                                    <CardDescription>User journey from signup to paid subscription</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {data.stages.length > 0 ? (
                                        <div className="space-y-2">
                                            {data.stages.map((stage, index) => (
                                                <div key={stage.stage} className="relative">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-32 text-sm font-medium truncate">{stage.stage}</div>
                                                        <div className="flex-1 relative">
                                                            <div className="h-12 bg-muted rounded-lg overflow-hidden">
                                                                <motion.div
                                                                    initial={{ width: 0 }}
                                                                    animate={{ width: `${(stage.count / maxCount) * 100}%` }}
                                                                    transition={{ duration: 0.5, delay: index * 0.1 }}
                                                                    className={cn("h-full rounded-lg flex items-center justify-end pr-3", getStageColor(index))}
                                                                >
                                                                    <span className="text-white font-semibold text-sm">{stage.count.toLocaleString()}</span>
                                                                </motion.div>
                                                            </div>
                                                        </div>
                                                        <div className="w-20 text-right">
                                                            <span className="text-sm font-semibold text-emerald-600">{stage.conversion_rate.toFixed(1)}%</span>
                                                        </div>
                                                    </div>
                                                    {index < data.stages.length - 1 && (
                                                        <div className="flex items-center gap-4 py-1">
                                                            <div className="w-32" />
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <ArrowDown className="h-4 w-4 text-muted-foreground" />
                                                                <span className="ml-2 text-xs text-red-500">-{stage.drop_off_rate.toFixed(1)}% drop-off</span>
                                                            </div>
                                                            <div className="w-20" />
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="flex items-center justify-center py-12 text-muted-foreground">No funnel data available</div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Stage Details Table */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                            <Card>
                                <CardHeader>
                                    <CardTitle>Stage Details</CardTitle>
                                    <CardDescription>Detailed metrics for each funnel stage</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="text-left p-3 text-sm font-medium text-muted-foreground">Stage</th>
                                                    <th className="text-right p-3 text-sm font-medium text-muted-foreground">Users</th>
                                                    <th className="text-right p-3 text-sm font-medium text-muted-foreground">Conversion Rate</th>
                                                    <th className="text-right p-3 text-sm font-medium text-muted-foreground">Drop-off Rate</th>
                                                    <th className="text-right p-3 text-sm font-medium text-muted-foreground">% of Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {data.stages.map((stage, index) => (
                                                    <tr key={stage.stage} className="border-b border-border/50 hover:bg-muted/50">
                                                        <td className="p-3">
                                                            <div className="flex items-center gap-2">
                                                                <div className={cn("w-3 h-3 rounded-full", getStageColor(index))} />
                                                                <span className="font-medium">{stage.stage}</span>
                                                            </div>
                                                        </td>
                                                        <td className="p-3 text-right font-mono">
                                                            {stage.count.toLocaleString()}
                                                        </td>
                                                        <td className="p-3 text-right">
                                                            <span className="text-emerald-600 font-semibold">
                                                                {stage.conversion_rate.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                        <td className="p-3 text-right">
                                                            <span className={cn(
                                                                "font-semibold",
                                                                stage.drop_off_rate > 30 ? "text-red-600" :
                                                                    stage.drop_off_rate > 15 ? "text-orange-600" : "text-muted-foreground"
                                                            )}>
                                                                {stage.drop_off_rate.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                        <td className="p-3 text-right text-muted-foreground">
                                                            {((stage.count / (data.stages[0]?.count || 1)) * 100).toFixed(1)}%
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </>
                ) : null}
            </div>
        </AdminLayout>
    )
}
