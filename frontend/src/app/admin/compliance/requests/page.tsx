"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    FileDown,
    Trash2,
    RefreshCw,
    CheckCircle2,
    Clock,
    XCircle,
    AlertTriangle,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Play,
    X,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
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
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    DataExportRequestListResponse,
    DataExportRequestItem,
    DeletionRequestListResponse,
    DeletionRequestItem,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

function getStatusBadge(status: string) {
    switch (status) {
        case "pending":
            return <Badge variant="outline" className="border-amber-500 text-amber-600"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
        case "processing":
            return <Badge variant="outline" className="border-blue-500 text-blue-600"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Processing</Badge>
        case "completed":
            return <Badge variant="default" className="bg-emerald-500"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>
        case "failed":
            return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
        case "scheduled":
            return <Badge variant="outline" className="border-purple-500 text-purple-600"><Clock className="h-3 w-3 mr-1" />Scheduled</Badge>
        case "cancelled":
            return <Badge variant="secondary"><X className="h-3 w-3 mr-1" />Cancelled</Badge>
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

export default function DataRequestsPage() {
    const [activeTab, setActiveTab] = useState("export")

    // Export requests state
    const [exportData, setExportData] = useState<DataExportRequestListResponse | null>(null)
    const [isLoadingExport, setIsLoadingExport] = useState(true)
    const [exportPage, setExportPage] = useState(1)
    const [exportStatus, setExportStatus] = useState("")

    // Deletion requests state
    const [deletionData, setDeletionData] = useState<DeletionRequestListResponse | null>(null)
    const [isLoadingDeletion, setIsLoadingDeletion] = useState(true)
    const [deletionPage, setDeletionPage] = useState(1)
    const [deletionStatus, setDeletionStatus] = useState("")

    // Processing state
    const [processingId, setProcessingId] = useState<string | null>(null)
    const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
    const [selectedDeletion, setSelectedDeletion] = useState<DeletionRequestItem | null>(null)
    const [cancelReason, setCancelReason] = useState("")
    const [isCancelling, setIsCancelling] = useState(false)

    const [isRefreshing, setIsRefreshing] = useState(false)
    const { addToast } = useToast()

    const fetchExportRequests = useCallback(async () => {
        try {
            const response = await adminApi.getDataExportRequests(
                exportPage,
                20,
                exportStatus || undefined
            )
            setExportData(response)
        } catch (error) {
            console.error("Failed to fetch export requests:", error)
        } finally {
            setIsLoadingExport(false)
        }
    }, [exportPage, exportStatus])

    const fetchDeletionRequests = useCallback(async () => {
        try {
            const response = await adminApi.getDeletionRequests(
                deletionPage,
                20,
                deletionStatus || undefined
            )
            setDeletionData(response)
        } catch (error) {
            console.error("Failed to fetch deletion requests:", error)
        } finally {
            setIsLoadingDeletion(false)
        }
    }, [deletionPage, deletionStatus])

    useEffect(() => {
        fetchExportRequests()
    }, [fetchExportRequests])

    useEffect(() => {
        fetchDeletionRequests()
    }, [fetchDeletionRequests])

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await Promise.all([fetchExportRequests(), fetchDeletionRequests()])
        setIsRefreshing(false)
    }

    const handleProcessExport = async (requestId: string) => {
        setProcessingId(requestId)
        try {
            const response = await adminApi.processDataExport(requestId)
            addToast({
                type: "success",
                title: "Export processing started",
                description: response.message,
            })
            fetchExportRequests()
        } catch (error) {
            console.error("Failed to process export:", error)
            addToast({
                type: "error",
                title: "Failed to process export",
                description: "Please try again later",
            })
        } finally {
            setProcessingId(null)
        }
    }

    const handleProcessDeletion = async (requestId: string) => {
        setProcessingId(requestId)
        try {
            const response = await adminApi.processDeletion(requestId)
            addToast({
                type: "success",
                title: "Deletion scheduled",
                description: response.message,
            })
            fetchDeletionRequests()
        } catch (error) {
            console.error("Failed to process deletion:", error)
            addToast({
                type: "error",
                title: "Failed to process deletion",
                description: "Please try again later",
            })
        } finally {
            setProcessingId(null)
        }
    }

    const handleCancelDeletion = async () => {
        if (!selectedDeletion) return

        setIsCancelling(true)
        try {
            const response = await adminApi.cancelDeletion(selectedDeletion.id, {
                reason: cancelReason || undefined,
            })
            addToast({
                type: "success",
                title: "Deletion cancelled",
                description: response.message,
            })
            setCancelDialogOpen(false)
            setSelectedDeletion(null)
            setCancelReason("")
            fetchDeletionRequests()
        } catch (error) {
            console.error("Failed to cancel deletion:", error)
            addToast({
                type: "error",
                title: "Failed to cancel deletion",
                description: "Please try again later",
            })
        } finally {
            setIsCancelling(false)
        }
    }

    const openCancelDialog = (deletion: DeletionRequestItem) => {
        setSelectedDeletion(deletion)
        setCancelReason("")
        setCancelDialogOpen(true)
    }

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Compliance", href: "/admin/compliance/requests" },
                { label: "Data Requests" },
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
                            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/25">
                                <FileDown className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Data Requests
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Manage user data export and deletion requests
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

                {/* Tabs */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList>
                            <TabsTrigger value="export" className="flex items-center gap-2">
                                <FileDown className="h-4 w-4" />
                                Export Requests
                                {exportData && exportData.total > 0 && (
                                    <Badge variant="secondary" className="ml-1">
                                        {exportData.total}
                                    </Badge>
                                )}
                            </TabsTrigger>
                            <TabsTrigger value="deletion" className="flex items-center gap-2">
                                <Trash2 className="h-4 w-4" />
                                Deletion Requests
                                {deletionData && deletionData.total > 0 && (
                                    <Badge variant="secondary" className="ml-1">
                                        {deletionData.total}
                                    </Badge>
                                )}
                            </TabsTrigger>
                        </TabsList>

                        {/* Export Requests Tab */}
                        <TabsContent value="export" className="mt-6">
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle>Data Export Requests</CardTitle>
                                            <CardDescription>
                                                User requests for their data export (GDPR compliance)
                                            </CardDescription>
                                        </div>
                                        <Select value={exportStatus} onValueChange={setExportStatus}>
                                            <SelectTrigger className="w-40">
                                                <SelectValue placeholder="All Status" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="">All Status</SelectItem>
                                                <SelectItem value="pending">Pending</SelectItem>
                                                <SelectItem value="processing">Processing</SelectItem>
                                                <SelectItem value="completed">Completed</SelectItem>
                                                <SelectItem value="failed">Failed</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {isLoadingExport ? (
                                        <div className="space-y-4">
                                            {[...Array(5)].map((_, i) => (
                                                <Skeleton key={i} className="h-16 w-full" />
                                            ))}
                                        </div>
                                    ) : exportData && exportData.items.length > 0 ? (
                                        <>
                                            <Table>
                                                <TableHeader>
                                                    <TableRow>
                                                        <TableHead>User</TableHead>
                                                        <TableHead>Status</TableHead>
                                                        <TableHead>Requested</TableHead>
                                                        <TableHead>Completed</TableHead>
                                                        <TableHead className="text-right">Actions</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {exportData.items.map((request) => (
                                                        <TableRow key={request.id}>
                                                            <TableCell>
                                                                <div>
                                                                    <p className="font-medium">{request.user_name || "Unknown"}</p>
                                                                    <p className="text-sm text-slate-500">{request.user_email}</p>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell>{getStatusBadge(request.status)}</TableCell>
                                                            <TableCell className="text-sm">
                                                                {formatTimestamp(request.requested_at)}
                                                            </TableCell>
                                                            <TableCell className="text-sm">
                                                                {request.completed_at ? formatTimestamp(request.completed_at) : "-"}
                                                            </TableCell>
                                                            <TableCell className="text-right">
                                                                {request.status === "pending" && (
                                                                    <Button
                                                                        size="sm"
                                                                        onClick={() => handleProcessExport(request.id)}
                                                                        disabled={processingId === request.id}
                                                                    >
                                                                        {processingId === request.id ? (
                                                                            <Loader2 className="h-4 w-4 animate-spin" />
                                                                        ) : (
                                                                            <>
                                                                                <Play className="h-4 w-4 mr-1" />
                                                                                Process
                                                                            </>
                                                                        )}
                                                                    </Button>
                                                                )}
                                                                {request.status === "completed" && request.download_url && (
                                                                    <Button
                                                                        size="sm"
                                                                        variant="outline"
                                                                        onClick={() => window.open(request.download_url!, "_blank")}
                                                                    >
                                                                        <FileDown className="h-4 w-4 mr-1" />
                                                                        Download
                                                                    </Button>
                                                                )}
                                                            </TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>

                                            {/* Pagination */}
                                            <div className="flex items-center justify-between mt-4">
                                                <p className="text-sm text-slate-500">
                                                    Page {exportData.page} of {exportData.total_pages}
                                                </p>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setExportPage(exportPage - 1)}
                                                        disabled={exportPage <= 1}
                                                    >
                                                        <ChevronLeft className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setExportPage(exportPage + 1)}
                                                        disabled={exportPage >= exportData.total_pages}
                                                    >
                                                        <ChevronRight className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="text-center py-12 text-slate-500">
                                            <FileDown className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No export requests found</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>

                        {/* Deletion Requests Tab */}
                        <TabsContent value="deletion" className="mt-6">
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle>Account Deletion Requests</CardTitle>
                                            <CardDescription>
                                                User requests for account deletion (30-day grace period)
                                            </CardDescription>
                                        </div>
                                        <Select value={deletionStatus} onValueChange={setDeletionStatus}>
                                            <SelectTrigger className="w-40">
                                                <SelectValue placeholder="All Status" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="">All Status</SelectItem>
                                                <SelectItem value="pending">Pending</SelectItem>
                                                <SelectItem value="scheduled">Scheduled</SelectItem>
                                                <SelectItem value="processing">Processing</SelectItem>
                                                <SelectItem value="completed">Completed</SelectItem>
                                                <SelectItem value="cancelled">Cancelled</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {isLoadingDeletion ? (
                                        <div className="space-y-4">
                                            {[...Array(5)].map((_, i) => (
                                                <Skeleton key={i} className="h-16 w-full" />
                                            ))}
                                        </div>
                                    ) : deletionData && deletionData.items.length > 0 ? (
                                        <>
                                            <Table>
                                                <TableHeader>
                                                    <TableRow>
                                                        <TableHead>User</TableHead>
                                                        <TableHead>Status</TableHead>
                                                        <TableHead>Requested</TableHead>
                                                        <TableHead>Scheduled For</TableHead>
                                                        <TableHead>Days Left</TableHead>
                                                        <TableHead className="text-right">Actions</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {deletionData.items.map((request) => (
                                                        <TableRow key={request.id}>
                                                            <TableCell>
                                                                <div>
                                                                    <p className="font-medium">{request.user_name || "Unknown"}</p>
                                                                    <p className="text-sm text-slate-500">{request.user_email}</p>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell>{getStatusBadge(request.status)}</TableCell>
                                                            <TableCell className="text-sm">
                                                                {formatTimestamp(request.requested_at)}
                                                            </TableCell>
                                                            <TableCell className="text-sm">
                                                                {formatTimestamp(request.scheduled_for)}
                                                            </TableCell>
                                                            <TableCell>
                                                                {request.status === "scheduled" || request.status === "pending" ? (
                                                                    <Badge
                                                                        variant={request.days_remaining <= 7 ? "destructive" : "outline"}
                                                                    >
                                                                        {request.days_remaining} days
                                                                    </Badge>
                                                                ) : (
                                                                    "-"
                                                                )}
                                                            </TableCell>
                                                            <TableCell className="text-right">
                                                                <div className="flex justify-end gap-2">
                                                                    {request.status === "pending" && (
                                                                        <Button
                                                                            size="sm"
                                                                            onClick={() => handleProcessDeletion(request.id)}
                                                                            disabled={processingId === request.id}
                                                                        >
                                                                            {processingId === request.id ? (
                                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                                            ) : (
                                                                                <>
                                                                                    <Play className="h-4 w-4 mr-1" />
                                                                                    Schedule
                                                                                </>
                                                                            )}
                                                                        </Button>
                                                                    )}
                                                                    {(request.status === "pending" || request.status === "scheduled") && (
                                                                        <Button
                                                                            size="sm"
                                                                            variant="outline"
                                                                            onClick={() => openCancelDialog(request)}
                                                                        >
                                                                            <X className="h-4 w-4 mr-1" />
                                                                            Cancel
                                                                        </Button>
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
                                                    Page {deletionData.page} of {deletionData.total_pages}
                                                </p>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setDeletionPage(deletionPage - 1)}
                                                        disabled={deletionPage <= 1}
                                                    >
                                                        <ChevronLeft className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setDeletionPage(deletionPage + 1)}
                                                        disabled={deletionPage >= deletionData.total_pages}
                                                    >
                                                        <ChevronRight className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="text-center py-12 text-slate-500">
                                            <Trash2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No deletion requests found</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </motion.div>
            </div>

            {/* Cancel Deletion Dialog */}
            <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                            Cancel Deletion Request
                        </DialogTitle>
                        <DialogDescription>
                            Are you sure you want to cancel this deletion request?
                            The user&apos;s account will not be deleted.
                        </DialogDescription>
                    </DialogHeader>
                    {selectedDeletion && (
                        <div className="py-4">
                            <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg mb-4">
                                <p className="font-medium">{selectedDeletion.user_name || "Unknown User"}</p>
                                <p className="text-sm text-slate-500">{selectedDeletion.user_email}</p>
                            </div>
                            <div className="space-y-2">
                                <Label>Cancellation Reason (optional)</Label>
                                <Textarea
                                    placeholder="Enter reason for cancellation..."
                                    value={cancelReason}
                                    onChange={(e) => setCancelReason(e.target.value)}
                                />
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setCancelDialogOpen(false)}
                            disabled={isCancelling}
                        >
                            Keep Request
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleCancelDeletion}
                            disabled={isCancelling}
                        >
                            {isCancelling ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Cancelling...
                                </>
                            ) : (
                                "Cancel Deletion"
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
