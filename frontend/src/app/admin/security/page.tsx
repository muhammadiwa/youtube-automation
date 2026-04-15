"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Shield,
    AlertTriangle,
    Lock,
    Globe,
    Users,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Clock,
    Ban,
    Activity,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
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
import type { SecurityDashboardResponse, SecurityEvent, SuspiciousIP } from "@/types/admin"
import { useToast } from "@/components/ui/toast"

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

function formatRelativeTime(timestamp: string): string {
    const now = new Date()
    const date = new Date(timestamp)
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
}

function getSeverityColor(severity: string): string {
    switch (severity) {
        case "critical":
            return "text-red-600 dark:text-red-400"
        case "high":
            return "text-orange-600 dark:text-orange-400"
        case "medium":
            return "text-amber-600 dark:text-amber-400"
        case "low":
            return "text-blue-600 dark:text-blue-400"
        default:
            return "text-slate-600 dark:text-slate-400"
    }
}

function getSeverityBgColor(severity: string): string {
    switch (severity) {
        case "critical":
            return "bg-red-100 dark:bg-red-900/30"
        case "high":
            return "bg-orange-100 dark:bg-orange-900/30"
        case "medium":
            return "bg-amber-100 dark:bg-amber-900/30"
        case "low":
            return "bg-blue-100 dark:bg-blue-900/30"
        default:
            return "bg-slate-100 dark:bg-slate-800"
    }
}

function MetricCard({
    title,
    value,
    icon: Icon,
    trend,
    description,
    variant = "default",
}: {
    title: string
    value: number | string
    icon: React.ElementType
    trend?: "up" | "down" | "stable"
    description?: string
    variant?: "default" | "warning" | "danger" | "success"
}) {
    const variantStyles = {
        default: "from-slate-500 to-slate-600 shadow-slate-500/25",
        warning: "from-amber-500 to-amber-600 shadow-amber-500/25",
        danger: "from-red-500 to-red-600 shadow-red-500/25",
        success: "from-emerald-500 to-emerald-600 shadow-emerald-500/25",
    }

    return (
        <Card>
            <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
                        <p className="text-3xl font-bold mt-1">{value}</p>
                        {description && (
                            <p className="text-xs text-slate-400 mt-1">{description}</p>
                        )}
                    </div>
                    <div className={cn(
                        "h-10 w-10 rounded-lg flex items-center justify-center bg-gradient-to-br shadow-lg",
                        variantStyles[variant]
                    )}>
                        <Icon className="h-5 w-5 text-white" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

export default function SecurityDashboardPage() {
    const [data, setData] = useState<SecurityDashboardResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const { addToast } = useToast()

    const fetchData = useCallback(async () => {
        try {
            const response = await adminApi.getSecurityDashboard()
            setData(response)
        } catch (error) {
            console.error("Failed to fetch security dashboard:", error)
            addToast({
                type: "error",
                title: "Failed to load security data",
                description: "Please try again later",
            })
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [addToast])

    useEffect(() => {
        fetchData()
        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchData, 60000)
        return () => clearInterval(interval)
    }, [fetchData])

    const handleRefresh = () => {
        setIsRefreshing(true)
        fetchData()
    }

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Compliance", href: "/admin/security" },
                { label: "Security Dashboard" },
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
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-lg shadow-red-500/25">
                                <Shield className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Security Dashboard
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Monitor security events and suspicious activity
                                </p>
                            </div>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                    >
                        <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                        Refresh
                    </Button>
                </motion.div>

                {/* Metrics Cards */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    {isLoading ? (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                            {[...Array(4)].map((_, i) => (
                                <Card key={i}>
                                    <CardContent className="pt-6">
                                        <Skeleton className="h-20 w-full" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : data && (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                            <MetricCard
                                title="Failed Logins (24h)"
                                value={data.failed_login_attempts_24h}
                                icon={Lock}
                                variant={data.failed_login_attempts_24h > 50 ? "danger" : data.failed_login_attempts_24h > 20 ? "warning" : "default"}
                            />
                            <MetricCard
                                title="Failed Logins (7d)"
                                value={data.failed_login_attempts_7d}
                                icon={AlertTriangle}
                                variant={data.failed_login_attempts_7d > 200 ? "danger" : "default"}
                            />
                            <MetricCard
                                title="Blocked IPs"
                                value={data.blocked_ips_count}
                                icon={Ban}
                                variant={data.blocked_ips_count > 0 ? "warning" : "success"}
                            />
                            <MetricCard
                                title="Active Sessions"
                                value={data.active_sessions_count}
                                icon={Users}
                                variant="default"
                            />
                        </div>
                    )}
                </motion.div>

                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Suspicious IPs */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <Card className="h-full">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Globe className="h-5 w-5 text-amber-500" />
                                    Suspicious IPs
                                </CardTitle>
                                <CardDescription>
                                    IP addresses with multiple failed login attempts
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {isLoading ? (
                                    <div className="space-y-3">
                                        {[...Array(5)].map((_, i) => (
                                            <Skeleton key={i} className="h-12 w-full" />
                                        ))}
                                    </div>
                                ) : data && data.suspicious_ips.length > 0 ? (
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>IP Address</TableHead>
                                                <TableHead className="text-right">Attempts</TableHead>
                                                <TableHead>Last Attempt</TableHead>
                                                <TableHead>Status</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.suspicious_ips.map((ip) => (
                                                <TableRow key={ip.ip_address}>
                                                    <TableCell className="font-mono text-sm">
                                                        {ip.ip_address}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <span className={cn(
                                                            "font-medium",
                                                            ip.failed_attempts > 10 ? "text-red-600" : "text-amber-600"
                                                        )}>
                                                            {ip.failed_attempts}
                                                        </span>
                                                    </TableCell>
                                                    <TableCell className="text-sm text-slate-500">
                                                        {formatRelativeTime(ip.last_attempt)}
                                                    </TableCell>
                                                    <TableCell>
                                                        {ip.blocked ? (
                                                            <Badge variant="destructive">Blocked</Badge>
                                                        ) : (
                                                            <Badge variant="outline">Monitoring</Badge>
                                                        )}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                ) : (
                                    <div className="text-center py-8 text-slate-500">
                                        <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500" />
                                        <p>No suspicious IPs detected</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Security Events Timeline */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <Card className="h-full">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Activity className="h-5 w-5 text-blue-500" />
                                    Security Events
                                </CardTitle>
                                <CardDescription>
                                    Recent security-related events
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {isLoading ? (
                                    <div className="space-y-3">
                                        {[...Array(5)].map((_, i) => (
                                            <Skeleton key={i} className="h-16 w-full" />
                                        ))}
                                    </div>
                                ) : data && data.recent_security_events.length > 0 ? (
                                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                                        {data.recent_security_events.map((event) => (
                                            <div
                                                key={event.id}
                                                className={cn(
                                                    "p-3 rounded-lg border",
                                                    getSeverityBgColor(event.severity)
                                                )}
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "capitalize",
                                                                    getSeverityColor(event.severity)
                                                                )}
                                                            >
                                                                {event.severity}
                                                            </Badge>
                                                            <span className="text-sm font-medium">
                                                                {event.event_type}
                                                            </span>
                                                        </div>
                                                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                                            {event.description}
                                                        </p>
                                                        {event.ip_address && (
                                                            <p className="text-xs text-slate-400 mt-1 font-mono">
                                                                IP: {event.ip_address}
                                                            </p>
                                                        )}
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-xs text-slate-500">
                                                            {formatRelativeTime(event.timestamp)}
                                                        </p>
                                                        {event.resolved ? (
                                                            <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-1 ml-auto" />
                                                        ) : (
                                                            <Clock className="h-4 w-4 text-amber-500 mt-1 ml-auto" />
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-slate-500">
                                        <Shield className="h-12 w-12 mx-auto mb-3 text-emerald-500" />
                                        <p>No security events</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </div>
        </AdminLayout>
    )
}
