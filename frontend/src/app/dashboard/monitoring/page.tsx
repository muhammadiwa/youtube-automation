"use client"

import { useState, useEffect, useCallback } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { ChannelTile } from "@/components/dashboard/channel-tile"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
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
import { Slider } from "@/components/ui/slider"
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
    Activity,
    Grid3x3,
    LayoutGrid,
    Save,
    RotateCcw,
    Monitor,
    CheckCircle,
    XCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

type GridSize = "small" | "medium" | "large"

interface LayoutPreferences {
    gridSize: GridSize
    autoRefresh: boolean
    refreshInterval: number
    filters: MonitoringFilters
}

const DEFAULT_PREFERENCES: LayoutPreferences = {
    gridSize: "medium",
    autoRefresh: true,
    refreshInterval: 30,
    filters: { status: "all", healthStatus: "all", tokenStatus: "all" },
}

const STORAGE_KEY = "monitoring-layout-preferences"

// Load preferences from localStorage
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

// Save preferences to localStorage
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
    const [expandedChannel, setExpandedChannel] = useState<string | null>(null)
    const [searchQuery, setSearchQuery] = useState("")
    const [preferences, setPreferences] = useState<LayoutPreferences>(DEFAULT_PREFERENCES)
    const [filterSheetOpen, setFilterSheetOpen] = useState(false)
    const [saveMessage, setSaveMessage] = useState<string | null>(null)

    // Load preferences on mount
    useEffect(() => {
        const loaded = loadPreferences()
        setPreferences(loaded)
    }, [])

    // Fetch data
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

    // Initial load
    useEffect(() => {
        const loadData = async () => {
            setLoading(true)
            await fetchData()
            setLoading(false)
        }
        loadData()
    }, [fetchData])

    // Auto-refresh
    useEffect(() => {
        if (!preferences.autoRefresh) return

        const interval = setInterval(async () => {
            setRefreshing(true)
            await fetchData()
            setRefreshing(false)
        }, preferences.refreshInterval * 1000)

        return () => clearInterval(interval)
    }, [preferences.autoRefresh, preferences.refreshInterval, fetchData])

    // Manual refresh
    const handleRefresh = async () => {
        setRefreshing(true)
        await fetchData()
        setRefreshing(false)
    }

    // Refresh single channel
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

    // Handle quick actions
    const handleQuickAction = (accountId: string, action: string) => {
        const channel = channels.find((ch) => ch.accountId === accountId)
        if (!channel) return

        switch (action) {
            case "view":
                window.open(`https://youtube.com/channel/${channel.account.channelId}`, "_blank")
                break
            case "start":
            case "stop":
                // These would trigger stream start/stop via API
                console.log(`${action} stream for channel ${accountId}`)
                break
        }
    }

    // Update filters
    const updateFilters = (newFilters: Partial<MonitoringFilters>) => {
        setPreferences((prev) => ({
            ...prev,
            filters: { ...prev.filters, ...newFilters },
        }))
    }

    // Save layout preferences
    const handleSaveLayout = () => {
        savePreferences(preferences)
        setSaveMessage("Layout saved!")
        setTimeout(() => setSaveMessage(null), 2000)
    }

    // Reset to defaults
    const handleResetLayout = () => {
        setPreferences(DEFAULT_PREFERENCES)
        savePreferences(DEFAULT_PREFERENCES)
        setSaveMessage("Reset to defaults!")
        setTimeout(() => setSaveMessage(null), 2000)
    }

    // Filter channels by search
    const filteredChannels = channels.filter((channel) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            channel.account.channelTitle.toLowerCase().includes(query) ||
            channel.currentStreamTitle?.toLowerCase().includes(query)
        )
    })

    // Sort channels: critical first, then live, then by alerts
    const sortedChannels = [...filteredChannels].sort((a, b) => {
        // Critical issues first
        if (a.healthStatus === "critical" && b.healthStatus !== "critical") return -1
        if (b.healthStatus === "critical" && a.healthStatus !== "critical") return 1
        // Then live streams
        if (a.streamStatus === "live" && b.streamStatus !== "live") return -1
        if (b.streamStatus === "live" && a.streamStatus !== "live") return 1
        // Then by alert count
        return b.alertCount - a.alertCount
    })

    // Grid column classes based on size
    const gridClasses = {
        small: "grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6",
        medium: "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4",
        large: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Monitoring" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Monitor className="h-8 w-8" />
                            Channel Monitoring
                        </h1>
                        <p className="text-muted-foreground">
                            Real-time status of all your YouTube channels
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {saveMessage && (
                            <Badge variant="secondary" className="animate-in fade-in">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {saveMessage}
                            </Badge>
                        )}
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleSaveLayout}
                            title="Save layout preferences"
                        >
                            <Save className="h-4 w-4 mr-1" />
                            Save Layout
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleResetLayout}
                            title="Reset to default layout"
                        >
                            <RotateCcw className="h-4 w-4 mr-1" />
                            Reset
                        </Button>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={handleRefresh}
                            disabled={refreshing}
                            title="Refresh all channels"
                        >
                            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                        </Button>
                    </div>
                </div>

                {/* Stats Overview */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
                        <Card className="border-0 shadow-sm">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold">{stats.totalChannels}</p>
                                <p className="text-xs text-muted-foreground">Total</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-red-600">{stats.liveChannels}</p>
                                <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                                    <Radio className="h-3 w-3" /> Live
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-blue-50 dark:bg-blue-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-blue-600">{stats.scheduledChannels}</p>
                                <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                                    <Calendar className="h-3 w-3" /> Scheduled
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-gray-500">{stats.offlineChannels}</p>
                                <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                                    <WifiOff className="h-3 w-3" /> Offline
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-red-600">{stats.errorChannels}</p>
                                <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                                    <AlertTriangle className="h-3 w-3" /> Errors
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-green-50 dark:bg-green-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-green-600">{stats.healthyChannels}</p>
                                <p className="text-xs text-muted-foreground">Healthy</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-yellow-50 dark:bg-yellow-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-yellow-600">{stats.warningChannels}</p>
                                <p className="text-xs text-muted-foreground">Warning</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-sm bg-red-50 dark:bg-red-950/20">
                            <CardContent className="p-3 text-center">
                                <p className="text-2xl font-bold text-red-600">{stats.criticalChannels}</p>
                                <p className="text-xs text-muted-foreground">Critical</p>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Filters and Controls */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                            {/* Search */}
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search channels..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>

                            <div className="flex flex-wrap items-center gap-3">
                                {/* Status Filter */}
                                <Select
                                    value={preferences.filters.status || "all"}
                                    onValueChange={(value) => updateFilters({ status: value as MonitoringFilters["status"] })}
                                >
                                    <SelectTrigger className="w-[140px]">
                                        <SelectValue placeholder="Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="live">
                                            <span className="flex items-center gap-2">
                                                <Radio className="h-3 w-3 text-red-500" /> Live
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="scheduled">
                                            <span className="flex items-center gap-2">
                                                <Calendar className="h-3 w-3 text-blue-500" /> Scheduled
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="offline">
                                            <span className="flex items-center gap-2">
                                                <WifiOff className="h-3 w-3" /> Offline
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="error">
                                            <span className="flex items-center gap-2">
                                                <AlertTriangle className="h-3 w-3 text-red-500" /> Error
                                            </span>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>

                                {/* Health Filter */}
                                <Select
                                    value={preferences.filters.healthStatus || "all"}
                                    onValueChange={(value) => updateFilters({ healthStatus: value as MonitoringFilters["healthStatus"] })}
                                >
                                    <SelectTrigger className="w-[140px]">
                                        <SelectValue placeholder="Health" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Health</SelectItem>
                                        <SelectItem value="healthy">
                                            <span className="flex items-center gap-2">
                                                <Activity className="h-3 w-3 text-green-500" /> Healthy
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="warning">
                                            <span className="flex items-center gap-2">
                                                <Activity className="h-3 w-3 text-yellow-500" /> Warning
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="critical">
                                            <span className="flex items-center gap-2">
                                                <Activity className="h-3 w-3 text-red-500" /> Critical
                                            </span>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>

                                {/* Token Filter */}
                                <Select
                                    value={preferences.filters.tokenStatus || "all"}
                                    onValueChange={(value) => updateFilters({ tokenStatus: value as MonitoringFilters["tokenStatus"] })}
                                >
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="Token" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Tokens</SelectItem>
                                        <SelectItem value="valid">
                                            <span className="flex items-center gap-2">
                                                <CheckCircle className="h-3 w-3 text-green-500" /> Valid
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="expiring">
                                            <span className="flex items-center gap-2">
                                                <AlertTriangle className="h-3 w-3 text-yellow-500" /> Expiring
                                            </span>
                                        </SelectItem>
                                        <SelectItem value="expired">
                                            <span className="flex items-center gap-2">
                                                <XCircle className="h-3 w-3 text-red-500" /> Expired
                                            </span>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>

                                {/* Grid Size Controls */}
                                <div className="flex items-center gap-1 border rounded-md p-1">
                                    <Button
                                        variant={preferences.gridSize === "small" ? "secondary" : "ghost"}
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() => setPreferences((p) => ({ ...p, gridSize: "small" }))}
                                        title="Small tiles"
                                    >
                                        <Grid3x3 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant={preferences.gridSize === "medium" ? "secondary" : "ghost"}
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() => setPreferences((p) => ({ ...p, gridSize: "medium" }))}
                                        title="Medium tiles"
                                    >
                                        <LayoutGrid className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant={preferences.gridSize === "large" ? "secondary" : "ghost"}
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() => setPreferences((p) => ({ ...p, gridSize: "large" }))}
                                        title="Large tiles"
                                    >
                                        <Monitor className="h-4 w-4" />
                                    </Button>
                                </div>

                                {/* Filter Sheet for more options */}
                                <Sheet open={filterSheetOpen} onOpenChange={setFilterSheetOpen}>
                                    <SheetTrigger asChild>
                                        <Button variant="outline" size="icon">
                                            <Filter className="h-4 w-4" />
                                        </Button>
                                    </SheetTrigger>
                                    <SheetContent>
                                        <SheetHeader>
                                            <SheetTitle>Monitoring Settings</SheetTitle>
                                        </SheetHeader>
                                        <div className="space-y-6 mt-6">
                                            {/* Auto Refresh Toggle */}
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <Label htmlFor="auto-refresh">Auto Refresh</Label>
                                                    <p className="text-sm text-muted-foreground">
                                                        Automatically refresh channel data
                                                    </p>
                                                </div>
                                                <Switch
                                                    id="auto-refresh"
                                                    checked={preferences.autoRefresh}
                                                    onCheckedChange={(checked) =>
                                                        setPreferences((p) => ({ ...p, autoRefresh: checked }))
                                                    }
                                                />
                                            </div>

                                            {/* Refresh Interval */}
                                            {preferences.autoRefresh && (
                                                <div className="space-y-3">
                                                    <div className="flex items-center justify-between">
                                                        <Label>Refresh Interval</Label>
                                                        <span className="text-sm text-muted-foreground">
                                                            {preferences.refreshInterval}s
                                                        </span>
                                                    </div>
                                                    <Slider
                                                        value={[preferences.refreshInterval]}
                                                        onValueChange={([value]) =>
                                                            setPreferences((p) => ({ ...p, refreshInterval: value }))
                                                        }
                                                        min={10}
                                                        max={120}
                                                        step={5}
                                                    />
                                                    <p className="text-xs text-muted-foreground">
                                                        10 seconds to 2 minutes
                                                    </p>
                                                </div>
                                            )}

                                            {/* Grid Size */}
                                            <div className="space-y-3">
                                                <Label>Grid Size</Label>
                                                <Select
                                                    value={preferences.gridSize}
                                                    onValueChange={(value: GridSize) =>
                                                        setPreferences((p) => ({ ...p, gridSize: value }))
                                                    }
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="small">Small (compact)</SelectItem>
                                                        <SelectItem value="medium">Medium (default)</SelectItem>
                                                        <SelectItem value="large">Large (detailed)</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>

                                            {/* Save/Reset buttons */}
                                            <div className="flex gap-2 pt-4">
                                                <Button onClick={handleSaveLayout} className="flex-1">
                                                    <Save className="h-4 w-4 mr-2" />
                                                    Save Preferences
                                                </Button>
                                                <Button variant="outline" onClick={handleResetLayout}>
                                                    <RotateCcw className="h-4 w-4 mr-2" />
                                                    Reset
                                                </Button>
                                            </div>
                                        </div>
                                    </SheetContent>
                                </Sheet>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Channel Grid */}
                {loading ? (
                    <div className={cn("grid gap-4", gridClasses[preferences.gridSize])}>
                        {[...Array(8)].map((_, i) => (
                            <Card key={i} className="border-0 shadow-lg">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <Skeleton className="h-12 w-12 rounded-full" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-3/4 mb-2" />
                                            <Skeleton className="h-3 w-1/2" />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : sortedChannels.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <Monitor className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No channels found</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchQuery || preferences.filters.status !== "all"
                                    ? "Try adjusting your filters"
                                    : "Connect YouTube accounts to start monitoring"}
                            </p>
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setSearchQuery("")
                                    setPreferences((p) => ({
                                        ...p,
                                        filters: DEFAULT_PREFERENCES.filters,
                                    }))
                                }}
                            >
                                Clear Filters
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className={cn("grid gap-4", gridClasses[preferences.gridSize])}>
                        {sortedChannels.map((channel) => (
                            <ChannelTile
                                key={channel.accountId}
                                channel={channel}
                                size={preferences.gridSize}
                                expanded={expandedChannel === channel.accountId}
                                onExpand={() =>
                                    setExpandedChannel(
                                        expandedChannel === channel.accountId ? null : channel.accountId
                                    )
                                }
                                onRefresh={() => handleRefreshChannel(channel.accountId)}
                                onQuickAction={(action) => handleQuickAction(channel.accountId, action)}
                            />
                        ))}
                    </div>
                )}

                {/* Auto-refresh indicator */}
                {preferences.autoRefresh && (
                    <div className="fixed bottom-4 right-4 bg-background border rounded-full px-3 py-1.5 shadow-lg flex items-center gap-2 text-sm">
                        <div className={cn("h-2 w-2 rounded-full", refreshing ? "bg-yellow-500 animate-pulse" : "bg-green-500")} />
                        <span className="text-muted-foreground">
                            Auto-refresh: {preferences.refreshInterval}s
                        </span>
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}
