"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    FileText,
    Plus,
    RefreshCw,
    CheckCircle2,
    Clock,
    Archive,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Eye,
    Power,
    Pencil,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RichTextEditor, RichTextViewer } from "@/components/ui/rich-text-editor"
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
    TermsOfServiceListResponse,
    TermsOfService,
    CreateTermsOfServiceRequest,
    UpdateTermsOfServiceRequest,
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
}

function getStatusBadge(status: string) {
    switch (status) {
        case "draft":
            return <Badge variant="outline" className="border-slate-500 text-slate-600"><Clock className="h-3 w-3 mr-1" />Draft</Badge>
        case "active":
            return <Badge variant="default" className="bg-emerald-500"><CheckCircle2 className="h-3 w-3 mr-1" />Active</Badge>
        case "archived":
            return <Badge variant="secondary"><Archive className="h-3 w-3 mr-1" />Archived</Badge>
        default:
            return <Badge variant="outline">{status}</Badge>
    }
}

export default function TermsOfServicePage() {
    const [data, setData] = useState<TermsOfServiceListResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [page, setPage] = useState(1)
    const [statusFilter, setStatusFilter] = useState("all")

    // Create dialog state
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [isCreating, setIsCreating] = useState(false)
    const [newTerms, setNewTerms] = useState<CreateTermsOfServiceRequest>({
        version: "",
        title: "",
        content: "",
        content_html: "",
        summary: "",
    })

    // Preview dialog state
    const [previewDialogOpen, setPreviewDialogOpen] = useState(false)
    const [selectedTerms, setSelectedTerms] = useState<TermsOfService | null>(null)

    // Edit dialog state
    const [editDialogOpen, setEditDialogOpen] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [editTerms, setEditTerms] = useState<UpdateTermsOfServiceRequest & { id: string; version: string }>({
        id: "",
        version: "",
        title: "",
        content: "",
        content_html: "",
        summary: "",
    })

    // Activate state
    const [activatingId, setActivatingId] = useState<string | null>(null)

    const { addToast } = useToast()

    const fetchTermsOfService = useCallback(async () => {
        try {
            const response = await adminApi.getTermsOfServiceList({
                page,
                page_size: 20,
                status: statusFilter !== "all" ? statusFilter : undefined,
            })
            setData(response)
        } catch (error) {
            console.error("Failed to fetch terms of service:", error)
            addToast({
                type: "error",
                title: "Failed to load terms of service",
                description: "Please try again later",
            })
        } finally {
            setIsLoading(false)
        }
    }, [page, statusFilter, addToast])

    useEffect(() => {
        fetchTermsOfService()
    }, [fetchTermsOfService])

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await fetchTermsOfService()
        setIsRefreshing(false)
    }

    const handleCreate = async () => {
        if (!newTerms.version || !newTerms.title || !newTerms.content) {
            addToast({
                type: "error",
                title: "Validation Error",
                description: "Version, title, and content are required",
            })
            return
        }

        setIsCreating(true)
        try {
            await adminApi.createTermsOfService(newTerms)
            addToast({
                type: "success",
                title: "Terms of Service Created",
                description: `Version ${newTerms.version} has been created as a draft`,
            })
            setCreateDialogOpen(false)
            setNewTerms({ version: "", title: "", content: "", content_html: "", summary: "" })
            fetchTermsOfService()
        } catch (error) {
            console.error("Failed to create terms of service:", error)
            addToast({
                type: "error",
                title: "Failed to create terms of service",
                description: "Please try again later",
            })
        } finally {
            setIsCreating(false)
        }
    }

    const handleActivate = async (termsId: string, version: string) => {
        setActivatingId(termsId)
        try {
            await adminApi.activateTermsOfService(termsId)
            addToast({
                type: "success",
                title: "Terms of Service Activated",
                description: `Version ${version} is now active. Users will be required to accept on next login.`,
            })
            fetchTermsOfService()
        } catch (error) {
            console.error("Failed to activate terms of service:", error)
            addToast({
                type: "error",
                title: "Failed to activate",
                description: "Please try again later",
            })
        } finally {
            setActivatingId(null)
        }
    }

    const openPreview = (terms: TermsOfService) => {
        setSelectedTerms(terms)
        setPreviewDialogOpen(true)
    }

    const openEdit = (terms: TermsOfService) => {
        setEditTerms({
            id: terms.id,
            version: terms.version,
            title: terms.title,
            content: terms.content_html || terms.content,
            content_html: terms.content_html || terms.content,
            summary: terms.summary || "",
            effective_date: terms.effective_date ? terms.effective_date.split("T")[0] : "",
        })
        setEditDialogOpen(true)
    }

    const handleEdit = async () => {
        if (!editTerms.title || !editTerms.content) {
            addToast({
                type: "error",
                title: "Validation Error",
                description: "Title and content are required",
            })
            return
        }

        setIsEditing(true)
        try {
            await adminApi.updateTermsOfService(editTerms.id, {
                title: editTerms.title,
                content: editTerms.content,
                content_html: editTerms.content_html,
                summary: editTerms.summary || undefined,
                effective_date: editTerms.effective_date || undefined,
            })
            addToast({
                type: "success",
                title: "Terms of Service Updated",
                description: `Version ${editTerms.version} has been updated`,
            })
            setEditDialogOpen(false)
            fetchTermsOfService()
        } catch (error) {
            console.error("Failed to update terms of service:", error)
            addToast({
                type: "error",
                title: "Failed to update",
                description: "Please try again later",
            })
        } finally {
            setIsEditing(false)
        }
    }

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Compliance", href: "/admin/compliance/requests" },
                { label: "Terms of Service" },
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
                                <FileText className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                    Terms of Service
                                </h1>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    Manage terms of service versions
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
                            New Version
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
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Version History</CardTitle>
                                    <CardDescription>
                                        All terms of service versions with their status
                                    </CardDescription>
                                </div>
                                <Select value={statusFilter} onValueChange={setStatusFilter}>
                                    <SelectTrigger className="w-40">
                                        <SelectValue placeholder="All Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="draft">Draft</SelectItem>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="archived">Archived</SelectItem>
                                    </SelectContent>
                                </Select>
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
                                                <TableHead>Version</TableHead>
                                                <TableHead>Title</TableHead>
                                                <TableHead>Status</TableHead>
                                                <TableHead>Effective Date</TableHead>
                                                <TableHead>Created</TableHead>
                                                <TableHead className="text-right">Actions</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.items.map((terms) => (
                                                <TableRow key={terms.id}>
                                                    <TableCell className="font-mono font-medium">
                                                        {terms.version}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div>
                                                            <p className="font-medium">{terms.title}</p>
                                                            {terms.summary && (
                                                                <p className="text-sm text-slate-500 truncate max-w-xs">
                                                                    {terms.summary}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>{getStatusBadge(terms.status)}</TableCell>
                                                    <TableCell className="text-sm">
                                                        {terms.effective_date
                                                            ? new Date(terms.effective_date).toLocaleDateString()
                                                            : "-"
                                                        }
                                                    </TableCell>
                                                    <TableCell className="text-sm">
                                                        {formatTimestamp(terms.created_at)}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <div className="flex justify-end gap-2">
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => openPreview(terms)}
                                                            >
                                                                <Eye className="h-4 w-4 mr-1" />
                                                                Preview
                                                            </Button>
                                                            {terms.status === "draft" && (
                                                                <>
                                                                    <Button
                                                                        size="sm"
                                                                        variant="outline"
                                                                        onClick={() => openEdit(terms)}
                                                                    >
                                                                        <Pencil className="h-4 w-4 mr-1" />
                                                                        Edit
                                                                    </Button>
                                                                    <Button
                                                                        size="sm"
                                                                        onClick={() => handleActivate(terms.id, terms.version)}
                                                                        disabled={activatingId === terms.id}
                                                                    >
                                                                        {activatingId === terms.id ? (
                                                                            <Loader2 className="h-4 w-4 animate-spin" />
                                                                        ) : (
                                                                            <>
                                                                                <Power className="h-4 w-4 mr-1" />
                                                                                Activate
                                                                            </>
                                                                        )}
                                                                    </Button>
                                                                </>
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
                                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>No terms of service versions found</p>
                                    <Button
                                        className="mt-4"
                                        onClick={() => setCreateDialogOpen(true)}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Create First Version
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Create Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Create New Terms of Service Version</DialogTitle>
                        <DialogDescription>
                            Create a new version of the terms of service. It will be saved as a draft until activated.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="version">Version *</Label>
                                <Input
                                    id="version"
                                    placeholder="e.g., 1.0.0"
                                    value={newTerms.version}
                                    onChange={(e) => setNewTerms({ ...newTerms, version: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="effective_date">Effective Date</Label>
                                <Input
                                    id="effective_date"
                                    type="date"
                                    value={newTerms.effective_date || ""}
                                    onChange={(e) => setNewTerms({ ...newTerms, effective_date: e.target.value })}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="title">Title *</Label>
                            <Input
                                id="title"
                                placeholder="Terms of Service"
                                value={newTerms.title}
                                onChange={(e) => setNewTerms({ ...newTerms, title: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="summary">Summary</Label>
                            <Input
                                id="summary"
                                placeholder="Brief summary of changes in this version"
                                value={newTerms.summary || ""}
                                onChange={(e) => setNewTerms({ ...newTerms, summary: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Content *</Label>
                            <RichTextEditor
                                content={newTerms.content}
                                onChange={(html) => setNewTerms({ ...newTerms, content: html, content_html: html })}
                                placeholder="Enter the full terms of service content..."
                                minHeight="250px"
                            />
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
                                    Creating...
                                </>
                            ) : (
                                "Create Draft"
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Preview Dialog */}
            <Dialog open={previewDialogOpen} onOpenChange={setPreviewDialogOpen}>
                <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            {selectedTerms?.title}
                        </DialogTitle>
                        <DialogDescription className="flex items-center gap-2">
                            Version {selectedTerms?.version}
                            {selectedTerms && getStatusBadge(selectedTerms.status)}
                        </DialogDescription>
                    </DialogHeader>
                    {selectedTerms && (
                        <div className="py-4">
                            {selectedTerms.summary && (
                                <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Summary</p>
                                    <p className="text-sm">{selectedTerms.summary}</p>
                                </div>
                            )}
                            <RichTextViewer content={selectedTerms.content_html || selectedTerms.content} />
                            <div className="mt-4 pt-4 border-t text-sm text-slate-500">
                                <p>Created: {formatTimestamp(selectedTerms.created_at)}</p>
                                {selectedTerms.activated_at && (
                                    <p>Activated: {formatTimestamp(selectedTerms.activated_at)}</p>
                                )}
                                {selectedTerms.effective_date && (
                                    <p>Effective: {new Date(selectedTerms.effective_date).toLocaleDateString()}</p>
                                )}
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setPreviewDialogOpen(false)}>
                            Close
                        </Button>
                        {selectedTerms?.status === "draft" && (
                            <Button
                                onClick={() => {
                                    handleActivate(selectedTerms.id, selectedTerms.version)
                                    setPreviewDialogOpen(false)
                                }}
                                disabled={activatingId === selectedTerms?.id}
                            >
                                {activatingId === selectedTerms?.id ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <>
                                        <Power className="h-4 w-4 mr-1" />
                                        Activate This Version
                                    </>
                                )}
                            </Button>
                        )}
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Edit Dialog */}
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Edit Terms of Service - Version {editTerms.version}</DialogTitle>
                        <DialogDescription>
                            Update the draft terms of service. Only draft versions can be edited.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="edit_version">Version</Label>
                                <Input
                                    id="edit_version"
                                    value={editTerms.version}
                                    disabled
                                    className="bg-slate-100 dark:bg-slate-800"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="edit_effective_date">Effective Date</Label>
                                <Input
                                    id="edit_effective_date"
                                    type="date"
                                    value={editTerms.effective_date || ""}
                                    onChange={(e) => setEditTerms({ ...editTerms, effective_date: e.target.value })}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="edit_title">Title *</Label>
                            <Input
                                id="edit_title"
                                placeholder="Terms of Service"
                                value={editTerms.title}
                                onChange={(e) => setEditTerms({ ...editTerms, title: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="edit_summary">Summary</Label>
                            <Input
                                id="edit_summary"
                                placeholder="Brief summary of changes in this version"
                                value={editTerms.summary || ""}
                                onChange={(e) => setEditTerms({ ...editTerms, summary: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Content *</Label>
                            <RichTextEditor
                                content={editTerms.content || ""}
                                onChange={(html) => setEditTerms({ ...editTerms, content: html, content_html: html })}
                                placeholder="Enter the full terms of service content..."
                                minHeight="250px"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setEditDialogOpen(false)}
                            disabled={isEditing}
                        >
                            Cancel
                        </Button>
                        <Button onClick={handleEdit} disabled={isEditing}>
                            {isEditing ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                "Save Changes"
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
