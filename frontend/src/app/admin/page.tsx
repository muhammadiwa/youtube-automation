"use client"

import { useState, useEffect, useCallback } from "react"
import {
    Users,
    CreditCard,
    TrendingUp,
    Activity,
    Video,
    DollarSign,
    BarChart3,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import {
    MetricsCard,
    GrowthCharts,
    RealtimePanel,
    DateRangeFilter,
    ExportButton,
    getDefaultDateRange,
    type DateRange,
} from "@/components/admin/dashboard"
import adminApi from "@/lib/api/admin"
import type { PlatformMetrics, GrowthMetrics } from "@/types/admin"

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
            // Determine granularity based on date range
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
                {/* Header with filters */}
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <BarChart3 className="h-6 w-6 text-blue-500" />
                            Admin Dashboard
                        </h1>
                        <p className="text-muted-foreground text-sm mt-1">
                            Platform overview and key metrics
                        </p>
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
                </div>

                {/* Key Metrics Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <MetricsCard
                        title="Total Users"
                        value={platformMetrics?.total_users ?? 0}
                        icon={Users}
                        iconColor="text-blue-500"
                        comparison={comparisonEnabled ? platformMetrics?.users_comparison : null}
                        isLoading={isLoadingPlatform}
                    />
                    <MetricsCard
                        title="Monthly Recurring Revenue"
                        value={platformMetrics?.mrr ?? 0}
                        icon={DollarSign}
                        iconColor="text-green-500"
                        comparison={comparisonEnabled ? platformMetrics?.mrr_comparison : null}
                        isLoading={isLoadingPlatform}
                        format="currency"
                    />
                    <MetricsCard
                        title="Annual Recurring Revenue"
                        value={platformMetrics?.arr ?? 0}
                        icon={TrendingUp}
                        iconColor="text-purple-500"
                        isLoading={isLoadingPlatform}
                        format="currency"
                    />
                    <MetricsCard
                        title="Active Subscriptions"
                        value={platformMetrics?.active_subscriptions ?? 0}
                        icon={CreditCard}
                        iconColor="text-orange-500"
                        isLoading={isLoadingPlatform}
                    />
                </div>

                {/* Secondary Metrics */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <MetricsCard
                        title="Active Users"
                        value={platformMetrics?.active_users ?? 0}
                        icon={Users}
                        iconColor="text-cyan-500"
                        isLoading={isLoadingPlatform}
                    />
                    <MetricsCard
                        title="New Users"
                        value={platformMetrics?.new_users ?? 0}
                        icon={Users}
                        iconColor="text-emerald-500"
                        isLoading={isLoadingPlatform}
                    />
                    <MetricsCard
                        title="Total Streams"
                        value={platformMetrics?.total_streams ?? 0}
                        icon={Activity}
                        iconColor="text-red-500"
                        comparison={comparisonEnabled ? platformMetrics?.streams_comparison : null}
                        isLoading={isLoadingPlatform}
                    />
                    <MetricsCard
                        title="Total Videos"
                        value={platformMetrics?.total_videos ?? 0}
                        icon={Video}
                        iconColor="text-pink-500"
                        isLoading={isLoadingPlatform}
                    />
                </div>

                {/* Real-time Metrics Panel */}
                <RealtimePanel autoRefresh={true} refreshInterval={30} />

                {/* Growth Charts */}
                <div>
                    <h2 className="text-lg font-semibold mb-4">Growth Trends</h2>
                    <GrowthCharts data={growthMetrics} isLoading={isLoadingGrowth} />
                </div>
            </div>
        </AdminLayout>
    )
}
