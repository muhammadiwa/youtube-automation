"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Database,
    Plus,
    RefreshCw,
    CheckCircle2,
    Clock,
    XCircle,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Download,
    HardDrive,
    Calendar,
    Settings,
    RotateCcw,
    Shield,
    AlertTriangle,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    BackupListResponse,
    Backup,
    BackupStatusSummary,
    BackupScheduleListResponse,
    BackupSchedule,
    CreateBackupRequest,
    UpdateBackupScheduleRequest,
    BackupType,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"


function formatTimestamp(timestamp: string | null): string {
    if (!timestamp) return "-"
    return new Date(timestamp).toLocaleString()
}

function formatFileSize(bytes: number | null): string {
    if (!bytes) return "-"
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function getStatusBadge(status: string) {
    switch (status) {
        case "pending":
            return <Badge variant="outline" className="border-amber-500 text-amber-600"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
        case "in_progress":
            return <Badge variant="outline" className="border-blue-500 text-blue-600"><Loader2 className="h-3 w-3 mr-1 animate-spin" />In Progress</Badge>
        case "completed":
            return <Badge variant="default" className="bg-emerald-500"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>
        case "verified":
            return <Badge variant="default" className="bg-green-600"><Shield className="h-3 w-3 mr-1" />Verified</Badge>
        case "failed":
            return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

function getBackupTypeLabel(type: BackupType): string {
    switch (type) {
        case "full":
            return "Full Backup"
        case "incremental":
            return "Incremental"
        case "differential":
            return "Differential"
        default:
            return type
    }
}

const BACKUP_TYPES: { value: BackupType; label: string; description: string }[] = [
    { value: "full", label: "Full Backup", description: "Complete backup of all data" },
    { value: "incremental", label: "Incremental", description: "Only changes since last backup" },
    { value: "differential", label: "Differential", description: "Changes since last full backup" },
]

const FREQUENCIES = [
    { value: "hourly", label: "Hourly" },
    { value: "daily", label: "Daily" },
    { value: "weekly", label: "Weekly" },
    { value: "monthly", label: "Monthly" },
]

export default function BackupsPage() {
    const [data, setData] = useState<BackupListResponse | null>(null)
    const [summary, setSummary] = useState<BackupStatusSummary | null>(null)
    const [schedules, setSchedules] = useState<BackupScheduleListResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [page, setPage] = useState(1)
    const [statusFilter, setStatusFilter] = useState("all")
    const [typeFilter, setTypeFilter] = useState("all")
    const [activeTab, setActiveTab] = useState("backups")

    // Create backup dialog state
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [isCreating, setIsCreating] = useState(false)
    const [newBackup, setNewBackup] = useState<CreateBackupRequest>({
        backup_type: "full",
        name: "",
        description: "",
        storage_provider: "local",
        retention_days: 30,
    })

    // Schedule config dialog state
    const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false)
    const [selectedSchedule, setSelectedSchedule] = useState<BackupSchedule | null>(null)
    const [isUpdatingSchedule, setIsUpdatingSchedule] = useState(false)
    const [scheduleUpdate, setScheduleUpdate] = useState<UpdateBackupScheduleRequest>({})

    // Restore dialog state
    const [restoreDialogOpen, setRestoreDialogOpen] = useState(false)
    const [selectedBackup, setSelectedBackup] = useState<Backup | null>(null)
    const [isRestoring, setIsRestoring] = useState(false)
    const [restoreReason, setRestoreReason] = useState("")

    const { addToast } = useToast()


    const fetchBackups = useCallback(async () => {
        try {
            const response = await adminApi.getBackups({
                page,
                page_size: 20,
                status: statusFilter !== "all" ? statusFilter : undefined,
                backup_type: typeFilter !== "all" ? typeFilter : undefined,
            })
            setData(response)
        } catch (error) {
            console.error("Failed to fetch backups:", error)
            addToast({
                type: "error",
                title: "Failed to load backups",
                description: "Please try again later",
            })
        }
    }, [page, statusFilter, typeFilter, addToast])

    const fetchSummary = useCallback(async () => {
        try {
            const response = await adminApi.getBackupStatusSummary()
            setSummary(response)
        } catch (error) {
            console.error("Failed to fetch backup summary:", error)
        }
    }, [])

    const fetchSchedules = useCallback(async () => {
        try {
            const response = await adminApi.getBackupSchedules()
            setSchedules(response)
        } catch (error) {
            console.error("Failed to fetch backup schedules:", error)
        }
    }, [])

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true)
            await Promise.all([fetchBackups(), fetchSummary(), fetchSchedules()])
            setIsLoading(false)
        }
        loadData()
    }, [fetchBackups, fetchSummary, fetchSchedules])

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await Promise.all([fetchBackups(), fetchSummary(), fetchSchedules()])
        setIsRefreshing(false)
    }

    const handleCreateBackup = async () => {
        if (!newBackup.name) {
            addToast({
                type: "error",
                title: "Validation Error",
                description: "Backup name is required",
            })
            return
        }

        setIsCreating(true)
        try {
            await adminApi.createBackup(newBackup)
            addToast({
                type: "success",
                title: "Backup Started",
                description: "The backup process has been initiated",
            })
            setCreateDialogOpen(false)
            setNewBackup({
                backup_type: "full",
                name: "",
                description: "",
                storage_provider: "local",
                retention_days: 30,
            })
            fetchBackups()
            fetchSummary()
        } catch (error) {
            console.error("Failed to create backup:", error)
            addToast({
                type: "error",
                title: "Failed to create backup",
                description: "Please try again later",
            })
        } finally {
            setIsCreating(false)
        }
    }

    const handleUpdateSchedule = async () => {
        if (!selectedSchedule) return

        setIsUpdatingSchedule(true)
        try {
            await adminApi.updateBackupSchedule(selectedSchedule.id, scheduleUpdate)
            addToast({
                type: "success",
                title: "Schedule Updated",
                description: "Backup schedule has been updated successfully",
            })
            setScheduleDialogOpen(false)
            setSelectedSchedule(null)
            setScheduleUpdate({})
            fetchSchedules()
        } catch (error) {
            console.error("Failed to update schedule:", error)
            addToast({
                type: "error",
                title: "Failed to update schedule",
                description: "Please try again later",
            })
        } finally {
            setIsUpdatingSchedule(false)
        }
    }

    const handleRequestRestore = async () => {
        if (!selectedBackup) return

        setIsRestoring(true)
        try {
            const response = await adminApi.requestRestore(selectedBackup.id, {
                reason: restoreReason || undefined,
            })
            addToast({
                type: "success",
                title: "Restore Requested",
                description: response.requires_approval
                    ? "Restore request submitted. Awaiting super_admin approval."
                    : "Restore process has been initiated.",
            })
            setRestoreDialogOpen(false)
            setSelectedBackup(null)
            setRestoreReason("")
        } catch (error) {
            console.error("Failed to request restore:", error)
            addToast({
                type: "error",
                title: "Failed to request restore",
                description: "Please try again later",
            })
        } finally {
            setIsRestoring(false)
        }
    }

    const openScheduleDialog = (schedule: BackupSchedule) => {
        setSelectedSchedule(schedule)
        setScheduleUpdate({
            name: schedule.name,
            backup_type: schedule.backup_type,
            frequency: schedule.frequency as "hourly" | "daily" | "weekly" | "monthly",
            retention_days: schedule.retention_days,
            max_backups: schedule.max_backups || undefined,
            storage_provider: schedule.storage_provider,
            storage_location: schedule.storage_location || undefined,
            is_active: schedule.is_active,
        })
        setScheduleDialogOpen(true)
    }

    const openRestoreDialog = (backup: Backup) => {
        setSelectedBackup(backup)
        setRestoreReason("")
        setRestoreDialogOpen(true)
    }


    return (
        <AdminLayout
            breadcrumbs={[
                { label: "System", href: "/admin/system" },
                { label: "Backups" },
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
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <Database className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Backup & Recovery
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Manage backups and disaster recovery
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                            Refresh
                        </Button>
                        <Button onClick={() => setCreateDialogOpen(true)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Create Backup
                        </Button>
                    </div>
                </motion.div>

                {/* Summary Cards */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
                >
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Backups</CardTitle>
                            <Database className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <Skeleton className="h-8 w-20" />
                            ) : (
                                <div className="text-2xl font-bold">{summary?.total_backups || 0}</div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {summary?.successful_backups || 0} successful
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Size</CardTitle>
                            <HardDrive className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <Skeleton className="h-8 w-20" />
                            ) : (
                                <div className="text-2xl font-bold">
                                    {formatFileSize(summary?.total_size_bytes || 0)}
                                </div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                Across all backups
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Last Backup</CardTitle>
                            <Clock className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <Skeleton className="h-8 w-32" />
                            ) : (
                                <div className="text-lg font-semibold">
                                    {summary?.last_successful_backup
                                        ? formatTimestamp(summary.last_successful_backup.completed_at)
                                        : "Never"}
                                </div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {summary?.last_successful_backup?.backup_type || "No"} backup
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Next Scheduled</CardTitle>
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <Skeleton className="h-8 w-32" />
                            ) : (
                                <div className="text-lg font-semibold">
                                    {summary?.next_scheduled_backup
                                        ? formatTimestamp(summary.next_scheduled_backup)
                                        : "Not scheduled"}
                                </div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {summary?.active_schedules || 0} active schedules
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Tabs */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList>
                            <TabsTrigger value="backups">
                                <Database className="h-4 w-4 mr-2" />
                                Backups
                            </TabsTrigger>
                            <TabsTrigger value="schedules">
                                <Calendar className="h-4 w-4 mr-2" />
                                Schedules
                            </TabsTrigger>
                        </TabsList>

                        {/* Backups Tab */}
                        <TabsContent value="backups" className="mt-4">
                            <Card>
                                <CardHeader>
                                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                                        <div>
                                            <CardTitle>Backup History</CardTitle>
                                            <CardDescription>
                                                All backup operations
                                            </CardDescription>
                                        </div>
                                        <div className="flex gap-2">
                                            <Select value={typeFilter} onValueChange={setTypeFilter}>
                                                <SelectTrigger className="w-40">
                                                    <SelectValue placeholder="All Types" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="all">All Types</SelectItem>
                                                    {BACKUP_TYPES.map((type) => (
                                                        <SelectItem key={type.value} value={type.value}>
                                                            {type.label}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                                <SelectTrigger className="w-40">
                                                    <SelectValue placeholder="All Status" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="all">All Status</SelectItem>
                                                    <SelectItem value="pending">Pending</SelectItem>
                                                    <SelectItem value="in_progress">In Progress</SelectItem>
                                                    <SelectItem value="completed">Completed</SelectItem>
                                                    <SelectItem value="verified">Verified</SelectItem>
                                                    <SelectItem value="failed">Failed</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {isLoading ? (
                                        <div className="space-y-4">
                                            {[...Array(5)].map((_, i) => (
                                                <Skeleton key={i} className="h-16 w-full" />
                                            ))}
                                        </div>
                                    ) : data && data.items.length > 0 ? (
                                        <>
                                            <Table>
                                                <TableHeader>
                                                    <TableRow>
                                                        <TableHead>Backup</TableHead>
                                                        <TableHead>Type</TableHead>
                                                        <TableHead>Status</TableHead>
                                                        <TableHead>Size</TableHead>
                                                        <TableHead>Created</TableHead>
                                                        <TableHead className="text-right">Actions</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {data.items.map((backup) => (
                                                        <TableRow key={backup.id}>
                                                            <TableCell>
                                                                <div>
                                                                    <p className="font-medium">{backup.name}</p>
                                                                    {backup.description && (
                                                                        <p className="text-sm text-slate-500 truncate max-w-xs">
                                                                            {backup.description}
                                                                        </p>
                                                                    )}
                                                                    {backup.is_scheduled && (
                                                                        <Badge variant="outline" className="mt-1 text-xs">
                                                                            <Calendar className="h-3 w-3 mr-1" />
                                                                            Scheduled
                                                                        </Badge>
                                                                    )}
                                                                </div>
                                                            </TableCell>
                                                            <TableCell>
                                                                <span className="text-sm">
                                                                    {getBackupTypeLabel(backup.backup_type)}
                                                                </span>
                                                            </TableCell>
                                                            <TableCell>
                                                                <div className="space-y-1">
                                                                    {getStatusBadge(backup.status)}
                                                                    {backup.status === "in_progress" && (
                                                                        <Progress value={backup.progress} className="h-1 w-20" />
                                                                    )}
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="text-sm">
                                                                {formatFileSize(backup.size_bytes)}
                                                            </TableCell>
                                                            <TableCell className="text-sm">
                                                                {formatTimestamp(backup.created_at)}
                                                            </TableCell>
                                                            <TableCell className="text-right">
                                                                <div className="flex justify-end gap-2">
                                                                    {(backup.status === "completed" || backup.status === "verified") && (
                                                                        <Button
                                                                            size="sm"
                                                                            variant="outline"
                                                                            onClick={() => openRestoreDialog(backup)}
                                                                        >
                                                                            <RotateCcw className="h-4 w-4 mr-1" />
                                                                            Restore
                                                                        </Button>
                                                                    )}
                                                                    {backup.status === "failed" && backup.error_message && (
                                                                        <Badge variant="destructive" className="cursor-help" title={backup.error_message}>
                                                                            <AlertTriangle className="h-3 w-3 mr-1" />
                                                                            Error
                                                                        </Badge>
                                                                    )}
                                                                </div>
                                                            </TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>

                                            {/* Pagination */}
                                            <div className="flex items-center justify-between mt-4">
                                                <p className="text-sm text-slate-500">
                                                    Page {data.page} of {data.total_pages}
                                                </p>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setPage(page - 1)}
                                                        disabled={page <= 1}
                                                    >
                                                        <ChevronLeft className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setPage(page + 1)}
                                                        disabled={page >= data.total_pages}
                                                    >
                                                        <ChevronRight className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="text-center py-12 text-slate-500">
                                            <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No backups found</p>
                                            <Button
                                                className="mt-4"
                                                onClick={() => setCreateDialogOpen(true)}
                                            >
                                                <Plus className="h-4 w-4 mr-2" />
                                                Create First Backup
                                            </Button>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>


                        {/* Schedules Tab */}
                        <TabsContent value="schedules" className="mt-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Backup Schedules</CardTitle>
                                    <CardDescription>
                                        Configure automated backup schedules
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {isLoading ? (
                                        <div className="space-y-4">
                                            {[...Array(3)].map((_, i) => (
                                                <Skeleton key={i} className="h-24 w-full" />
                                            ))}
                                        </div>
                                    ) : schedules && schedules.items.length > 0 ? (
                                        <div className="grid gap-4 md:grid-cols-2">
                                            {schedules.items.map((schedule) => (
                                                <Card key={schedule.id} className="relative">
                                                    <CardHeader className="pb-2">
                                                        <div className="flex items-center justify-between">
                                                            <CardTitle className="text-base">{schedule.name}</CardTitle>
                                                            <Badge variant={schedule.is_active ? "default" : "secondary"}>
                                                                {schedule.is_active ? "Active" : "Inactive"}
                                                            </Badge>
                                                        </div>
                                                    </CardHeader>
                                                    <CardContent className="space-y-3">
                                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                                            <div>
                                                                <p className="text-slate-500">Type</p>
                                                                <p className="font-medium">{getBackupTypeLabel(schedule.backup_type)}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-slate-500">Frequency</p>
                                                                <p className="font-medium capitalize">{schedule.frequency}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-slate-500">Retention</p>
                                                                <p className="font-medium">{schedule.retention_days} days</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-slate-500">Storage</p>
                                                                <p className="font-medium capitalize">{schedule.storage_provider}</p>
                                                            </div>
                                                        </div>
                                                        <div className="pt-2 border-t">
                                                            <div className="flex items-center justify-between text-sm">
                                                                <div>
                                                                    <p className="text-slate-500">Next Run</p>
                                                                    <p className="font-medium">
                                                                        {schedule.next_run_at
                                                                            ? formatTimestamp(schedule.next_run_at)
                                                                            : "Not scheduled"}
                                                                    </p>
                                                                </div>
                                                                <Button
                                                                    size="sm"
                                                                    variant="outline"
                                                                    onClick={() => openScheduleDialog(schedule)}
                                                                >
                                                                    <Settings className="h-4 w-4 mr-1" />
                                                                    Configure
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-12 text-slate-500">
                                            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No backup schedules configured</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </motion.div>
            </div>


            {/* Create Backup Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Create Manual Backup</DialogTitle>
                        <DialogDescription>
                            Create a new backup of the system data.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="backup_type">Backup Type *</Label>
                            <Select
                                value={newBackup.backup_type}
                                onValueChange={(value) => setNewBackup({ ...newBackup, backup_type: value as BackupType })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select backup type" />
                                </SelectTrigger>
                                <SelectContent>
                                    {BACKUP_TYPES.map((type) => (
                                        <SelectItem key={type.value} value={type.value}>
                                            <div>
                                                <p>{type.label}</p>
                                                <p className="text-xs text-slate-500">{type.description}</p>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="name">Backup Name *</Label>
                            <Input
                                id="name"
                                placeholder="e.g., Pre-deployment backup"
                                value={newBackup.name}
                                onChange={(e) => setNewBackup({ ...newBackup, name: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                placeholder="Optional description for this backup"
                                value={newBackup.description || ""}
                                onChange={(e) => setNewBackup({ ...newBackup, description: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="storage_provider">Storage Provider</Label>
                                <Select
                                    value={newBackup.storage_provider}
                                    onValueChange={(value) => setNewBackup({ ...newBackup, storage_provider: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select storage" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="local">Local Storage</SelectItem>
                                        <SelectItem value="s3">Amazon S3</SelectItem>
                                        <SelectItem value="gcs">Google Cloud Storage</SelectItem>
                                        <SelectItem value="azure">Azure Blob Storage</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="retention_days">Retention (days)</Label>
                                <Input
                                    id="retention_days"
                                    type="number"
                                    min={1}
                                    max={365}
                                    value={newBackup.retention_days || 30}
                                    onChange={(e) => setNewBackup({ ...newBackup, retention_days: parseInt(e.target.value) || 30 })}
                                />
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setCreateDialogOpen(false)}
                            disabled={isCreating}
                        >
                            Cancel
                        </Button>
                        <Button onClick={handleCreateBackup} disabled={isCreating}>
                            {isCreating ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Database className="h-4 w-4 mr-2" />
                                    Create Backup
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>


            {/* Schedule Config Dialog */}
            <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Configure Backup Schedule</DialogTitle>
                        <DialogDescription>
                            Update the backup schedule configuration.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="schedule_name">Schedule Name</Label>
                            <Input
                                id="schedule_name"
                                value={scheduleUpdate.name || ""}
                                onChange={(e) => setScheduleUpdate({ ...scheduleUpdate, name: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="schedule_type">Backup Type</Label>
                                <Select
                                    value={scheduleUpdate.backup_type}
                                    onValueChange={(value) => setScheduleUpdate({ ...scheduleUpdate, backup_type: value as BackupType })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {BACKUP_TYPES.map((type) => (
                                            <SelectItem key={type.value} value={type.value}>
                                                {type.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="frequency">Frequency</Label>
                                <Select
                                    value={scheduleUpdate.frequency}
                                    onValueChange={(value) => setScheduleUpdate({ ...scheduleUpdate, frequency: value as "hourly" | "daily" | "weekly" | "monthly" })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select frequency" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {FREQUENCIES.map((freq) => (
                                            <SelectItem key={freq.value} value={freq.value}>
                                                {freq.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="schedule_retention">Retention (days)</Label>
                                <Input
                                    id="schedule_retention"
                                    type="number"
                                    min={1}
                                    max={365}
                                    value={scheduleUpdate.retention_days || 30}
                                    onChange={(e) => setScheduleUpdate({ ...scheduleUpdate, retention_days: parseInt(e.target.value) || 30 })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_backups">Max Backups</Label>
                                <Input
                                    id="max_backups"
                                    type="number"
                                    min={1}
                                    placeholder="Unlimited"
                                    value={scheduleUpdate.max_backups || ""}
                                    onChange={(e) => setScheduleUpdate({ ...scheduleUpdate, max_backups: e.target.value ? parseInt(e.target.value) : undefined })}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="storage_location">Storage Location</Label>
                            <Input
                                id="storage_location"
                                placeholder="e.g., /backups or s3://bucket/path"
                                value={scheduleUpdate.storage_location || ""}
                                onChange={(e) => setScheduleUpdate({ ...scheduleUpdate, storage_location: e.target.value })}
                            />
                        </div>
                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="is_active"
                                checked={scheduleUpdate.is_active ?? true}
                                onChange={(e) => setScheduleUpdate({ ...scheduleUpdate, is_active: e.target.checked })}
                                className="h-4 w-4 rounded border-gray-300"
                            />
                            <Label htmlFor="is_active">Schedule is active</Label>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setScheduleDialogOpen(false)}
                            disabled={isUpdatingSchedule}
                        >
                            Cancel
                        </Button>
                        <Button onClick={handleUpdateSchedule} disabled={isUpdatingSchedule}>
                            {isUpdatingSchedule ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Settings className="h-4 w-4 mr-2" />
                                    Save Changes
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>


            {/* Restore Confirmation Dialog */}
            <Dialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-amber-600">
                            <AlertTriangle className="h-5 w-5" />
                            Confirm Restore
                        </DialogTitle>
                        <DialogDescription>
                            You are about to restore the system from a backup. This action requires super_admin approval.
                        </DialogDescription>
                    </DialogHeader>
                    {selectedBackup && (
                        <div className="space-y-4 py-4">
                            <div className="rounded-lg bg-amber-50 dark:bg-amber-950/20 p-4 border border-amber-200 dark:border-amber-800">
                                <p className="text-sm text-amber-800 dark:text-amber-200">
                                    <strong>Warning:</strong> Restoring from a backup will replace current data with the backup data.
                                    A pre-restore snapshot will be created automatically.
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label>Backup Details</Label>
                                <div className="rounded-lg border p-3 space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Name:</span>
                                        <span className="font-medium">{selectedBackup.name}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Type:</span>
                                        <span className="font-medium">{getBackupTypeLabel(selectedBackup.backup_type)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Created:</span>
                                        <span className="font-medium">{formatTimestamp(selectedBackup.created_at)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Size:</span>
                                        <span className="font-medium">{formatFileSize(selectedBackup.size_bytes)}</span>
                                    </div>
                                    {selectedBackup.is_verified && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-500">Verified:</span>
                                            <Badge variant="default" className="bg-green-600">
                                                <Shield className="h-3 w-3 mr-1" />
                                                Yes
                                            </Badge>
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="restore_reason">Reason for Restore</Label>
                                <Textarea
                                    id="restore_reason"
                                    placeholder="Describe why you need to restore from this backup..."
                                    value={restoreReason}
                                    onChange={(e) => setRestoreReason(e.target.value)}
                                />
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setRestoreDialogOpen(false)}
                            disabled={isRestoring}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleRequestRestore}
                            disabled={isRestoring}
                        >
                            {isRestoring ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Requesting...
                                </>
                            ) : (
                                <>
                                    <RotateCcw className="h-4 w-4 mr-2" />
                                    Request Restore
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
