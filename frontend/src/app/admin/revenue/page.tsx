"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    DollarSign,
    TrendingUp,
    TrendingDown,
    RefreshCcw,
    CreditCard,
    PieChart,
    BarChart3,
    AlertCircle,
    Calendar,
    ArrowUpRight,
    ArrowDownRight,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { Calendar as CalendarComponent } from "@/components/ui/calendar"
import { format, subDays, subMonths } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { RevenueAnalytics } from "@/types/admin"


function MetricCard({
    title,
    value,
    icon: Icon,
    trend,
    gradient,
    delay = 0,
    subtitle,
}: {
    title: string
    value: string
    icon: React.ComponentType<{ className?: string }>
    trend?: { value: number; isPositive: boolean }
    gradient: string
    delay?: number
    subtitle?: string
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay }}
            className="h-full"
        >
            <Card className="relative overflow-hidden border border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-all duration-300 group bg-white dark:bg-slate-900 h-full">
                <div className={cn("absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity bg-gradient-to-br", gradient)} />
                <CardContent className="p-6 h-full flex flex-col justify-between min-h-[140px]">
                    <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                            <p className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
                            {subtitle && (
                                <p className="text-xs text-muted-foreground">{subtitle}</p>
                            )}
                        </div>
                        <div className={cn(
                            "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm flex-shrink-0",
                            gradient
                        )}>
                            <Icon className="h-6 w-6 text-white" />
                        </div>
                    </div>
                    <div className="mt-3">
                        {trend !== undefined && (
                            <div className={cn(
                                "flex items-center gap-1 text-sm font-medium",
                                trend.isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400"
                            )}>
                                {trend.isPositive ? (
                                    <ArrowUpRight className="h-4 w-4" />
                                ) : (
                                    <ArrowDownRight className="h-4 w-4" />
                                )}
                                {Math.abs(trend.value).toFixed(1)}% vs previous period
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

function RevenueChart({
    data,
    title,
    description,
    type,
}: {
    data: { name: string; value: number; count: number }[]
    title: string
    description: string
    type: "plan" | "gateway"
}) {
    const total = data.reduce((sum, item) => sum + item.value, 0)
    const colors = type === "plan"
        ? ["bg-blue-500", "bg-purple-500", "bg-amber-500", "bg-emerald-500"]
        : ["bg-indigo-500", "bg-pink-500", "bg-cyan-500", "bg-orange-500"]

    return (
        <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    {type === "plan" ? <PieChart className="h-5 w-5" /> : <BarChart3 className="h-5 w-5" />}
                    {title}
                </CardTitle>
                <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent>
                {data.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                            <BarChart3 className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <p className="text-muted-foreground">No data available</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Bar visualization */}
                        <div className="h-4 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex">
                            {data.map((item, index) => {
                                const percentage = total > 0 ? (item.value / total) * 100 : 0
                                return (
                                    <div
                                        key={item.name}
                                        className={cn("h-full transition-all", colors[index % colors.length])}
                                        style={{ width: `${percentage}%` }}
                                    />
                                )
                            })}
                        </div>

                        {/* Legend */}
                        <div className="space-y-3">
                            {data.map((item, index) => {
                                const percentage = total > 0 ? (item.value / total) * 100 : 0
                                return (
                                    <div key={item.name} className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={cn("h-3 w-3 rounded-full", colors[index % colors.length])} />
                                            <span className="font-medium capitalize">{item.name}</span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <span className="text-sm text-muted-foreground">
                                                {item.count} transactions
                                            </span>
                                            <span className="font-semibold">
                                                ${item.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            </span>
                                            <span className="text-sm text-muted-foreground w-12 text-right">
                                                {percentage.toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}


export default function AdminRevenuePage() {
    const [analytics, setAnalytics] = useState<RevenueAnalytics | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Date range
    const [dateRange, setDateRange] = useState<string>("30d")
    const [startDate, setStartDate] = useState<Date | undefined>()
    const [endDate, setEndDate] = useState<Date | undefined>()

    const fetchAnalytics = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            let start: string | undefined
            let end: string | undefined

            if (dateRange === "custom" && startDate && endDate) {
                start = startDate.toISOString()
                end = endDate.toISOString()
            } else if (dateRange !== "custom") {
                const now = new Date()
                end = now.toISOString()
                switch (dateRange) {
                    case "7d":
                        start = subDays(now, 7).toISOString()
                        break
                    case "30d":
                        start = subDays(now, 30).toISOString()
                        break
                    case "90d":
                        start = subDays(now, 90).toISOString()
                        break
                    case "12m":
                        start = subMonths(now, 12).toISOString()
                        break
                }
            }

            const data = await adminApi.getRevenueAnalytics({
                start_date: start,
                end_date: end,
            })
            setAnalytics(data)
        } catch (err) {
            console.error("Failed to fetch revenue analytics:", err)
            setError("Failed to load revenue analytics. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [dateRange, startDate, endDate])

    useEffect(() => {
        fetchAnalytics()
    }, [fetchAnalytics])

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount)
    }

    const revenueByPlanData = analytics?.revenue_by_plan.map(item => ({
        name: item.plan,
        value: item.revenue,
        count: item.transaction_count,
    })) || []

    const revenueByGatewayData = analytics?.revenue_by_gateway.map(item => ({
        name: item.gateway,
        value: item.revenue,
        count: item.transaction_count,
    })) || []

    return (
        <AdminLayout breadcrumbs={[{ label: "Revenue Analytics" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Revenue Analytics
                        </h1>
                        <p className="text-muted-foreground">
                            Track revenue metrics, MRR, ARR, and payment gateway performance
                        </p>
                    </div>

                    {/* Date Range Filter */}
                    <div className="flex items-center gap-3">
                        <Select value={dateRange} onValueChange={setDateRange}>
                            <SelectTrigger className="w-[150px]">
                                <SelectValue placeholder="Select range" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="7d">Last 7 days</SelectItem>
                                <SelectItem value="30d">Last 30 days</SelectItem>
                                <SelectItem value="90d">Last 90 days</SelectItem>
                                <SelectItem value="12m">Last 12 months</SelectItem>
                                <SelectItem value="custom">Custom range</SelectItem>
                            </SelectContent>
                        </Select>

                        {dateRange === "custom" && (
                            <div className="flex items-center gap-2">
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button variant="outline" size="sm">
                                            <Calendar className="h-4 w-4 mr-2" />
                                            {startDate ? format(startDate, "PP") : "Start"}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0" align="start">
                                        <CalendarComponent
                                            mode="single"
                                            selected={startDate}
                                            onSelect={setStartDate}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                                <span className="text-muted-foreground">to</span>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button variant="outline" size="sm">
                                            <Calendar className="h-4 w-4 mr-2" />
                                            {endDate ? format(endDate, "PP") : "End"}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0" align="start">
                                        <CalendarComponent
                                            mode="single"
                                            selected={endDate}
                                            onSelect={setEndDate}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                            </div>
                        )}
                    </div>
                </motion.div>


                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="relative">
                            <div className="h-16 w-16 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 animate-spin" />
                            <DollarSign className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-emerald-500" />
                        </div>
                        <p className="mt-4 text-muted-foreground">Loading revenue analytics...</p>
                    </div>
                ) : error ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                            <AlertCircle className="h-8 w-8 text-red-500" />
                        </div>
                        <p className="text-lg font-medium text-red-500 mb-2">Failed to load analytics</p>
                        <p className="text-muted-foreground mb-4">{error}</p>
                        <Button onClick={fetchAnalytics} className="rounded-xl">
                            Try Again
                        </Button>
                    </div>
                ) : analytics ? (
                    <>
                        {/* Key Metrics */}
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <MetricCard
                                title="Monthly Recurring Revenue"
                                value={formatCurrency(analytics.mrr)}
                                icon={DollarSign}
                                trend={{ value: analytics.growth_rate, isPositive: analytics.growth_rate >= 0 }}
                                gradient="from-emerald-500 to-emerald-600"
                                delay={0}
                                subtitle="MRR"
                            />
                            <MetricCard
                                title="Annual Recurring Revenue"
                                value={formatCurrency(analytics.arr)}
                                icon={TrendingUp}
                                trend={{ value: analytics.growth_rate, isPositive: analytics.growth_rate >= 0 }}
                                gradient="from-blue-500 to-blue-600"
                                delay={0.05}
                                subtitle="ARR"
                            />
                            <MetricCard
                                title="Total Revenue"
                                value={formatCurrency(analytics.total_revenue)}
                                icon={CreditCard}
                                gradient="from-violet-500 to-violet-600"
                                delay={0.1}
                                subtitle="In selected period"
                            />
                            <MetricCard
                                title="Refund Rate"
                                value={`${analytics.refund_rate.toFixed(2)}%`}
                                icon={RefreshCcw}
                                trend={{ value: analytics.refund_rate, isPositive: analytics.refund_rate <= 2 }}
                                gradient={analytics.refund_rate > 5 ? "from-red-500 to-red-600" : "from-amber-500 to-amber-600"}
                                delay={0.15}
                                subtitle={`${analytics.refund_count} refunds (${formatCurrency(analytics.total_refunds)})`}
                            />
                        </div>

                        {/* Charts */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                            >
                                <RevenueChart
                                    data={revenueByPlanData}
                                    title="Revenue by Plan"
                                    description="Revenue breakdown by subscription plan tier"
                                    type="plan"
                                />
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.25 }}
                            >
                                <RevenueChart
                                    data={revenueByGatewayData}
                                    title="Revenue by Gateway"
                                    description="Revenue breakdown by payment gateway"
                                    type="gateway"
                                />
                            </motion.div>
                        </div>

                        {/* Period Info */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                <CardContent className="p-4">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-sm">
                                        <div className="space-y-1">
                                            <span className="text-muted-foreground">
                                                Data period: {format(new Date(analytics.period_start), "PPP")} - {format(new Date(analytics.period_end), "PPP")}
                                            </span>
                                            <p className="text-xs text-muted-foreground">
                                                💱 All amounts in USD • IDR and other currencies converted using real-time exchange rates from exchangerate-api.com
                                            </p>
                                        </div>
                                        <Button variant="ghost" size="sm" onClick={fetchAnalytics}>
                                            <RefreshCcw className="h-4 w-4 mr-2" />
                                            Refresh
                                        </Button>
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
