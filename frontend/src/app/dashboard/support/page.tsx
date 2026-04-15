"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
    Ticket,
    Plus,
    RefreshCcw,
    Clock,
    MessageSquare,
    AlertCircle,
    CheckCircle2,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Filter,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
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
    DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { supportApi } from "@/lib/api/support"
import type { SupportTicket, TicketStats } from "@/lib/api/support"
import { useToast } from "@/hooks/use-toast"

const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    open: { label: "Open", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: AlertCircle },
    in_progress: { label: "In Progress", color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: Clock },
    waiting_user: { label: "Waiting Reply", color: "bg-purple-500/10 text-purple-500 border-purple-500/20", icon: MessageSquare },
    resolved: { label: "Resolved", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: CheckCircle2 },
    closed: { label: "Closed", color: "bg-gray-500/10 text-gray-500 border-gray-500/20", icon: CheckCircle2 },
}

const priorityConfig: Record<string, { label: string; color: string }> = {
    low: { label: "Low", color: "bg-gray-500/10 text-gray-500" },
    medium: { label: "Medium", color: "bg-blue-500/10 text-blue-500" },
    high: { label: "High", color: "bg-amber-500/10 text-amber-500" },
    urgent: { label: "Urgent", color: "bg-red-500/10 text-red-500" },
}

const categoryOptions = [
    { value: "technical", label: "Technical Issue" },
    { value: "billing", label: "Billing & Payment" },
    { value: "account", label: "Account" },
    { value: "feature", label: "Feature Request" },
    { value: "other", label: "Other" },
]

export default function SupportPage() {
    const { addToast } = useToast()
    const [tickets, setTickets] = useState<SupportTicket[]>([])
    const [stats, setStats] = useState<TicketStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal] = useState(0)
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [newTicket, setNewTicket] = useState({ subject: "", description: "", category: "", priority: "medium" })

    useEffect(() => {
        loadTickets()
        loadStats()
    }, [page, statusFilter])

    const loadTickets = async () => {
        try {
            setLoading(true)
            const params: Record<string, string | number | boolean | undefined> = { page, page_size: 10 }
            if (statusFilter && statusFilter !== "all") {
                params.status = statusFilter
            }
            const data = await supportApi.getTickets(params)
            setTickets(data.items || [])
            setTotal(data.total || 0)
            setTotalPages(data.total_pages || 1)
        } catch (error) {
            console.error("Failed to fetch tickets:", error)
            setTickets([])
        } finally {
            setLoading(false)
        }
    }

    const loadStats = async () => {
        try {
            const data = await supportApi.getStats()
            setStats(data)
        } catch (error) {
            console.error("Failed to fetch stats:", error)
        }
    }

    const handleCreateTicket = async () => {
        // Validation
        if (!newTicket.subject || newTicket.subject.length < 5) {
            addToast({ type: "error", title: "Validation Error", description: "Subject must be at least 5 characters long." })
            return
        }
        if (!newTicket.description || newTicket.description.length < 10) {
            addToast({ type: "error", title: "Validation Error", description: "Description must be at least 10 characters long." })
            return
        }

        setIsSubmitting(true)
        try {
            await supportApi.createTicket({
                subject: newTicket.subject,
                description: newTicket.description,
                category: newTicket.category || undefined,
                priority: newTicket.priority as "low" | "medium" | "high" | "urgent"
            })
            setIsDialogOpen(false)
            setNewTicket({ subject: "", description: "", category: "", priority: "medium" })
            loadTickets()
            loadStats()
            addToast({ type: "success", title: "Ticket Created", description: "Your support ticket has been submitted." })
        } catch (error: any) {
            console.error("Failed to create ticket:", error)

            // Handle validation errors from backend
            if (error?.response?.data?.detail) {
                const details = error.response.data.detail
                if (Array.isArray(details)) {
                    const errorMsg = details.map((d: any) => d.msg).join(", ")
                    addToast({ type: "error", title: "Validation Error", description: errorMsg })
                } else {
                    addToast({ type: "error", title: "Error", description: details })
                }
            } else {
                addToast({ type: "error", title: "Error", description: "Failed to create ticket. Please try again." })
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleRefresh = () => {
        loadTickets()
        loadStats()
    }

    const getRelativeTime = (dateString: string) => {
        const diffMs = Date.now() - new Date(dateString).getTime()
        const mins = Math.floor(diffMs / 60000)
        const hrs = Math.floor(diffMs / 3600000)
        const days = Math.floor(diffMs / 86400000)
        if (mins < 60) return `${mins}m ago`
        if (hrs < 24) return `${hrs}h ago`
        if (days < 7) return `${days}d ago`
        return new Date(dateString).toLocaleDateString()
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">Support</h1>
                        <p className="text-muted-foreground">Get help from our support team</p>
                    </div>
                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button><Plus className="mr-2 h-4 w-4" />New Ticket</Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[500px]">
                            <DialogHeader>
                                <DialogTitle>Create Support Ticket</DialogTitle>
                                <DialogDescription>Describe your issue and we will get back to you.</DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                    <Label>Subject <span className="text-xs text-muted-foreground">({newTicket.subject.length}/5 min)</span></Label>
                                    <Input
                                        placeholder="Brief description (min 5 characters)"
                                        value={newTicket.subject}
                                        onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                                        className={newTicket.subject.length > 0 && newTicket.subject.length < 5 ? "border-red-500" : ""}
                                    />
                                    {newTicket.subject.length > 0 && newTicket.subject.length < 5 && (
                                        <p className="text-xs text-red-500">Subject must be at least 5 characters</p>
                                    )}
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Category</Label>
                                        <Select value={newTicket.category} onValueChange={(v) => setNewTicket({ ...newTicket, category: v })}>
                                            <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                                            <SelectContent>
                                                {categoryOptions.map((c) => (<SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Priority</Label>
                                        <Select value={newTicket.priority} onValueChange={(v) => setNewTicket({ ...newTicket, priority: v })}>
                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="low">Low</SelectItem>
                                                <SelectItem value="medium">Medium</SelectItem>
                                                <SelectItem value="high">High</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>Description <span className="text-xs text-muted-foreground">({newTicket.description.length}/10 min)</span></Label>
                                    <Textarea
                                        placeholder="Provide details about your issue (min 10 characters)..."
                                        rows={5}
                                        value={newTicket.description}
                                        onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                                        className={newTicket.description.length > 0 && newTicket.description.length < 10 ? "border-red-500" : ""}
                                    />
                                    {newTicket.description.length > 0 && newTicket.description.length < 10 && (
                                        <p className="text-xs text-red-500">Description must be at least 10 characters</p>
                                    )}
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                                <Button
                                    onClick={handleCreateTicket}
                                    disabled={isSubmitting || newTicket.subject.length < 5 || newTicket.description.length < 10}
                                >
                                    {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Create
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total</CardTitle>
                            <Ticket className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent><div className="text-2xl font-bold">{stats?.total ?? 0}</div></CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Open</CardTitle>
                            <AlertCircle className="h-4 w-4 text-blue-500" />
                        </CardHeader>
                        <CardContent><div className="text-2xl font-bold text-blue-500">{stats?.open ?? 0}</div></CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
                            <Clock className="h-4 w-4 text-amber-500" />
                        </CardHeader>
                        <CardContent><div className="text-2xl font-bold text-amber-500">{stats?.in_progress ?? 0}</div></CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        </CardHeader>
                        <CardContent><div className="text-2xl font-bold text-emerald-500">{stats?.resolved ?? 0}</div></CardContent>
                    </Card>
                </div>

                <div className="flex items-center gap-4">
                    <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
                        <SelectTrigger className="w-[180px]"><Filter className="mr-2 h-4 w-4" /><SelectValue placeholder="Filter" /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All</SelectItem>
                            <SelectItem value="open">Open</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="waiting_user">Waiting</SelectItem>
                            <SelectItem value="resolved">Resolved</SelectItem>
                            <SelectItem value="closed">Closed</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="outline" size="icon" onClick={handleRefresh}><RefreshCcw className="h-4 w-4" /></Button>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Your Tickets</CardTitle>
                        <CardDescription>{total} ticket{total !== 1 ? "s" : ""}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="space-y-4">{[...Array(3)].map((_, i) => (<Skeleton key={i} className="h-24 w-full" />))}</div>
                        ) : tickets.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <Ticket className="h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-medium">No tickets yet</h3>
                                <p className="text-muted-foreground mt-1">Create a ticket to get help</p>
                                <Button className="mt-4" onClick={() => setIsDialogOpen(true)}><Plus className="mr-2 h-4 w-4" />Create Ticket</Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {tickets.map((ticket) => {
                                    const st = statusConfig[ticket.status] || statusConfig.open
                                    const pr = priorityConfig[ticket.priority] || priorityConfig.medium
                                    const Icon = st.icon
                                    return (
                                        <Link key={ticket.id} href={`/dashboard/support/${ticket.id}`}>
                                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer">
                                                <div className="flex items-start gap-4">
                                                    <div className={cn("p-2 rounded-full", st.color)}><Icon className="h-4 w-4" /></div>
                                                    <div>
                                                        <h4 className="font-medium">{ticket.subject}</h4>
                                                        <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                                                            {ticket.category && <span className="capitalize">{ticket.category}</span>}
                                                            <span>•</span>
                                                            <span>{getRelativeTime(ticket.created_at)}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="flex items-center gap-1 text-muted-foreground"><MessageSquare className="h-4 w-4" /><span className="text-sm">{ticket.message_count}</span></div>
                                                    <Badge variant="outline" className={pr.color}>{pr.label}</Badge>
                                                    <Badge variant="outline" className={st.color}>{st.label}</Badge>
                                                </div>
                                            </motion.div>
                                        </Link>
                                    )
                                })}
                            </div>
                        )}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-between mt-6">
                                <p className="text-sm text-muted-foreground">Page {page} of {totalPages}</p>
                                <div className="flex items-center gap-2">
                                    <Button variant="outline" size="sm" onClick={() => setPage(page - 1)} disabled={page === 1}><ChevronLeft className="h-4 w-4" /></Button>
                                    <Button variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={page === totalPages}><ChevronRight className="h-4 w-4" /></Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
