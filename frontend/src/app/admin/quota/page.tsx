"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Gauge,
    RefreshCw,
    AlertTriangle,
    CheckCircle2,
    Users,
    Youtube,
    TrendingUp,
    AlertCircle,
    ChevronDown,
    ChevronRight,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    QuotaDashboardResponse,
    QuotaAlertsResponse,
    UserQuotaUsage,
} from "@/types/admin"

// Helper functions
function getUsageColor(percent: number): string {
    if (percent >= 90) return "text-red-600 dark:text-red-400"
    if (percent >= 80) return "text-amber-600 dark:text-amber-400"
    return "text-emerald-600 dark:text-emerald-400"
}

function getProgressColor(percent: number): string {
    if (percent >= 90) return "bg-red-500"
    if (percent >= 80) return "bg-amber-500"
    return "bg-emerald-500"
}

// User Quota Row Component
function UserQuotaRow({ user }: { user: UserQuotaUsage }) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <>
            <TableRow className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <TableCell>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="p-0 h-auto"
                        onClick={() => setIsOpen(!isOpen)}
                    >
                        {isOpen ? (
                            <ChevronDown className="h-4 w-4 mr-2" />
                        ) : (
                            <ChevronRight className="h-4 w-4 mr-2" />
                        )}
                    </Button>
                </TableCell>
                <TableCell>
                    <div>
                        <p className="font-medium text-slate-900 dark:text-white">
                            {user.user_name || "Unknown"}
                        </p>
                        <p className="text-sm text-slate-500">{user.user_email}</p>
                    </div>
                </TableCell>
                <TableCell className="text-center">
                    <Badge variant="outline">{user.account_count}</Badge>
                </TableCell>
                <TableCell className="text-right">
                    {user.total_quota_used.toLocaleString()}
                </TableCell>
                <TableCell>
                    <div className="flex items-center gap-2">
                        <Progress
                            value={user.highest_usage_percent}
                            className={cn("w-20 h-2", getProgressColor(user.highest_usage_percent))}
                        />
                        <span className={cn("text-sm font-medium", getUsageColor(user.highest_usage_percent))}>
                            {user.highest_usage_percent.toFixed(1)}%
                        </span>
                    </div>
                </TableCell>
                <TableCell className="text-right">
                    {user.highest_usage_percent >= 80 ? (
                        <Badge variant="destructive" className="gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            High Usage
                        </Badge>
                    ) : (
                        <Badge variant="secondary" className="gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            Normal
                        </Badge>
                    )}
                </TableCell>
            </TableRow>
            {isOpen && (
                <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td colSpan={6} className="p-0">
                        <div className="px-8 py-4">
                            <h4 className="text-sm font-medium mb-3 text-slate-700 dark:text-slate-300">
                                Account Details
                            </h4>
                            <div className="grid gap-3">
                                {user.accounts.map((account) => (
                                    <div
                                        key={account.account_id}
                                        className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                                                <Youtube className="h-4 w-4 text-red-600" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-sm">{account.channel_title}</p>
                                                <p className="text-xs text-slate-500">
                                                    {account.daily_quota_used.toLocaleString()} / {account.daily_quota_limit.toLocaleString()} quota
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <Progress
                                                value={account.usage_percent}
                                                className={cn("w-24 h-2", getProgressColor(account.usage_percent))}
                                            />
                                            <span className={cn("text-sm font-medium w-14 text-right", getUsageColor(account.usage_percent))}>
                                                {account.usage_percent.toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </td>
                </tr>
            )}
        </>
    )
}


// Alerts Panel
function AlertsPanel({ data, isLoading }: { data: QuotaAlertsResponse | null; isLoading: boolean }) {
    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-40 w-full" />
                </CardContent>
            </Card>
        )
    }

    if (!data) return null

    return (
        <Card className="border border-slate-200/60 dark:border-slate-700/60">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        Quota Alerts
                    </CardTitle>
                    <div className="flex gap-2">
                        {data.critical_count > 0 && (
                            <Badge variant="destructive">{data.critical_count} Critical (&gt;90%)</Badge>
                        )}
                        {data.warning_count > 0 && (
                            <Badge variant="outline" className="border-amber-500 text-amber-600">
                                {data.warning_count} Warning (&gt;80%)
                            </Badge>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {data.alerts.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                        <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500" />
                        <p>No quota alerts - all accounts within normal usage</p>
                    </div>
                ) : (
                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                        {data.alerts.map((alert) => (
                            <div
                                key={alert.id}
                                className={cn(
                                    "p-4 rounded-lg border",
                                    alert.usage_percent >= 90
                                        ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                                        : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
                                )}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3">
                                        <div className={cn(
                                            "h-10 w-10 rounded-full flex items-center justify-center",
                                            alert.usage_percent >= 90
                                                ? "bg-red-100 dark:bg-red-900/50"
                                                : "bg-amber-100 dark:bg-amber-900/50"
                                        )}>
                                            <AlertCircle className={cn(
                                                "h-5 w-5",
                                                alert.usage_percent >= 90 ? "text-red-600" : "text-amber-600"
                                            )} />
                                        </div>
                                        <div>
                                            <p className="font-medium text-slate-900 dark:text-white">
                                                {alert.channel_title}
                                            </p>
                                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                                {alert.user_email}
                                            </p>
                                            <p className="text-sm text-slate-500 mt-1">
                                                {alert.quota_used.toLocaleString()} / {alert.quota_limit.toLocaleString()} quota used
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={cn(
                                            "text-2xl font-bold",
                                            getUsageColor(alert.usage_percent)
                                        )}>
                                            {alert.usage_percent.toFixed(1)}%
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1">
                                            Triggered {new Date(alert.triggered_at).toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

// Main Page Component
export default function QuotaDashboardPage() {
    const [dashboardData, setDashboardData] = useState<QuotaDashboardResponse | null>(null)
    const [alertsData, setAlertsData] = useState<QuotaAlertsResponse | null>(null)
    const [isLoadingDashboard, setIsLoadingDashboard] = useState(true)
    const [isLoadingAlerts, setIsLoadingAlerts] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const fetchDashboardData = useCallback(async () => {
        try {
            const data = await adminApi.getQuotaDashboard()
            setDashboardData(data)
        } catch (error) {
            console.error("Failed to fetch quota dashboard:", error)
        } finally {
            setIsLoadingDashboard(false)
        }
    }, [])

    const fetchAlertsData = useCallback(async () => {
        try {
            const data = await adminApi.getQuotaAlerts()
            setAlertsData(data)
        } catch (error) {
            console.error("Failed to fetch quota alerts:", error)
        } finally {
            setIsLoadingAlerts(false)
        }
    }, [])

    const refreshAll = useCallback(async () => {
        setIsRefreshing(true)
        await Promise.all([fetchDashboardData(), fetchAlertsData()])
        setIsRefreshing(false)
    }, [fetchDashboardData, fetchAlertsData])

    useEffect(() => {
        fetchDashboardData()
        fetchAlertsData()

        // Auto-refresh every 60 seconds
        const interval = setInterval(refreshAll, 60000)
        return () => clearInterval(interval)
    }, [fetchDashboardData, fetchAlertsData, refreshAll])

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "System", href: "/admin/system" },
                { label: "Quota Management" },
            ]}
        >
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
                                <Gauge className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    YouTube API Quota
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Monitor daily quota usage across all accounts
                                </p>
                            </div>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        onClick={refreshAll}
                        disabled={isRefreshing}
                    >
                        <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                        Refresh
                    </Button>
                </motion.div>

                {/* Overview Cards */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    {isLoadingDashboard ? (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {[...Array(4)].map((_, i) => (
                                <Card key={i}>
                                    <CardContent className="p-6">
                                        <Skeleton className="h-20 w-full" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : dashboardData && (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {/* Platform Usage */}
                            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                <CardContent className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                            <TrendingUp className="h-5 w-5 text-blue-600" />
                                        </div>
                                        <Badge variant={dashboardData.platform_usage_percent >= 80 ? "destructive" : "secondary"}>
                                            {dashboardData.platform_usage_percent.toFixed(1)}%
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-1">Platform Usage</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {dashboardData.total_daily_quota_used.toLocaleString()}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        of {dashboardData.total_daily_quota_limit.toLocaleString()} total
                                    </p>
                                    <Progress
                                        value={dashboardData.platform_usage_percent}
                                        className="mt-3 h-2"
                                    />
                                </CardContent>
                            </Card>

                            {/* Total Accounts */}
                            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                <CardContent className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="h-10 w-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                                            <Youtube className="h-5 w-5 text-red-600" />
                                        </div>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-1">YouTube Accounts</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {dashboardData.total_accounts}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        across {dashboardData.total_users_with_accounts} users
                                    </p>
                                </CardContent>
                            </Card>

                            {/* High Usage Accounts */}
                            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                <CardContent className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="h-10 w-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                                            <AlertTriangle className="h-5 w-5 text-amber-600" />
                                        </div>
                                        {dashboardData.accounts_over_80_percent > 0 && (
                                            <Badge variant="outline" className="border-amber-500 text-amber-600">
                                                Warning
                                            </Badge>
                                        )}
                                    </div>
                                    <p className="text-sm text-slate-500 mb-1">Accounts &gt;80%</p>
                                    <p className="text-2xl font-bold text-amber-600">
                                        {dashboardData.accounts_over_80_percent}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        approaching quota limit
                                    </p>
                                </CardContent>
                            </Card>

                            {/* Critical Accounts */}
                            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                                <CardContent className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="h-10 w-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                                            <AlertCircle className="h-5 w-5 text-red-600" />
                                        </div>
                                        {dashboardData.accounts_over_90_percent > 0 && (
                                            <Badge variant="destructive">Critical</Badge>
                                        )}
                                    </div>
                                    <p className="text-sm text-slate-500 mb-1">Accounts &gt;90%</p>
                                    <p className="text-2xl font-bold text-red-600">
                                        {dashboardData.accounts_over_90_percent}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        at critical usage level
                                    </p>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </motion.div>

                {/* Alerts Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <AlertsPanel data={alertsData} isLoading={isLoadingAlerts} />
                </motion.div>

                {/* High Usage Users Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Users className="h-5 w-5 text-purple-500" />
                                    High Usage Users
                                </CardTitle>
                                <p className="text-sm text-slate-500">
                                    Users with accounts exceeding {dashboardData?.alert_threshold_percent || 80}% quota
                                </p>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {isLoadingDashboard ? (
                                <Skeleton className="h-40 w-full" />
                            ) : dashboardData?.high_usage_users.length === 0 ? (
                                <div className="text-center py-8 text-slate-500">
                                    <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500" />
                                    <p>No high usage users - all accounts within normal limits</p>
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-10"></TableHead>
                                            <TableHead>User</TableHead>
                                            <TableHead className="text-center">Accounts</TableHead>
                                            <TableHead className="text-right">Total Quota Used</TableHead>
                                            <TableHead>Highest Usage</TableHead>
                                            <TableHead className="text-right">Status</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {dashboardData?.high_usage_users.map((user) => (
                                            <UserQuotaRow key={user.user_id} user={user} />
                                        ))}
                                    </TableBody>
                                </Table>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </AdminLayout>
    )
}
