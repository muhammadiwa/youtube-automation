"use client"

import { useState, useEffect, useCallback, useRef } from "react"
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
import adminApi, { AdminTicketDetail, AdminTicketMessage } from "@/lib/api/admin"
import { useAdminSupportRealtime } from "@/hooks/use-admin-support-realtime"

// Status config
const statusConfig = {
    open: { label: "Open", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: AlertCircle },
    in_progress: { label: "In Progress", color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: Clock },
    waiting_user: { label: "Waiting User", color: "bg-purple-500/10 text-purple-500 border-purple-500/20", icon: Clock },
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
    const ticketIdRef = useRef(ticketId)
    const { addToast } = useToast()
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const [ticket, setTicket] = useState<AdminTicketDetail | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [replyContent, setReplyContent] = useState("")
    const [isSending, setIsSending] = useState(false)
    const [isUpdating, setIsUpdating] = useState(false)

    // Get admin ID from localStorage (assuming it's stored after login)
    const [adminId, setAdminId] = useState<string | null>(null)

    // Keep ticketIdRef in sync
    useEffect(() => {
        ticketIdRef.current = ticketId
    }, [ticketId])

    useEffect(() => {
        // Get admin ID from localStorage - stored as user_id
        const userId = localStorage.getItem("user_id")
        if (userId) {
            console.log("[AdminSupport] User ID loaded from localStorage:", userId)
            setAdminId(userId)
        } else {
            // Fallback: try to get from "user" object if exists
            const userData = localStorage.getItem("user")
            if (userData) {
                try {
                    const user = JSON.parse(userData)
                    console.log("[AdminSupport] User data loaded from 'user' key:", user.id)
                    setAdminId(user.id)
                } catch (error) {
                    console.error("[AdminSupport] Failed to parse user data:", error)
                }
            } else {
                console.warn("[AdminSupport] No user ID found in localStorage")
            }
        }
    }, [])

    // Real-time updates via WebSocket
    const { subscribeToTicket, unsubscribeFromTicket, isConnected } = useAdminSupportRealtime({
        adminId: adminId || undefined,
        onNewMessage: (tid, payload) => {
            console.log("[AdminSupport] onNewMessage called:", tid, payload)
            if (tid === ticketIdRef.current) {
                const msg = payload as unknown as AdminTicketMessage
                setTicket(prev => {
                    if (!prev) {
                        console.log("[AdminSupport] No ticket state, skipping message")
                        return null
                    }
                    // Check if message already exists to prevent duplicates
                    const exists = prev.messages.some(m => m.id === msg.id)
                    if (exists) {
                        console.log("[AdminSupport] Message already exists, skipping")
                        return prev
                    }
                    console.log("[AdminSupport] Adding new message to state")
                    return {
                        ...prev,
                        messages: [...prev.messages, msg],
                    }
                })
                scrollToBottom()
            }
        },
        onStatusChange: (tid, _, newStatus) => {
            console.log("[AdminSupport] onStatusChange called:", tid, newStatus)
            if (tid === ticketIdRef.current) {
                setTicket(prev => prev ? { ...prev, status: newStatus } : null)
            }
        },
    })

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    // Subscribe to ticket when connected
    useEffect(() => {
        if (ticketId && isConnected) {
            console.log("[AdminSupport] Subscribing to ticket:", ticketId)
            subscribeToTicket(ticketId)
        }
    }, [ticketId, isConnected, subscribeToTicket])

    const fetchTicket = useCallback(async () => {
        setIsLoading(true)
        try {
            const data = await adminApi.getSupportTicketDetail(ticketId)
            setTicket(data)
        } catch (error) {
            console.error("Failed to fetch ticket:", error)
            addToast({ type: "error", title: "Error", description: "Failed to load ticket details" })
        } finally {
            setIsLoading(false)
        }
    }, [ticketId, addToast])

    useEffect(() => {
        fetchTicket()
    }, [fetchTicket])

    // Cleanup: unsubscribe when component unmounts or ticketId changes
    useEffect(() => {
        return () => {
            if (ticketId) {
                console.log("[AdminSupport] Cleanup: unsubscribing from ticket:", ticketId)
                unsubscribeFromTicket(ticketId)
            }
        }
    }, [ticketId, unsubscribeFromTicket])

    useEffect(() => {
        scrollToBottom()
    }, [ticket?.messages])
    const handleSendReply = async () => {
        if (!replyContent.trim() || !ticket) return
        setIsSending(true)
        try {
            const response = await adminApi.replyToTicket(ticketId, {
                content: replyContent,
                send_email: true,
            })

            // Add new message to the list - construct message from response
            const newMessage: AdminTicketMessage = {
                id: response.message_id,
                ticket_id: response.ticket_id,
                sender_id: "", // Will be filled by backend
                sender_type: "admin",
                sender_name: "You",
                sender_email: null,
                content: response.content,
                attachments: null,
                created_at: response.created_at,
            }

            setTicket(prev => prev ? {
                ...prev,
                messages: [...prev.messages, newMessage],
            } : null)

            setReplyContent("")
            addToast({ type: "success", title: "Reply sent", description: "Your reply has been sent to the user." })
        } catch (error) {
            console.error("Failed to send reply:", error)
            addToast({ type: "error", title: "Error", description: "Failed to send reply" })
        } finally {
            setIsSending(false)
        }
    }

    const handleStatusChange = async (newStatus: string) => {
        if (!ticket) return
        setIsUpdating(true)
        try {
            await adminApi.updateTicketStatus(ticketId, {
                status: newStatus,
                notify_user: true,
            })
            setTicket(prev => prev ? { ...prev, status: newStatus } : null)
            addToast({ type: "success", title: "Status updated", description: `Ticket status changed to ${newStatus}.` })
        } catch (error) {
            console.error("Failed to update status:", error)
            addToast({ type: "error", title: "Error", description: "Failed to update status" })
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

    const StatusIcon = statusConfig[ticket.status as keyof typeof statusConfig]?.icon || AlertCircle
    const statusStyle = statusConfig[ticket.status as keyof typeof statusConfig] || statusConfig.open
    const priorityStyle = priorityConfig[ticket.priority as keyof typeof priorityConfig] || priorityConfig.medium

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
                                    <Badge variant="outline" className={statusStyle.color}><StatusIcon className="h-3 w-3 mr-1" />{statusStyle.label}</Badge>
                                    <Badge variant="outline" className={priorityStyle.color}>{priorityStyle.label}</Badge>
                                    {ticket.category && <Badge variant="outline">{ticket.category}</Badge>}
                                    {isConnected && (
                                        <span className="flex items-center gap-1 text-xs text-emerald-500">
                                            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                                            Live
                                        </span>
                                    )}
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
                                <SelectItem value="waiting_user">Waiting User</SelectItem>
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
                                <Avatar className="h-12 w-12"><AvatarFallback>{ticket.user.name.split(" ").map(n => n[0]).join("")}</AvatarFallback></Avatar>
                                <div>
                                    <p className="font-medium">{ticket.user.name}</p>
                                    <p className="text-sm text-muted-foreground">{ticket.user.email}</p>
                                </div>
                                <div className="ml-auto text-right text-sm text-muted-foreground">
                                    <p>Created: {formatDate(ticket.created_at)}</p>
                                    <p>Updated: {formatDate(ticket.updated_at)}</p>
                                </div>
                            </div>
                            {ticket.description && (
                                <div className="mt-4 p-3 bg-muted rounded-lg">
                                    <p className="text-sm font-medium mb-1">Description:</p>
                                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">{ticket.description}</p>
                                </div>
                            )}
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
                                    <Avatar className="h-8 w-8"><AvatarFallback className={message.sender_type === "admin" ? "bg-primary text-primary-foreground" : ""}>{(message.sender_name || "U").split(" ").map(n => n[0]).join("")}</AvatarFallback></Avatar>
                                    <div className={cn("flex-1 max-w-[80%]", message.sender_type === "admin" && "text-right")}>
                                        <div className={cn("inline-block p-3 rounded-lg", message.sender_type === "admin" ? "bg-primary text-primary-foreground" : "bg-muted")}>
                                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">{message.sender_name || "Unknown"} • {formatDate(message.created_at)}</p>
                                    </div>
                                </motion.div>
                            ))}
                            <div ref={messagesEndRef} />

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
