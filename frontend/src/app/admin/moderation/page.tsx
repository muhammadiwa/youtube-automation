"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Shield,
    Search,
    Filter,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    AlertTriangle,
    Eye,
    CheckCircle,
    Trash2,
    MessageSquareWarning,
    Video,
    MessageSquare,
    Radio,
    Image,
    Clock,
    Users,
    Flag,
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
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    ContentReportSummary,
    ModerationFilters,
    ReportSeverity,
    ReportStatus,
    ContentType,
} from "@/types/admin"
import { ReportDetailModal } from "@/components/admin/moderation"


const severityConfig: Record<ReportSeverity, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
    critical: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        icon: <AlertCircle className="h-3.5 w-3.5" />,
        label: "Critical",
    },
    high: {
        color: "text-orange-600 dark:text-orange-400",
        bg: "bg-orange-500/10 border-orange-500/20",
        icon: <AlertTriangle className="h-3.5 w-3.5" />,
        label: "High",
    },
    medium: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        icon: <Flag className="h-3.5 w-3.5" />,
        label: "Medium",
    },
    low: {
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-500/10 border-blue-500/20",
        icon: <Flag className="h-3.5 w-3.5" />,
        label: "Low",
    },
}

const statusConfig: Record<ReportStatus, { color: string; bg: string; label: string }> = {
    pending: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        label: "Pending",
    },
    reviewed: {
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-500/10 border-blue-500/20",
        label: "Reviewed",
    },
    approved: {
        color: "text-emerald-600 dark:text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        label: "Approved",
    },
    removed: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        label: "Removed",
    },
}

const contentTypeConfig: Record<ContentType, { icon: React.ReactNode; label: string }> = {
    video: { icon: <Video className="h-4 w-4" />, label: "Video" },
    comment: { icon: <MessageSquare className="h-4 w-4" />, label: "Comment" },
    stream: { icon: <Radio className="h-4 w-4" />, label: "Stream" },
    thumbnail: { icon: <Image className="h-4 w-4" />, label: "Thumbnail" },
}

function StatsCard({
    title,
    value,
    icon: Icon,
    gradient,
    delay = 0,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
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
                <CardContent className="p-5 h-full flex flex-col justify-between min-h-[100px]">
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
                </CardContent>
            </Card>
        </motion.div>
    )
}


export default function AdminModerationPage() {
    const [reports, setReports] = useState<ContentReportSummary[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(10)
    const [totalPages, setTotalPages] = useState(0)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filters
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("pending")
    const [severityFilter, setSeverityFilter] = useState<string>("all")
    const [contentTypeFilter, setContentTypeFilter] = useState<string>("all")
    const [showFilters, setShowFilters] = useState(false)

    // Modal state
    const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
    const [isModalOpen, setIsModalOpen] = useState(false)

    // Stats
    const [stats, setStats] = useState({
        pending: 0,
        critical: 0,
        high: 0,
        resolved: 0,
    })

    const fetchReports = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const filters: ModerationFilters = {}
            if (search) filters.search = search
            if (statusFilter && statusFilter !== "all") filters.status = statusFilter as ReportStatus
            if (severityFilter && severityFilter !== "all") filters.severity = severityFilter as ReportSeverity
            if (contentTypeFilter && contentTypeFilter !== "all") filters.content_type = contentTypeFilter as ContentType

            const response = await adminApi.getModerationQueue({
                page,
                page_size: pageSize,
                filters,
            })
            setReports(response.items)
            setTotal(response.total)
            setTotalPages(response.total_pages)

            // Calculate stats from response
            const pendingCount = response.items.filter(r => r.status === "pending").length
            const criticalCount = response.items.filter(r => r.severity === "critical").length
            const highCount = response.items.filter(r => r.severity === "high").length
            const resolvedCount = response.items.filter(r => r.status === "approved" || r.status === "removed").length

            setStats({
                pending: response.total,
                critical: criticalCount,
                high: highCount,
                resolved: resolvedCount,
            })
        } catch (err) {
            console.error("Failed to fetch moderation queue:", err)
            setError("Failed to load moderation queue. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [page, pageSize, search, statusFilter, severityFilter, contentTypeFilter])

    useEffect(() => {
        fetchReports()
    }, [fetchReports])

    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1)
        }, 300)
        return () => clearTimeout(timer)
    }, [search])

    const handleViewReport = (reportId: string) => {
        setSelectedReportId(reportId)
        setIsModalOpen(true)
    }

    const handleModalClose = () => {
        setIsModalOpen(false)
        setSelectedReportId(null)
    }

    const handleActionComplete = () => {
        fetchReports()
        handleModalClose()
    }

    const clearFilters = () => {
        setSearch("")
        setStatusFilter("pending")
        setSeverityFilter("all")
        setContentTypeFilter("all")
        setPage(1)
    }

    const hasActiveFilters = search || statusFilter !== "pending" || severityFilter !== "all" || contentTypeFilter !== "all"


    return (
        <AdminLayout breadcrumbs={[{ label: "Moderation" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Content Moderation
                        </h1>
                        <p className="text-muted-foreground">
                            Review and moderate reported content to maintain platform quality
                        </p>
                    </div>
                </motion.div>

                {/* Stats Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <StatsCard
                        title="Pending Reports"
                        value={stats.pending.toLocaleString()}
                        icon={Clock}
                        gradient="from-amber-500 to-amber-600"
                        delay={0}
                    />
                    <StatsCard
                        title="Critical"
                        value={stats.critical.toLocaleString()}
                        icon={AlertCircle}
                        gradient="from-red-500 to-red-600"
                        delay={0.05}
                    />
                    <StatsCard
                        title="High Priority"
                        value={stats.high.toLocaleString()}
                        icon={AlertTriangle}
                        gradient="from-orange-500 to-orange-600"
                        delay={0.1}
                    />
                    <StatsCard
                        title="Resolved Today"
                        value={stats.resolved.toLocaleString()}
                        icon={CheckCircle}
                        gradient="from-emerald-500 to-emerald-600"
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
                                        placeholder="Search by content or reason..."
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        className="pl-12 h-12 text-base bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500/20"
                                    />
                                </div>

                                {/* Quick Filters */}
                                <div className="flex items-center gap-3 flex-wrap">
                                    <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[140px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="pending">Pending</SelectItem>
                                            <SelectItem value="reviewed">Reviewed</SelectItem>
                                            <SelectItem value="approved">Approved</SelectItem>
                                            <SelectItem value="removed">Removed</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    <Select value={severityFilter} onValueChange={(v) => { setSeverityFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[140px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Severity" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Severity</SelectItem>
                                            <SelectItem value="critical">Critical</SelectItem>
                                            <SelectItem value="high">High</SelectItem>
                                            <SelectItem value="medium">Medium</SelectItem>
                                            <SelectItem value="low">Low</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => setShowFilters(!showFilters)}
                                        className={cn(
                                            "h-12 px-4 rounded-xl border-slate-200 dark:border-slate-700",
                                            showFilters && "bg-blue-50 dark:bg-blue-900/20 border-blue-500/50"
                                        )}
                                    >
                                        <Filter className="h-5 w-5 mr-2" />
                                        More Filters
                                    </Button>

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

                            {/* Advanced Filters */}
                            {showFilters && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700 flex flex-wrap gap-6"
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm font-medium">Content Type:</span>
                                        <Select value={contentTypeFilter} onValueChange={(v) => { setContentTypeFilter(v); setPage(1) }}>
                                            <SelectTrigger className="w-[150px] h-10 rounded-xl">
                                                <SelectValue placeholder="All Types" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="all">All Types</SelectItem>
                                                <SelectItem value="video">Video</SelectItem>
                                                <SelectItem value="comment">Comment</SelectItem>
                                                <SelectItem value="stream">Stream</SelectItem>
                                                <SelectItem value="thumbnail">Thumbnail</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </motion.div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Reports Table */}
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
                                        <Shield className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-blue-500" />
                                    </div>
                                    <p className="mt-4 text-muted-foreground">Loading moderation queue...</p>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                                        <AlertCircle className="h-8 w-8 text-red-500" />
                                    </div>
                                    <p className="text-lg font-medium text-red-500 mb-2">Failed to load reports</p>
                                    <p className="text-muted-foreground mb-4">{error}</p>
                                    <Button onClick={fetchReports} className="rounded-xl">
                                        Try Again
                                    </Button>
                                </div>
                            ) : reports.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-20 w-20 rounded-full bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center mb-4">
                                        <CheckCircle className="h-10 w-10 text-emerald-500" />
                                    </div>
                                    <p className="text-lg font-medium mb-2">No reports found</p>
                                    <p className="text-muted-foreground mb-4">
                                        {hasActiveFilters ? "Try adjusting your filters" : "The moderation queue is empty"}
                                    </p>
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
                                                <TableHead className="font-semibold">Content</TableHead>
                                                <TableHead className="font-semibold">Severity</TableHead>
                                                <TableHead className="font-semibold">Reports</TableHead>
                                                <TableHead className="font-semibold">Status</TableHead>
                                                <TableHead className="font-semibold">Owner</TableHead>
                                                <TableHead className="font-semibold">Reported</TableHead>
                                                <TableHead className="w-[120px]">Actions</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {reports.map((report, index) => (
                                                <motion.tr
                                                    key={report.id}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: index * 0.05 }}
                                                    className="group hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors"
                                                >
                                                    <TableCell>
                                                        <div className="flex items-center gap-3">
                                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                                                                {contentTypeConfig[report.content_type]?.icon}
                                                            </div>
                                                            <div className="max-w-[250px]">
                                                                <p className="font-medium text-slate-900 dark:text-white truncate">
                                                                    {contentTypeConfig[report.content_type]?.label}
                                                                </p>
                                                                <p className="text-sm text-muted-foreground truncate">
                                                                    {report.content_preview || report.reason}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge
                                                            variant="outline"
                                                            className={cn(
                                                                "gap-1.5 font-medium rounded-lg px-3 py-1",
                                                                severityConfig[report.severity].bg,
                                                                severityConfig[report.severity].color
                                                            )}
                                                        >
                                                            {severityConfig[report.severity].icon}
                                                            {severityConfig[report.severity].label}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-1.5">
                                                            <Users className="h-4 w-4 text-muted-foreground" />
                                                            <span className="font-semibold">{report.report_count}</span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge
                                                            variant="outline"
                                                            className={cn(
                                                                "font-medium rounded-lg px-3 py-1",
                                                                statusConfig[report.status].bg,
                                                                statusConfig[report.status].color
                                                            )}
                                                        >
                                                            {statusConfig[report.status].label}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {report.content_owner_email || "Unknown"}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => handleViewReport(report.id)}
                                                                className="h-8 w-8 p-0 rounded-lg"
                                                            >
                                                                <Eye className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </TableCell>
                                                </motion.tr>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}


                            {/* Pagination */}
                            {!isLoading && !error && reports.length > 0 && (
                                <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-700">
                                    <p className="text-sm text-muted-foreground">
                                        Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} reports
                                    </p>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                            className="h-9 rounded-lg"
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
                                                        variant={page === pageNum ? "default" : "ghost"}
                                                        size="sm"
                                                        onClick={() => setPage(pageNum)}
                                                        className={cn(
                                                            "h-9 w-9 p-0 rounded-lg",
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
                                            className="h-9 rounded-lg"
                                        >
                                            Next
                                            <ChevronRight className="h-4 w-4 ml-1" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Report Detail Modal */}
            <ReportDetailModal
                reportId={selectedReportId}
                isOpen={isModalOpen}
                onClose={handleModalClose}
                onActionComplete={handleActionComplete}
            />
        </AdminLayout>
    )
}
