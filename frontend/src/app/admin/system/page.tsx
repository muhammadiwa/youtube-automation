"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Server,
    Database,
    HardDrive,
    Cpu,
    Activity,
    RefreshCw,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Clock,
    Zap,
    Users,
    RotateCcw,
    AlertCircle,
    Loader2,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    SystemHealthResponse,
    JobQueueResponse,
    WorkerStatusResponse,
    ErrorAlertsResponse,
    ComponentHealth,
    WorkerInfo,
    HealthStatus,
    ComponentStatusType,
    WorkerStatusType,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"


// Helper functions
function getStatusColor(status: HealthStatus | ComponentStatusType | WorkerStatusType): string {
    switch (status) {
        case "healthy":
        case "active":
            return "text-emerald-600 dark:text-emerald-400"
        case "degraded":
        case "idle":
            return "text-amber-600 dark:text-amber-400"
        case "critical":
        case "down":
        case "unhealthy":
        case "offline":
            return "text-red-600 dark:text-red-400"
        default:
            return "text-slate-600 dark:text-slate-400"
    }
}

function getStatusBgColor(status: HealthStatus | ComponentStatusType | WorkerStatusType): string {
    switch (status) {
        case "healthy":
        case "active":
            return "bg-emerald-100 dark:bg-emerald-900/30"
        case "degraded":
        case "idle":
            return "bg-amber-100 dark:bg-amber-900/30"
        case "critical":
        case "down":
        case "unhealthy":
        case "offline":
            return "bg-red-100 dark:bg-red-900/30"
        default:
            return "bg-slate-100 dark:bg-slate-800"
    }
}

function getStatusIcon(status: HealthStatus | ComponentStatusType | WorkerStatusType) {
    switch (status) {
        case "healthy":
        case "active":
            return CheckCircle2
        case "degraded":
        case "idle":
            return AlertTriangle
        case "critical":
        case "down":
        case "unhealthy":
        case "offline":
            return XCircle
        default:
            return AlertCircle
    }
}

function getComponentIcon(name: string) {
    const lowerName = name.toLowerCase()
    if (lowerName.includes("api") || lowerName.includes("server")) return Server
    if (lowerName.includes("database") || lowerName.includes("db") || lowerName.includes("postgres")) return Database
    if (lowerName.includes("redis") || lowerName.includes("cache")) return HardDrive
    if (lowerName.includes("worker") || lowerName.includes("celery")) return Cpu
    if (lowerName.includes("agent")) return Users
    return Activity
}

function formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (days > 0) return `${days}d ${hours}h ${minutes}m`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
}

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

// Component Status Card
function ComponentStatusCard({ component, delay = 0 }: { component: ComponentHealth; delay?: number }) {
    const StatusIcon = getStatusIcon(component.status)
    const ComponentIcon = getComponentIcon(component.name)

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay }}
        >
            <Card className={cn(
                "border transition-all duration-300 hover:shadow-md",
                component.status === "healthy"
                    ? "border-emerald-200 dark:border-emerald-800/50"
                    : component.status === "degraded"
                        ? "border-amber-200 dark:border-amber-800/50"
                        : "border-red-200 dark:border-red-800/50"
            )}>
                <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "h-10 w-10 rounded-lg flex items-center justify-center",
                                getStatusBgColor(component.status)
                            )}>
                                <ComponentIcon className={cn("h-5 w-5", getStatusColor(component.status))} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-900 dark:text-white capitalize">
                                    {component.name}
                                </h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <StatusIcon className={cn("h-4 w-4", getStatusColor(component.status))} />
                                    <span className={cn("text-sm font-medium capitalize", getStatusColor(component.status))}>
                                        {component.status}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-4 space-y-2 text-sm">
                        {component.latency_ms !== null && (
                            <div className="flex justify-between">
                                <span className="text-slate-500 dark:text-slate-400">Latency</span>
                                <span className="font-medium text-slate-900 dark:text-white">
                                    {component.latency_ms.toFixed(1)}ms
                                </span>
                            </div>
                        )}
                        {component.error_rate !== null && (
                            <div className="flex justify-between">
                                <span className="text-slate-500 dark:text-slate-400">Error Rate</span>
                                <span className={cn(
                                    "font-medium",
                                    component.error_rate > 5 ? "text-red-600" : "text-slate-900 dark:text-white"
                                )}>
                                    {component.error_rate.toFixed(2)}%
                                </span>
                            </div>
                        )}
                        <div className="flex justify-between">
                            <span className="text-slate-500 dark:text-slate-400">Last Check</span>
                            <span className="font-medium text-slate-900 dark:text-white">
                                {new Date(component.last_check).toLocaleTimeString()}
                            </span>
                        </div>
                    </div>

                    {component.message && (
                        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2 rounded">
                            {component.message}
                        </p>
                    )}

                    {component.suggested_action && (
                        <div className="mt-3 p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800/50">
                            <p className="text-sm text-amber-700 dark:text-amber-400">
                                <strong>Suggested:</strong> {component.suggested_action}
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </motion.div>
    )
}


// Job Queue Card
function JobQueueCard({ data, isLoading }: { data: JobQueueResponse | null; isLoading: boolean }) {
    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent className="space-y-4">
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-20 w-full" />
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
                        <Activity className="h-5 w-5 text-blue-500" />
                        Job Queue Status
                    </CardTitle>
                    <Badge variant={data.total_dlq > 0 ? "destructive" : "secondary"}>
                        {data.total_dlq > 0 ? `${data.total_dlq} in DLQ` : "Healthy"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900 dark:text-white">{data.total_depth}</p>
                        <p className="text-sm text-slate-500">Queue Depth</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{data.total_processing}</p>
                        <p className="text-sm text-slate-500">Processing</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{data.total_failed}</p>
                        <p className="text-sm text-slate-500">Failed</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-2xl font-bold text-amber-600">{data.total_dlq}</p>
                        <p className="text-sm text-slate-500">Dead Letter</p>
                    </div>
                </div>

                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Queue</TableHead>
                            <TableHead className="text-right">Depth</TableHead>
                            <TableHead className="text-right">Processing</TableHead>
                            <TableHead className="text-right">Rate/s</TableHead>
                            <TableHead className="text-right">Failed</TableHead>
                            <TableHead className="text-right">DLQ</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.queues.map((queue) => (
                            <TableRow key={queue.queue_name}>
                                <TableCell className="font-medium">{queue.queue_name}</TableCell>
                                <TableCell className="text-right">{queue.depth}</TableCell>
                                <TableCell className="text-right">{queue.processing}</TableCell>
                                <TableCell className="text-right">{queue.processing_rate.toFixed(2)}</TableCell>
                                <TableCell className="text-right">
                                    <span className={queue.failed_jobs > 0 ? "text-red-600 font-medium" : ""}>
                                        {queue.failed_jobs}
                                    </span>
                                </TableCell>
                                <TableCell className="text-right">
                                    <span className={queue.dlq_count > 0 ? "text-amber-600 font-medium" : ""}>
                                        {queue.dlq_count}
                                    </span>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}

// Workers Dashboard
function WorkersDashboard({
    data,
    isLoading,
    onRestartWorker
}: {
    data: WorkerStatusResponse | null
    isLoading: boolean
    onRestartWorker: (workerId: string) => void
}) {
    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent className="space-y-4">
                    <Skeleton className="h-20 w-full" />
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
                        <Cpu className="h-5 w-5 text-purple-500" />
                        Workers Status
                    </CardTitle>
                    <Badge variant={data.unhealthy_workers > 0 ? "destructive" : "secondary"}>
                        {data.active_workers}/{data.total_workers} Active
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-500">Overall Utilization</span>
                        <span className="font-medium">{data.utilization_percent.toFixed(1)}%</span>
                    </div>
                    <Progress value={data.utilization_percent} className="h-2" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-emerald-600">{data.active_workers}</p>
                        <p className="text-sm text-slate-500">Active</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-600">{data.idle_workers}</p>
                        <p className="text-sm text-slate-500">Idle</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{data.unhealthy_workers}</p>
                        <p className="text-sm text-slate-500">Unhealthy</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{data.current_load}</p>
                        <p className="text-sm text-slate-500">Current Load</p>
                    </div>
                </div>

                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Worker</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Load</TableHead>
                            <TableHead className="text-right">Jobs</TableHead>
                            <TableHead className="text-right">Completed</TableHead>
                            <TableHead className="text-right">Failed</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.workers.map((worker) => {
                            const StatusIcon = getStatusIcon(worker.status)
                            return (
                                <TableRow key={worker.id}>
                                    <TableCell>
                                        <div>
                                            <p className="font-medium">{worker.name}</p>
                                            {worker.hostname && (
                                                <p className="text-xs text-slate-500">{worker.hostname}</p>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <StatusIcon className={cn("h-4 w-4", getStatusColor(worker.status))} />
                                            <span className={cn("capitalize text-sm", getStatusColor(worker.status))}>
                                                {worker.status}
                                            </span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <Progress value={worker.load} className="w-16 h-2" />
                                            <span className="text-sm">{worker.load.toFixed(0)}%</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">{worker.current_jobs}</TableCell>
                                    <TableCell className="text-right">{worker.completed_jobs}</TableCell>
                                    <TableCell className="text-right">
                                        <span className={worker.failed_jobs > 0 ? "text-red-600 font-medium" : ""}>
                                            {worker.failed_jobs}
                                        </span>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => onRestartWorker(worker.id)}
                                            disabled={worker.status === "offline"}
                                        >
                                            <RotateCcw className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            )
                        })}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}


// Error Alerts Panel
function ErrorAlertsPanel({ data, isLoading }: { data: ErrorAlertsResponse | null; isLoading: boolean }) {
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
                        Recent Alerts
                    </CardTitle>
                    <div className="flex gap-2">
                        {data.critical_count > 0 && (
                            <Badge variant="destructive">{data.critical_count} Critical</Badge>
                        )}
                        {data.warning_count > 0 && (
                            <Badge variant="outline" className="border-amber-500 text-amber-600">
                                {data.warning_count} Warning
                            </Badge>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {data.alerts.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                        <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500" />
                        <p>No recent alerts</p>
                    </div>
                ) : (
                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                        {data.alerts.map((alert) => (
                            <div
                                key={alert.id}
                                className={cn(
                                    "p-3 rounded-lg border",
                                    alert.severity === "critical"
                                        ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                                        : alert.severity === "warning"
                                            ? "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
                                            : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                                )}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-2">
                                        <AlertCircle className={cn(
                                            "h-5 w-5 mt-0.5",
                                            alert.severity === "critical" ? "text-red-600" :
                                                alert.severity === "warning" ? "text-amber-600" : "text-blue-600"
                                        )} />
                                        <div>
                                            <p className="font-medium text-slate-900 dark:text-white">
                                                {alert.message}
                                            </p>
                                            <p className="text-sm text-slate-500 mt-1">
                                                Component: {alert.component}
                                            </p>
                                            {alert.correlation_id && (
                                                <p className="text-xs text-slate-400 mt-1 font-mono">
                                                    ID: {alert.correlation_id}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="text-right text-sm text-slate-500">
                                        <p>{new Date(alert.occurred_at).toLocaleTimeString()}</p>
                                        <Badge variant="outline" className="mt-1 capitalize">
                                            {alert.severity}
                                        </Badge>
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
export default function SystemMonitoringPage() {
    const [healthData, setHealthData] = useState<SystemHealthResponse | null>(null)
    const [jobQueueData, setJobQueueData] = useState<JobQueueResponse | null>(null)
    const [workerData, setWorkerData] = useState<WorkerStatusResponse | null>(null)
    const [alertsData, setAlertsData] = useState<ErrorAlertsResponse | null>(null)

    const [isLoadingHealth, setIsLoadingHealth] = useState(true)
    const [isLoadingJobs, setIsLoadingJobs] = useState(true)
    const [isLoadingWorkers, setIsLoadingWorkers] = useState(true)
    const [isLoadingAlerts, setIsLoadingAlerts] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const [restartDialogOpen, setRestartDialogOpen] = useState(false)
    const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null)
    const [restartReason, setRestartReason] = useState("")
    const [isRestarting, setIsRestarting] = useState(false)
    const { addToast } = useToast()

    const fetchHealthData = useCallback(async () => {
        try {
            const data = await adminApi.getSystemHealth()
            setHealthData(data)
        } catch (error) {
            console.error("Failed to fetch system health:", error)
        } finally {
            setIsLoadingHealth(false)
        }
    }, [])

    const fetchJobQueueData = useCallback(async () => {
        try {
            const data = await adminApi.getJobQueueStatus()
            setJobQueueData(data)
        } catch (error) {
            console.error("Failed to fetch job queue status:", error)
        } finally {
            setIsLoadingJobs(false)
        }
    }, [])

    const fetchWorkerData = useCallback(async () => {
        try {
            const data = await adminApi.getWorkerStatus()
            setWorkerData(data)
        } catch (error) {
            console.error("Failed to fetch worker status:", error)
        } finally {
            setIsLoadingWorkers(false)
        }
    }, [])

    const fetchAlertsData = useCallback(async () => {
        try {
            const data = await adminApi.getErrorAlerts(50)
            setAlertsData(data)
        } catch (error) {
            console.error("Failed to fetch error alerts:", error)
        } finally {
            setIsLoadingAlerts(false)
        }
    }, [])

    const refreshAll = useCallback(async () => {
        setIsRefreshing(true)
        await Promise.all([
            fetchHealthData(),
            fetchJobQueueData(),
            fetchWorkerData(),
            fetchAlertsData(),
        ])
        setIsRefreshing(false)
    }, [fetchHealthData, fetchJobQueueData, fetchWorkerData, fetchAlertsData])

    useEffect(() => {
        fetchHealthData()
        fetchJobQueueData()
        fetchWorkerData()
        fetchAlertsData()

        // Auto-refresh every 30 seconds
        const interval = setInterval(refreshAll, 30000)
        return () => clearInterval(interval)
    }, [fetchHealthData, fetchJobQueueData, fetchWorkerData, fetchAlertsData, refreshAll])

    const handleRestartWorker = (workerId: string) => {
        setSelectedWorkerId(workerId)
        setRestartReason("")
        setRestartDialogOpen(true)
    }

    const confirmRestartWorker = async () => {
        if (!selectedWorkerId) return

        setIsRestarting(true)
        try {
            await adminApi.restartWorker(selectedWorkerId, {
                reason: restartReason || undefined,
                graceful: true,
            })
            addToast({
                type: "success",
                title: "Worker restart initiated",
                message: "The worker is being restarted gracefully",
            })
            setRestartDialogOpen(false)
            fetchWorkerData()
        } catch (error) {
            console.error("Failed to restart worker:", error)
            addToast({
                type: "error",
                title: "Failed to restart worker",
                message: "An error occurred while restarting the worker",
            })
        } finally {
            setIsRestarting(false)
        }
    }

    const OverallStatusIcon = healthData ? getStatusIcon(healthData.overall_status) : Activity

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "System", href: "/admin/system" },
                { label: "Monitoring" },
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
                            <div className={cn(
                                "h-10 w-10 rounded-xl flex items-center justify-center shadow-lg",
                                healthData?.overall_status === "healthy"
                                    ? "bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-emerald-500/25"
                                    : healthData?.overall_status === "degraded"
                                        ? "bg-gradient-to-br from-amber-500 to-amber-600 shadow-amber-500/25"
                                        : "bg-gradient-to-br from-red-500 to-red-600 shadow-red-500/25"
                            )}>
                                <Server className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    System Monitoring
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Monitor system health, job queues, and workers
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {healthData && (
                            <div className={cn(
                                "flex items-center gap-2 px-4 py-2 rounded-lg",
                                getStatusBgColor(healthData.overall_status)
                            )}>
                                <OverallStatusIcon className={cn("h-5 w-5", getStatusColor(healthData.overall_status))} />
                                <span className={cn("font-medium capitalize", getStatusColor(healthData.overall_status))}>
                                    System {healthData.overall_status}
                                </span>
                            </div>
                        )}
                        <Button
                            variant="outline"
                            onClick={refreshAll}
                            disabled={isRefreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>
                </motion.div>

                {/* System Info Bar */}
                {healthData && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <Card className="border border-slate-200/60 dark:border-slate-700/60">
                            <CardContent className="py-3">
                                <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
                                    <div className="flex items-center gap-6">
                                        <div className="flex items-center gap-2">
                                            <Zap className="h-4 w-4 text-slate-400" />
                                            <span className="text-slate-500">Version:</span>
                                            <span className="font-medium">{healthData.version}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Clock className="h-4 w-4 text-slate-400" />
                                            <span className="text-slate-500">Uptime:</span>
                                            <span className="font-medium">{formatUptime(healthData.uptime_seconds)}</span>
                                        </div>
                                    </div>
                                    <div className="text-slate-500">
                                        Last updated: {formatTimestamp(healthData.timestamp)}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {/* Component Status Cards */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <h2 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">
                        Component Health
                    </h2>
                    {isLoadingHealth ? (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
                            {[...Array(5)].map((_, i) => (
                                <Card key={i}>
                                    <CardContent className="p-4">
                                        <Skeleton className="h-24 w-full" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
                            {healthData?.components.map((component, index) => (
                                <ComponentStatusCard
                                    key={component.name}
                                    component={component}
                                    delay={index * 0.05}
                                />
                            ))}
                        </div>
                    )}
                </motion.div>

                {/* Tabs for Job Queue and Workers */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <Tabs defaultValue="jobs" className="space-y-4">
                        <TabsList>
                            <TabsTrigger value="jobs" className="flex items-center gap-2">
                                <Activity className="h-4 w-4" />
                                Job Queues
                            </TabsTrigger>
                            <TabsTrigger value="workers" className="flex items-center gap-2">
                                <Cpu className="h-4 w-4" />
                                Workers
                            </TabsTrigger>
                            <TabsTrigger value="alerts" className="flex items-center gap-2">
                                <AlertTriangle className="h-4 w-4" />
                                Alerts
                                {alertsData && alertsData.critical_count > 0 && (
                                    <Badge variant="destructive" className="ml-1 h-5 px-1.5">
                                        {alertsData.critical_count}
                                    </Badge>
                                )}
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="jobs">
                            <JobQueueCard data={jobQueueData} isLoading={isLoadingJobs} />
                        </TabsContent>

                        <TabsContent value="workers">
                            <WorkersDashboard
                                data={workerData}
                                isLoading={isLoadingWorkers}
                                onRestartWorker={handleRestartWorker}
                            />
                        </TabsContent>

                        <TabsContent value="alerts">
                            <ErrorAlertsPanel data={alertsData} isLoading={isLoadingAlerts} />
                        </TabsContent>
                    </Tabs>
                </motion.div>
            </div>

            {/* Worker Restart Dialog */}
            <Dialog open={restartDialogOpen} onOpenChange={setRestartDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Restart Worker</DialogTitle>
                        <DialogDescription>
                            This will gracefully stop current jobs and restart the worker.
                            Jobs will be reassigned to other workers.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="restart-reason">Reason (optional)</Label>
                            <Textarea
                                id="restart-reason"
                                placeholder="Enter reason for restart..."
                                value={restartReason}
                                onChange={(e) => setRestartReason(e.target.value)}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setRestartDialogOpen(false)}
                            disabled={isRestarting}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={confirmRestartWorker}
                            disabled={isRestarting}
                        >
                            {isRestarting ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Restarting...
                                </>
                            ) : (
                                <>
                                    <RotateCcw className="h-4 w-4 mr-2" />
                                    Restart Worker
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
