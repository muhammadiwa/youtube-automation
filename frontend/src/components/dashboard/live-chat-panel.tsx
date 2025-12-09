"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import {
    MessageSquare,
    Send,
    MoreVertical,
    Trash2,
    Clock,
    Ban,
    Shield,
    Crown,
    Star,
    AlertTriangle,
    Loader2,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { moderationApi, type ChatMessage } from "@/lib/api/moderation"
import { cn } from "@/lib/utils"

interface LiveChatPanelProps {
    eventId: string
    isLive?: boolean
}

interface SlowModeState {
    enabled: boolean
    delay: number
}

export function LiveChatPanel({ eventId, isLive = false }: LiveChatPanelProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [newMessage, setNewMessage] = useState("")
    const [loading, setLoading] = useState(true)
    const [sending, setSending] = useState(false)
    const [slowMode, setSlowMode] = useState<SlowModeState>({ enabled: false, delay: 0 })
    const [timeoutDialogOpen, setTimeoutDialogOpen] = useState(false)
    const [selectedUser, setSelectedUser] = useState<{ id: string; name: string } | null>(null)
    const [timeoutDuration, setTimeoutDuration] = useState("60")
    const scrollRef = useRef<HTMLDivElement>(null)
    const wsRef = useRef<WebSocket | null>(null)

    // Load initial messages
    const loadMessages = useCallback(async () => {
        try {
            setLoading(true)
            const response = await moderationApi.getChatMessages(eventId, { page_size: 50 })
            setMessages(response.items || [])
        } catch (error) {
            console.error("Failed to load chat messages:", error)
        } finally {
            setLoading(false)
        }
    }, [eventId])

    // WebSocket connection for real-time messages
    useEffect(() => {
        loadMessages()

        // Simulate WebSocket connection for real-time updates
        // In production, this would connect to actual WebSocket server
        const simulateWebSocket = () => {
            const interval = setInterval(() => {
                if (!isLive) return
                // Simulate incoming messages for demo
                const demoUsers = ["Viewer123", "Fan456", "User789", "Subscriber001", "Member_Pro"]
                const demoMessages = [
                    "Great stream!",
                    "Hello everyone!",
                    "Love the content!",
                    "First time here!",
                    "Amazing quality!",
                    "Keep it up!",
                    "This is awesome!",
                ]
                const randomUser = demoUsers[Math.floor(Math.random() * demoUsers.length)]
                const randomMessage = demoMessages[Math.floor(Math.random() * demoMessages.length)]

                const newMsg: ChatMessage = {
                    id: Date.now().toString(),
                    event_id: eventId,
                    author_id: `user_${Math.random().toString(36).substr(2, 9)}`,
                    author_name: randomUser,
                    message: randomMessage,
                    is_moderator: Math.random() > 0.9,
                    is_owner: false,
                    is_member: Math.random() > 0.7,
                    timestamp: new Date().toISOString(),
                }
                setMessages((prev) => [...prev.slice(-99), newMsg])
            }, 3000 + Math.random() * 5000)

            return () => clearInterval(interval)
        }

        const cleanup = simulateWebSocket()
        return cleanup
    }, [eventId, isLive, loadMessages])

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    const handleSendMessage = async () => {
        if (!newMessage.trim() || sending) return

        try {
            setSending(true)
            // In production, this would send via API
            const moderatorMsg: ChatMessage = {
                id: Date.now().toString(),
                event_id: eventId,
                author_id: "moderator",
                author_name: "Moderator",
                message: newMessage,
                is_moderator: true,
                is_owner: false,
                is_member: true,
                timestamp: new Date().toISOString(),
            }
            setMessages((prev) => [...prev, moderatorMsg])
            setNewMessage("")
        } catch (error) {
            console.error("Failed to send message:", error)
        } finally {
            setSending(false)
        }
    }

    const handleDeleteMessage = async (messageId: string) => {
        try {
            await moderationApi.moderateMessage(eventId, messageId, "delete")
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === messageId ? { ...msg, moderation_status: "deleted" } : msg
                )
            )
        } catch (error) {
            console.error("Failed to delete message:", error)
        }
    }

    const handleHideMessage = async (messageId: string) => {
        try {
            await moderationApi.moderateMessage(eventId, messageId, "hide")
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === messageId ? { ...msg, moderation_status: "hidden" } : msg
                )
            )
        } catch (error) {
            console.error("Failed to hide message:", error)
        }
    }

    const handleTimeoutUser = async () => {
        if (!selectedUser) return
        try {
            await moderationApi.timeoutUser(eventId, selectedUser.id, parseInt(timeoutDuration))
            setTimeoutDialogOpen(false)
            setSelectedUser(null)
        } catch (error) {
            console.error("Failed to timeout user:", error)
        }
    }

    const handleBanUser = async (userId: string) => {
        if (!confirm("Are you sure you want to ban this user?")) return
        try {
            await moderationApi.banUser(eventId, userId)
        } catch (error) {
            console.error("Failed to ban user:", error)
        }
    }

    const toggleSlowMode = async () => {
        try {
            if (slowMode.enabled) {
                await moderationApi.disableSlowMode(eventId)
                setSlowMode({ enabled: false, delay: 0 })
            } else {
                await moderationApi.enableSlowMode(eventId, 30)
                setSlowMode({ enabled: true, delay: 30 })
            }
        } catch (error) {
            console.error("Failed to toggle slow mode:", error)
        }
    }

    const openTimeoutDialog = (userId: string, userName: string) => {
        setSelectedUser({ id: userId, name: userName })
        setTimeoutDialogOpen(true)
    }

    const getUserBadge = (msg: ChatMessage) => {
        if (msg.is_owner) {
            return (
                <Badge className="bg-red-500 text-white text-[10px] px-1 py-0">
                    <Crown className="h-2.5 w-2.5 mr-0.5" />
                    Owner
                </Badge>
            )
        }
        if (msg.is_moderator) {
            return (
                <Badge className="bg-blue-500 text-white text-[10px] px-1 py-0">
                    <Shield className="h-2.5 w-2.5 mr-0.5" />
                    Mod
                </Badge>
            )
        }
        if (msg.is_member) {
            return (
                <Badge className="bg-green-500 text-white text-[10px] px-1 py-0">
                    <Star className="h-2.5 w-2.5 mr-0.5" />
                    Member
                </Badge>
            )
        }
        return null
    }

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp)
        return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
    }

    return (
        <>
            <Card className="h-full flex flex-col border-0 shadow-lg">
                <CardHeader className="pb-2 border-b">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <MessageSquare className="h-5 w-5" />
                            Live Chat
                            {isLive && (
                                <span className="flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                                </span>
                            )}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                            {slowMode.enabled && (
                                <Badge variant="secondary" className="text-xs">
                                    <Clock className="h-3 w-3 mr-1" />
                                    Slow Mode ({slowMode.delay}s)
                                </Badge>
                            )}
                            <Button
                                variant={slowMode.enabled ? "default" : "outline"}
                                size="sm"
                                onClick={toggleSlowMode}
                                title={slowMode.enabled ? "Disable Slow Mode" : "Enable Slow Mode"}
                            >
                                <Clock className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
                    {/* Messages Area */}
                    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                        {loading ? (
                            <div className="flex items-center justify-center h-full">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                                <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
                                <p className="text-sm">No messages yet</p>
                                <p className="text-xs">Chat messages will appear here</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {messages.map((msg) => (
                                    <div
                                        key={msg.id}
                                        className={cn(
                                            "group p-2 rounded-lg transition-colors",
                                            msg.moderation_status === "deleted" && "opacity-50 line-through",
                                            msg.moderation_status === "hidden" && "opacity-50 bg-yellow-500/10",
                                            msg.moderation_status === "flagged" && "bg-red-500/10 border border-red-500/20",
                                            !msg.moderation_status && "hover:bg-muted/50"
                                        )}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-1.5 flex-wrap">
                                                    {getUserBadge(msg)}
                                                    <span
                                                        className={cn(
                                                            "font-medium text-sm",
                                                            msg.is_owner && "text-red-500",
                                                            msg.is_moderator && "text-blue-500",
                                                            msg.is_member && "text-green-500"
                                                        )}
                                                    >
                                                        {msg.author_name}
                                                    </span>
                                                    <span className="text-xs text-muted-foreground">
                                                        {formatTime(msg.timestamp)}
                                                    </span>
                                                </div>
                                                <p className="text-sm mt-0.5 break-words">{msg.message}</p>
                                                {msg.moderation_status === "flagged" && (
                                                    <div className="flex items-center gap-1 mt-1 text-xs text-red-500">
                                                        <AlertTriangle className="h-3 w-3" />
                                                        <span>Flagged: {msg.moderation_reason}</span>
                                                    </div>
                                                )}
                                            </div>
                                            {!msg.is_owner && msg.moderation_status !== "deleted" && (
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                        >
                                                            <MoreVertical className="h-3 w-3" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuItem onClick={() => handleDeleteMessage(msg.id)}>
                                                            <Trash2 className="mr-2 h-4 w-4" />
                                                            Delete Message
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem onClick={() => handleHideMessage(msg.id)}>
                                                            <AlertTriangle className="mr-2 h-4 w-4" />
                                                            Hide Message
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem
                                                            onClick={() => openTimeoutDialog(msg.author_id, msg.author_name)}
                                                        >
                                                            <Clock className="mr-2 h-4 w-4" />
                                                            Timeout User
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem
                                                            className="text-destructive"
                                                            onClick={() => handleBanUser(msg.author_id)}
                                                        >
                                                            <Ban className="mr-2 h-4 w-4" />
                                                            Ban User
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </ScrollArea>

                    {/* Message Input */}
                    <div className="p-4 border-t bg-muted/30">
                        <div className="flex gap-2">
                            <Input
                                placeholder={isLive ? "Send a message as moderator..." : "Chat is offline"}
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
                                disabled={!isLive || sending}
                                className="flex-1"
                            />
                            <Button
                                onClick={handleSendMessage}
                                disabled={!isLive || !newMessage.trim() || sending}
                                size="icon"
                            >
                                {sending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Send className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Timeout Dialog */}
            <Dialog open={timeoutDialogOpen} onOpenChange={setTimeoutDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Timeout User</DialogTitle>
                        <DialogDescription>
                            Temporarily prevent {selectedUser?.name} from sending messages.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Duration</Label>
                            <Select value={timeoutDuration} onValueChange={setTimeoutDuration}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="60">1 minute</SelectItem>
                                    <SelectItem value="300">5 minutes</SelectItem>
                                    <SelectItem value="600">10 minutes</SelectItem>
                                    <SelectItem value="1800">30 minutes</SelectItem>
                                    <SelectItem value="3600">1 hour</SelectItem>
                                    <SelectItem value="86400">24 hours</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setTimeoutDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleTimeoutUser}>Timeout User</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    )
}
