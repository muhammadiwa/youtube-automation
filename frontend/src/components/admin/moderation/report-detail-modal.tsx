"use client"

import { useState, useEffect } from "react"
import {
    AlertCircle,
    AlertTriangle,
    CheckCircle,
    Trash2,
    MessageSquareWarning,
    Video,
    MessageSquare,
    Radio,
    Image,
    User,
    Flag,
    Loader2,
} from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    ContentReportDetail,
    ReportSeverity,
    ReportStatus,
    ContentType,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

interface ReportDetailModalProps {
    reportId: string | null
    isOpen: boolean
    onClose: () => void
    onActionComplete: () => void
}

const severityConfig: Record<ReportSeverity, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
    critical: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        icon: <AlertCircle className="h-4 w-4" />,
        label: "Critical",
    },
    high: {
        color: "text-orange-600 dark:text-orange-400",
        bg: "bg-orange-500/10 border-orange-500/20",
        icon: <AlertTriangle className="h-4 w-4" />,
        label: "High",
    },
    medium: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        icon: <Flag className="h-4 w-4" />,
        label: "Medium",
    },
    low: {
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-500/10 border-blue-500/20",
        icon: <Flag className="h-4 w-4" />,
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
    video: { icon: <Video className="h-5 w-5" />, label: "Video" },
    comment: { icon: <MessageSquare className="h-5 w-5" />, label: "Comment" },
    stream: { icon: <Radio className="h-5 w-5" />, label: "Stream" },
    thumbnail: { icon: <Image className="h-5 w-5" />, label: "Thumbnail" },
}

type ActionMode = "none" | "approve" | "remove" | "warn"

export function ReportDetailModal({
    reportId,
    isOpen,
    onClose,
    onActionComplete,
}: ReportDetailModalProps) {
    const { addToast } = useToast()
    const [report, setReport] = useState<ContentReportDetail | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Action states
    const [actionMode, setActionMode] = useState<ActionMode>("none")
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [approveNotes, setApproveNotes] = useState("")
    const [removeReason, setRemoveReason] = useState("")
    const [notifyUser, setNotifyUser] = useState(true)
    const [warnReason, setWarnReason] = useState("")

    useEffect(() => {
        if (reportId && isOpen) {
            fetchReportDetail()
        }
    }, [reportId, isOpen])

    useEffect(() => {
        if (!isOpen) {
            // Reset state when modal closes
            setActionMode("none")
            setApproveNotes("")
            setRemoveReason("")
            setNotifyUser(true)
            setWarnReason("")
        }
    }, [isOpen])

    const fetchReportDetail = async () => {
        if (!reportId) return

        setIsLoading(true)
        setError(null)
        try {
            const data = await adminApi.getReportDetail(reportId)
            setReport(data)
        } catch (err) {
            console.error("Failed to fetch report detail:", err)
            setError("Failed to load report details")
        } finally {
            setIsLoading(false)
        }
    }

    const handleApprove = async () => {
        if (!reportId) return

        setIsSubmitting(true)
        try {
            await adminApi.approveContent(reportId, { notes: approveNotes || undefined })
            addToast({
                type: "success",
                title: "Content Approved",
                description: "The content has been approved and reports dismissed.",
            })
            onActionComplete()
        } catch (err) {
            console.error("Failed to approve content:", err)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to approve content. Please try again.",
            })
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleRemove = async () => {
        if (!reportId || !removeReason.trim()) return

        setIsSubmitting(true)
        try {
            await adminApi.removeContent(reportId, {
                reason: removeReason,
                notify_user: notifyUser,
            })
            addToast({
                type: "success",
                title: "Content Removed",
                description: "The content has been removed and the user has been notified.",
            })
            onActionComplete()
        } catch (err) {
            console.error("Failed to remove content:", err)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to remove content. Please try again.",
            })
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleWarn = async () => {
        if (!report?.content_owner.id || !warnReason.trim()) return

        setIsSubmitting(true)
        try {
            await adminApi.warnUser(report.content_owner.id, {
                reason: warnReason,
                related_report_id: reportId || undefined,
            })
            addToast({
                type: "success",
                title: "Warning Issued",
                description: "The user has been warned and notified.",
            })
            onActionComplete()
        } catch (err) {
            console.error("Failed to warn user:", err)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to issue warning. Please try again.",
            })
        } finally {
            setIsSubmitting(false)
        }
    }


    const renderActionPanel = () => {
        if (report?.status !== "pending") {
            return (
                <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg text-center">
                    <p className="text-sm text-muted-foreground">
                        This report has already been {report?.status}
                    </p>
                </div>
            )
        }

        switch (actionMode) {
            case "approve":
                return (
                    <div className="space-y-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                        <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                            <CheckCircle className="h-5 w-5" />
                            <span className="font-medium">Approve Content</span>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="approve-notes">Notes (optional)</Label>
                            <Textarea
                                id="approve-notes"
                                placeholder="Add any notes about this approval..."
                                value={approveNotes}
                                onChange={(e) => setApproveNotes(e.target.value)}
                                className="min-h-[80px]"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button
                                onClick={handleApprove}
                                disabled={isSubmitting}
                                className="bg-emerald-600 hover:bg-emerald-700"
                            >
                                {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                Confirm Approval
                            </Button>
                            <Button variant="outline" onClick={() => setActionMode("none")}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                )
            case "remove":
                return (
                    <div className="space-y-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                        <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                            <Trash2 className="h-5 w-5" />
                            <span className="font-medium">Remove Content</span>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="remove-reason">Reason for removal *</Label>
                            <Textarea
                                id="remove-reason"
                                placeholder="Explain why this content is being removed..."
                                value={removeReason}
                                onChange={(e) => setRemoveReason(e.target.value)}
                                className="min-h-[80px]"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <Switch
                                id="notify-user"
                                checked={notifyUser}
                                onCheckedChange={setNotifyUser}
                            />
                            <Label htmlFor="notify-user">Notify content owner</Label>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                onClick={handleRemove}
                                disabled={isSubmitting || !removeReason.trim()}
                                variant="destructive"
                            >
                                {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                Confirm Removal
                            </Button>
                            <Button variant="outline" onClick={() => setActionMode("none")}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                )

            case "warn":
                return (
                    <div className="space-y-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                            <MessageSquareWarning className="h-5 w-5" />
                            <span className="font-medium">Warn User</span>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="warn-reason">Warning message *</Label>
                            <Textarea
                                id="warn-reason"
                                placeholder="Explain why the user is being warned..."
                                value={warnReason}
                                onChange={(e) => setWarnReason(e.target.value)}
                                className="min-h-[80px]"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button
                                onClick={handleWarn}
                                disabled={isSubmitting || !warnReason.trim()}
                                className="bg-amber-600 hover:bg-amber-700"
                            >
                                {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                Issue Warning
                            </Button>
                            <Button variant="outline" onClick={() => setActionMode("none")}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                )
            default:
                return (
                    <div className="flex flex-wrap gap-2">
                        <Button
                            onClick={() => setActionMode("approve")}
                            className="bg-emerald-600 hover:bg-emerald-700"
                        >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                        </Button>
                        <Button
                            onClick={() => setActionMode("remove")}
                            variant="destructive"
                        >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Remove
                        </Button>
                        <Button
                            onClick={() => setActionMode("warn")}
                            variant="outline"
                            className="border-amber-500 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                        >
                            <MessageSquareWarning className="h-4 w-4 mr-2" />
                            Warn User
                        </Button>
                    </div>
                )
        }
    }


    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Flag className="h-5 w-5 text-amber-500" />
                        Report Details
                    </DialogTitle>
                    <DialogDescription>
                        Review the reported content and take appropriate action
                    </DialogDescription>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                    </div>
                ) : error ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
                        <p className="text-red-500">{error}</p>
                        <Button onClick={fetchReportDetail} className="mt-4">
                            Try Again
                        </Button>
                    </div>
                ) : report ? (
                    <div className="space-y-6">
                        {/* Content Info */}
                        <div className="flex items-start gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                                {contentTypeConfig[report.content_type]?.icon}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="font-semibold">
                                        {contentTypeConfig[report.content_type]?.label}
                                    </span>
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "gap-1 font-medium",
                                            severityConfig[report.severity].bg,
                                            severityConfig[report.severity].color
                                        )}
                                    >
                                        {severityConfig[report.severity].icon}
                                        {severityConfig[report.severity].label}
                                    </Badge>
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "font-medium",
                                            statusConfig[report.status].bg,
                                            statusConfig[report.status].color
                                        )}
                                    >
                                        {statusConfig[report.status].label}
                                    </Badge>
                                </div>
                                {report.content_preview && (
                                    <p className="text-sm text-muted-foreground line-clamp-3">
                                        {report.content_preview}
                                    </p>
                                )}
                            </div>
                        </div>


                        {/* Report Details Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <p className="text-sm text-muted-foreground">Report Count</p>
                                <p className="font-semibold">{report.report_count} reports</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm text-muted-foreground">Reported</p>
                                <p className="font-semibold">
                                    {format(new Date(report.created_at), "PPp")}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm text-muted-foreground">Reason Category</p>
                                <p className="font-semibold capitalize">
                                    {report.reason_category || "Not specified"}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm text-muted-foreground">Content ID</p>
                                <p className="font-mono text-sm truncate">{report.content_id}</p>
                            </div>
                        </div>

                        <Separator />

                        {/* Report Reason */}
                        <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2">
                                <Flag className="h-4 w-4 text-amber-500" />
                                Report Reason
                            </h4>
                            <p className="text-sm bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg">
                                {report.reason}
                            </p>
                        </div>

                        <Separator />

                        {/* Content Owner */}
                        <div className="space-y-2">
                            <h4 className="font-semibold flex items-center gap-2">
                                <User className="h-4 w-4 text-blue-500" />
                                Content Owner
                            </h4>
                            <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500 text-white font-semibold">
                                    {report.content_owner.name?.charAt(0).toUpperCase() || "?"}
                                </div>
                                <div>
                                    <p className="font-medium">{report.content_owner.name || "Unknown"}</p>
                                    <p className="text-sm text-muted-foreground">
                                        {report.content_owner.email || "No email"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Reporter Info */}
                        {report.reporter && (
                            <>
                                <Separator />
                                <div className="space-y-2">
                                    <h4 className="font-semibold flex items-center gap-2">
                                        <User className="h-4 w-4 text-slate-500" />
                                        Reporter
                                    </h4>
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-500 text-white font-semibold">
                                            {report.reporter.name?.charAt(0).toUpperCase() || "?"}
                                        </div>
                                        <div>
                                            <p className="font-medium">{report.reporter.name || "Anonymous"}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {report.reporter.email || "No email"}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        <Separator />

                        {/* Actions */}
                        <div className="space-y-4">
                            <h4 className="font-semibold">Actions</h4>
                            {renderActionPanel()}
                        </div>
                    </div>
                ) : null}
            </DialogContent>
        </Dialog>
    )
}
