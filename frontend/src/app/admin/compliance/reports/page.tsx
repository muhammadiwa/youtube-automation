"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    FileBarChart,
    Plus,
    RefreshCw,
    CheckCircle2,
    Clock,
    XCircle,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Download,
    FileText,
    Shield,
    Users,
    Database,
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
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    ComplianceReportListResponse,
    ComplianceReport,
    CreateComplianceReportRequest,
    ComplianceReportType,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

function formatFileSize(bytes: number | null): string {
    if (!bytes) return "-"
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getStatusBadge(status: string) {
    switch (status) {
        case "pending":
            return <Badge variant="outline" className="border-amber-500 text-amber-600"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
        case "generating":
            return <Badge variant="outline" className="border-blue-500 text-blue-600"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Generating</Badge>
        case "completed":
            return <Badge variant="default" className="bg-emerald-500"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>
        case "failed":
            return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

function getReportTypeIcon(type: ComplianceReportType) {
    switch (type) {
        case "data_processing":
            return <Database className="h-4 w-4" />
        case "user_activity":
            return <Users className="h-4 w-4" />
        case "security_audit":
            return <Shield className="h-4 w-4" />
        case "gdpr_compliance":
            return <FileText className="h-4 w-4" />
        case "full_audit":
            return <FileBarChart className="h-4 w-4" />
        default:
            return <FileText className="h-4 w-4" />
    }
}

function getReportTypeLabel(type: ComplianceReportType): string {
    switch (type) {
        case "data_processing":
            return "Data Processing"
        case "user_activity":
            return "User Activity"
        case "security_audit":
            return "Security Audit"
        case "gdpr_compliance":
            return "GDPR Compliance"
        case "full_audit":
            return "Full Audit"
        default:
            return type
    }
}

const REPORT_TYPES: { value: ComplianceReportType; label: string; description: string }[] = [
    { value: "data_processing", label: "Data Processing", description: "Report on data processing activities" },
    { value: "user_activity", label: "User Activity", description: "Report on user activities and actions" },
    { value: "security_audit", label: "Security Audit", description: "Security audit and vulnerability report" },
    { value: "gdpr_compliance", label: "GDPR Compliance", description: "GDPR compliance status report" },
    { value: "full_audit", label: "Full Audit", description: "Comprehensive audit report" },
]

export default function ComplianceReportsPage() {
    const [data, setData] = useState<ComplianceReportListResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [page, setPage] = useState(1)
    const [statusFilter, setStatusFilter] = useState("all")
    const [typeFilter, setTypeFilter] = useState("all")

    // Create dialog state
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [isCreating, setIsCreating] = useState(false)
    const [newReport, setNewReport] = useState<CreateComplianceReportRequest>({
        report_type: "full_audit",
        title: "",
        description: "",
    })

    const { addToast } = useToast()

    const fetchReports = useCallback(async () => {
        try {
            const response = await adminApi.getComplianceReports({
                page,
                page_size: 20,
                status: statusFilter !== "all" ? statusFilter : undefined,
                report_type: typeFilter !== "all" ? typeFilter : undefined,
            })
            setData(response)
        } catch (error) {
            console.error("Failed to fetch compliance reports:", error)
            addToast({
                type: "error",
                title: "Failed to load reports",
                description: "Please try again later",
            })
        } finally {
            setIsLoading(false)
        }
    }, [page, statusFilter, typeFilter, addToast])

    useEffect(() => {
        fetchReports()
    }, [fetchReports])

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await fetchReports()
        setIsRefreshing(false)
    }

    const handleCreate = async () => {
        if (!newReport.title) {
            addToast({
                type: "error",
                title: "Validation Error",
                description: "Title is required",
            })
            return
        }

        setIsCreating(true)
        try {
            await adminApi.createComplianceReport(newReport)
            addToast({
                type: "success",
                title: "Report Generation Started",
                description: "The compliance report is being generated",
            })
            setCreateDialogOpen(false)
            setNewReport({ report_type: "full_audit", title: "", description: "" })
            fetchReports()
        } catch (error) {
            console.error("Failed to create compliance report:", error)
            addToast({
                type: "error",
                title: "Failed to generate report",
                description: "Please try again later",
            })
        } finally {
            setIsCreating(false)
        }
    }

    const handleDownload = (report: ComplianceReport) => {
        if (!report.file_path) {
            addToast({
                type: "error",
                title: "Download not available",
                description: "Report file is not available",
            })
            return
        }

        // In a real implementation, this would download the file
        addToast({
            type: "info",
            title: "Download Started",
            description: `Downloading ${report.title}`,
        })
    }

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Compliance", href: "/admin/compliance/requests" },
                { label: "Reports" },
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
                                <FileBarChart className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Compliance Reports
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Generate and manage audit-ready compliance reports
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
                            Generate Report
                        </Button>
                    </div>
                </motion.div>

                {/* Main Content */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <CardTitle>Report History</CardTitle>
                                    <CardDescription>
                                        All generated compliance reports
                                    </CardDescription>
                                </div>
                                <div className="flex gap-2">
                                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                                        <SelectTrigger className="w-40">
                                            <SelectValue placeholder="All Types" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Types</SelectItem>
                                            {REPORT_TYPES.map((type) => (
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
                                            <SelectItem value="generating">Generating</SelectItem>
                                            <SelectItem value="completed">Completed</SelectItem>
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
                                                <TableHead>Report</TableHead>
                                                <TableHead>Type</TableHead>
                                                <TableHead>Status</TableHead>
                                                <TableHead>Date Range</TableHead>
                                                <TableHead>Size</TableHead>
                                                <TableHead>Created</TableHead>
                                                <TableHead className="text-right">Actions</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.items.map((report) => (
                                                <TableRow key={report.id}>
                                                    <TableCell>
                                                        <div>
                                                            <p className="font-medium">{report.title}</p>
                                                            {report.description && (
                                                                <p className="text-sm text-slate-500 truncate max-w-xs">
                                                                    {report.description}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            {getReportTypeIcon(report.report_type)}
                                                            <span className="text-sm">
                                                                {getReportTypeLabel(report.report_type)}
                                                            </span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>{getStatusBadge(report.status)}</TableCell>
                                                    <TableCell className="text-sm">
                                                        {report.start_date && report.end_date ? (
                                                            <>
                                                                {new Date(report.start_date).toLocaleDateString()} -{" "}
                                                                {new Date(report.end_date).toLocaleDateString()}
                                                            </>
                                                        ) : (
                                                            "-"
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-sm">
                                                        {formatFileSize(report.file_size)}
                                                    </TableCell>
                                                    <TableCell className="text-sm">
                                                        {formatTimestamp(report.created_at)}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        {report.status === "completed" && report.file_path && (
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => handleDownload(report)}
                                                            >
                                                                <Download className="h-4 w-4 mr-1" />
                                                                Download
                                                            </Button>
                                                        )}
                                                        {report.status === "failed" && report.error_message && (
                                                            <Badge variant="destructive" className="cursor-help" title={report.error_message}>
                                                                <AlertTriangle className="h-3 w-3 mr-1" />
                                                                Error
                                                            </Badge>
                                                        )}
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
                                    <FileBarChart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>No compliance reports found</p>
                                    <Button
                                        className="mt-4"
                                        onClick={() => setCreateDialogOpen(true)}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Generate First Report
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Create Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Generate Compliance Report</DialogTitle>
                        <DialogDescription>
                            Generate an audit-ready compliance report for your records.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="report_type">Report Type *</Label>
                            <Select
                                value={newReport.report_type}
                                onValueChange={(value) => setNewReport({ ...newReport, report_type: value as ComplianceReportType })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select report type" />
                                </SelectTrigger>
                                <SelectContent>
                                    {REPORT_TYPES.map((type) => (
                                        <SelectItem key={type.value} value={type.value}>
                                            <div className="flex items-center gap-2">
                                                {getReportTypeIcon(type.value)}
                                                <div>
                                                    <p>{type.label}</p>
                                                    <p className="text-xs text-slate-500">{type.description}</p>
                                                </div>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="title">Title *</Label>
                            <Input
                                id="title"
                                placeholder="e.g., Q4 2024 Compliance Report"
                                value={newReport.title}
                                onChange={(e) => setNewReport({ ...newReport, title: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                placeholder="Optional description for this report"
                                value={newReport.description || ""}
                                onChange={(e) => setNewReport({ ...newReport, description: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="start_date">Start Date</Label>
                                <Input
                                    id="start_date"
                                    type="date"
                                    value={newReport.start_date || ""}
                                    onChange={(e) => setNewReport({ ...newReport, start_date: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="end_date">End Date</Label>
                                <Input
                                    id="end_date"
                                    type="date"
                                    value={newReport.end_date || ""}
                                    onChange={(e) => setNewReport({ ...newReport, end_date: e.target.value })}
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
                        <Button onClick={handleCreate} disabled={isCreating}>
                            {isCreating ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <FileBarChart className="h-4 w-4 mr-2" />
                                    Generate Report
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
