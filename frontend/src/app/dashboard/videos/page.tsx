"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Search, Filter, Upload, Grid3x3, List, MoreVertical, Trash2, Edit, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
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
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { videosApi, type VideoFilters } from "@/lib/api/videos"
import { accountsApi } from "@/lib/api/accounts"
import type { Video, YouTubeAccount } from "@/types"

export default function VideosPage() {
    const router = useRouter()
    const [videos, setVideos] = useState<Video[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
    const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set())
    const [bulkMode, setBulkMode] = useState(false)

    // Filters
    const [filters, setFilters] = useState<VideoFilters>({
        page: 1,
        pageSize: 20,
        sortBy: "date",
        sortOrder: "desc",
    })
    const [searchQuery, setSearchQuery] = useState("")
    const [pagination, setPagination] = useState({
        total: 0,
        page: 1,
        pageSize: 20,
        totalPages: 0,
    })

    useEffect(() => {
        loadAccounts()
    }, [])

    useEffect(() => {
        loadVideos()
    }, [filters])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(data)
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadVideos = async () => {
        try {
            setLoading(true)
            const response = await videosApi.getVideos(filters)
            setVideos(response.items)
            setPagination({
                total: response.total,
                page: response.page,
                pageSize: response.pageSize,
                totalPages: response.totalPages,
            })
        } catch (error) {
            console.error("Failed to load videos:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = (value: string) => {
        setSearchQuery(value)
        setFilters((prev) => ({ ...prev, search: value, page: 1 }))
    }

    const handleFilterChange = (key: keyof VideoFilters, value: any) => {
        setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
    }

    const handleSelectVideo = (videoId: string) => {
        const newSelected = new Set(selectedVideos)
        if (newSelected.has(videoId)) {
            newSelected.delete(videoId)
        } else {
            newSelected.add(videoId)
        }
        setSelectedVideos(newSelected)
    }

    const handleSelectAll = () => {
        if (selectedVideos.size === videos.length) {
            setSelectedVideos(new Set())
        } else {
            setSelectedVideos(new Set(videos.map((v) => v.id)))
        }
    }

    const handleBulkDelete = async () => {
        if (selectedVideos.size === 0) return

        if (!confirm(`Delete ${selectedVideos.size} video(s)?`)) return

        try {
            await videosApi.bulkDelete(Array.from(selectedVideos))
            setSelectedVideos(new Set())
            setBulkMode(false)
            loadVideos()
        } catch (error) {
            console.error("Failed to delete videos:", error)
        }
    }

    const getStatusBadge = (status: Video["status"]) => {
        const variants: Record<Video["status"], { variant: any; label: string }> = {
            draft: { variant: "secondary", label: "Draft" },
            uploading: { variant: "default", label: "Uploading" },
            processing: { variant: "default", label: "Processing" },
            published: { variant: "default", label: "Published" },
            scheduled: { variant: "outline", label: "Scheduled" },
        }
        const config = variants[status]
        return <Badge variant={config.variant}>{config.label}</Badge>
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Videos</h1>
                    <p className="text-muted-foreground">
                        Manage your video library across all channels
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => router.push("/dashboard/videos/bulk-upload")}>
                        Bulk Upload
                    </Button>
                    <Button onClick={() => router.push("/dashboard/videos/upload")}>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload Video
                    </Button>
                </div>
            </div>

            {/* Filters and Search */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <div className="flex flex-1 gap-2">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search videos by title or description..."
                                    value={searchQuery}
                                    onChange={(e) => handleSearch(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <Select
                                value={filters.accountId || "all"}
                                onValueChange={(value) =>
                                    handleFilterChange("accountId", value === "all" ? undefined : value)
                                }
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
                                value={filters.status || "all"}
                                onValueChange={(value) =>
                                    handleFilterChange("status", value === "all" ? undefined : value)
                                }
                            >
                                <SelectTrigger className="w-[150px]">
                                    <SelectValue placeholder="All Status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="draft">Draft</SelectItem>
                                    <SelectItem value="uploading">Uploading</SelectItem>
                                    <SelectItem value="processing">Processing</SelectItem>
                                    <SelectItem value="published">Published</SelectItem>
                                    <SelectItem value="scheduled">Scheduled</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select
                                value={filters.visibility || "all"}
                                onValueChange={(value) =>
                                    handleFilterChange("visibility", value === "all" ? undefined : value)
                                }
                            >
                                <SelectTrigger className="w-[150px]">
                                    <SelectValue placeholder="All Visibility" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Visibility</SelectItem>
                                    <SelectItem value="public">Public</SelectItem>
                                    <SelectItem value="unlisted">Unlisted</SelectItem>
                                    <SelectItem value="private">Private</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select
                                value={`${filters.sortBy}-${filters.sortOrder}`}
                                onValueChange={(value) => {
                                    const [sortBy, sortOrder] = value.split("-")
                                    setFilters((prev) => ({
                                        ...prev,
                                        sortBy: sortBy as any,
                                        sortOrder: sortOrder as any,
                                    }))
                                }}
                            >
                                <SelectTrigger className="w-[150px]">
                                    <SelectValue placeholder="Sort by" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="date-desc">Newest First</SelectItem>
                                    <SelectItem value="date-asc">Oldest First</SelectItem>
                                    <SelectItem value="views-desc">Most Views</SelectItem>
                                    <SelectItem value="views-asc">Least Views</SelectItem>
                                    <SelectItem value="status-asc">Status A-Z</SelectItem>
                                </SelectContent>
                            </Select>

                            <div className="flex gap-1 border rounded-md">
                                <Button
                                    variant={viewMode === "grid" ? "secondary" : "ghost"}
                                    size="icon"
                                    onClick={() => setViewMode("grid")}
                                >
                                    <Grid3x3 className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant={viewMode === "list" ? "secondary" : "ghost"}
                                    size="icon"
                                    onClick={() => setViewMode("list")}
                                >
                                    <List className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Bulk Actions Toolbar */}
            {bulkMode && (
                <Card className="bg-muted">
                    <CardContent className="py-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <Checkbox
                                    checked={selectedVideos.size === videos.length && videos.length > 0}
                                    onCheckedChange={handleSelectAll}
                                />
                                <span className="text-sm font-medium">
                                    {selectedVideos.size} video(s) selected
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={handleBulkDelete}
                                    disabled={selectedVideos.size === 0}
                                >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete Selected
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => {
                                    setBulkMode(false)
                                    setSelectedVideos(new Set())
                                }}>
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Toggle Bulk Mode */}
            {!bulkMode && videos.length > 0 && (
                <div className="flex justify-end">
                    <Button variant="outline" size="sm" onClick={() => setBulkMode(true)}>
                        <Checkbox className="mr-2 h-4 w-4" />
                        Bulk Select
                    </Button>
                </div>
            )}

            {/* Videos Grid/List */}
            {loading ? (
                <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" : "space-y-4"}>
                    {[...Array(8)].map((_, i) => (
                        <Card key={i}>
                            <Skeleton className="aspect-video w-full" />
                            <CardContent className="p-4">
                                <Skeleton className="h-4 w-3/4 mb-2" />
                                <Skeleton className="h-3 w-1/2" />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : videos.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-muted-foreground">No videos found</p>
                        <Button className="mt-4" onClick={() => router.push("/dashboard/videos/upload")}>
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Your First Video
                        </Button>
                    </CardContent>
                </Card>
            ) : viewMode === "grid" ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {videos.map((video) => (
                        <Card key={video.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                            <div className="relative">
                                {bulkMode && (
                                    <div className="absolute top-2 left-2 z-10">
                                        <Checkbox
                                            checked={selectedVideos.has(video.id)}
                                            onCheckedChange={() => handleSelectVideo(video.id)}
                                            className="bg-white"
                                        />
                                    </div>
                                )}
                                <img
                                    src={video.thumbnailUrl || "/placeholder-thumbnail.jpg"}
                                    alt={video.title}
                                    className="w-full aspect-video object-cover cursor-pointer"
                                    onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                />
                                <div className="absolute bottom-2 right-2">
                                    {getStatusBadge(video.status)}
                                </div>
                            </div>
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <h3
                                            className="font-semibold truncate cursor-pointer hover:text-primary"
                                            onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                        >
                                            {video.title}
                                        </h3>
                                        <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <Eye className="h-3 w-3" />
                                                {formatNumber(video.viewCount)}
                                            </span>
                                            <Badge variant="outline" className="text-xs">
                                                {video.visibility}
                                            </Badge>
                                        </div>
                                    </div>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem
                                                onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                            >
                                                <Edit className="mr-2 h-4 w-4" />
                                                Edit
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                className="text-destructive"
                                                onClick={async () => {
                                                    if (confirm("Delete this video?")) {
                                                        await videosApi.deleteVideo(video.id)
                                                        loadVideos()
                                                    }
                                                }}
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
            ) : (
                <div className="space-y-2">
                    {videos.map((video) => (
                        <Card key={video.id}>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-4">
                                    {bulkMode && (
                                        <Checkbox
                                            checked={selectedVideos.has(video.id)}
                                            onCheckedChange={() => handleSelectVideo(video.id)}
                                        />
                                    )}
                                    <img
                                        src={video.thumbnailUrl || "/placeholder-thumbnail.jpg"}
                                        alt={video.title}
                                        className="w-32 aspect-video object-cover rounded cursor-pointer"
                                        onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <h3
                                            className="font-semibold cursor-pointer hover:text-primary"
                                            onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                        >
                                            {video.title}
                                        </h3>
                                        <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                                            {video.description}
                                        </p>
                                        <div className="flex items-center gap-4 mt-2">
                                            {getStatusBadge(video.status)}
                                            <Badge variant="outline">{video.visibility}</Badge>
                                            <span className="text-sm text-muted-foreground">
                                                {formatNumber(video.viewCount)} views
                                            </span>
                                            <span className="text-sm text-muted-foreground">
                                                {formatNumber(video.likeCount)} likes
                                            </span>
                                        </div>
                                    </div>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem
                                                onClick={() => router.push(`/dashboard/videos/${video.id}/edit`)}
                                            >
                                                <Edit className="mr-2 h-4 w-4" />
                                                Edit
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                className="text-destructive"
                                                onClick={async () => {
                                                    if (confirm("Delete this video?")) {
                                                        await videosApi.deleteVideo(video.id)
                                                        loadVideos()
                                                    }
                                                }}
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
            {pagination.totalPages > 1 && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                        Showing {(pagination.page - 1) * pagination.pageSize + 1} to{" "}
                        {Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total} videos
                    </p>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={pagination.page === 1}
                            onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! - 1 }))}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={pagination.page === pagination.totalPages}
                            onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! + 1 }))}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
