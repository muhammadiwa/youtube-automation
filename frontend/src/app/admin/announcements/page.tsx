"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Megaphone,
    Plus,
    RefreshCcw,
    Search,
    MoreHorizontal,
    Pencil,
    Trash2,
    Eye,
    EyeOff,
    Calendar,
    CheckCircle2,
    AlertCircle,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
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
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import adminApi, { type Announcement } from "@/lib/api/admin"

const typeConfig = {
    info: { label: "Info", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: AlertCircle },
    warning: { label: "Warning", color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: AlertCircle },
    success: { label: "Success", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: CheckCircle2 },
    error: { label: "Error", color: "bg-red-500/10 text-red-500 border-red-500/20", icon: AlertCircle },
}

export default function AnnouncementsPage() {
    const { addToast } = useToast()

    const [announcements, setAnnouncements] = useState<Announcement[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")

    // Form state
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null)
    const [formTitle, setFormTitle] = useState("")
    const [formContent, setFormContent] = useState("")
    const [formType, setFormType] = useState<"info" | "warning" | "success" | "error">("info")
    const [formIsDismissible, setFormIsDismissible] = useState(true)
    const [formHasDateRange, setFormHasDateRange] = useState(false)
    const [formStartDate, setFormStartDate] = useState("")
    const [formEndDate, setFormEndDate] = useState("")
    const [isSaving, setIsSaving] = useState(false)

    // Delete state
    const [deleteAnnouncementItem, setDeleteAnnouncementItem] = useState<Announcement | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)

    // Preview state
    const [previewAnnouncement, setPreviewAnnouncement] = useState<Announcement | null>(null)

    const fetchAnnouncements = useCallback(async () => {
        setIsLoading(true)
        try {
            const data = await adminApi.getAnnouncements({
                page,
                page_size: 20,
                active_only: statusFilter === "active",
            })
            setAnnouncements(data.items)
            setTotal(data.total)
            setTotalPages(data.total_pages)
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to load announcements"
            addToast({ type: "error", title: "Error", description: message })
            setAnnouncements([])
            setTotal(0)
            setTotalPages(1)
        } finally {
            setIsLoading(false)
        }
    }, [page, statusFilter, addToast])

    useEffect(() => {
        fetchAnnouncements()
    }, [fetchAnnouncements])

    const resetForm = () => {
        setFormTitle("")
        setFormContent("")
        setFormType("info")
        setFormIsDismissible(true)
        setFormHasDateRange(false)
        setFormStartDate("")
        setFormEndDate("")
        setEditingAnnouncement(null)
    }

    const openCreateForm = () => {
        resetForm()
        setFormStartDate(new Date().toISOString().split("T")[0])
        setIsFormOpen(true)
    }

    const openEditForm = (announcement: Announcement) => {
        setEditingAnnouncement(announcement)
        setFormTitle(announcement.title)
        setFormContent(announcement.content)
        setFormType(announcement.announcement_type)
        setFormIsDismissible(announcement.is_dismissible)
        setFormHasDateRange(!!(announcement.start_date || announcement.end_date))
        setFormStartDate(announcement.start_date?.split("T")[0] || "")
        setFormEndDate(announcement.end_date?.split("T")[0] || "")
        setIsFormOpen(true)
    }

    const handleSave = async () => {
        if (!formTitle.trim() || !formContent.trim()) return
        setIsSaving(true)
        try {
            const payload = {
                title: formTitle,
                content: formContent,
                announcement_type: formType,
                is_dismissible: formIsDismissible,
                start_date: formStartDate ? `${formStartDate}T00:00:00` : new Date().toISOString(),
                end_date: formHasDateRange && formEndDate ? `${formEndDate}T23:59:59` : null,
            }
            if (editingAnnouncement) {
                await adminApi.updateAnnouncement(editingAnnouncement.id, payload)
            } else {
                await adminApi.createAnnouncement(payload)
            }
            addToast({ type: "success", title: editingAnnouncement ? "Announcement updated" : "Announcement created", description: "Your changes have been saved." })
            setIsFormOpen(false)
            resetForm()
            fetchAnnouncements()
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to save announcement. Please try again." })
        } finally {
            setIsSaving(false)
        }
    }

    const handleToggleActive = async (announcement: Announcement) => {
        try {
            await adminApi.updateAnnouncement(announcement.id, { is_active: !announcement.is_active })
            fetchAnnouncements()
            addToast({ type: "success", title: announcement.is_active ? "Announcement hidden" : "Announcement activated", description: announcement.is_active ? "The announcement is now hidden from users." : "The announcement is now visible to users." })
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to update announcement status." })
        }
    }

    const handleDelete = async () => {
        if (!deleteAnnouncementItem) return
        setIsDeleting(true)
        try {
            await adminApi.deleteAnnouncement(deleteAnnouncementItem.id)
            addToast({ type: "success", title: "Announcement deleted", description: "The announcement has been removed." })
            setDeleteAnnouncementItem(null)
            fetchAnnouncements()
        } catch {
            addToast({ type: "error", title: "Error", description: "Failed to delete announcement." })
        } finally {
            setIsDeleting(false)
        }
    }

    const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString()

    const filteredAnnouncements = announcements.filter(a => {
        if (searchQuery && !a.title.toLowerCase().includes(searchQuery.toLowerCase()) && !a.content.toLowerCase().includes(searchQuery.toLowerCase())) return false
        if (statusFilter === "active" && !a.is_active) return false
        if (statusFilter === "inactive" && a.is_active) return false
        return true
    })

    return (
        <AdminLayout breadcrumbs={[{ label: "Announcements" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, delay: 0.1 }} className="h-12 w-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/25">
                                <Megaphone className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">Announcements</h1>
                                <p className="text-muted-foreground">Manage platform-wide announcements and banners</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="icon" onClick={fetchAnnouncements} disabled={isLoading}><RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} /></Button>
                        <Button onClick={openCreateForm}><Plus className="h-4 w-4 mr-2" />Create Announcement</Button>
                    </div>
                </motion.div>

                {/* Filters */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex flex-col sm:flex-row gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input placeholder="Search announcements..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                                </div>
                                <Select value={statusFilter} onValueChange={setStatusFilter}>
                                    <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="inactive">Inactive</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Announcements List */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card>
                        <CardHeader>
                            <CardTitle>All Announcements</CardTitle>
                            <CardDescription>{total} announcements</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-12">
                                    <div className="h-12 w-12 rounded-full border-4 border-amber-500/20 border-t-amber-500 animate-spin" />
                                    <p className="mt-4 text-muted-foreground">Loading announcements...</p>
                                </div>
                            ) : filteredAnnouncements.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Megaphone className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>No announcements found</p>
                                    <Button onClick={openCreateForm} className="mt-4"><Plus className="h-4 w-4 mr-2" />Create First Announcement</Button>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {filteredAnnouncements.map((announcement, index) => {
                                        const TypeIcon = typeConfig[announcement.announcement_type].icon
                                        return (
                                            <motion.div key={announcement.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.05 }} className={cn("p-4 rounded-lg border transition-colors", announcement.is_active ? "hover:bg-muted/50" : "opacity-60 bg-muted/30")}>
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="flex items-start gap-3 flex-1 min-w-0">
                                                        <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center shrink-0", typeConfig[announcement.announcement_type].color.split(" ")[0])}>
                                                            <TypeIcon className={cn("h-5 w-5", typeConfig[announcement.announcement_type].color.split(" ")[1])} />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 flex-wrap">
                                                                <span className="font-medium">{announcement.title}</span>
                                                                <Badge variant="outline" className={typeConfig[announcement.announcement_type].color}>{typeConfig[announcement.announcement_type].label}</Badge>
                                                                {announcement.is_active ? (
                                                                    <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20"><Eye className="h-3 w-3 mr-1" />Active</Badge>
                                                                ) : (
                                                                    <Badge variant="outline" className="bg-gray-500/10 text-gray-500 border-gray-500/20"><EyeOff className="h-3 w-3 mr-1" />Hidden</Badge>
                                                                )}
                                                                {announcement.is_dismissible && <Badge variant="outline">Dismissible</Badge>}
                                                            </div>
                                                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{announcement.content}</p>
                                                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                                <span>Created: {formatDate(announcement.created_at)}</span>
                                                                {announcement.created_by_name && <span>By: {announcement.created_by_name}</span>}
                                                                {announcement.start_date && <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(announcement.start_date)} - {announcement.end_date ? formatDate(announcement.end_date) : "No end"}</span>}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuItem onClick={() => setPreviewAnnouncement(announcement)}><Eye className="h-4 w-4 mr-2" />Preview</DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => openEditForm(announcement)}><Pencil className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => handleToggleActive(announcement)}>
                                                                {announcement.is_active ? <><EyeOff className="h-4 w-4 mr-2" />Hide</> : <><Eye className="h-4 w-4 mr-2" />Activate</>}
                                                            </DropdownMenuItem>
                                                            <DropdownMenuSeparator />
                                                            <DropdownMenuItem onClick={() => setDeleteAnnouncementItem(announcement)} className="text-red-600"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </div>
                                            </motion.div>
                                        )
                                    })}
                                </div>
                            )}

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between mt-6 pt-6 border-t">
                                    <p className="text-sm text-muted-foreground">Page {page} of {totalPages}</p>
                                    <div className="flex items-center gap-2">
                                        <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</Button>
                                        <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Next</Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Create/Edit Dialog */}
            <Dialog open={isFormOpen} onOpenChange={(open) => { if (!open) resetForm(); setIsFormOpen(open); }}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>{editingAnnouncement ? "Edit Announcement" : "Create Announcement"}</DialogTitle>
                        <DialogDescription>
                            {editingAnnouncement ? "Update the announcement details below." : "Create a new announcement to display to users."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="grid gap-2">
                            <Label htmlFor="title">Title</Label>
                            <Input id="title" placeholder="Announcement title..." value={formTitle} onChange={(e) => setFormTitle(e.target.value)} />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="content">Content</Label>
                            <Textarea id="content" placeholder="Announcement content..." value={formContent} onChange={(e) => setFormContent(e.target.value)} rows={4} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Type</Label>
                            <Select value={formType} onValueChange={(v) => setFormType(v as typeof formType)}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="info">Info</SelectItem>
                                    <SelectItem value="warning">Warning</SelectItem>
                                    <SelectItem value="success">Success</SelectItem>
                                    <SelectItem value="error">Error</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <Label>Dismissible</Label>
                                <p className="text-sm text-muted-foreground">Allow users to dismiss this announcement</p>
                            </div>
                            <Switch checked={formIsDismissible} onCheckedChange={setFormIsDismissible} />
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Set End Date</Label>
                                    <p className="text-sm text-muted-foreground">Automatically hide after a specific date</p>
                                </div>
                                <Switch checked={formHasDateRange} onCheckedChange={setFormHasDateRange} />
                            </div>
                            {formHasDateRange && (
                                <div className="p-4 rounded-lg border bg-muted/30">
                                    <div className="grid gap-2">
                                        <Label htmlFor="endDate">End Date</Label>
                                        <Input id="endDate" type="date" value={formEndDate} onChange={(e) => setFormEndDate(e.target.value)} min={new Date().toISOString().split("T")[0]} />
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsFormOpen(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={!formTitle.trim() || !formContent.trim() || isSaving}>
                            {isSaving ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : null}
                            {isSaving ? "Saving..." : editingAnnouncement ? "Update" : "Create"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Preview Dialog */}
            <Dialog open={!!previewAnnouncement} onOpenChange={() => setPreviewAnnouncement(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Announcement Preview</DialogTitle>
                        <DialogDescription>This is how the announcement will appear to users.</DialogDescription>
                    </DialogHeader>
                    {previewAnnouncement && (
                        <div className={cn("p-4 rounded-lg border-l-4",
                            previewAnnouncement.announcement_type === "info" && "bg-blue-500/10 border-blue-500",
                            previewAnnouncement.announcement_type === "warning" && "bg-amber-500/10 border-amber-500",
                            previewAnnouncement.announcement_type === "success" && "bg-emerald-500/10 border-emerald-500",
                            previewAnnouncement.announcement_type === "error" && "bg-red-500/10 border-red-500"
                        )}>
                            <div className="flex items-start gap-3">
                                {(() => { const Icon = typeConfig[previewAnnouncement.announcement_type].icon; return <Icon className={cn("h-5 w-5 mt-0.5", typeConfig[previewAnnouncement.announcement_type].color.split(" ")[1])} />; })()}
                                <div className="flex-1">
                                    <p className="font-medium">{previewAnnouncement.title}</p>
                                    <p className="text-sm mt-1">{previewAnnouncement.content}</p>
                                </div>
                                {previewAnnouncement.is_dismissible && <Button variant="ghost" size="sm" className="shrink-0">Dismiss</Button>}
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button onClick={() => setPreviewAnnouncement(null)}>Close</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteAnnouncementItem} onOpenChange={() => setDeleteAnnouncementItem(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Announcement</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete &quot;{deleteAnnouncementItem?.title}&quot;? This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteAnnouncementItem(null)}>Cancel</Button>
                        <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? "Deleting..." : "Delete"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
