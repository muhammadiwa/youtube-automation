"use client"

import { useState, useEffect, useCallback } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { ChannelCard } from "@/components/dashboard/channel-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { monitoringApi } from "@/lib/api"
import type { ChannelStatus, MonitoringFilters, MonitoringStats } from "@/lib/api/monitoring"
import {
    Search,
    Filter,
    RefreshCw,
    Radio,
    Calendar,
    WifiOff,
    AlertTriangle,
    Save,
    RotateCcw,
    Monitor,
    CheckCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface LayoutPreferences {
    autoRefresh: boolean
    refreshInterval: number
    filters: MonitoringFilters
}

const DEFAULT_PREFERENCES: LayoutPreferences = {
    autoRefresh: true,
    refreshInterval: 30,
    filters: { status: "all", healthStatus: "all", tokenStatus: "all" },
}

const STORAGE_KEY = "monitoring-layout-preferences"

function loadPreferences(): LayoutPreferences {
    if (typeof window === "undefined") return DEFAULT_PREFERENCES
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
            return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) }
        }
    } catch (e) {
        console.error("Failed to load preferences:", e)
    }
    return DEFAULT_PREFERENCES
}

function savePreferences(prefs: LayoutPreferences): void {
    if (typeof window === "undefined") return
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
    } catch (e) {
        console.error("Failed to save preferences:", e)
    }
}

export default function MonitoringPage() {
    const [channels, setChannels] = useState<ChannelStatus[]>([])
    const [stats, setStats] = useState<MonitoringStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const [preferences, setPreferences] = useState<LayoutPreferences>(DEFAULT_PREFERENCES)
    const [filterSheetOpen, setFilterSheetOpen] = useState(false)
    const [saveMessage, setSaveMessage] = useState<string | null>(null)

    useEffect(() => {
        const loaded = loadPreferences()
        setPreferences(loaded)
    }, [])

    const fetchData = useCallback(async () => {
        try {
            const [channelsData, statsData] = await Promise.all([
                monitoringApi.getChannelStatuses(preferences.filters),
                monitoringApi.getStats(),
            ])
            setChannels(channelsData)
            setStats(statsData)
        } catch (error) {
            console.error("Failed to fetch monitoring data:", error)
        }
    }, [preferences.filters])

    useEffect(() => {
        const loadData = async () => {
            setLoading(true)
            await fetchData()
            setLoading(false)
        }
        loadData()
    }, [fetchData])

    useEffect(() => {
        if (!preferences.autoRefresh) return
        const interval = setInterval(async () => {
            setRefreshing(true)
            await fetchData()
            setRefreshing(false)
        }, preferences.refreshInterval * 1000)
        return () => clearInterval(interval)
    }, [preferences.autoRefresh, preferences.refreshInterval, fetchData])

    const handleRefresh = async () => {
        setRefreshing(true)
        await fetchData()
        setRefreshing(false)
    }

    const handleRefreshChannel = async (accountId: string) => {
        try {
            const updated = await monitoringApi.refreshChannel(accountId)
            setChannels((prev) =>
                prev.map((ch) => (ch.accountId === accountId ? updated : ch))
            )
        } catch (error) {
            console.error("Failed to refresh channel:", error)
        }
    }

    const handleQuickAction = (accountId: string, action: string) => {
        const channel = channels.find((ch) => ch.accountId === accountId)
        if (!channel) return
        if (action === "view") {
            window.open(`https://youtube.com/channel/${channel.account.channelId}`, "_blank")
        }
    }

    const updateFilters = (newFilters: Partial<MonitoringFilters>) => {
        setPreferences((prev) => ({
            ...prev,
            filters: { ...prev.filters, ...newFilters },
        }))
    }

    const handleSaveLayout = () => {
        savePreferences(preferences)
        setSaveMessage("Saved!")
        setTimeout(() => setSaveMessage(null), 2000)
    }

    const handleResetLayout = () => {
        setPreferences(DEFAULT_PREFERENCES)
        savePreferences(DEFAULT_PREFERENCES)
        setSaveMessage("Reset!")
        setTimeout(() => setSaveMessage(null), 2000)
    }

    const filteredChannels = channels.filter((channel) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            channel.account.channelTitle.toLowerCase().includes(query) ||
            channel.currentStreamTitle?.toLowerCase().includes(query)
        )
    })

    const sortedChannels = [...filteredChannels].sort((a, b) => {
        if (a.healthStatus === "critical" && b.healthStatus !== "critical") return -1
        if (b.healthStatus === "critical" && a.healthStatus !== "critical") return 1
        if (a.streamStatus === "live" && b.streamStatus !== "live") return -1
        if (b.streamStatus === "live" && a.streamStatus !== "live") return 1
        return b.alertCount - a.alertCount
    })

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Monitoring" },
            ]}
        >
            <div className="space-y-4">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Monitor className="h-6 w-6" />
                            Channel Monitoring
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Real-time status of your YouTube channels
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {saveMessage && (
                            <Badge variant="secondary" className="text-xs">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {saveMessage}
                            </Badge>
                        )}
                        <Button variant="outline" size="sm" onClick={handleSaveLayout}>
                            <Save className="h-4 w-4 sm:mr-1" />
                            <span className="hidden sm:inline">Save</span>
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleResetLayout}>
                            <RotateCcw className="h-4 w-4 sm:mr-1" />
                            <span className="hidden sm:inline">Reset</span>
                        </Button>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={handleRefresh}
                            disabled={refreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                        </Button>
                    </div>
                </div>

                {/* Stats Overview */}
                {stats && (
                    <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                        <Card className="col-span-1">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold">{stats.totalChannels}</p>
                                <p className="text-[10px] text-muted-foreground">Total</p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-red-600">{stats.liveChannels}</p>
                                <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5">
                                    <Radio className="h-2.5 w-2.5" /> Live
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-blue-50 dark:bg-blue-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-blue-600">{stats.scheduledChannels}</p>
                                <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5">
                                    <Calendar className="h-2.5 w-2.5" /> Sched
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-gray-500">{stats.offlineChannels}</p>
                                <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5">
                                    <WifiOff className="h-2.5 w-2.5" /> Off
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-red-600">{stats.errorChannels}</p>
                                <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5">
                                    <AlertTriangle className="h-2.5 w-2.5" /> Err
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-green-50 dark:bg-green-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-green-600">{stats.healthyChannels}</p>
                                <p className="text-[10px] text-muted-foreground">OK</p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-yellow-50 dark:bg-yellow-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-yellow-600">{stats.warningChannels}</p>
                                <p className="text-[10px] text-muted-foreground">Warn</p>
                            </CardContent>
                        </Card>
                        <Card className="col-span-1 bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-2 text-center">
                                <p className="text-lg font-bold text-red-600">{stats.criticalChannels}</p>
                                <p className="text-[10px] text-muted-foreground">Crit</p>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Search and Filters */}
                <div className="flex flex-col sm:flex-row gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search channels..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9"
                        />
                    </div>
                    <Sheet open={filterSheetOpen} onOpenChange={setFilterSheetOpen}>
                        <SheetTrigger asChild>
                            <Button variant="outline" size="icon">
                                <Filter className="h-4 w-4" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent>
                            <SheetHeader>
                                <SheetTitle>Filters</SheetTitle>
                            </SheetHeader>
                            <div className="space-y-4 mt-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Stream Status</label>
                                    <Select
                                        value={preferences.filters.status}
                                        onValueChange={(value) => updateFilters({ status: value as MonitoringFilters["status"] })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All</SelectItem>
                                            <SelectItem value="live">Live</SelectItem>
                                            <SelectItem value="scheduled">Scheduled</SelectItem>
                                            <SelectItem value="offline">Offline</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Health Status</label>
                                    <Select
                                        value={preferences.filters.healthStatus}
                                        onValueChange={(value) => updateFilters({ healthStatus: value as MonitoringFilters["healthStatus"] })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All</SelectItem>
                                            <SelectItem value="healthy">Healthy</SelectItem>
                                            <SelectItem value="warning">Warning</SelectItem>
                                            <SelectItem value="critical">Critical</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Token Status</label>
                                    <Select
                                        value={preferences.filters.tokenStatus}
                                        onValueChange={(value) => updateFilters({ tokenStatus: value as MonitoringFilters["tokenStatus"] })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All</SelectItem>
                                            <SelectItem value="valid">Valid</SelectItem>
                                            <SelectItem value="expiring">Expiring Soon</SelectItem>
                                            <SelectItem value="expired">Expired</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>

                {/* Channel List */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[...Array(6)].map((_, i) => (
                            <Skeleton key={i} className="h-48" />
                        ))}
                    </div>
                ) : sortedChannels.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <Monitor className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No channels found</h3>
                            <p className="text-muted-foreground">
                                {searchQuery
                                    ? "Try adjusting your search query"
                                    : "Connect your YouTube accounts to start monitoring"}
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {sortedChannels.map((channel) => (
                            <ChannelCard
                                key={channel.accountId}
                                channel={channel}
                                onRefresh={() => handleRefreshChannel(channel.accountId)}
                                onQuickAction={(action) => handleQuickAction(channel.accountId, action)}
                            />
                        ))}
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}
