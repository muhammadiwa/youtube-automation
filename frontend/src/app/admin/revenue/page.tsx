"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    DollarSign,
    TrendingUp,
    TrendingDown,
    RefreshCcw,
    CreditCard,
    Calendar,
    ArrowUpRight,
    ArrowDownRight,
    Wallet,
    PiggyBank,
    Receipt,
    Sparkles,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar as CalendarComponent } from "@/components/ui/calendar"
import { Skeleton } from "@/components/ui/skeleton"
import { format, subDays, subMonths } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { RevenueAnalytics } from "@/types/admin"
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts"

// Animated counter component
function AnimatedCounter({ value, prefix = "", suffix = "", duration = 1000 }: {
    value: number
    prefix?: string
    suffix?: string
    duration?: number
}) {
    const [displayValue, setDisplayValue] = useState(0)

    useEffect(() => {
        let startTime: number
        let animationFrame: number

        const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp
            const progress = Math.min((timestamp - startTime) / duration, 1)
            setDisplayValue(Math.floor(progress * value))
            if (progress < 1) {
                animationFrame = requestAnimationFrame(animate)
            }
        }

        animationFrame = requestAnimationFrame(animate)
        return () => cancelAnimationFrame(animationFrame)
    }, [value, duration])

    return (
        <span>
            {prefix}{displayValue.toLocaleString()}{suffix}
        </span>
    )
}

// Gradient colors for charts
const CHART_COLORS = {
    primary: ["#3b82f6", "#8b5cf6"],
    success: ["#10b981", "#34d399"],
    warning: ["#f59e0b", "#fbbf24"],
    danger: ["#ef4444", "#f87171"],
}

const PIE_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#06b6d4"]

export default function AdminRevenuePage() {
    const [analytics, setAnalytics] = useState<RevenueAnalytics | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
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
                    case "7d": start = subDays(now, 7).toISOString(); break
                    case "30d": start = subDays(now, 30).toISOString(); break
                    case "90d": start = subDays(now, 90).toISOString(); break
                    case "12m": start = subMonths(now, 12).toISOString(); break
                }
            }

            const data = await adminApi.getRevenueAnalytics({ start_date: start, end_date: end })
            setAnalytics(data)
        } catch (err) {
            console.error("Failed to fetch revenue analytics:", err)
            setError("Failed to load revenue analytics")
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

    // Prepare chart data
    const revenueByPlanData = analytics?.revenue_by_plan.map(item => ({
        name: item.plan.charAt(0).toUpperCase() + item.plan.slice(1),
        value: item.revenue,
        count: item.transaction_count,
    })) || []

    const revenueByGatewayData = analytics?.revenue_by_gateway.map(item => ({
        name: item.gateway.charAt(0).toUpperCase() + item.gateway.slice(1),
        value: item.revenue,
        count: item.transaction_count,
    })) || []

    // Mock trend data for area chart (in real app, this would come from API)
    const trendData = [
        { month: "Jan", revenue: analytics?.mrr ? analytics.mrr * 0.7 : 0 },
        { month: "Feb", revenue: analytics?.mrr ? analytics.mrr * 0.75 : 0 },
        { month: "Mar", revenue: analytics?.mrr ? analytics.mrr * 0.8 : 0 },
        { month: "Apr", revenue: analytics?.mrr ? analytics.mrr * 0.85 : 0 },
        { month: "May", revenue: analytics?.mrr ? analytics.mrr * 0.9 : 0 },
        { month: "Jun", revenue: analytics?.mrr ? analytics.mrr : 0 },
    ]

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
                        <div className="flex items-center gap-3">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
                                className="h-12 w-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25"
                            >
                                <DollarSign className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                                    Revenue Analytics
                                </h1>
                                <p className="text-muted-foreground">
                                    Track your revenue metrics and financial performance
                                </p>
                            </div>
                        </div>
                    </div>

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
                                        <CalendarComponent mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
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
                                        <CalendarComponent mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                                    </PopoverContent>
                                </Popover>
                            </div>
                        )}

                        <Button variant="outline" size="icon" onClick={fetchAnalytics} disabled={isLoading}>
                            <RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                        </Button>
                    </div>
                </motion.div>

                {isLoading ? (
                    <div className="space-y-6">
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {[1, 2, 3, 4].map((i) => (
                                <Card key={i}>
                                    <CardContent className="p-6">
                                        <Skeleton className="h-4 w-24 mb-2" />
                                        <Skeleton className="h-8 w-32" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                        <div className="grid gap-6 lg:grid-cols-2">
                            <Card><CardContent className="p-6"><Skeleton className="h-[300px]" /></CardContent></Card>
                            <Card><CardContent className="p-6"><Skeleton className="h-[300px]" /></CardContent></Card>
                        </div>
                    </div>
                ) : error ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex flex-col items-center justify-center py-20 text-center"
                    >
                        <div className="h-20 w-20 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                            <TrendingDown className="h-10 w-10 text-red-500" />
                        </div>
                        <p className="text-lg font-medium text-red-500 mb-2">Failed to load analytics</p>
                        <p className="text-muted-foreground mb-4">{error}</p>
                        <Button onClick={fetchAnalytics}>Try Again</Button>
                    </motion.div>
                ) : analytics ? (
                    <>
                        {/* Key Metrics Cards */}
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {/* MRR Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                            >
                                <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-xl shadow-emerald-500/20">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                                    <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full translate-y-12 -translate-x-12" />
                                    <CardContent className="p-6 relative">
                                        <div className="flex items-center justify-between mb-4">
                                            <p className="text-sm font-medium text-emerald-100">Monthly Recurring Revenue</p>
                                            <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                                                <Wallet className="h-5 w-5" />
                                            </div>
                                        </div>
                                        <p className="text-3xl font-bold mb-2">
                                            <AnimatedCounter value={analytics.mrr} prefix="$" />
                                        </p>
                                        <div className={cn(
                                            "flex items-center gap-1 text-sm",
                                            analytics.growth_rate >= 0 ? "text-emerald-100" : "text-red-200"
                                        )}>
                                            {analytics.growth_rate >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                                            {Math.abs(analytics.growth_rate).toFixed(1)}% vs last period
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* ARR Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.15 }}
                            >
                                <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-xl shadow-blue-500/20">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                                    <CardContent className="p-6 relative">
                                        <div className="flex items-center justify-between mb-4">
                                            <p className="text-sm font-medium text-blue-100">Annual Recurring Revenue</p>
                                            <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                                                <PiggyBank className="h-5 w-5" />
                                            </div>
                                        </div>
                                        <p className="text-3xl font-bold mb-2">
                                            <AnimatedCounter value={analytics.arr} prefix="$" />
                                        </p>
                                        <p className="text-sm text-blue-100">Projected annual revenue</p>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* Total Revenue Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                            >
                                <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-xl shadow-violet-500/20">
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                                    <CardContent className="p-6 relative">
                                        <div className="flex items-center justify-between mb-4">
                                            <p className="text-sm font-medium text-violet-100">Total Revenue</p>
                                            <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                                                <CreditCard className="h-5 w-5" />
                                            </div>
                                        </div>
                                        <p className="text-3xl font-bold mb-2">
                                            <AnimatedCounter value={analytics.total_revenue} prefix="$" />
                                        </p>
                                        <p className="text-sm text-violet-100">In selected period</p>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* Refund Rate Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.25 }}
                            >
                                <Card className={cn(
                                    "relative overflow-hidden border-0 text-white shadow-xl",
                                    analytics.refund_rate > 5
                                        ? "bg-gradient-to-br from-red-500 to-rose-600 shadow-red-500/20"
                                        : "bg-gradient-to-br from-amber-500 to-orange-600 shadow-amber-500/20"
                                )}>
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                                    <CardContent className="p-6 relative">
                                        <div className="flex items-center justify-between mb-4">
                                            <p className="text-sm font-medium opacity-90">Refund Rate</p>
                                            <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                                                <Receipt className="h-5 w-5" />
                                            </div>
                                        </div>
                                        <p className="text-3xl font-bold mb-2">{analytics.refund_rate.toFixed(2)}%</p>
                                        <p className="text-sm opacity-90">
                                            {analytics.refund_count} refunds ({formatCurrency(analytics.total_refunds)})
                                        </p>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Charts Section */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Revenue Trend Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                            >
                                <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                    <CardHeader>
                                        <div className="flex items-center gap-2">
                                            <Sparkles className="h-5 w-5 text-emerald-500" />
                                            <CardTitle>Revenue Trend</CardTitle>
                                        </div>
                                        <CardDescription>Monthly revenue growth over time</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-[300px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={trendData}>
                                                    <defs>
                                                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                                    <XAxis dataKey="month" className="text-xs" />
                                                    <YAxis className="text-xs" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                                                    <Tooltip
                                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                                                        formatter={(value: number) => [formatCurrency(value), "Revenue"]}
                                                    />
                                                    <Area
                                                        type="monotone"
                                                        dataKey="revenue"
                                                        stroke="#10b981"
                                                        strokeWidth={3}
                                                        fill="url(#revenueGradient)"
                                                    />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* Revenue by Plan - Pie Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.35 }}
                            >
                                <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                    <CardHeader>
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="h-5 w-5 text-blue-500" />
                                            <CardTitle>Revenue by Plan</CardTitle>
                                        </div>
                                        <CardDescription>Distribution across subscription tiers</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-[300px]">
                                            {revenueByPlanData.length > 0 ? (
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <PieChart>
                                                        <Pie
                                                            data={revenueByPlanData}
                                                            cx="50%"
                                                            cy="50%"
                                                            innerRadius={60}
                                                            outerRadius={100}
                                                            paddingAngle={5}
                                                            dataKey="value"
                                                            animationBegin={0}
                                                            animationDuration={1000}
                                                        >
                                                            {revenueByPlanData.map((_, index) => (
                                                                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                                            ))}
                                                        </Pie>
                                                        <Tooltip
                                                            contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                                                            formatter={(value: number) => [formatCurrency(value), "Revenue"]}
                                                        />
                                                        <Legend />
                                                    </PieChart>
                                                </ResponsiveContainer>
                                            ) : (
                                                <div className="h-full flex items-center justify-center text-muted-foreground">
                                                    No plan data available
                                                </div>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Revenue by Gateway - Bar Chart */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Wallet className="h-5 w-5 text-violet-500" />
                                        <CardTitle>Revenue by Payment Gateway</CardTitle>
                                    </div>
                                    <CardDescription>Transaction volume and revenue per gateway</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        {revenueByGatewayData.length > 0 ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={revenueByGatewayData} layout="vertical">
                                                    <defs>
                                                        <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                                                            <stop offset="0%" stopColor="#8b5cf6" />
                                                            <stop offset="100%" stopColor="#a78bfa" />
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
                                                    <XAxis type="number" className="text-xs" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                                                    <YAxis type="category" dataKey="name" className="text-xs" width={80} />
                                                    <Tooltip
                                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                                                        formatter={(value: number, name: string) => {
                                                            if (name === "value") return [formatCurrency(value), "Revenue"]
                                                            return [value, name]
                                                        }}
                                                    />
                                                    <Bar dataKey="value" fill="url(#barGradient)" radius={[0, 8, 8, 0]} animationDuration={1000} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        ) : (
                                            <div className="h-full flex items-center justify-center text-muted-foreground">
                                                No gateway data available
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Period Info */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.45 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
                                <CardContent className="p-4">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-sm">
                                        <div className="space-y-1">
                                            <span className="text-muted-foreground">
                                                📅 Data period: {format(new Date(analytics.period_start), "PPP")} - {format(new Date(analytics.period_end), "PPP")}
                                            </span>
                                            <p className="text-xs text-muted-foreground">
                                                💱 All amounts in USD • IDR and other currencies converted using real-time exchange rates
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
