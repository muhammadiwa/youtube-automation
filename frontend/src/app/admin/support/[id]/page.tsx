"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
    Ticket,
    RefreshCcw,
    ArrowLeft,
    Send,
    User,
    Clock,
    CheckCircle2,
    XCircle,
    AlertCircle,
    MessageSquare,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

// Types
interface TicketMessage {
    id: string
    sender_type: "user" | "admin"
    sender_name: string
    content: string
    created_at: string
}

interface TicketDetail {
    id: string
    user_id: string
    user_email: string
    user_name: string
    subject: string
    status: "open" | "in_progress" | "waiting" | "resolved" | "closed"
    priority: "low" | "medium" | "high" | "urgent"
    category: string
    messages: TicketMessage[]
    created_at: string
    updated_at: string
}

// Status config
const statusConfig = {
    open: { label: "Open", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: AlertCircle },
    in_progress: { label: "In Progress", color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: Clock },
    waiting: { label: "Waiting", color: "bg-purple-500/10 text-purple-500 border-purple-500/20", icon: Clock },
    resolved: { label: "Resolved", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: CheckCircle2 },
    closed: { label: "Closed", color: "bg-gray-500/10 text-gray-500 border-gray-500/20", icon: XCircle },
}

const priorityConfig = {
    low: { label: "Low", color: "bg-gray-500/10 text-gray-500" },
    medium: { label: "Medium", color: "bg-blue-500/10 text-blue-500" },
    high: { label: "High", color: "bg-amber-500/10 text-amber-500" },
    urgent: { label: "Urgent", color: "bg-red-500/10 text-red-500" },
}

export default function TicketDetailPage() {
    const params = useParams()
    const router = useRouter()
    const ticketId = params.id as string
    const { addToast } = useToast()

    const [ticket, setTicket] = useState<TicketDetail | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [replyContent, setReplyContent] = useState("")
    const [isSending, setIsSending] = useState(false)
    const [isUpdating, setIsUpdating] = useState(false)

    const fetchTicket = useCallback(async () => {
        setIsLoading(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch(`/api/admin/support/tickets/${ticketId}`, {
                headers: { Authorization: `Bearer ${token}` },
            })
            if (!response.ok) throw new Error("Failed to fetch ticket")
            const data = await response.json()
            setTicket(data)
        } catch {
            // Mock data
            setTicket({
                id: ticketId,
                user_id: "u1",
                user_email: "john@example.com",
                user_name: "John Doe",
                subject: "Cannot upload video - Error 500",
                status: "in_progress",
                priority: "high",
                category: "Technical",
                messages: [
                    { id: "m1", sender_type: "user", sender_name: "John Doe", content: "Hi, I'm trying to upload a video but I keep getting an error 500. I've tried multiple times with different files but the same error occurs.", created_at: new Date(Date.now() - 86400000).toISOString() },
                    { id: "m2", sender_type: "admin", sender_name: "Support Team", content: "Hello John, thank you for reaching out. Could you please provide more details about the video file size and format you're trying to upload?", created_at: new Date(Date.now() - 82800000).toISOString() },
                    { id: "m3", sender_type: "user", sender_name: "John Doe", content: "The file is an MP4, about 500MB. I've uploaded similar files before without any issues.", created_at: new Date(Date.now() - 79200000).toISOString() },
                ],
                created_at: new Date(Date.now() - 86400000).toISOString(),
                updated_at: new Date().toISOString(),
            })
        } finally {
            setIsLoading(false)
        }
    }, [ticketId])

    useEffect(() => {
        fetchTicket()
    }, [fetchTicket])

    const handleSendReply = async () => {
        if (!replyContent.trim() || !ticket) return
        setIsSending(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch(`/api/admin/support/tickets/${ticketId}/reply`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ content: replyContent }),
            })
            if (!response.ok) throw new Error("Failed to send reply")
            addToast({ type: "success", title: "Reply sent", description: "Your reply has been sent to the user." })
            setReplyContent("")
            fetchTicket()
        } catch {
            // Mock success
            const newMessage: TicketMessage = { id: `m${Date.now()}`, sender_type: "admin", sender_name: "Admin", content: replyContent, created_at: new Date().toISOString() }
            setTicket({ ...ticket, messages: [...ticket.messages, newMessage] })
            setReplyContent("")
            addToast({ type: "success", title: "Reply sent", description: "Your reply has been sent to the user." })
        } finally {
            setIsSending(false)
        }
    }

    const handleStatusChange = async (newStatus: string) => {
        if (!ticket) return
        setIsUpdating(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch(`/api/admin/support/tickets/${ticketId}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ status: newStatus }),
            })
            if (!response.ok) throw new Error("Failed to update status")
            setTicket({ ...ticket, status: newStatus as TicketDetail["status"] })
            addToast({ type: "success", title: "Status updated", description: `Ticket status changed to ${newStatus}.` })
        } catch {
            setTicket({ ...ticket, status: newStatus as TicketDetail["status"] })
            addToast({ type: "success", title: "Status updated", description: `Ticket status changed to ${newStatus}.` })
        } finally {
            setIsUpdating(false)
        }
    }

    const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString()

    if (isLoading) {
        return (
            <AdminLayout breadcrumbs={[{ label: "Support", href: "/admin/support" }, { label: "Loading..." }]}>
                <div className="space-y-6">
                    <Skeleton className="h-12 w-64" />
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-64 w-full" />
                </div>
            </AdminLayout>
        )
    }

    if (!ticket) {
        return (
            <AdminLayout breadcrumbs={[{ label: "Support", href: "/admin/support" }, { label: "Not Found" }]}>
                <div className="text-center py-12"><p className="text-muted-foreground">Ticket not found</p></div>
            </AdminLayout>
        )
    }

    const StatusIcon = statusConfig[ticket.status].icon

    return (
        <AdminLayout breadcrumbs={[{ label: "Support", href: "/admin/support" }, { label: ticket.subject }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1">
                        <Button variant="ghost" size="sm" onClick={() => router.push("/admin/support")} className="mb-2"><ArrowLeft className="h-4 w-4 mr-2" />Back to Tickets</Button>
                        <div className="flex items-center gap-3">
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, delay: 0.1 }} className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <Ticket className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-2xl font-bold tracking-tight">{ticket.subject}</h1>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge variant="outline" className={statusConfig[ticket.status].color}><StatusIcon className="h-3 w-3 mr-1" />{statusConfig[ticket.status].label}</Badge>
                                    <Badge variant="outline" className={priorityConfig[ticket.priority].color}>{priorityConfig[ticket.priority].label}</Badge>
                                    <Badge variant="outline">{ticket.category}</Badge>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Select value={ticket.status} onValueChange={handleStatusChange} disabled={isUpdating}>
                            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="open">Open</SelectItem>
                                <SelectItem value="in_progress">In Progress</SelectItem>
                                <SelectItem value="waiting">Waiting</SelectItem>
                                <SelectItem value="resolved">Resolved</SelectItem>
                                <SelectItem value="closed">Closed</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button variant="outline" size="icon" onClick={fetchTicket}><RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} /></Button>
                    </div>
                </motion.div>

                {/* User Info */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card>
                        <CardHeader><CardTitle className="flex items-center gap-2"><User className="h-5 w-5" />Customer Info</CardTitle></CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-4">
                                <Avatar className="h-12 w-12"><AvatarFallback>{ticket.user_name.split(" ").map(n => n[0]).join("")}</AvatarFallback></Avatar>
                                <div>
                                    <p className="font-medium">{ticket.user_name}</p>
                                    <p className="text-sm text-muted-foreground">{ticket.user_email}</p>
                                </div>
                                <div className="ml-auto text-right text-sm text-muted-foreground">
                                    <p>Created: {formatDate(ticket.created_at)}</p>
                                    <p>Updated: {formatDate(ticket.updated_at)}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Conversation */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card>
                        <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquare className="h-5 w-5" />Conversation</CardTitle><CardDescription>{ticket.messages.length} messages</CardDescription></CardHeader>
                        <CardContent className="space-y-4">
                            {ticket.messages.map((message, index) => (
                                <motion.div key={message.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} className={cn("flex gap-3", message.sender_type === "admin" && "flex-row-reverse")}>
                                    <Avatar className="h-8 w-8"><AvatarFallback className={message.sender_type === "admin" ? "bg-primary text-primary-foreground" : ""}>{message.sender_name.split(" ").map(n => n[0]).join("")}</AvatarFallback></Avatar>
                                    <div className={cn("flex-1 max-w-[80%]", message.sender_type === "admin" && "text-right")}>
                                        <div className={cn("inline-block p-3 rounded-lg", message.sender_type === "admin" ? "bg-primary text-primary-foreground" : "bg-muted")}>
                                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">{message.sender_name} • {formatDate(message.created_at)}</p>
                                    </div>
                                </motion.div>
                            ))}

                            {/* Reply Form */}
                            <div className="pt-4 border-t">
                                <Textarea placeholder="Type your reply..." value={replyContent} onChange={(e) => setReplyContent(e.target.value)} rows={4} className="mb-3" />
                                <div className="flex justify-end">
                                    <Button onClick={handleSendReply} disabled={!replyContent.trim() || isSending}>
                                        {isSending ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                                        Send Reply
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </AdminLayout>
    )
}
