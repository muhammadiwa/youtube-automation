"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    CreditCard,
    Search,
    Filter,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    Users,
    TrendingUp,
    Calendar,
    MoreHorizontal,
    ArrowUpCircle,
    ArrowDownCircle,
    Clock,
    DollarSign,
    CheckCircle2,
    XCircle,
    PauseCircle,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
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
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { AdminSubscription, AdminSubscriptionFilters } from "@/types/admin"
import { SubscriptionDetailModal } from "@/components/admin/subscriptions/subscription-detail-modal"


const statusConfig: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
    active: {
        color: "text-emerald-600 dark:text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        icon: <CheckCircle2 className="h-3 w-3" />,
        label: "Active",
    },
    canceled: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        icon: <XCircle className="h-3 w-3" />,
        label: "Canceled",
    },
    past_due: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        icon: <AlertCircle className="h-3 w-3" />,
        label: "Past Due",
    },
    trialing: {
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-500/10 border-blue-500/20",
        icon: <Clock className="h-3 w-3" />,
        label: "Trial",
    },
    paused: {
        color: "text-slate-600 dark:text-slate-400",
        bg: "bg-slate-500/10 border-slate-500/20",
        icon: <PauseCircle className="h-3 w-3" />,
        label: "Paused",
    },
}

const planConfig: Record<string, { color: string; bg: string }> = {
    free: { color: "text-slate-600", bg: "bg-slate-100 dark:bg-slate-800" },
    starter: { color: "text-blue-600", bg: "bg-blue-100 dark:bg-blue-900/30" },
    professional: { color: "text-purple-600", bg: "bg-purple-100 dark:bg-purple-900/30" },
    enterprise: { color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-900/30" },
}

function StatsCard({
    title,
    value,
    icon: Icon,
    trend,
    gradient,
    delay = 0,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    trend?: { value: number; isPositive: boolean }
    gradient: string
    delay?: number
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
                <CardContent className="p-5 h-full flex flex-col justify-between min-h-[120px]">
                    <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                            <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
                        </div>
                        <div className={cn(
                            "flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm flex-shrink-0",
                            gradient
                        )}>
                            <Icon className="h-5 w-5 text-white" />
                        </div>
                    </div>
                    <div className="mt-2">
                        {trend ? (
                            <div className={cn(
                                "flex items-center gap-1 text-xs font-medium",
                                trend.isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400"
                            )}>
                                <TrendingUp className={cn("h-3 w-3", !trend.isPositive && "rotate-180")} />
                                {trend.value}% from last month
                            </div>
                        ) : (
                            <div className="h-4" />
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}


export default function AdminSubscriptionsPage() {
    const [subscriptions, setSubscriptions] = useState<AdminSubscription[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(10)
    const [totalPages, setTotalPages] = useState(0)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filters
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [planFilter, setPlanFilter] = useState<string>("all")

    // Modal state
    const [selectedSubscription, setSelectedSubscription] = useState<AdminSubscription | null>(null)
    const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)

    // Stats
    const [stats, setStats] = useState({
        total: 0,
        active: 0,
        mrr: 0,
        churnRate: 0,
    })

    const fetchSubscriptions = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const filters: AdminSubscriptionFilters = {}
            if (search) filters.user_search = search
            if (statusFilter && statusFilter !== "all") filters.status = statusFilter
            if (planFilter && planFilter !== "all") filters.plan = planFilter

            const response = await adminApi.getSubscriptions({
                page,
                page_size: pageSize,
                filters,
            })
            setSubscriptions(response.items)
            setTotal(response.total)
            setTotalPages(response.total_pages)

            // Calculate stats from response
            const activeCount = response.items.filter(s => s.status === "active").length
            setStats(prev => ({
                ...prev,
                total: response.total,
                active: activeCount,
            }))
        } catch (err) {
            console.error("Failed to fetch subscriptions:", err)
            setError("Failed to load subscriptions. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [page, pageSize, search, statusFilter, planFilter])

    const fetchRevenueStats = useCallback(async () => {
        try {
            const revenue = await adminApi.getRevenueAnalytics()
            setStats(prev => ({
                ...prev,
                mrr: revenue.mrr,
                churnRate: revenue.refund_rate,
            }))
        } catch (err) {
            console.error("Failed to fetch revenue stats:", err)
        }
    }, [])

    useEffect(() => {
        fetchSubscriptions()
    }, [fetchSubscriptions])

    useEffect(() => {
        fetchRevenueStats()
    }, [fetchRevenueStats])

    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1)
        }, 300)
        return () => clearTimeout(timer)
    }, [search])

    const handleViewSubscription = (subscription: AdminSubscription) => {
        setSelectedSubscription(subscription)
        setIsDetailModalOpen(true)
    }

    const handleSubscriptionUpdated = () => {
        fetchSubscriptions()
        fetchRevenueStats()
    }

    const clearFilters = () => {
        setSearch("")
        setStatusFilter("all")
        setPlanFilter("all")
        setPage(1)
    }

    const hasActiveFilters = search || statusFilter !== "all" || planFilter !== "all"

    const getStatusConfig = (status: string) => {
        return statusConfig[status] || statusConfig.active
    }

    const getPlanConfig = (plan: string) => {
        return planConfig[plan.toLowerCase()] || planConfig.free
    }


    return (
        <AdminLayout breadcrumbs={[{ label: "Subscriptions" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Subscription Management
                        </h1>
                        <p className="text-muted-foreground">
                            Manage user subscriptions, upgrades, and billing
                        </p>
                    </div>
                </motion.div>

                {/* Stats Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <StatsCard
                        title="Total Subscriptions"
                        value={stats.total.toLocaleString()}
                        icon={CreditCard}
                        trend={{ value: 8.5, isPositive: true }}
                        gradient="from-blue-500 to-blue-600"
                        delay={0}
                    />
                    <StatsCard
                        title="Active Subscriptions"
                        value={stats.active.toLocaleString()}
                        icon={CheckCircle2}
                        trend={{ value: 5.2, isPositive: true }}
                        gradient="from-emerald-500 to-emerald-600"
                        delay={0.05}
                    />
                    <StatsCard
                        title="Monthly Revenue"
                        value={`$${stats.mrr.toLocaleString()}`}
                        icon={DollarSign}
                        trend={{ value: 12.3, isPositive: true }}
                        gradient="from-violet-500 to-violet-600"
                        delay={0.1}
                    />
                    <StatsCard
                        title="Churn Rate"
                        value={`${stats.churnRate.toFixed(1)}%`}
                        icon={TrendingUp}
                        trend={{ value: 0.5, isPositive: false }}
                        gradient="from-amber-500 to-amber-600"
                        delay={0.15}
                    />
                </div>

                {/* Search and Filters */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardContent className="p-6">
                            <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
                                {/* Search */}
                                <div className="relative flex-1">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by user email or name..."
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        className="pl-12 h-12 text-base bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500/20"
                                    />
                                </div>

                                {/* Quick Filters */}
                                <div className="flex items-center gap-3 flex-wrap">
                                    <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[150px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="active">Active</SelectItem>
                                            <SelectItem value="canceled">Canceled</SelectItem>
                                            <SelectItem value="past_due">Past Due</SelectItem>
                                            <SelectItem value="trialing">Trial</SelectItem>
                                            <SelectItem value="paused">Paused</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    <Select value={planFilter} onValueChange={(v) => { setPlanFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[150px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Plan" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Plans</SelectItem>
                                            <SelectItem value="free">Free</SelectItem>
                                            <SelectItem value="starter">Starter</SelectItem>
                                            <SelectItem value="professional">Professional</SelectItem>
                                            <SelectItem value="enterprise">Enterprise</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    {hasActiveFilters && (
                                        <Button
                                            variant="ghost"
                                            size="lg"
                                            onClick={clearFilters}
                                            className="h-12 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                                        >
                                            Clear All
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Subscriptions Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900 overflow-hidden">
                        <CardContent className="p-0">
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-20">
                                    <div className="relative">
                                        <div className="h-16 w-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
                                        <CreditCard className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-blue-500" />
                                    </div>
                                    <p className="mt-4 text-muted-foreground">Loading subscriptions...</p>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                                        <AlertCircle className="h-8 w-8 text-red-500" />
                                    </div>
                                    <p className="text-lg font-medium text-red-500 mb-2">Failed to load subscriptions</p>
                                    <p className="text-muted-foreground mb-4">{error}</p>
                                    <Button onClick={fetchSubscriptions} className="rounded-xl">
                                        Try Again
                                    </Button>
                                </div>
                            ) : subscriptions.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-20 w-20 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                                        <CreditCard className="h-10 w-10 text-muted-foreground" />
                                    </div>
                                    <p className="text-lg font-medium mb-2">No subscriptions found</p>
                                    <p className="text-muted-foreground mb-4">Try adjusting your search or filters</p>
                                    {hasActiveFilters && (
                                        <Button variant="outline" onClick={clearFilters} className="rounded-xl">
                                            Clear Filters
                                        </Button>
                                    )}
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-slate-50/50 dark:bg-slate-800/50 hover:bg-slate-50/50 dark:hover:bg-slate-800/50">
                                                <TableHead className="font-semibold">User</TableHead>
                                                <TableHead className="font-semibold">Plan</TableHead>
                                                <TableHead className="font-semibold">Status</TableHead>
                                                <TableHead className="font-semibold">Billing Cycle</TableHead>
                                                <TableHead className="font-semibold">Period End</TableHead>
                                                <TableHead className="font-semibold">Created</TableHead>
                                                <TableHead className="w-[70px]"></TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {subscriptions.map((subscription, index) => {
                                                const statusCfg = getStatusConfig(subscription.status)
                                                const planCfg = getPlanConfig(subscription.plan_tier)
                                                return (
                                                    <motion.tr
                                                        key={subscription.id}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        transition={{ delay: index * 0.05 }}
                                                        className="group cursor-pointer hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors"
                                                        onClick={() => handleViewSubscription(subscription)}
                                                    >
                                                        <TableCell>
                                                            <div className="flex items-center gap-4">
                                                                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold text-sm shadow-lg shadow-blue-500/20">
                                                                    {(subscription.user_name || subscription.user_email || "U").charAt(0).toUpperCase()}
                                                                </div>
                                                                <div>
                                                                    <p className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                                                        {subscription.user_name || "Unknown User"}
                                                                    </p>
                                                                    <p className="text-sm text-muted-foreground">{subscription.user_email || "No email"}</p>
                                                                </div>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Badge className={cn("capitalize rounded-lg font-medium", planCfg.bg, planCfg.color)}>
                                                                {subscription.plan_tier}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "gap-1.5 font-medium rounded-lg px-3 py-1",
                                                                    statusCfg.bg,
                                                                    statusCfg.color
                                                                )}
                                                            >
                                                                {statusCfg.icon}
                                                                {statusCfg.label}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell>
                                                            <span className="capitalize text-sm">{subscription.billing_cycle}</span>
                                                        </TableCell>
                                                        <TableCell className="text-sm text-muted-foreground">
                                                            {format(new Date(subscription.current_period_end), "MMM d, yyyy")}
                                                        </TableCell>
                                                        <TableCell className="text-sm text-muted-foreground">
                                                            {formatDistanceToNow(new Date(subscription.created_at), { addSuffix: true })}
                                                        </TableCell>
                                                        <TableCell>
                                                            <DropdownMenu>
                                                                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                                                    <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <MoreHorizontal className="h-5 w-5" />
                                                                    </Button>
                                                                </DropdownMenuTrigger>
                                                                <DropdownMenuContent align="end" className="w-48">
                                                                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewSubscription(subscription) }}>
                                                                        <CreditCard className="h-4 w-4 mr-2" />
                                                                        View Details
                                                                    </DropdownMenuItem>
                                                                    <DropdownMenuSeparator />
                                                                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewSubscription(subscription) }}>
                                                                        <ArrowUpCircle className="h-4 w-4 mr-2" />
                                                                        Upgrade Plan
                                                                    </DropdownMenuItem>
                                                                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewSubscription(subscription) }}>
                                                                        <ArrowDownCircle className="h-4 w-4 mr-2" />
                                                                        Downgrade Plan
                                                                    </DropdownMenuItem>
                                                                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewSubscription(subscription) }}>
                                                                        <Clock className="h-4 w-4 mr-2" />
                                                                        Extend Subscription
                                                                    </DropdownMenuItem>
                                                                </DropdownMenuContent>
                                                            </DropdownMenu>
                                                        </TableCell>
                                                    </motion.tr>
                                                )
                                            })}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Pagination */}
                {!isLoading && !error && subscriptions.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="flex items-center justify-between"
                    >
                        <p className="text-sm text-muted-foreground">
                            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} subscriptions
                        </p>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="rounded-lg"
                            >
                                <ChevronLeft className="h-4 w-4 mr-1" />
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
                                            onClick={() => setPage(pageNum)}
                                            className={cn(
                                                "w-9 h-9 rounded-lg",
                                                page === pageNum && "bg-blue-600 hover:bg-blue-700"
                                            )}
                                        >
                                            {pageNum}
                                        </Button>
                                    )
                                })}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="rounded-lg"
                            >
                                Next
                                <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Subscription Detail Modal */}
            <SubscriptionDetailModal
                subscription={selectedSubscription}
                isOpen={isDetailModalOpen}
                onClose={() => {
                    setIsDetailModalOpen(false)
                    setSelectedSubscription(null)
                }}
                onUpdated={handleSubscriptionUpdated}
            />
        </AdminLayout>
    )
}
