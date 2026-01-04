"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Search, Video, RefreshCw } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { StreamJobCard } from "./stream-job-card"
import { ResourceDashboardCard } from "./resource-dashboard"
import {
    streamJobsApi,
    type StreamJob,
    type StreamJobStatus,
} from "@/lib/api/stream-jobs"

interface VideoToLiveListProps {
    accountId?: string
    showResourceDashboard?: boolean
}

export function VideoToLiveList({ accountId, showResourceDashboard = true }: VideoToLiveListProps) {
    const router = useRouter()
    const [jobs, setJobs] = useState<StreamJob[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    // Filters
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [pagination, setPagination] = useState({
        total: 0,
        page: 1,
        pageSize: 12,
    })

    const loadJobs = async (showRefreshing = false) => {
        try {
            if (showRefreshing) setRefreshing(true)
            else setLoading(true)

            const response = await streamJobsApi.getStreamJobs({
                status: statusFilter !== "all" ? (statusFilter as StreamJobStatus) : undefined,
                accountId: accountId,
                page: pagination.page,
                pageSize: pagination.pageSize,
            })

            setJobs(response.jobs)
            setPagination((prev) => ({
                ...prev,
                total: response.total,
            }))
        } catch (error) {
            console.error("Failed to load stream jobs:", error)
            setJobs([])
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        loadJobs()
    }, [statusFilter, accountId, pagination.page])

    // Auto-refresh every 30 seconds for active streams
    useEffect(() => {
        const hasActiveStreams = jobs.some((job) =>
            ["starting", "running", "stopping"].includes(job.status)
        )

        if (hasActiveStreams) {
            const interval = setInterval(() => loadJobs(true), 30000)
            return () => clearInterval(interval)
        }
    }, [jobs])

    // Filter by search query
    const filteredJobs = useMemo(() => {
        if (!searchQuery) return jobs
        const query = searchQuery.toLowerCase()
        return jobs.filter(
            (job) =>
                job.title.toLowerCase().includes(query) ||
                job.description?.toLowerCase().includes(query)
        )
    }, [jobs, searchQuery])

    const handleRefresh = () => {
        loadJobs(true)
    }

    if (loading) {
        return (
            <div className="space-y-6">
                {showResourceDashboard && <Skeleton className="h-32 w-full" />}
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
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Resource Dashboard */}
            {showResourceDashboard && jobs.length > 0 && <ResourceDashboardCard />}

            {/* Filters */}
            <Card className="border-0 shadow-lg">
                <CardContent className="pt-6">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <div className="flex flex-1 gap-2">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search Video-to-Live streams..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-[150px]">
                                    <SelectValue placeholder="All Status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="running">Running</SelectItem>
                                    <SelectItem value="starting">Starting</SelectItem>
                                    <SelectItem value="scheduled">Scheduled</SelectItem>
                                    <SelectItem value="pending">Pending</SelectItem>
                                    <SelectItem value="stopped">Stopped</SelectItem>
                                    <SelectItem value="completed">Completed</SelectItem>
                                    <SelectItem value="failed">Failed</SelectItem>
                                </SelectContent>
                            </Select>

                            <Button
                                variant="outline"
                                size="icon"
                                onClick={handleRefresh}
                                disabled={refreshing}
                            >
                                <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Stream Jobs Grid */}
            {filteredJobs.length === 0 ? (
                <Card className="border-0 shadow-lg">
                    <CardContent className="py-12 text-center">
                        <Video className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No Video-to-Live streams found</h3>
                        <p className="text-muted-foreground">
                            {searchQuery || statusFilter !== "all"
                                ? "Try adjusting your filters"
                                : "Stream pre-recorded videos as live content 24/7"}
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredJobs.map((job) => (
                        <StreamJobCard key={job.id} job={job} onUpdate={handleRefresh} />
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
    )
}

export default VideoToLiveList
