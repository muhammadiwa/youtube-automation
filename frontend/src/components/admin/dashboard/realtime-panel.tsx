"use client"

import { useEffect, useState, useCallback } from "react"
import { Activity, Users, Zap, Clock, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { RealtimeMetrics } from "@/types/admin"

interface RealtimePanelProps {
    autoRefresh?: boolean
    refreshInterval?: number // in seconds
}

interface MetricItemProps {
    label: string
    value: string | number
    icon: React.ElementType
    iconColor: string
    isLoading?: boolean
}

function MetricItem({ label, value, icon: Icon, iconColor, isLoading }: MetricItemProps) {
    if (isLoading) {
        return (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <div className="space-y-1">
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="h-5 w-16" />
                </div>
            </div>
        )
    }

    return (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
            <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", iconColor)}>
                <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-lg font-semibold">{typeof value === "number" ? value.toLocaleString() : value}</p>
            </div>
        </div>
    )
}

export function RealtimePanel({ autoRefresh = true, refreshInterval = 30 }: RealtimePanelProps) {
    const [metrics, setMetrics] = useState<RealtimeMetrics | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const fetchMetrics = useCallback(async (showRefreshing = false) => {
        if (showRefreshing) setIsRefreshing(true)
        try {
            const data = await adminApi.getRealtimeMetrics()
            setMetrics(data)
            setLastUpdated(new Date())
        } catch (error) {
            console.error("Failed to fetch realtime metrics:", error)
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [])

    useEffect(() => {
        fetchMetrics()

        if (autoRefresh) {
            const interval = setInterval(() => {
                fetchMetrics()
            }, refreshInterval * 1000)

            return () => clearInterval(interval)
        }
    }, [fetchMetrics, autoRefresh, refreshInterval])

    const handleManualRefresh = () => {
        fetchMetrics(true)
    }

    return (
        <Card className="border-0 shadow-md">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        <CardTitle className="text-base font-semibold">Real-time Metrics</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                        {lastUpdated && (
                            <span className="text-xs text-muted-foreground">
                                Updated {lastUpdated.toLocaleTimeString()}
                            </span>
                        )}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={handleManualRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <MetricItem
                        label="Active Streams"
                        value={metrics?.active_streams ?? 0}
                        icon={Activity}
                        iconColor="bg-green-500"
                        isLoading={isLoading}
                    />
                    <MetricItem
                        label="Concurrent Users"
                        value={metrics?.concurrent_users ?? 0}
                        icon={Users}
                        iconColor="bg-blue-500"
                        isLoading={isLoading}
                    />
                    <MetricItem
                        label="API Requests/min"
                        value={metrics?.api_requests_per_minute ?? 0}
                        icon={Zap}
                        iconColor="bg-purple-500"
                        isLoading={isLoading}
                    />
                    <MetricItem
                        label="Active Jobs"
                        value={metrics?.active_jobs ?? 0}
                        icon={Activity}
                        iconColor="bg-orange-500"
                        isLoading={isLoading}
                    />
                    <MetricItem
                        label="Queue Depth"
                        value={metrics?.queue_depth ?? 0}
                        icon={Clock}
                        iconColor="bg-yellow-500"
                        isLoading={isLoading}
                    />
                    <MetricItem
                        label="Avg Response Time"
                        value={metrics ? `${metrics.avg_response_time_ms.toFixed(0)}ms` : "0ms"}
                        icon={Clock}
                        iconColor="bg-cyan-500"
                        isLoading={isLoading}
                    />
                </div>
            </CardContent>
        </Card>
    )
}
