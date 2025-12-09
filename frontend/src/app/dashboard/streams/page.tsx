"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import {
    Search,
    Plus,
    Grid3x3,
    Calendar,
    MoreVertical,
    Trash2,
    Edit,
    Play,
    Square,
    Radio,
    Clock,
    Users,
    Settings,
    Zap,
    Activity,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
import { streamsApi, type LiveEvent } from "@/lib/api/streams"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

// Calendar view component
function CalendarView({ events, onEventClick }: { events: LiveEvent[]; onEventClick: (event: LiveEvent) => void }) {
    const today = new Date()
    const [currentMonth, setCurrentMonth] = useState(today.getMonth())
    const [currentYear, setCurrentYear] = useState(today.getFullYear())

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay()

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    const getEventsForDay = (day: number) => {
        return events.filter((event) => {
            const eventDate = new Date(event.scheduled_start)
            return (
                eventDate.getDate() === day &&
                eventDate.getMonth() === currentMonth &&
                eventDate.getFullYear() === currentYear
            )
        })
    }

    const prevMonth = () => {
        if (currentMonth === 0) {
            setCurrentMonth(11)
            setCurrentYear(currentYear - 1)
        } else {
            setCurrentMonth(currentMonth - 1)
        }
    }

    const nextMonth = () => {
        if (currentMonth === 11) {
            setCurrentMonth(0)
            setCurrentYear(currentYear + 1)
        } else {
            setCurrentMonth(currentMonth + 1)
        }
    }

    return (
        <Card className="border-0 shadow-lg">
            <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">
                        {monthNames[currentMonth]} {currentYear}
                    </h3>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={prevMonth}>
                            ←
                        </Button>
                        <Button variant="outline" size="sm" onClick={nextMonth}>
                            →
                        </Button>
                    </div>
                </div>
                <div className="grid grid-cols-7 gap-1">
                    {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                        <div key={day} className="text-center text-sm font-medium text-muted-foreground p-2">
                            {day}
                        </div>
                    ))}
                    {Array.from({ length: firstDayOfMonth }).map((_, i) => (
                        <div key={`empty-${i}`} className="p-2" />
                    ))}
                    {Array.from({ length: daysInMonth }).map((_, i) => {
                        const day = i + 1
                        const dayEvents = getEventsForDay(day)
                        const isToday =
                            day === today.getDate() &&
                            currentMonth === today.getMonth() &&
                            currentYear === today.getFullYear()

                        return (
                            <div
                                key={day}
                                className={`min-h-[80px] p-1 border rounded-md ${isToday ? "bg-primary/10 border-primary" : "border-border"
                                    }`}
                            >
                                <div className={`text-sm ${isToday ? "font-bold text-primary" : ""}`}>
                                    {day}
                                </div>
                                <div className="space-y-1 mt-1">
                                    {dayEvents.slice(0, 2).map((event) => (
                                        <div
                                            key={event.id}
                                            onClick={() => onEventClick(event)}
                                            className={`text-xs p-1 rounded cursor-pointer truncate ${event.status === "live"
                                                ? "bg-red-500 text-white"
                                                : event.status === "scheduled"
                                                    ? "bg-blue-500 text-white"
                                                    : "bg-gray-200 dark:bg-gray-700"
                                                }`}
                                        >
                                            {event.title}
                                        </div>
                                    ))}
                                    {dayEvents.length > 2 && (
                                        <div className="text-xs text-muted-foreground">
                                            +{dayEvents.length - 2} more
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </CardContent>
        </Card>
    )
}

export default function StreamsPage() {
    const router = useRouter()
    const [events, setEvents] = useState<LiveEvent[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState<"grid" | "calendar">("grid")

    // Filters
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [pagination, setPagination] = useState({
        total: 0,
        page: 1,
        pageSize: 12,
    })

    useEffect(() => {
        loadAccounts()
        loadEvents()
    }, [statusFilter, accountFilter, pagination.page])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
            setAccounts([])
        }
    }

    const loadEvents = async () => {
        try {
            setLoading(true)
            const response = await streamsApi.getEvents({
                account_id: accountFilter !== "all" ? accountFilter : undefined,
                status: statusFilter !== "all" ? statusFilter : undefined,
                page: pagination.page,
                page_size: pagination.pageSize,
            })
            setEvents(response.items || [])
            setPagination((prev) => ({
                ...prev,
                total: response.total || 0,
            }))
        } catch (error) {
            console.error("Failed to load events:", error)
            setEvents([])
        } finally {
            setLoading(false)
        }
    }

    // Filter events by search query
    const filteredEvents = useMemo(() => {
        if (!searchQuery) return events
        const query = searchQuery.toLowerCase()
        return events.filter(
            (event) =>
                event.title.toLowerCase().includes(query) ||
                event.description?.toLowerCase().includes(query)
        )
    }, [events, searchQuery])

    const handleDeleteEvent = async (eventId: string) => {
        if (!confirm("Are you sure you want to delete this stream?")) return
        try {
            await streamsApi.deleteEvent(eventId)
            loadEvents()
        } catch (error) {
            console.error("Failed to delete event:", error)
        }
    }

    const handleStartStream = async (eventId: string) => {
        try {
            await streamsApi.startEvent(eventId)
            loadEvents()
        } catch (error) {
            console.error("Failed to start stream:", error)
        }
    }

    const handleStopStream = async (eventId: string) => {
        if (!confirm("Are you sure you want to stop this stream?")) return
        try {
            await streamsApi.stopEvent(eventId)
            loadEvents()
        } catch (error) {
            console.error("Failed to stop stream:", error)
        }
    }

    const getStatusBadge = (status: LiveEvent["status"]) => {
        switch (status) {
            case "live":
                return (
                    <Badge className="bg-red-500 text-white animate-pulse">
                        <Radio className="mr-1 h-3 w-3" />
                        LIVE
                    </Badge>
                )
            case "scheduled":
                return (
                    <Badge variant="default" className="bg-blue-500 text-white">
                        <Clock className="mr-1 h-3 w-3" />
                        Scheduled
                    </Badge>
                )
            case "ended":
                return (
                    <Badge variant="secondary">
                        <Square className="mr-1 h-3 w-3" />
                        Ended
                    </Badge>
                )
            case "cancelled":
                return (
                    <Badge variant="outline" className="text-muted-foreground">
                        Cancelled
                    </Badge>
                )
            default:
                return <Badge variant="outline">{status}</Badge>
        }
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

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Streams" }]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Live Streams</h1>
                        <p className="text-muted-foreground">
                            Manage your live streaming events across all channels
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                                >
                                    <Plus className="mr-2 h-4 w-4" />
                                    New Stream
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => router.push("/dashboard/streams/create")}>
                                    <Zap className="mr-2 h-4 w-4" />
                                    Quick Stream
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => router.push("/dashboard/streams/create-playlist")}>
                                    <Play className="mr-2 h-4 w-4" />
                                    Playlist Stream
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                {/* Filters and Search */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                            <div className="flex flex-1 gap-2">
                                <div className="relative flex-1 max-w-md">
                                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        placeholder="Search streams by title..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-9"
                                    />
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2">
                                <Select
                                    value={accountFilter}
                                    onValueChange={setAccountFilter}
                                >
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

                                <Select
                                    value={statusFilter}
                                    onValueChange={setStatusFilter}
                                >
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="All Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="live">Live</SelectItem>
                                        <SelectItem value="scheduled">Scheduled</SelectItem>
                                        <SelectItem value="ended">Ended</SelectItem>
                                        <SelectItem value="cancelled">Cancelled</SelectItem>
                                    </SelectContent>
                                </Select>

                                <div className="flex gap-1 border rounded-md">
                                    <Button
                                        variant={viewMode === "grid" ? "secondary" : "ghost"}
                                        size="icon"
                                        onClick={() => setViewMode("grid")}
                                        title="Grid View"
                                    >
                                        <Grid3x3 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant={viewMode === "calendar" ? "secondary" : "ghost"}
                                        size="icon"
                                        onClick={() => setViewMode("calendar")}
                                        title="Calendar View"
                                    >
                                        <Calendar className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Content */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[...Array(6)].map((_, i) => (
                            <Card key={i} className="border-0 shadow-lg">
                                <Skeleton className="aspect-video w-full" />
                                <CardContent className="p-4">
                                    <Skeleton className="h-4 w-3/4 mb-2" />
                                    <Skeleton className="h-3 w-1/2" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : filteredEvents.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <Radio className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No streams found</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchQuery || statusFilter !== "all" || accountFilter !== "all"
                                    ? "Try adjusting your filters"
                                    : "Create your first live stream to get started"}
                            </p>
                            <Button
                                className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                                onClick={() => router.push("/dashboard/streams/create")}
                            >
                                <Plus className="mr-2 h-4 w-4" />
                                Create Stream
                            </Button>
                        </CardContent>
                    </Card>
                ) : viewMode === "calendar" ? (
                    <CalendarView
                        events={filteredEvents}
                        onEventClick={(event) => router.push(`/dashboard/streams/${event.id}/control`)}
                    />
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredEvents.map((event) => (
                            <Card
                                key={event.id}
                                className="overflow-hidden border-0 shadow-lg hover:shadow-xl transition-shadow"
                            >
                                <div className="relative">
                                    <img
                                        src={event.thumbnail_url || "/placeholder-stream.jpg"}
                                        alt={event.title}
                                        className="w-full aspect-video object-cover cursor-pointer"
                                        onClick={() => router.push(`/dashboard/streams/${event.id}/control`)}
                                    />
                                    <div className="absolute top-2 left-2">
                                        {getStatusBadge(event.status)}
                                    </div>
                                    {event.status === "live" && event.viewer_count !== undefined && (
                                        <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                                            <Users className="h-3 w-3" />
                                            {event.viewer_count.toLocaleString()}
                                        </div>
                                    )}
                                </div>
                                <CardContent className="p-4">
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <h3
                                                className="font-semibold truncate cursor-pointer hover:text-primary"
                                                onClick={() => router.push(`/dashboard/streams/${event.id}/control`)}
                                            >
                                                {event.title}
                                            </h3>
                                            <p className="text-sm text-muted-foreground truncate">
                                                {getAccountName(event.account_id)}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {formatDate(event.scheduled_start)}
                                            </p>
                                        </div>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon">
                                                    <MoreVertical className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                {event.status === "scheduled" && (
                                                    <DropdownMenuItem onClick={() => handleStartStream(event.id)}>
                                                        <Play className="mr-2 h-4 w-4" />
                                                        Start Stream
                                                    </DropdownMenuItem>
                                                )}
                                                {event.status === "live" && (
                                                    <DropdownMenuItem onClick={() => handleStopStream(event.id)}>
                                                        <Square className="mr-2 h-4 w-4" />
                                                        Stop Stream
                                                    </DropdownMenuItem>
                                                )}
                                                <DropdownMenuItem
                                                    onClick={() => router.push(`/dashboard/streams/${event.id}/control`)}
                                                >
                                                    <Settings className="mr-2 h-4 w-4" />
                                                    Control Panel
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={() => router.push(`/dashboard/streams/${event.id}/simulcast`)}
                                                >
                                                    <Radio className="mr-2 h-4 w-4" />
                                                    Simulcast
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={() => router.push(`/dashboard/streams/${event.id}/health`)}
                                                >
                                                    <Activity className="mr-2 h-4 w-4" />
                                                    Health Monitor
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    onClick={() => router.push(`/dashboard/streams/${event.id}/edit`)}
                                                >
                                                    <Edit className="mr-2 h-4 w-4" />
                                                    Edit
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    className="text-destructive"
                                                    onClick={() => handleDeleteEvent(event.id)}
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
                {pagination.total > pagination.pageSize && (
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            Showing {(pagination.page - 1) * pagination.pageSize + 1} to{" "}
                            {Math.min(pagination.page * pagination.pageSize, pagination.total)} of{" "}
                            {pagination.total} streams
                        </p>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={pagination.page === 1}
                                onClick={() => setPagination((prev) => ({ ...prev, page: prev.page - 1 }))}
                            >
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={pagination.page * pagination.pageSize >= pagination.total}
                                onClick={() => setPagination((prev) => ({ ...prev, page: prev.page + 1 }))}
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
