"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
    ArrowLeft,
    Send,
    Clock,
    User,
    Shield,
    AlertCircle,
    CheckCircle2,
    MessageSquare,
    Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { supportApi, SupportTicketDetail, TicketMessage } from "@/lib/api/support"
import { useSupportRealtime } from "@/hooks/use-support-realtime"
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

export default function TicketDetailPage() {
    const params = useParams()
    const router = useRouter()
    const { addToast } = useToast()
    const ticketId = params.id as string
    const ticketIdRef = useRef(ticketId)

    const [ticket, setTicket] = useState<SupportTicketDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [newMessage, setNewMessage] = useState("")
    const [sending, setSending] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Keep ticketIdRef in sync
    useEffect(() => {
        ticketIdRef.current = ticketId
    }, [ticketId])

    // Real-time updates
    const { subscribeToTicket, unsubscribeFromTicket, isConnected } = useSupportRealtime({
        onNewMessage: (tid, payload) => {
            console.log("[UserSupport] onNewMessage called:", tid, payload)
            if (tid === ticketIdRef.current) {
                const msg = payload as unknown as TicketMessage
                setTicket(prev => {
                    if (!prev) {
                        console.log("[UserSupport] No ticket state, skipping message")
                        return null
                    }
                    // Check if message already exists to prevent duplicates
                    const exists = prev.messages.some(m => m.id === msg.id)
                    if (exists) {
                        console.log("[UserSupport] Message already exists, skipping")
                        return prev
                    }
                    console.log("[UserSupport] Adding new message to state")
                    return {
                        ...prev,
                        messages: [...prev.messages, msg],
                    }
                })
            }
        },
        onStatusChange: (tid, _, newStatus) => {
            console.log("[UserSupport] onStatusChange called:", tid, newStatus)
            if (tid === ticketIdRef.current) {
                setTicket(prev => prev ? { ...prev, status: newStatus as SupportTicketDetail["status"] } : null)
            }
        },
    })

    useEffect(() => {
        loadTicket()
    }, [ticketId])

    // Subscribe to ticket when connected
    useEffect(() => {
        if (ticketId && isConnected) {
            console.log("[UserSupport] Subscribing to ticket:", ticketId)
            subscribeToTicket(ticketId)
        }
    }, [ticketId, isConnected, subscribeToTicket])

    // Cleanup: unsubscribe when component unmounts or ticketId changes
    useEffect(() => {
        return () => {
            if (ticketId) {
                console.log("[UserSupport] Cleanup: unsubscribing from ticket:", ticketId)
                unsubscribeFromTicket(ticketId)
            }
        }
    }, [ticketId, unsubscribeFromTicket])

    useEffect(() => {
        scrollToBottom()
    }, [ticket?.messages])

    const loadTicket = async () => {
        try {
            setLoading(true)
            const data = await supportApi.getTicketDetail(ticketId)
            setTicket(data)
        } catch (error) {
            console.error("Failed to load ticket:", error)
            addToast({ type: "error", title: "Error", description: "Failed to load ticket" })
        } finally {
            setLoading(false)
        }
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    const handleSendMessage = async () => {
        if (!newMessage.trim() || sending) return

        setSending(true)
        try {
            const msg = await supportApi.addMessage(ticketId, { content: newMessage.trim() })
            setTicket(prev => prev ? {
                ...prev,
                messages: [...prev.messages, msg],
            } : null)
            setNewMessage("")
            addToast({ type: "success", title: "Sent", description: "Message sent successfully" })
        } catch (error) {
            console.error("Failed to send message:", error)
            addToast({ type: "error", title: "Error", description: "Failed to send message" })
        } finally {
            setSending(false)
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString()
    }

    if (loading) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-[600px] w-full" />
                </div>
            </DashboardLayout>
        )
    }

    if (!ticket) {
        return (
            <DashboardLayout>
                <div className="flex flex-col items-center justify-center py-12">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">Ticket not found</h3>
                    <Button className="mt-4" onClick={() => router.push("/dashboard/support")}>
                        <ArrowLeft className="mr-2 h-4 w-4" />Back to Support
                    </Button>
                </div>
            </DashboardLayout>
        )
    }

    const st = statusConfig[ticket.status] || statusConfig.open
    const pr = priorityConfig[ticket.priority] || priorityConfig.medium
    const StatusIcon = st.icon
    const isResolved = ticket.status === "resolved" || ticket.status === "closed"

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/support")}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div className="flex-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-xl font-bold">{ticket.subject}</h1>
                            {isConnected && (
                                <span className="flex items-center gap-1 text-xs text-emerald-500">
                                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                                    Live
                                </span>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className={st.color}>
                                <StatusIcon className="mr-1 h-3 w-3" />{st.label}
                            </Badge>
                            <Badge variant="outline" className={pr.color}>{pr.label}</Badge>
                            {ticket.category && (
                                <Badge variant="secondary" className="capitalize">{ticket.category}</Badge>
                            )}
                        </div>
                    </div>
                </div>

                {/* Ticket Info */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Ticket Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">{ticket.description}</p>
                        <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
                            <span>Created: {formatDate(ticket.created_at)}</span>
                            <span>Updated: {formatDate(ticket.updated_at)}</span>
                            {ticket.resolved_at && <span>Resolved: {formatDate(ticket.resolved_at)}</span>}
                        </div>
                    </CardContent>
                </Card>

                {/* Messages */}
                <Card className="flex flex-col h-[500px]">
                    <CardHeader className="border-b">
                        <CardTitle className="text-sm flex items-center gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Conversation ({ticket.messages.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                        {ticket.messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                                <MessageSquare className="h-8 w-8 mb-2" />
                                <p>No messages yet</p>
                            </div>
                        ) : (
                            ticket.messages.map((msg, idx) => {
                                const isUser = msg.sender_type === "user"
                                return (
                                    <motion.div
                                        key={msg.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        className={cn(
                                            "flex gap-3",
                                            isUser ? "flex-row-reverse" : ""
                                        )}
                                    >
                                        <Avatar className="h-8 w-8">
                                            <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
                                                {isUser ? <User className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className={cn(
                                            "max-w-[70%] rounded-lg p-3",
                                            isUser
                                                ? "bg-primary text-primary-foreground"
                                                : "bg-muted"
                                        )}>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs font-medium">
                                                    {msg.sender_name || (isUser ? "You" : "Support Team")}
                                                </span>
                                                <span className={cn(
                                                    "text-xs",
                                                    isUser ? "text-primary-foreground/70" : "text-muted-foreground"
                                                )}>
                                                    {formatDate(msg.created_at)}
                                                </span>
                                            </div>
                                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                                        </div>
                                    </motion.div>
                                )
                            })
                        )}
                        <div ref={messagesEndRef} />
                    </CardContent>

                    {/* Message Input */}
                    {!isResolved && (
                        <div className="border-t p-4">
                            <div className="flex gap-2">
                                <Textarea
                                    placeholder="Type your message..."
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter" && !e.shiftKey) {
                                            e.preventDefault()
                                            handleSendMessage()
                                        }
                                    }}
                                    className="min-h-[80px] resize-none"
                                />
                                <Button
                                    onClick={handleSendMessage}
                                    disabled={!newMessage.trim() || sending}
                                    className="self-end"
                                >
                                    {sending ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Send className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                Press Enter to send, Shift+Enter for new line
                            </p>
                        </div>
                    )}

                    {isResolved && (
                        <div className="border-t p-4 bg-muted/50">
                            <p className="text-sm text-muted-foreground text-center">
                                This ticket has been {ticket.status}. Create a new ticket if you need further assistance.
                            </p>
                        </div>
                    )}
                </Card>
            </div>
        </DashboardLayout>
    )
}
