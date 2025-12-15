"use client"

import { useState, useEffect, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { AccountCard } from "@/components/dashboard/account-card"
import { ConnectAccountModal } from "@/components/dashboard/connect-account-modal"
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { accountsApi } from "@/lib/api"
import { YouTubeAccount } from "@/types"
import {
    Plus,
    Search,
    LayoutGrid,
    List,
    Youtube,
    AlertCircle,
    X,
    Users,
    Video,
    CheckCircle,
    Clock,
    AlertTriangle,
    ChevronLeft,
    ChevronRight,
    ChevronsLeft,
    ChevronsRight,
    RefreshCw,
    SlidersHorizontal
} from "lucide-react"

const ITEMS_PER_PAGE_OPTIONS = [12, 24, 48, 96]

export default function AccountsPage() {
    const searchParams = useSearchParams()
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [view, setView] = useState<"grid" | "list">("grid")
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [connectModalOpen, setConnectModalOpen] = useState(false)
    const [errorMessage, setErrorMessage] = useState<string | null>(null)
    const [currentPage, setCurrentPage] = useState(1)
    const [itemsPerPage, setItemsPerPage] = useState(12)
    const [refreshing, setRefreshing] = useState(false)

    useEffect(() => {
        const error = searchParams.get("error")
        if (error) {
            setErrorMessage(decodeURIComponent(error))
            window.history.replaceState({}, "", "/dashboard/accounts")
        }
        loadAccounts()
    }, [searchParams])

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1)
    }, [searchQuery, statusFilter, itemsPerPage])

    const loadAccounts = async () => {
        try {
            setLoading(true)
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
            setAccounts([])
        } finally {
            setLoading(false)
        }
    }

    const handleRefresh = async () => {
        setRefreshing(true)
        await loadAccounts()
        setRefreshing(false)
    }

    // Filter and paginate accounts
    const { filteredAccounts, paginatedAccounts, totalPages, stats } = useMemo(() => {
        let filtered = [...accounts]

        // Filter by status
        if (statusFilter !== "all") {
            filtered = filtered.filter((account) => account.status === statusFilter)
        }

        // Filter by search query
        if (searchQuery) {
            const query = searchQuery.toLowerCase()
            filtered = filtered.filter((account) =>
                (account.channelTitle || "").toLowerCase().includes(query)
            )
        }

        // Calculate stats
        const stats = {
            total: accounts.length,
            active: accounts.filter(a => a.status === "active").length,
            expired: accounts.filter(a => a.status === "expired").length,
            error: accounts.filter(a => a.status === "error").length,
            totalSubscribers: accounts.reduce((sum, a) => sum + (a.subscriberCount || 0), 0),
            totalVideos: accounts.reduce((sum, a) => sum + (a.videoCount || 0), 0),
        }

        // Pagination
        const totalPages = Math.ceil(filtered.length / itemsPerPage)
        const startIndex = (currentPage - 1) * itemsPerPage
        const paginatedAccounts = filtered.slice(startIndex, startIndex + itemsPerPage)

        return { filteredAccounts: filtered, paginatedAccounts, totalPages, stats }
    }, [accounts, searchQuery, statusFilter, currentPage, itemsPerPage])

    const handlePageChange = (page: number) => {
        setCurrentPage(Math.max(1, Math.min(page, totalPages)))
        window.scrollTo({ top: 0, behavior: "smooth" })
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + "M"
        if (num >= 1000) return (num / 1000).toFixed(1) + "K"
        return num.toString()
    }

    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Accounts" }]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">YouTube Accounts</h1>
                        <p className="text-muted-foreground mt-1">
                            Manage and monitor your connected YouTube channels
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={handleRefresh}
                            disabled={refreshing}
                        >
                            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
                        </Button>
                        <Button
                            onClick={() => setConnectModalOpen(true)}
                            size="lg"
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                        >
                            <Plus className="mr-2 h-4 w-4" />
                            Connect Account
                        </Button>
                    </div>
                </div>

                {/* Stats Cards */}
                {!loading && accounts.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 border-slate-200 dark:border-slate-700">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-slate-500/10">
                                        <Youtube className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{stats.total}</p>
                                        <p className="text-xs text-muted-foreground">Total Accounts</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950 dark:to-emerald-900 border-emerald-200 dark:border-emerald-800">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-emerald-500/10">
                                        <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{stats.active}</p>
                                        <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70">Active</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-950 dark:to-amber-900 border-amber-200 dark:border-amber-800">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-amber-500/10">
                                        <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">{stats.expired}</p>
                                        <p className="text-xs text-amber-600/70 dark:text-amber-400/70">Expired</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 border-red-200 dark:border-red-800">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-red-500/10">
                                        <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-red-700 dark:text-red-300">{stats.error}</p>
                                        <p className="text-xs text-red-600/70 dark:text-red-400/70">Errors</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border-blue-200 dark:border-blue-800">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/10">
                                        <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{formatNumber(stats.totalSubscribers)}</p>
                                        <p className="text-xs text-blue-600/70 dark:text-blue-400/70">Subscribers</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border-purple-200 dark:border-purple-800">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/10">
                                        <Video className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{formatNumber(stats.totalVideos)}</p>
                                        <p className="text-xs text-purple-600/70 dark:text-purple-400/70">Videos</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Filters */}
                <Card>
                    <CardContent className="p-4">
                        <div className="flex flex-col lg:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search by channel name..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                            <div className="flex flex-wrap items-center gap-3">
                                <Select value={statusFilter} onValueChange={setStatusFilter}>
                                    <SelectTrigger className="w-[160px]">
                                        <SlidersHorizontal className="h-4 w-4 mr-2" />
                                        <SelectValue placeholder="Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="active">
                                            <div className="flex items-center gap-2">
                                                <div className="h-2 w-2 rounded-full bg-emerald-500" />
                                                Active
                                            </div>
                                        </SelectItem>
                                        <SelectItem value="expired">
                                            <div className="flex items-center gap-2">
                                                <div className="h-2 w-2 rounded-full bg-amber-500" />
                                                Expired
                                            </div>
                                        </SelectItem>
                                        <SelectItem value="error">
                                            <div className="flex items-center gap-2">
                                                <div className="h-2 w-2 rounded-full bg-red-500" />
                                                Error
                                            </div>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>
                                <Select value={itemsPerPage.toString()} onValueChange={(v) => setItemsPerPage(Number(v))}>
                                    <SelectTrigger className="w-[130px]">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {ITEMS_PER_PAGE_OPTIONS.map((option) => (
                                            <SelectItem key={option} value={option.toString()}>
                                                {option} per page
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <ToggleGroup
                                    type="single"
                                    value={view}
                                    onValueChange={(v) => v && setView(v as "grid" | "list")}
                                    className="bg-muted rounded-lg p-1"
                                >
                                    <ToggleGroupItem value="grid" aria-label="Grid view" className="px-3">
                                        <LayoutGrid className="h-4 w-4" />
                                    </ToggleGroupItem>
                                    <ToggleGroupItem value="list" aria-label="List view" className="px-3">
                                        <List className="h-4 w-4" />
                                    </ToggleGroupItem>
                                </ToggleGroup>
                            </div>
                        </div>
                        {(searchQuery || statusFilter !== "all") && (
                            <div className="flex items-center gap-2 mt-3 pt-3 border-t">
                                <span className="text-sm text-muted-foreground">Filters:</span>
                                {searchQuery && (
                                    <Badge variant="secondary" className="gap-1">
                                        Search: {searchQuery}
                                        <button onClick={() => setSearchQuery("")} className="ml-1 hover:text-destructive">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </Badge>
                                )}
                                {statusFilter !== "all" && (
                                    <Badge variant="secondary" className="gap-1">
                                        Status: {statusFilter}
                                        <button onClick={() => setStatusFilter("all")} className="ml-1 hover:text-destructive">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </Badge>
                                )}
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => { setSearchQuery(""); setStatusFilter("all"); }}
                                    className="text-xs"
                                >
                                    Clear all
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Error Alert */}
                {errorMessage && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Connection Failed</AlertTitle>
                        <AlertDescription className="flex items-center justify-between">
                            <span>{errorMessage}</span>
                            <Button variant="ghost" size="sm" onClick={() => setErrorMessage(null)}>
                                <X className="h-4 w-4" />
                            </Button>
                        </AlertDescription>
                    </Alert>
                )}

                {/* Accounts Grid/List */}
                {loading ? (
                    <div className={view === "grid"
                        ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                        : "space-y-4"
                    }>
                        {Array.from({ length: itemsPerPage > 12 ? 12 : itemsPerPage }).map((_, i) => (
                            <Skeleton key={i} className={view === "grid" ? "h-72 rounded-xl" : "h-24 rounded-xl"} />
                        ))}
                    </div>
                ) : paginatedAccounts.length === 0 ? (
                    <Card className="border-dashed">
                        <CardContent className="py-16">
                            <div className="text-center">
                                <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                                    <Youtube className="h-8 w-8 text-muted-foreground" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">
                                    {accounts.length === 0 ? "No accounts connected" : "No accounts found"}
                                </h3>
                                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                                    {accounts.length === 0
                                        ? "Connect your first YouTube account to start managing your channels, videos, and analytics."
                                        : "Try adjusting your search or filters to find what you're looking for."}
                                </p>
                                {accounts.length === 0 ? (
                                    <Button
                                        onClick={() => setConnectModalOpen(true)}
                                        size="lg"
                                        className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                                    >
                                        <Plus className="mr-2 h-4 w-4" />
                                        Connect Your First Account
                                    </Button>
                                ) : (
                                    <Button variant="outline" onClick={() => { setSearchQuery(""); setStatusFilter("all"); }}>
                                        Clear Filters
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        <div className={view === "grid"
                            ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                            : "space-y-4"
                        }>
                            {paginatedAccounts.map((account) => (
                                <AccountCard
                                    key={account.id}
                                    account={account}
                                    view={view}
                                    onRefresh={async (id) => {
                                        try {
                                            await accountsApi.refreshToken(id)
                                            await loadAccounts()
                                        } catch (e) {
                                            console.error("Failed to refresh token:", e)
                                        }
                                    }}
                                    onDisconnect={async (id) => {
                                        if (confirm("Are you sure you want to disconnect this account?")) {
                                            try {
                                                await accountsApi.disconnectAccount(id)
                                                await loadAccounts()
                                            } catch (e) {
                                                console.error("Failed to disconnect:", e)
                                            }
                                        }
                                    }}
                                />
                            ))}
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <Card>
                                <CardContent className="p-4">
                                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                                        <p className="text-sm text-muted-foreground">
                                            Showing <span className="font-medium">{((currentPage - 1) * itemsPerPage) + 1}</span> to{" "}
                                            <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredAccounts.length)}</span> of{" "}
                                            <span className="font-medium">{filteredAccounts.length}</span> accounts
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => handlePageChange(1)}
                                                disabled={currentPage === 1}
                                            >
                                                <ChevronsLeft className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => handlePageChange(currentPage - 1)}
                                                disabled={currentPage === 1}
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                            </Button>

                                            <div className="flex items-center gap-1">
                                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                    let pageNum: number
                                                    if (totalPages <= 5) {
                                                        pageNum = i + 1
                                                    } else if (currentPage <= 3) {
                                                        pageNum = i + 1
                                                    } else if (currentPage >= totalPages - 2) {
                                                        pageNum = totalPages - 4 + i
                                                    } else {
                                                        pageNum = currentPage - 2 + i
                                                    }
                                                    return (
                                                        <Button
                                                            key={pageNum}
                                                            variant={currentPage === pageNum ? "default" : "outline"}
                                                            size="icon"
                                                            onClick={() => handlePageChange(pageNum)}
                                                            className="w-10"
                                                        >
                                                            {pageNum}
                                                        </Button>
                                                    )
                                                })}
                                            </div>

                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => handlePageChange(currentPage + 1)}
                                                disabled={currentPage === totalPages}
                                            >
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => handlePageChange(totalPages)}
                                                disabled={currentPage === totalPages}
                                            >
                                                <ChevronsRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </>
                )}

                <ConnectAccountModal open={connectModalOpen} onOpenChange={setConnectModalOpen} />
            </div>
        </DashboardLayout>
    )
}
