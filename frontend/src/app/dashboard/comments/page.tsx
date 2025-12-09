"use client"

import { useState, useEffect } from "react"
import {
    MessageSquare,
    Search,
    Reply,
    Trash2,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Loader2,
    MoreHorizontal,
    ThumbsUp,
    Video,
    RefreshCw,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { moderationApi, type Comment, type CommentsResponse } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import { SentimentBadge, AttentionIndicator } from "@/components/dashboard/sentiment-indicator"
import type { YouTubeAccount } from "@/types"

// Status badge component
function StatusBadge({ status }: { status: Comment["status"] }) {
    const config = {
        published: { label: "Published", variant: "default" as const },
        held: { label: "Held", variant: "secondary" as const },
        deleted: { label: "Deleted", variant: "destructive" as const },
        spam: { label: "Spam", variant: "outline" as const },
    }

    const { label, variant } = config[status]
    return <Badge variant={variant}>{label}</Badge>
}

export default function CommentsPage() {
    const [comments, setComments] = useState<Comment[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const pageSize = 20

    // Filters
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [sentimentFilter, setSentimentFilter] = useState<string>("all")
    const [statusFilter, setStatusFilter] = useState<string>("all")

    // Selection
    const [selectedComments, setSelectedComments] = useState<Set<string>>(new Set())

    // Reply state
    const [replyingTo, setReplyingTo] = useState<string | null>(null)
    const [replyText, setReplyText] = useState("")
    const [sendingReply, setSendingReply] = useState(false)

    // Bulk action state
    const [bulkActionLoading, setBulkActionLoading] = useState(false)

    useEffect(() => {
        loadAccounts()
    }, [])

    useEffect(() => {
        loadComments()
    }, [accountFilter, sentimentFilter, statusFilter, page])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadComments = async () => {
        try {
            setLoading(true)
            const params: Parameters<typeof moderationApi.getComments>[0] = {
                page,
                page_size: pageSize,
            }
            if (accountFilter !== "all") params.account_id = accountFilter
            if (sentimentFilter !== "all") params.sentiment = sentimentFilter
            if (statusFilter !== "all") params.status = statusFilter

            const response: CommentsResponse = await moderationApi.getComments(params)
            setComments(response.items)
            setTotal(response.total)
        } catch (error) {
            console.error("Failed to load comments:", error)
        } finally {
            setLoading(false)
        }
    }

    const filteredComments = comments.filter((comment) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            comment.text.toLowerCase().includes(query) ||
            comment.author_name.toLowerCase().includes(query)
        )
    })

    const handleSelectAll = (checked: boolean) => {
        if (checked) {
            setSelectedComments(new Set(filteredComments.map((c) => c.id)))
        } else {
            setSelectedComments(new Set())
        }
    }

    const handleSelectComment = (commentId: string, checked: boolean) => {
        const newSelected = new Set(selectedComments)
        if (checked) {
            newSelected.add(commentId)
        } else {
            newSelected.delete(commentId)
        }
        setSelectedComments(newSelected)
    }

    const handleReply = async (commentId: string) => {
        if (!replyText.trim()) return

        try {
            setSendingReply(true)
            await moderationApi.replyToComment(commentId, replyText)
            setReplyingTo(null)
            setReplyText("")
            loadComments()
        } catch (error) {
            console.error("Failed to send reply:", error)
            alert("Failed to send reply")
        } finally {
            setSendingReply(false)
        }
    }

    const handleDelete = async (commentId: string) => {
        if (!confirm("Are you sure you want to delete this comment?")) return
        try {
            await moderationApi.deleteComment(commentId)
            loadComments()
        } catch (error) {
            console.error("Failed to delete comment:", error)
        }
    }

    const handleMarkSpam = async (commentId: string) => {
        try {
            await moderationApi.markAsSpam(commentId)
            loadComments()
        } catch (error) {
            console.error("Failed to mark as spam:", error)
        }
    }

    const handleApprove = async (commentId: string) => {
        try {
            await moderationApi.approveComment(commentId)
            loadComments()
        } catch (error) {
            console.error("Failed to approve comment:", error)
        }
    }

    const handleBulkAction = async (action: "delete" | "spam" | "approve") => {
        if (selectedComments.size === 0) return
        if (!confirm(`Are you sure you want to ${action} ${selectedComments.size} comments?`)) return

        try {
            setBulkActionLoading(true)
            await moderationApi.bulkModerateComments(Array.from(selectedComments), action)
            setSelectedComments(new Set())
            loadComments()
        } catch (error) {
            console.error("Failed to perform bulk action:", error)
            alert("Failed to perform bulk action")
        } finally {
            setBulkActionLoading(false)
        }
    }

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })
    }

    const totalPages = Math.ceil(total / pageSize)

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Comments" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <MessageSquare className="h-8 w-8" />
                            Comment Inbox
                        </h1>
                        <p className="text-muted-foreground">
                            Manage comments from all your YouTube channels in one place
                        </p>
                    </div>
                    <Button
                        variant="outline"
                        onClick={() => loadComments()}
                        disabled={loading}
                    >
                        <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                        Refresh
                    </Button>
                </div>

                {/* Filters */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search comments..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                            <div className="flex flex-wrap gap-2">
                                <Select value={accountFilter} onValueChange={setAccountFilter}>
                                    <SelectTrigger className="w-[180px]">
                                        <SelectValue placeholder="All Accounts" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Accounts</SelectItem>
                                        {accounts.map((account) => (
                                            <SelectItem key={account.id} value={account.id}>
                                                {account.channelTitle}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="Sentiment" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Sentiments</SelectItem>
                                        <SelectItem value="positive">Positive</SelectItem>
                                        <SelectItem value="neutral">Neutral</SelectItem>
                                        <SelectItem value="negative">Negative</SelectItem>
                                    </SelectContent>
                                </Select>
                                <Select value={statusFilter} onValueChange={setStatusFilter}>
                                    <SelectTrigger className="w-[140px]">
                                        <SelectValue placeholder="Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="published">Published</SelectItem>
                                        <SelectItem value="held">Held</SelectItem>
                                        <SelectItem value="spam">Spam</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Bulk Actions Toolbar */}
                {selectedComments.size > 0 && (
                    <Card className="border-0 shadow-lg bg-primary/5">
                        <CardContent className="py-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                    {selectedComments.size} comment{selectedComments.size > 1 ? "s" : ""} selected
                                </span>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleBulkAction("approve")}
                                        disabled={bulkActionLoading}
                                    >
                                        <CheckCircle className="mr-2 h-4 w-4" />
                                        Approve
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleBulkAction("spam")}
                                        disabled={bulkActionLoading}
                                    >
                                        <AlertTriangle className="mr-2 h-4 w-4" />
                                        Mark Spam
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={() => handleBulkAction("delete")}
                                        disabled={bulkActionLoading}
                                    >
                                        {bulkActionLoading ? (
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Trash2 className="mr-2 h-4 w-4" />
                                        )}
                                        Delete
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setSelectedComments(new Set())}
                                    >
                                        <XCircle className="mr-2 h-4 w-4" />
                                        Clear
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Comments List */}
                {loading ? (
                    <div className="space-y-4">
                        {[...Array(5)].map((_, i) => (
                            <Card key={i} className="border-0 shadow-lg">
                                <CardContent className="p-6">
                                    <div className="flex gap-4">
                                        <Skeleton className="h-10 w-10 rounded-full" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-32 mb-2" />
                                            <Skeleton className="h-16 w-full mb-2" />
                                            <Skeleton className="h-3 w-48" />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : filteredComments.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No comments found</h3>
                            <p className="text-muted-foreground">
                                {searchQuery || accountFilter !== "all" || sentimentFilter !== "all" || statusFilter !== "all"
                                    ? "Try adjusting your filters"
                                    : "Comments from your videos will appear here"}
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-4">
                        {/* Select All */}
                        <div className="flex items-center gap-2 px-2">
                            <Checkbox
                                checked={selectedComments.size === filteredComments.length && filteredComments.length > 0}
                                onCheckedChange={handleSelectAll}
                            />
                            <span className="text-sm text-muted-foreground">Select all</span>
                        </div>

                        {filteredComments.map((comment) => (
                            <Card
                                key={comment.id}
                                className={`border-0 shadow-lg transition-colors ${comment.sentiment === "negative" ? "border-l-4 border-l-red-500" : ""
                                    } ${selectedComments.has(comment.id) ? "bg-primary/5" : ""}`}
                            >
                                <CardContent className="p-6">
                                    <div className="flex gap-4">
                                        <Checkbox
                                            checked={selectedComments.has(comment.id)}
                                            onCheckedChange={(checked) =>
                                                handleSelectComment(comment.id, checked as boolean)
                                            }
                                            className="mt-1"
                                        />
                                        <Avatar className="h-10 w-10">
                                            <AvatarImage src={comment.author_avatar} />
                                            <AvatarFallback>
                                                {comment.author_name.charAt(0).toUpperCase()}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                                <span className="font-semibold">{comment.author_name}</span>
                                                <SentimentBadge sentiment={comment.sentiment} />
                                                <StatusBadge status={comment.status} />
                                                {comment.is_reply && (
                                                    <Badge variant="outline" className="text-xs">
                                                        Reply
                                                    </Badge>
                                                )}
                                                <AttentionIndicator sentiment={comment.sentiment} />
                                            </div>
                                            <p className="text-sm mb-3 whitespace-pre-wrap">{comment.text}</p>

                                            {/* Video Preview */}
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3 p-2 bg-muted/50 rounded-md">
                                                <Video className="h-4 w-4" />
                                                <span>Video ID: {comment.video_id}</span>
                                                <span className="mx-2">•</span>
                                                <span>{getAccountName(comment.account_id)}</span>
                                            </div>

                                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                <span>{formatDate(comment.created_at)}</span>
                                                <span className="flex items-center gap-1">
                                                    <ThumbsUp className="h-3 w-3" />
                                                    {comment.like_count}
                                                </span>
                                                {comment.reply_count > 0 && (
                                                    <span className="flex items-center gap-1">
                                                        <Reply className="h-3 w-3" />
                                                        {comment.reply_count} replies
                                                    </span>
                                                )}
                                            </div>

                                            {/* Quick Reply */}
                                            {replyingTo === comment.id ? (
                                                <div className="mt-4 space-y-2">
                                                    <Textarea
                                                        placeholder="Write your reply..."
                                                        value={replyText}
                                                        onChange={(e) => setReplyText(e.target.value)}
                                                        rows={3}
                                                    />
                                                    <div className="flex gap-2">
                                                        <Button
                                                            size="sm"
                                                            onClick={() => handleReply(comment.id)}
                                                            disabled={sendingReply || !replyText.trim()}
                                                        >
                                                            {sendingReply && (
                                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                            )}
                                                            Send Reply
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => {
                                                                setReplyingTo(null)
                                                                setReplyText("")
                                                            }}
                                                        >
                                                            Cancel
                                                        </Button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="mt-3 flex gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => setReplyingTo(comment.id)}
                                                    >
                                                        <Reply className="mr-2 h-4 w-4" />
                                                        Reply
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon">
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                {comment.status !== "published" && (
                                                    <DropdownMenuItem onClick={() => handleApprove(comment.id)}>
                                                        <CheckCircle className="mr-2 h-4 w-4" />
                                                        Approve
                                                    </DropdownMenuItem>
                                                )}
                                                <DropdownMenuItem onClick={() => handleMarkSpam(comment.id)}>
                                                    <AlertTriangle className="mr-2 h-4 w-4" />
                                                    Mark as Spam
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    onClick={() => handleDelete(comment.id)}
                                                    className="text-destructive"
                                                >
                                                    <Trash2 className="mr-2 h-4 w-4" />
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} comments
                        </p>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={page === 1}
                            >
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                            >
                                Next
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}
