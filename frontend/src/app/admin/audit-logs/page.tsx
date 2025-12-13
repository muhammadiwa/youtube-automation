"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    FileText,
    Search,
    Filter,
    Download,
    RefreshCw,
    User,
    ChevronLeft,
    ChevronRight,
    Loader2,
    X,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    AuditLogListResponse,
    AuditLogEntry,
    AuditLogFilters,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

// Action types synced with backend AuditAction enum (backend/app/modules/auth/audit.py)
const ACTION_TYPES = [
    { value: "", label: "All Actions" },
    // Authentication
    { value: "login", label: "Login" },
    { value: "login_failed", label: "Login Failed" },
    { value: "logout", label: "Logout" },
    { value: "register", label: "Register" },
    // Password
    { value: "password_change", label: "Password Change" },
    { value: "password_reset_request", label: "Password Reset Request" },
    { value: "password_reset_complete", label: "Password Reset Complete" },
    // 2FA
    { value: "2fa_setup", label: "2FA Setup" },
    { value: "2fa_enable", label: "2FA Enable" },
    { value: "2fa_disable", label: "2FA Disable" },
    { value: "2fa_backup_regenerate", label: "2FA Backup Regenerate" },
    // Account
    { value: "account_update", label: "Account Update" },
    { value: "account_delete", label: "Account Delete" },
    // YouTube Account
    { value: "youtube_account_connect", label: "YouTube Account Connect" },
    { value: "youtube_account_disconnect", label: "YouTube Account Disconnect" },
    { value: "youtube_token_refresh", label: "YouTube Token Refresh" },
    // Admin
    { value: "admin_action", label: "Admin Action" },
]

const RESOURCE_TYPES = [
    { value: "", label: "All Resources" },
    { value: "user", label: "User" },
    { value: "admin", label: "Admin" },
    { value: "subscription", label: "Subscription" },
    { value: "payment", label: "Payment" },
    { value: "refund", label: "Refund" },
    { value: "discount_code", label: "Discount Code" },
    { value: "promotion", label: "Promotion" },
    { value: "video", label: "Video" },
    { value: "stream", label: "Stream" },
    { value: "youtube_account", label: "YouTube Account" },
    { value: "content_report", label: "Content Report" },
    { value: "moderation", label: "Moderation" },
    { value: "system_config", label: "System Config" },
    { value: "backup", label: "Backup" },
    { value: "export_request", label: "Export Request" },
    { value: "deletion_request", label: "Deletion Request" },
    { value: "terms_of_service", label: "Terms of Service" },
    { value: "compliance_report", label: "Compliance Report" },
    { value: "worker", label: "Worker" },
    { value: "job", label: "Job" },
]

// Event types (from details.event field)
const EVENT_TYPES = [
    { value: "", label: "All Events" },
    // Security events
    { value: "admin_access_denied", label: "Admin Access Denied" },
    { value: "access_denied", label: "Access Denied" },
    { value: "unauthorized_access", label: "Unauthorized Access" },
    // Admin events
    { value: "subscription_modified", label: "Subscription Modified" },
    { value: "discount_code_created", label: "Discount Code Created" },
    { value: "discount_code_updated", label: "Discount Code Updated" },
    { value: "discount_code_deleted", label: "Discount Code Deleted" },
    { value: "user_suspended", label: "User Suspended" },
    { value: "user_activated", label: "User Activated" },
    { value: "user_impersonated", label: "User Impersonated" },
    { value: "password_reset_by_admin", label: "Password Reset by Admin" },
    { value: "refund_processed", label: "Refund Processed" },
    { value: "config_updated", label: "Config Updated" },
    { value: "backup_created", label: "Backup Created" },
    { value: "backup_restored", label: "Backup Restored" },
    { value: "content_approved", label: "Content Approved" },
    { value: "content_removed", label: "Content Removed" },
    { value: "user_warned", label: "User Warned" },
]

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

function getActionBadgeVariant(action: string): "default" | "secondary" | "destructive" | "outline" {
    if (action.includes("delete") || action.includes("remove") || action.includes("suspend")) {
        return "destructive"
    }
    if (action.includes("create") || action.includes("activate")) {
        return "default"
    }
    if (action.includes("login") || action.includes("logout")) {
        return "secondary"
    }
    return "outline"
}

export default function AuditLogsPage() {
    const [data, setData] = useState<AuditLogListResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(20)

    // Filters
    const [filters, setFilters] = useState<AuditLogFilters>({})
    const [searchQuery, setSearchQuery] = useState("")
    const [actionType, setActionType] = useState("all")
    const [resourceType, setResourceType] = useState("all")
    const [eventType, setEventType] = useState("all")
    const [dateFrom, setDateFrom] = useState("")
    const [dateTo, setDateTo] = useState("")

    // Export dialog
    const [exportDialogOpen, setExportDialogOpen] = useState(false)
    const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv")
    const [isExporting, setIsExporting] = useState(false)

    // Detail dialog
    const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null)

    const { addToast } = useToast()

    const fetchData = useCallback(async () => {
        try {
            const currentFilters: AuditLogFilters = {
                ...filters,
                search: searchQuery || undefined,
                // Convert "all" back to undefined for backend
                action_type: actionType && actionType !== "all" ? actionType : undefined,
                resource_type: resourceType && resourceType !== "all" ? resourceType : undefined,
                event_type: eventType && eventType !== "all" ? eventType : undefined,
                date_from: dateFrom || undefined,
                date_to: dateTo || undefined,
            }
            const response = await adminApi.getAuditLogs(page, pageSize, currentFilters)
            setData(response)
        } catch (error) {
            console.error("Failed to fetch audit logs:", error)
            addToast({
                type: "error",
                title: "Failed to load audit logs",
                description: "Please try again later",
            })
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [page, pageSize, filters, searchQuery, actionType, resourceType, eventType, dateFrom, dateTo, addToast])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const handleRefresh = () => {
        setIsRefreshing(true)
        fetchData()
    }

    const handleSearch = () => {
        setPage(1)
        fetchData()
    }

    const handleClearFilters = () => {
        setSearchQuery("")
        setActionType("all")
        setResourceType("all")
        setEventType("all")
        setDateFrom("")
        setDateTo("")
        setFilters({})
        setPage(1)
    }

    const handleExport = async () => {
        setIsExporting(true)
        try {
            const response = await adminApi.exportAuditLogs({
                format: exportFormat,
                date_from: dateFrom || undefined,
                date_to: dateTo || undefined,
                action_type: actionType && actionType !== "all" ? actionType : undefined,
                resource_type: resourceType && resourceType !== "all" ? resourceType : undefined,
            })

            addToast({
                type: "success",
                title: "Export started",
                description: `${response.record_count} records will be exported`,
            })
            setExportDialogOpen(false)

            // Open download URL
            if (response.download_url) {
                window.open(response.download_url, "_blank")
            }
        } catch (error) {
            console.error("Failed to export audit logs:", error)
            addToast({
                type: "error",
                title: "Export failed",
                description: "Please try again later",
            })
        } finally {
            setIsExporting(false)
        }
    }

    const hasActiveFilters = searchQuery || (actionType && actionType !== "all") || (resourceType && resourceType !== "all") || (eventType && eventType !== "all") || dateFrom || dateTo

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Compliance", href: "/admin/audit-logs" },
                { label: "Audit Logs" },
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
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                                <FileText className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Audit Logs
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Track all admin and system actions
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button
                            variant="outline"
                            onClick={() => setExportDialogOpen(true)}
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Export
                        </Button>
                        <Button
                            variant="outline"
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>
                </motion.div>

                {/* Filters */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <Card>
                        <CardContent className="pt-6">
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
                                <div className="lg:col-span-2">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                        <Input
                                            placeholder="Search in details..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                                            className="pl-10"
                                        />
                                    </div>
                                </div>
                                <Select value={actionType} onValueChange={setActionType}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Action Type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {ACTION_TYPES.map((type) => (
                                            <SelectItem key={type.value} value={type.value || "all"}>
                                                {type.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Select value={resourceType} onValueChange={setResourceType}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Resource Type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {RESOURCE_TYPES.map((type) => (
                                            <SelectItem key={type.value} value={type.value || "all"}>
                                                {type.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Select value={eventType} onValueChange={setEventType}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Event Type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {EVENT_TYPES.map((type) => (
                                            <SelectItem key={type.value} value={type.value || "all"}>
                                                {type.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <div className="flex gap-2">
                                    <Button onClick={handleSearch} className="flex-1">
                                        <Filter className="h-4 w-4 mr-2" />
                                        Apply
                                    </Button>
                                    {hasActiveFilters && (
                                        <Button variant="ghost" size="icon" onClick={handleClearFilters}>
                                            <X className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                            <div className="grid gap-4 md:grid-cols-2 mt-4">
                                <div>
                                    <Label className="text-xs text-slate-500">From Date</Label>
                                    <Input
                                        type="datetime-local"
                                        value={dateFrom}
                                        onChange={(e) => setDateFrom(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <Label className="text-xs text-slate-500">To Date</Label>
                                    <Input
                                        type="datetime-local"
                                        value={dateTo}
                                        onChange={(e) => setDateTo(e.target.value)}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Audit Logs Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <span>Audit Log Entries</span>
                                {data && (
                                    <span className="text-sm font-normal text-slate-500">
                                        {data.total} total entries
                                    </span>
                                )}
                            </CardTitle>
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
                                                <TableHead>Timestamp</TableHead>
                                                <TableHead>Actor</TableHead>
                                                <TableHead>Action</TableHead>
                                                <TableHead>Event</TableHead>
                                                <TableHead>IP Address</TableHead>
                                                <TableHead className="text-right">Details</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.items.map((log) => (
                                                <TableRow
                                                    key={log.id}
                                                    className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50"
                                                    onClick={() => setSelectedLog(log)}
                                                >
                                                    <TableCell className="text-sm">
                                                        {formatTimestamp(log.timestamp)}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            <User className="h-4 w-4 text-slate-400" />
                                                            <div>
                                                                <p className="font-medium text-sm">
                                                                    {log.actor_name || log.actor_email || "System"}
                                                                </p>
                                                                {log.actor_email && log.actor_name && (
                                                                    <p className="text-xs text-slate-500">{log.actor_email}</p>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant={getActionBadgeVariant(log.action)}>
                                                            {log.action}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        {log.event ? (
                                                            <span className="text-sm text-slate-600 dark:text-slate-400">
                                                                {log.event}
                                                            </span>
                                                        ) : log.resource_type ? (
                                                            <div className="text-sm">
                                                                <span className="text-slate-600 dark:text-slate-400">
                                                                    {log.resource_type}
                                                                </span>
                                                                {log.resource_id && (
                                                                    <span className="text-xs text-slate-400 ml-1">
                                                                        #{log.resource_id.slice(0, 8)}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        ) : (
                                                            <span className="text-slate-400">-</span>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-slate-500">
                                                        {log.ip_address || "-"}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <Button variant="ghost" size="sm">
                                                            View
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>

                                    {/* Pagination */}
                                    <div className="flex items-center justify-between mt-4 pt-4 border-t">
                                        <p className="text-sm text-slate-500">
                                            Showing {((data.page - 1) * pageSize) + 1} - {Math.min(data.page * pageSize, data.total)} of {data.total} entries
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(1)}
                                                disabled={page <= 1}
                                            >
                                                First
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(page - 1)}
                                                disabled={page <= 1}
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                            </Button>
                                            <span className="text-sm px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded">
                                                {data.page} / {data.total_pages}
                                            </span>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(page + 1)}
                                                disabled={page >= data.total_pages}
                                            >
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setPage(data.total_pages)}
                                                disabled={page >= data.total_pages}
                                            >
                                                Last
                                            </Button>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-12 text-slate-500">
                                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>No audit logs found</p>
                                    {hasActiveFilters && (
                                        <Button
                                            variant="link"
                                            onClick={handleClearFilters}
                                            className="mt-2"
                                        >
                                            Clear filters
                                        </Button>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Export Dialog */}
            <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Export Audit Logs</DialogTitle>
                        <DialogDescription>
                            Export audit logs with current filters applied
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Export Format</Label>
                            <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as "csv" | "json")}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="csv">CSV</SelectItem>
                                    <SelectItem value="json">JSON</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        {hasActiveFilters && (
                            <p className="text-sm text-slate-500">
                                Current filters will be applied to the export.
                            </p>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setExportDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleExport} disabled={isExporting}>
                            {isExporting ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Exporting...
                                </>
                            ) : (
                                <>
                                    <Download className="h-4 w-4 mr-2" />
                                    Export
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Log Detail Dialog */}
            <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Audit Log Details</DialogTitle>
                    </DialogHeader>
                    {selectedLog && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-xs text-slate-500">Timestamp</Label>
                                    <p className="font-medium">{formatTimestamp(selectedLog.timestamp)}</p>
                                </div>
                                <div>
                                    <Label className="text-xs text-slate-500">Action</Label>
                                    <Badge variant={getActionBadgeVariant(selectedLog.action)}>
                                        {selectedLog.action}
                                    </Badge>
                                </div>
                                <div>
                                    <Label className="text-xs text-slate-500">Actor</Label>
                                    <p className="font-medium">{selectedLog.actor_name || selectedLog.actor_email || "System"}</p>
                                    {selectedLog.actor_email && selectedLog.actor_name && (
                                        <p className="text-sm text-slate-500">{selectedLog.actor_email}</p>
                                    )}
                                </div>
                                <div>
                                    <Label className="text-xs text-slate-500">IP Address</Label>
                                    <p className="font-medium font-mono text-sm">{selectedLog.ip_address || "-"}</p>
                                </div>
                                {selectedLog.event && (
                                    <div>
                                        <Label className="text-xs text-slate-500">Event</Label>
                                        <p className="font-medium">{selectedLog.event}</p>
                                    </div>
                                )}
                                {selectedLog.resource_type && (
                                    <div>
                                        <Label className="text-xs text-slate-500">Resource Type</Label>
                                        <p className="font-medium">{selectedLog.resource_type}</p>
                                    </div>
                                )}
                                {selectedLog.resource_id && (
                                    <div className="col-span-2">
                                        <Label className="text-xs text-slate-500">Resource ID</Label>
                                        <p className="font-mono text-sm bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded inline-block">
                                            {selectedLog.resource_id}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {selectedLog.user_agent && (
                                <div>
                                    <Label className="text-xs text-slate-500">User Agent</Label>
                                    <p className="text-sm text-slate-600 dark:text-slate-400 break-all bg-slate-50 dark:bg-slate-800/50 p-2 rounded mt-1">
                                        {selectedLog.user_agent}
                                    </p>
                                </div>
                            )}

                            {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                                <div>
                                    <Label className="text-xs text-slate-500">Additional Details</Label>
                                    <div className="mt-1 p-3 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-auto max-h-60">
                                        <table className="w-full text-sm">
                                            <tbody>
                                                {Object.entries(selectedLog.details).map(([key, value]) => (
                                                    <tr key={key} className="border-b border-slate-200 dark:border-slate-700 last:border-0">
                                                        <td className="py-1.5 pr-4 text-slate-500 font-medium whitespace-nowrap">
                                                            {key}
                                                        </td>
                                                        <td className="py-1.5 text-slate-900 dark:text-slate-100 font-mono text-xs break-all">
                                                            {typeof value === "object" ? JSON.stringify(value) : String(value)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {/* Log ID for reference */}
                            <div className="pt-2 border-t">
                                <Label className="text-xs text-slate-400">Log ID</Label>
                                <p className="font-mono text-xs text-slate-400">{selectedLog.id}</p>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
