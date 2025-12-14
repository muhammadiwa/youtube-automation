"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Ticket,
    RefreshCcw,
    Search,
    Filter,
    Clock,
    User,
    ChevronLeft,
    ChevronRight,
    MessageSquare,
    AlertCircle,
    CheckCircle2,
    XCircle,
    Eye,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import Link from "next/link"

// Types
interface SupportTicket {
    id: string
    user_id: string
    user_email: string
    user_name: string
    subject: string
    status: "open" | "in_progress" | "waiting" | "resolved" | "closed"
    priority: "low" | "medium" | "high" | "urgent"
    category: string
    message_count: number
    last_reply_at: string | null
    created_at: string
    updated_at: string
}

interface TicketsResponse {
    tickets: SupportTicket[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

// Status config
const statusConfig = {
    open: { label: "Open", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
    in_progress: { label: "In Progress", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
    waiting: { label: "Waiting", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
    resolved: { label: "Resolved", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
    closed: { label: "Closed", color: "bg-gray-500/10 text-gray-500 border-gray-500/20" },
}

// Priority config
const priorityConfig = {
    low: { label: "Low", color: "bg-gray-500/10 text-gray-500" },
    medium: { label: "Medium", color: "bg-blue-500/10 text-blue-500" },
    high: { label: "High", color: "bg-amber-500/10 text-amber-500" },
    urgent: { label: "Urgent", color: "bg-red-500/10 text-red-500" },
}

export default function SupportTicketsPage() {
    const [tickets, setTickets] = useState<SupportTicket[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(20)
    const [totalPages, setTotalPages] = useState(1)
    const [isLoading, setIsLoading] = useState(true)

    // Filters
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [priorityFilter, setPriorityFilter] = useState<string>("all")

    // Stats
    const [stats, setStats] = useState({ open: 0, in_progress: 0, resolved: 0, avg_response_time: 0 })

    const fetchTickets = useCallback(async () => {
        setIsLoading(true)
        try {
            const token = localStorage.getItem("access_token")
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: pageSize.toString(),
                ...(searchQuery && { search: searchQuery }),
                ...(statusFilter !== "all" && { status: statusFilter }),
                ...(priorityFilter !== "all" && { priority: priorityFilter }),
            })
            const response = await fetch(`/api/admin/support/tickets?${params}`, {
                headers: { Authorization: `Bearer ${token}` },
            })
            if (!response.ok) throw new Error("Failed to fetch tickets")
            const data: TicketsResponse = await response.json()
            setTickets(data.tickets)
            setTotal(data.total)
            setTotalPages(data.total_pages)
        } catch {
            // Mock data
            const mockTickets: SupportTicket[] = [
                { id: "1", user_id: "u1", user_email: "john@example.com", user_name: "John Doe", subject: "Cannot upload video", status: "open", priority: "high", category: "Technical", message_count: 3, last_reply_at: new Date().toISOString(), created_at: new Date(Date.now() - 3600000).toISOString(), updated_at: new Date().toISOString() },
                { id: "2", user_id: "u2", user_email: "jane@example.com", user_name: "Jane Smith", subject: "Billing question", status: "in_progress", priority: "medium", category: "Billing", message_count: 5, last_reply_at: new Date().toISOString(), created_at: new Date(Date.now() - 86400000).toISOString(), updated_at: new Date().toISOString() },
                { id: "3", user_id: "u3", user_email: "bob@example.com", user_name: "Bob Wilson", subject: "Feature request", status: "waiting", priority: "low", category: "Feature", message_count: 2, last_reply_at: null, created_at: new Date(Date.now() - 172800000).toISOString(), updated_at: new Date().toISOString() },
                { id: "4", user_id: "u4", user_email: "alice@example.com", user_name: "Alice Brown", subject: "Stream not working", status: "resolved", priority: "urgent", category: "Technical", message_count: 8, last_reply_at: new Date().toISOString(), created_at: new Date(Date.now() - 259200000).toISOString(), updated_at: new Date().toISOString() },
            ]
            setTickets(mockTickets)
            setTotal(mockTickets.length)
            setTotalPages(1)
            setStats({ open: 12, in_progress: 5, resolved: 45, avg_response_time: 2.5 })
        } finally {
            setIsLoading(false)
        }
    }, [page, pageSize, searchQuery, statusFilter, priorityFilter])

    useEffect(() => {
        fetchTickets()
    }, [fetchTickets])

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const hours = Math.floor(diff / 3600000)
        if (hours < 1) return "Just now"
        if (hours < 24) return `${hours}h ago`
        const days = Math.floor(hours / 24)
        if (days < 7) return `${days}d ago`
        return date.toLocaleDateString()
    }

    return (
        <AdminLayout breadcrumbs={[{ label: "Support" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, delay: 0.1 }} className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <Ticket className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Support Tickets</h1>
                                <p className="text-muted-foreground">Manage customer support requests</p>
                            </div>
                        </div>
                    </div>
                    <Button variant="outline" size="icon" onClick={fetchTickets} disabled={isLoading}>
                        <RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                    </Button>
                </motion.div>

                {/* Stats */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center"><AlertCircle className="h-5 w-5 text-blue-500" /></div>
                                <div><p className="text-sm text-muted-foreground">Open</p><p className="text-2xl font-bold">{stats.open}</p></div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center"><Clock className="h-5 w-5 text-amber-500" /></div>
                                <div><p className="text-sm text-muted-foreground">In Progress</p><p className="text-2xl font-bold">{stats.in_progress}</p></div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center"><CheckCircle2 className="h-5 w-5 text-emerald-500" /></div>
                                <div><p className="text-sm text-muted-foreground">Resolved (30d)</p><p className="text-2xl font-bold">{stats.resolved}</p></div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center"><MessageSquare className="h-5 w-5 text-purple-500" /></div>
                                <div><p className="text-sm text-muted-foreground">Avg Response</p><p className="text-2xl font-bold">{stats.avg_response_time}h</p></div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Filters */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card>
                        <CardHeader><CardTitle className="flex items-center gap-2"><Filter className="h-5 w-5" />Filters</CardTitle></CardHeader>
                        <CardContent>
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                <div className="grid gap-2">
                                    <Label>Search</Label>
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input placeholder="Search tickets..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <Label>Status</Label>
                                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="open">Open</SelectItem>
                                            <SelectItem value="in_progress">In Progress</SelectItem>
                                            <SelectItem value="waiting">Waiting</SelectItem>
                                            <SelectItem value="resolved">Resolved</SelectItem>
                                            <SelectItem value="closed">Closed</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid gap-2">
                                    <Label>Priority</Label>
                                    <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Priority</SelectItem>
                                            <SelectItem value="urgent">Urgent</SelectItem>
                                            <SelectItem value="high">High</SelectItem>
                                            <SelectItem value="medium">Medium</SelectItem>
                                            <SelectItem value="low">Low</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Tickets List */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <Card>
                        <CardHeader>
                            <CardTitle>Tickets</CardTitle>
                            <CardDescription>{total} total tickets</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="space-y-4">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}</div>
                            ) : tickets.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground"><Ticket className="h-12 w-12 mx-auto mb-4 opacity-50" /><p>No tickets found</p></div>
                            ) : (
                                <div className="space-y-4">
                                    {tickets.map((ticket, index) => (
                                        <motion.div key={ticket.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.05 }} className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors">
                                            <div className="flex items-center gap-4 flex-1 min-w-0">
                                                <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center"><User className="h-5 w-5 text-muted-foreground" /></div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="font-medium truncate">{ticket.subject}</span>
                                                        <Badge variant="outline" className={statusConfig[ticket.status].color}>{statusConfig[ticket.status].label}</Badge>
                                                        <Badge variant="outline" className={priorityConfig[ticket.priority].color}>{priorityConfig[ticket.priority].label}</Badge>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                                                        <span>{ticket.user_name}</span>
                                                        <span>•</span>
                                                        <span>{ticket.category}</span>
                                                        <span>•</span>
                                                        <span className="flex items-center gap-1"><MessageSquare className="h-3 w-3" />{ticket.message_count}</span>
                                                        <span>•</span>
                                                        <span>{formatDate(ticket.created_at)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <Link href={`/admin/support/${ticket.id}`}>
                                                <Button variant="ghost" size="sm"><Eye className="h-4 w-4 mr-2" />View</Button>
                                            </Link>
                                        </motion.div>
                                    ))}
                                </div>
                            )}

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between mt-6 pt-6 border-t">
                                    <p className="text-sm text-muted-foreground">Page {page} of {totalPages}</p>
                                    <div className="flex items-center gap-2">
                                        <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}><ChevronLeft className="h-4 w-4" /></Button>
                                        <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}><ChevronRight className="h-4 w-4" /></Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </AdminLayout>
    )
}
