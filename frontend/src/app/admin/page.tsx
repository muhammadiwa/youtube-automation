"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Users,
    CreditCard,
    TrendingUp,
    Activity,
    Video,
    DollarSign,
    BarChart3,
    Sparkles,
    ArrowUpRight,
    ArrowDownRight,
    Zap,
    Minus,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    GrowthCharts,
    RealtimePanel,
    DateRangeFilter,
    ExportButton,
    getDefaultDateRange,
    type DateRange,
} from "@/components/admin/dashboard"
import adminApi from "@/lib/api/admin"
import type { PlatformMetrics, GrowthMetrics, PeriodComparison } from "@/types/admin"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"

// Enhanced Metrics Card Component with fixed height
function EnhancedMetricsCard({
    title,
    value,
    icon: Icon,
    gradient,
    comparison,
    isLoading,
    format = "number",
    delay = 0,
}: {
    title: string
    value: number
    icon: React.ComponentType<{ className?: string }>
    gradient: string
    comparison?: PeriodComparison | null
    isLoading?: boolean
    format?: "number" | "currency"
    delay?: number
}) {
    const formatValue = (val: number) => {
        if (format === "currency") {
            return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(val)
        }
        return val.toLocaleString()
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay }}
            className="h-full"
        >
            <Card className="relative overflow-hidden border border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-all duration-300 group bg-white dark:bg-slate-900 h-full">
                <div className={cn("absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity bg-gradient-to-br", gradient)} />
                <CardContent className="p-5 h-full flex flex-col justify-between min-h-[140px]">
                    {isLoading ? (
                        <div className="space-y-3">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-8 w-28" />
                            <Skeleton className="h-3 w-20" />
                        </div>
                    ) : (
                        <>
                            <div className="flex items-start justify-between">
                                <div className="space-y-1 flex-1">
                                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                                    <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{formatValue(value)}</p>
                                </div>
                                <div className={cn(
                                    "flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm flex-shrink-0",
                                    gradient
                                )}>
                                    <Icon className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <div className="mt-3">
                                {comparison ? (
                                    <div className={cn(
                                        "flex items-center gap-1.5 text-xs font-medium",
                                        comparison.trend === "up" ? "text-emerald-600 dark:text-emerald-400" :
                                            comparison.trend === "down" ? "text-red-500 dark:text-red-400" :
                                                "text-slate-500 dark:text-slate-400"
                                    )}>
                                        {comparison.trend === "up" ? (
                                            <ArrowUpRight className="h-3.5 w-3.5" />
                                        ) : comparison.trend === "down" ? (
                                            <ArrowDownRight className="h-3.5 w-3.5" />
                                        ) : (
                                            <Minus className="h-3.5 w-3.5" />
                                        )}
                                        <span>{Math.abs(comparison.change_percent).toFixed(1)}%</span>
                                        <span className="text-slate-400 dark:text-slate-500 font-normal">vs last period</span>
                                    </div>
                                ) : (
                                    <div className="h-4" />
                                )}
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>
        </motion.div>
    )
}

export default function AdminDashboardPage() {
    const [dateRange, setDateRange] = useState<DateRange>(getDefaultDateRange())
    const [comparisonEnabled, setComparisonEnabled] = useState(true)
    const [platformMetrics, setPlatformMetrics] = useState<PlatformMetrics | null>(null)
    const [growthMetrics, setGrowthMetrics] = useState<GrowthMetrics | null>(null)
    const [isLoadingPlatform, setIsLoadingPlatform] = useState(true)
    const [isLoadingGrowth, setIsLoadingGrowth] = useState(true)

    const fetchPlatformMetrics = useCallback(async () => {
        setIsLoadingPlatform(true)
        try {
            const data = await adminApi.getPlatformMetrics({
                start_date: dateRange.startDate.toISOString(),
                end_date: dateRange.endDate.toISOString(),
            })
            setPlatformMetrics(data)
        } catch (error) {
            console.error("Failed to fetch platform metrics:", error)
        } finally {
            setIsLoadingPlatform(false)
        }
    }, [dateRange])

    const fetchGrowthMetrics = useCallback(async () => {
        setIsLoadingGrowth(true)
        try {
            const daysDiff = Math.ceil(
                (dateRange.endDate.getTime() - dateRange.startDate.getTime()) / (1000 * 60 * 60 * 24)
            )
            let granularity: "daily" | "weekly" | "monthly" = "daily"
            if (daysDiff > 90) granularity = "monthly"
            else if (daysDiff > 30) granularity = "weekly"

            const data = await adminApi.getGrowthMetrics({
                start_date: dateRange.startDate.toISOString(),
                end_date: dateRange.endDate.toISOString(),
                granularity,
            })
            setGrowthMetrics(data)
        } catch (error) {
            console.error("Failed to fetch growth metrics:", error)
        } finally {
            setIsLoadingGrowth(false)
        }
    }, [dateRange])

    useEffect(() => {
        fetchPlatformMetrics()
        fetchGrowthMetrics()
    }, [fetchPlatformMetrics, fetchGrowthMetrics])

    return (
        <AdminLayout breadcrumbs={[{ label: "Dashboard" }]}>
            <div className="space-y-6">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
                >
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <BarChart3 className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Admin Dashboard
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Platform overview and key performance metrics
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <DateRangeFilter
                            value={dateRange}
                            onChange={setDateRange}
                            showComparison={true}
                            comparisonEnabled={comparisonEnabled}
                            onComparisonChange={setComparisonEnabled}
                        />
                        <ExportButton dateRange={dateRange} />
                    </div>
                </motion.div>

                {/* Primary Metrics - Fixed height grid */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <EnhancedMetricsCard
                        title="Total Users"
                        value={platformMetrics?.total_users ?? 0}
                        icon={Users}
                        gradient="from-blue-500 to-blue-600"
                        comparison={comparisonEnabled ? platformMetrics?.users_comparison : null}
                        isLoading={isLoadingPlatform}
                        delay={0}
                    />
                    <EnhancedMetricsCard
                        title="Monthly Recurring Revenue"
                        value={platformMetrics?.mrr ?? 0}
                        icon={DollarSign}
                        gradient="from-emerald-500 to-emerald-600"
                        comparison={comparisonEnabled ? platformMetrics?.mrr_comparison : null}
                        isLoading={isLoadingPlatform}
                        format="currency"
                        delay={0.05}
                    />
                    <EnhancedMetricsCard
                        title="Annual Recurring Revenue"
                        value={platformMetrics?.arr ?? 0}
                        icon={TrendingUp}
                        gradient="from-violet-500 to-violet-600"
                        isLoading={isLoadingPlatform}
                        format="currency"
                        delay={0.1}
                    />
                    <EnhancedMetricsCard
                        title="Active Subscriptions"
                        value={platformMetrics?.active_subscriptions ?? 0}
                        icon={CreditCard}
                        gradient="from-amber-500 to-orange-500"
                        isLoading={isLoadingPlatform}
                        delay={0.15}
                    />
                </div>

                {/* Secondary Metrics */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <EnhancedMetricsCard
                        title="Active Users"
                        value={platformMetrics?.active_users ?? 0}
                        icon={Zap}
                        gradient="from-cyan-500 to-cyan-600"
                        isLoading={isLoadingPlatform}
                        delay={0.2}
                    />
                    <EnhancedMetricsCard
                        title="New Users"
                        value={platformMetrics?.new_users ?? 0}
                        icon={Sparkles}
                        gradient="from-pink-500 to-rose-500"
                        isLoading={isLoadingPlatform}
                        delay={0.25}
                    />
                    <EnhancedMetricsCard
                        title="Total Streams"
                        value={platformMetrics?.total_streams ?? 0}
                        icon={Activity}
                        gradient="from-red-500 to-red-600"
                        comparison={comparisonEnabled ? platformMetrics?.streams_comparison : null}
                        isLoading={isLoadingPlatform}
                        delay={0.3}
                    />
                    <EnhancedMetricsCard
                        title="Total Videos"
                        value={platformMetrics?.total_videos ?? 0}
                        icon={Video}
                        gradient="from-purple-500 to-purple-600"
                        isLoading={isLoadingPlatform}
                        delay={0.35}
                    />
                </div>

                {/* Real-time Metrics Panel */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                >
                    <RealtimePanel autoRefresh={true} refreshInterval={30} />
                </motion.div>

                {/* Growth Charts */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.45 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardHeader className="pb-4">
                            <CardTitle className="text-lg flex items-center gap-3">
                                <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
                                    <TrendingUp className="h-4 w-4 text-white" />
                                </div>
                                <span className="text-slate-900 dark:text-white">Growth Trends</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-0">
                            <GrowthCharts data={growthMetrics} isLoading={isLoadingGrowth} />
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </AdminLayout>
    )
}
