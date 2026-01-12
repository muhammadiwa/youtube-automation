"use client"

import { useState, useEffect } from "react"
import { Cpu, HardDrive, Wifi, AlertTriangle, Activity } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { streamJobsApi, type ResourceDashboard, type SlotStatus } from "@/lib/api/stream-jobs"

interface ResourceDashboardProps {
    refreshInterval?: number // in milliseconds
}

export function ResourceDashboardCard({ refreshInterval = 10000 }: ResourceDashboardProps) {
    const [resources, setResources] = useState<ResourceDashboard | null>(null)
    const [slotStatus, setSlotStatus] = useState<SlotStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const loadData = async () => {
        try {
            const [resourceData, slotData] = await Promise.all([
                streamJobsApi.getResourceUsage(),
                streamJobsApi.getSlotStatus(),
            ])
            setResources(resourceData)
            setSlotStatus(slotData)
            setError(null)
        } catch (err) {
            console.error("Failed to load resource data:", err)
            setError("Failed to load resource data")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadData()
        const interval = setInterval(loadData, refreshInterval)
        return () => clearInterval(interval)
    }, [refreshInterval])

    if (loading) {
        return (
            <Card className="border-0 shadow-lg">
                <CardHeader className="pb-2">
                    <Skeleton className="h-5 w-40" />
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-20" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        )
    }

    if (error || !resources || !slotStatus) {
        return null
    }

    const { aggregate } = resources
    const cpuPercent = Math.min(100, aggregate.totalCpuPercent)
    const memoryPercent = Math.min(100, (aggregate.totalMemoryMb / 8192) * 100) // Assume 8GB max

    return (
        <Card className="border-0 shadow-lg">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Activity className="h-5 w-5 text-primary" />
                        Resource Usage
                    </CardTitle>
                    {aggregate.isWarning && (
                        <Badge variant="destructive" className="animate-pulse">
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            High Usage
                        </Badge>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Slot Usage */}
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Stream Slots</span>
                                        <span className="font-medium">
                                            {slotStatus.usedSlots}/{slotStatus.totalSlots}
                                        </span>
                                    </div>
                                    <Progress
                                        value={(slotStatus.usedSlots / slotStatus.totalSlots) * 100}
                                        className="h-2"
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        {slotStatus.availableSlots} available ({slotStatus.plan})
                                    </p>
                                </div>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Active streams: {slotStatus.usedSlots}</p>
                                <p>Plan limit: {slotStatus.totalSlots} streams</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    {/* CPU and Memory hidden for SaaS - internal infrastructure */}

                    {/* Bandwidth */}
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground flex items-center gap-1">
                                            <Wifi className="h-3 w-3" />
                                            Bandwidth
                                        </span>
                                        <span className="font-medium">
                                            {(aggregate.totalBandwidthKbps / 1000).toFixed(1)} Mbps
                                        </span>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {aggregate.activeStreams} active stream{aggregate.activeStreams !== 1 ? "s" : ""}
                                    </p>
                                </div>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Total upload bandwidth</p>
                                <p>Est. remaining capacity: {aggregate.estimatedRemainingSlots} streams</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>

                {/* Per-stream breakdown (collapsed by default) */}
                {resources.streams.length > 0 && (
                    <details className="mt-4">
                        <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                            View per-stream breakdown ({resources.streams.length} streams)
                        </summary>
                        <div className="mt-2 space-y-2">
                            {resources.streams.map((stream) => (
                                <div
                                    key={stream.streamJobId}
                                    className="flex items-center justify-between text-sm p-2 bg-muted/50 rounded"
                                >
                                    <span className="truncate max-w-[200px]">{stream.title}</span>
                                    <div className="flex items-center gap-4 text-muted-foreground">
                                        <span>CPU: {stream.cpuPercent?.toFixed(1) || 0}%</span>
                                        <span>RAM: {stream.memoryMb?.toFixed(0) || 0} MB</span>
                                        <span>{stream.bitrateKbps?.toFixed(0) || 0} kbps</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </details>
                )}
            </CardContent>
        </Card>
    )
}

export default ResourceDashboardCard
