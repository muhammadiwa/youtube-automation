"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
    Users,
    Search,
    Filter,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    Loader2,
    Eye,
    MoreHorizontal,
    UserX,
    UserCheck,
    KeyRound,
    UserCog,
    TrendingUp,
    UserPlus,
    ShieldAlert,
    CalendarDays,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { UserSummary, UserFilters, UserStatus } from "@/types/admin"

const statusConfig: Record<UserStatus, { color: string; bg: string; icon: React.ReactNode }> = {
    active: {
        color: "text-emerald-600 dark:text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        icon: <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />,
    },
    suspended: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        icon: <ShieldAlert className="h-3 w-3" />,
    },
    pending: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        icon: <div className="h-2 w-2 rounded-full bg-amber-500" />,
    },
}

const statusLabels: Record<UserStatus, string> = {
    active: "Active",
    suspended: "Suspended",
    pending: "Pending",
}

// Stats Card Component with fixed height
function StatsCard({
    title,
    value,
    icon: Icon,
    trend,
    gradient,
    delay = 0,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    trend?: { value: number; isPositive: boolean }
    gradient: string
    delay?: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay }}
            className="h-full"
        >
            <Card className="relative overflow-hidden border border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-all duration-300 group bg-white dark:bg-slate-900 h-full">
                <div className={cn("absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity bg-gradient-to-br", gradient)} />
                <CardContent className="p-5 h-full flex flex-col justify-between min-h-[120px]">
                    <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                            <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
                        </div>
                        <div className={cn(
                            "flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm flex-shrink-0",
                            gradient
                        )}>
                            <Icon className="h-5 w-5 text-white" />
                        </div>
                    </div>
                    <div className="mt-2">
                        {trend ? (
                            <div className={cn(
                                "flex items-center gap-1 text-xs font-medium",
                                trend.isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400"
                            )}>
                                <TrendingUp className={cn("h-3 w-3", !trend.isPositive && "rotate-180")} />
                                {trend.value}% from last month
                            </div>
                        ) : (
                            <div className="h-4" />
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

export default function AdminUsersPage() {
    const router = useRouter()
    const [users, setUsers] = useState<UserSummary[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(10)
    const [totalPages, setTotalPages] = useState(0)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filters
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [planFilter, setPlanFilter] = useState<string>("all")
    const [registeredAfter, setRegisteredAfter] = useState<Date | undefined>()
    const [registeredBefore, setRegisteredBefore] = useState<Date | undefined>()
    const [showFilters, setShowFilters] = useState(false)

    // Stats
    const [stats, setStats] = useState({
        total: 0,
        active: 0,
        suspended: 0,
        newThisMonth: 0,
    })

    const fetchStats = useCallback(async () => {
        try {
            const statsResponse = await adminApi.getUserStats()
            setStats({
                total: statsResponse.total,
                active: statsResponse.active,
                suspended: statsResponse.suspended,
                newThisMonth: statsResponse.new_this_month,
            })
        } catch (err) {
            console.error("Failed to fetch user stats:", err)
        }
    }, [])

    const fetchUsers = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const filters: UserFilters = {}
            if (search) filters.search = search
            if (statusFilter && statusFilter !== "all") filters.status = statusFilter as UserStatus
            if (planFilter && planFilter !== "all") filters.plan = planFilter
            if (registeredAfter) filters.registered_after = registeredAfter.toISOString()
            if (registeredBefore) filters.registered_before = registeredBefore.toISOString()

            const response = await adminApi.getUsers({
                page,
                page_size: pageSize,
                filters,
            })
            setUsers(response.items)
            setTotal(response.total)
            setTotalPages(response.total_pages)
        } catch (err) {
            console.error("Failed to fetch users:", err)
            setError("Failed to load users. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [page, pageSize, search, statusFilter, planFilter, registeredAfter, registeredBefore])

    useEffect(() => {
        fetchUsers()
    }, [fetchUsers])

    useEffect(() => {
        fetchStats()
    }, [fetchStats])

    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1)
        }, 300)
        return () => clearTimeout(timer)
    }, [search])

    const handleViewUser = (userId: string) => {
        router.push(`/admin/users/${userId}`)
    }

    const clearFilters = () => {
        setSearch("")
        setStatusFilter("all")
        setPlanFilter("all")
        setRegisteredAfter(undefined)
        setRegisteredBefore(undefined)
        setPage(1)
    }

    const hasActiveFilters = search || statusFilter !== "all" || planFilter !== "all" || registeredAfter || registeredBefore

    return (
        <AdminLayout breadcrumbs={[{ label: "Users" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            User Management
                        </h1>
                        <p className="text-muted-foreground">
                            Manage platform users, subscriptions, and access controls
                        </p>
                    </div>
                </motion.div>

                {/* Stats Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <StatsCard
                        title="Total Users"
                        value={stats.total.toLocaleString()}
                        icon={Users}
                        trend={{ value: 12.5, isPositive: true }}
                        gradient="from-blue-500 to-blue-600"
                        delay={0}
                    />
                    <StatsCard
                        title="Active Users"
                        value={stats.active.toLocaleString()}
                        icon={UserCheck}
                        trend={{ value: 8.2, isPositive: true }}
                        gradient="from-emerald-500 to-emerald-600"
                        delay={0.05}
                    />
                    <StatsCard
                        title="Suspended"
                        value={stats.suspended.toLocaleString()}
                        icon={UserX}
                        trend={{ value: 2.1, isPositive: false }}
                        gradient="from-red-500 to-red-600"
                        delay={0.1}
                    />
                    <StatsCard
                        title="New This Month"
                        value={stats.newThisMonth.toLocaleString()}
                        icon={UserPlus}
                        trend={{ value: 15.3, isPositive: true }}
                        gradient="from-violet-500 to-violet-600"
                        delay={0.15}
                    />
                </div>

                {/* Search and Filters */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardContent className="p-6">
                            <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
                                {/* Search */}
                                <div className="relative flex-1">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by email, name, or ID..."
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        className="pl-12 h-12 text-base bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500/20"
                                    />
                                </div>

                                {/* Quick Filters */}
                                <div className="flex items-center gap-3 flex-wrap">
                                    <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[150px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="active">Active</SelectItem>
                                            <SelectItem value="suspended">Suspended</SelectItem>
                                            <SelectItem value="pending">Pending</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    <Select value={planFilter} onValueChange={(v) => { setPlanFilter(v); setPage(1) }}>
                                        <SelectTrigger className="w-[150px] h-12 rounded-xl bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
                                            <SelectValue placeholder="Plan" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Plans</SelectItem>
                                            <SelectItem value="free">Free</SelectItem>
                                            <SelectItem value="starter">Starter</SelectItem>
                                            <SelectItem value="professional">Professional</SelectItem>
                                            <SelectItem value="enterprise">Enterprise</SelectItem>
                                        </SelectContent>
                                    </Select>

                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => setShowFilters(!showFilters)}
                                        className={cn(
                                            "h-12 px-4 rounded-xl border-slate-200 dark:border-slate-700",
                                            showFilters && "bg-blue-50 dark:bg-blue-900/20 border-blue-500/50"
                                        )}
                                    >
                                        <Filter className="h-5 w-5 mr-2" />
                                        More Filters
                                    </Button>

                                    {hasActiveFilters && (
                                        <Button
                                            variant="ghost"
                                            size="lg"
                                            onClick={clearFilters}
                                            className="h-12 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                                        >
                                            Clear All
                                        </Button>
                                    )}
                                </div>
                            </div>

                            {/* Advanced Filters */}
                            {showFilters && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700 flex flex-wrap gap-6"
                                >
                                    <div className="flex items-center gap-3">
                                        <CalendarDays className="h-5 w-5 text-muted-foreground" />
                                        <span className="text-sm font-medium">Registered after:</span>
                                        <Popover>
                                            <PopoverTrigger asChild>
                                                <Button variant="outline" className="h-10 rounded-xl">
                                                    {registeredAfter ? format(registeredAfter, "PP") : "Select date"}
                                                </Button>
                                            </PopoverTrigger>
                                            <PopoverContent className="w-auto p-0" align="start">
                                                <Calendar
                                                    mode="single"
                                                    selected={registeredAfter}
                                                    onSelect={(d: Date | undefined) => { setRegisteredAfter(d); setPage(1) }}
                                                    initialFocus
                                                />
                                            </PopoverContent>
                                        </Popover>
                                        {registeredAfter && (
                                            <Button variant="ghost" size="sm" onClick={() => setRegisteredAfter(undefined)} className="h-8 w-8 p-0">×</Button>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <CalendarDays className="h-5 w-5 text-muted-foreground" />
                                        <span className="text-sm font-medium">Registered before:</span>
                                        <Popover>
                                            <PopoverTrigger asChild>
                                                <Button variant="outline" className="h-10 rounded-xl">
                                                    {registeredBefore ? format(registeredBefore, "PP") : "Select date"}
                                                </Button>
                                            </PopoverTrigger>
                                            <PopoverContent className="w-auto p-0" align="start">
                                                <Calendar
                                                    mode="single"
                                                    selected={registeredBefore}
                                                    onSelect={(d: Date | undefined) => { setRegisteredBefore(d); setPage(1) }}
                                                    initialFocus
                                                />
                                            </PopoverContent>
                                        </Popover>
                                        {registeredBefore && (
                                            <Button variant="ghost" size="sm" onClick={() => setRegisteredBefore(undefined)} className="h-8 w-8 p-0">×</Button>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Users Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900 overflow-hidden">
                        <CardContent className="p-0">
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-20">
                                    <div className="relative">
                                        <div className="h-16 w-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
                                        <Users className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-blue-500" />
                                    </div>
                                    <p className="mt-4 text-muted-foreground">Loading users...</p>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                                        <AlertCircle className="h-8 w-8 text-red-500" />
                                    </div>
                                    <p className="text-lg font-medium text-red-500 mb-2">Failed to load users</p>
                                    <p className="text-muted-foreground mb-4">{error}</p>
                                    <Button onClick={fetchUsers} className="rounded-xl">
                                        Try Again
                                    </Button>
                                </div>
                            ) : users.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <div className="h-20 w-20 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                                        <Users className="h-10 w-10 text-muted-foreground" />
                                    </div>
                                    <p className="text-lg font-medium mb-2">No users found</p>
                                    <p className="text-muted-foreground mb-4">Try adjusting your search or filters</p>
                                    {hasActiveFilters && (
                                        <Button variant="outline" onClick={clearFilters} className="rounded-xl">
                                            Clear Filters
                                        </Button>
                                    )}
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-slate-50/50 dark:bg-slate-800/50 hover:bg-slate-50/50 dark:hover:bg-slate-800/50">
                                                <TableHead className="font-semibold">User</TableHead>
                                                <TableHead className="font-semibold">Status</TableHead>
                                                <TableHead className="font-semibold">Plan</TableHead>
                                                <TableHead className="font-semibold">Warnings</TableHead>
                                                <TableHead className="font-semibold">Registered</TableHead>
                                                <TableHead className="font-semibold">Last Active</TableHead>
                                                <TableHead className="w-[70px]"></TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {users.map((user, index) => (
                                                <motion.tr
                                                    key={user.id}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: index * 0.05 }}
                                                    className="group cursor-pointer hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors"
                                                    onClick={() => handleViewUser(user.id)}
                                                >
                                                    <TableCell>
                                                        <div className="flex items-center gap-4">
                                                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold text-sm shadow-lg shadow-blue-500/20">
                                                                {user.name.charAt(0).toUpperCase()}
                                                            </div>
                                                            <div>
                                                                <p className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                                                    {user.name}
                                                                </p>
                                                                <p className="text-sm text-muted-foreground">{user.email}</p>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge
                                                            variant="outline"
                                                            className={cn(
                                                                "gap-1.5 font-medium rounded-lg px-3 py-1",
                                                                statusConfig[user.status].bg,
                                                                statusConfig[user.status].color
                                                            )}
                                                        >
                                                            {statusConfig[user.status].icon}
                                                            {statusLabels[user.status]}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="secondary" className="capitalize rounded-lg font-medium">
                                                            {user.plan_name || "Free"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        {user.warning_count > 0 ? (
                                                            <Badge variant="destructive" className="rounded-lg font-semibold">
                                                                {user.warning_count} warning{user.warning_count > 1 ? "s" : ""}
                                                            </Badge>
                                                        ) : (
                                                            <span className="text-muted-foreground text-sm">None</span>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {format(new Date(user.created_at), "MMM d, yyyy")}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {user.last_login_at
                                                            ? formatDistanceToNow(new Date(user.last_login_at), { addSuffix: true })
                                                            : "Never"}
                                                    </TableCell>
                                                    <TableCell>
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                                                <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <MoreHorizontal className="h-5 w-5" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="w-48 rounded-xl p-2">
                                                                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewUser(user.id) }} className="rounded-lg cursor-pointer">
                                                                    <Eye className="h-4 w-4 mr-3" />
                                                                    View Details
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                {user.status === "suspended" ? (
                                                                    <DropdownMenuItem onClick={(e) => e.stopPropagation()} className="rounded-lg cursor-pointer text-emerald-600">
                                                                        <UserCheck className="h-4 w-4 mr-3" />
                                                                        Activate User
                                                                    </DropdownMenuItem>
                                                                ) : (
                                                                    <DropdownMenuItem onClick={(e) => e.stopPropagation()} className="rounded-lg cursor-pointer text-red-600">
                                                                        <UserX className="h-4 w-4 mr-3" />
                                                                        Suspend User
                                                                    </DropdownMenuItem>
                                                                )}
                                                                <DropdownMenuItem onClick={(e) => e.stopPropagation()} className="rounded-lg cursor-pointer">
                                                                    <KeyRound className="h-4 w-4 mr-3" />
                                                                    Reset Password
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={(e) => e.stopPropagation()} className="rounded-lg cursor-pointer text-purple-600">
                                                                    <UserCog className="h-4 w-4 mr-3" />
                                                                    Impersonate
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </TableCell>
                                                </motion.tr>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}

                            {/* Pagination */}
                            {!isLoading && !error && users.length > 0 && (
                                <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30">
                                    <p className="text-sm text-muted-foreground">
                                        Showing <span className="font-semibold text-foreground">{(page - 1) * pageSize + 1}</span> to{" "}
                                        <span className="font-semibold text-foreground">{Math.min(page * pageSize, total)}</span> of{" "}
                                        <span className="font-semibold text-foreground">{total}</span> users
                                    </p>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                            className="h-9 rounded-lg"
                                        >
                                            <ChevronLeft className="h-4 w-4 mr-1" />
                                            Previous
                                        </Button>
                                        <div className="flex items-center gap-1">
                                            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                const pageNum = i + 1
                                                return (
                                                    <Button
                                                        key={pageNum}
                                                        variant={page === pageNum ? "default" : "ghost"}
                                                        size="sm"
                                                        onClick={() => setPage(pageNum)}
                                                        className={cn(
                                                            "h-9 w-9 rounded-lg",
                                                            page === pageNum && "bg-blue-500 hover:bg-blue-600"
                                                        )}
                                                    >
                                                        {pageNum}
                                                    </Button>
                                                )
                                            })}
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                            disabled={page === totalPages}
                                            className="h-9 rounded-lg"
                                        >
                                            Next
                                            <ChevronRight className="h-4 w-4 ml-1" />
                                        </Button>
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
