"use client"

/**
 * Video Library Page
 * 
 * Main page for video library management (library-first approach).
 * Users can upload videos to library, organize in folders, and then upload to YouTube.
 * Requirements: 1.1, 1.2, 1.3, 4.2
 */

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    Upload,
    Search,
    Grid3x3,
    List,
    Star,
    Folder,
    MoreVertical,
    Play,
    Trash2,
    Edit,
    FolderPlus,
    Radio,
    CheckSquare,
    Square
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
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toast"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { VideoUsageBadgeCompact } from "@/components/videos/video-usage-badge"
import { CreateFolderDialog } from "@/components/videos/create-folder-dialog"
import { EditFolderDialog } from "@/components/videos/edit-folder-dialog"
import { DeleteFolderDialog } from "@/components/videos/delete-folder-dialog"
import { MoveToFolderDialog } from "@/components/videos/move-to-folder-dialog"
import { UploadToYouTubeDialog } from "@/components/videos/upload-to-youtube-dialog"
import { CreateStreamDialog } from "@/components/videos/create-stream-dialog"
import { BulkActionsBar } from "@/components/videos/bulk-actions-bar"
import { BulkUploadDialog } from "@/components/videos/bulk-upload-dialog"
import { BulkMoveDialog } from "@/components/videos/bulk-move-dialog"
import { BulkDeleteDialog } from "@/components/videos/bulk-delete-dialog"
import { AdvancedFilterPanel, type AdvancedFilters } from "@/components/videos/advanced-filter-panel"
import { videoLibraryApi, type LibraryVideoFilters, type VideoFolder } from "@/lib/api/video-library"
import { accountsApi } from "@/lib/api/accounts"
import type { Video, YouTubeAccount } from "@/types"

export default function VideoLibraryPage() {
    const router = useRouter()
    const { addToast } = useToast()

    // State
    const [videos, setVideos] = useState<Video[]>([])
    const [folders, setFolders] = useState<VideoFolder[]>([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
    const [selectedFolder, setSelectedFolder] = useState<string | null>(null)

    // Drag and drop state
    const [draggedVideoId, setDraggedVideoId] = useState<string | null>(null)
    const [dropTargetFolderId, setDropTargetFolderId] = useState<string | null>(null)

    // Bulk selection
    const [bulkSelectionMode, setBulkSelectionMode] = useState(false)
    const [selectedVideoIds, setSelectedVideoIds] = useState<Set<string>>(new Set())

    // Dialog states
    const [createFolderOpen, setCreateFolderOpen] = useState(false)
    const [editFolderOpen, setEditFolderOpen] = useState(false)
    const [deleteFolderOpen, setDeleteFolderOpen] = useState(false)
    const [moveToFolderOpen, setMoveToFolderOpen] = useState(false)
    const [uploadToYouTubeOpen, setUploadToYouTubeOpen] = useState(false)
    const [createStreamOpen, setCreateStreamOpen] = useState(false)
    const [bulkUploadOpen, setBulkUploadOpen] = useState(false)
    const [bulkMoveOpen, setBulkMoveOpen] = useState(false)
    const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
    const [selectedFolderForEdit, setSelectedFolderForEdit] = useState<VideoFolder | null>(null)
    const [selectedVideoForMove, setSelectedVideoForMove] = useState<Video | null>(null)
    const [selectedVideoForUpload, setSelectedVideoForUpload] = useState<Video | null>(null)
    const [selectedVideoForStream, setSelectedVideoForStream] = useState<Video | null>(null)
    const [deleteVideoOpen, setDeleteVideoOpen] = useState(false)
    const [videoToDelete, setVideoToDelete] = useState<Video | null>(null)

    // YouTube accounts
    const [youtubeAccounts, setYoutubeAccounts] = useState<YouTubeAccount[]>([])

    // Load YouTube accounts
    useEffect(() => {
        loadYouTubeAccounts()
    }, [])

    // Filters
    const [filters, setFilters] = useState<LibraryVideoFilters>({
        page: 1,
        limit: 20,
        sortBy: "created_at",
        sortOrder: "desc",
    })
    const [searchQuery, setSearchQuery] = useState("")
    const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>({})
    const [pagination, setPagination] = useState({
        total: 0,
        page: 1,
        pageSize: 20,
        totalPages: 0,
    })

    // Load data
    useEffect(() => {
        loadFolders()
    }, [])

    useEffect(() => {
        loadVideos()
    }, [filters])

    const loadFolders = async () => {
        try {
            const data = await videoLibraryApi.getAllFolders()
            setFolders(data)
        } catch (error) {
            console.error("Failed to load folders:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to load folders",
            })
        }
    }

    const loadVideos = async () => {
        try {
            setLoading(true)
            const response = await videoLibraryApi.getLibraryVideos(filters)
            setVideos(response.items)
            setPagination({
                total: response.total,
                page: response.page,
                pageSize: response.pageSize,
                totalPages: response.totalPages,
            })
        } catch (error) {
            console.error("Failed to load videos:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to load videos",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = () => {
        setFilters({ ...filters, search: searchQuery, page: 1 })
    }

    const handleFolderSelect = (folderId: string | null) => {
        setSelectedFolder(folderId)
        setFilters({ ...filters, folderId, page: 1 })
    }

    const handleToggleFavorite = async (videoId: string) => {
        try {
            await videoLibraryApi.toggleFavorite(videoId)
            loadVideos()
            addToast({
                type: "success",
                title: "Success",
                description: "Video favorite status updated",
            })
        } catch (error) {
            console.error("Failed to toggle favorite:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to update favorite status",
            })
        }
    }

    const handleDeleteVideo = (video: Video) => {
        setVideoToDelete(video)
        setDeleteVideoOpen(true)
    }

    const confirmDeleteVideo = async () => {
        if (!videoToDelete) return

        try {
            await videoLibraryApi.deleteFromLibrary(videoToDelete.id)
            loadVideos()
            addToast({
                type: "success",
                title: "Success",
                description: "Video deleted successfully",
            })
        } catch (error) {
            console.error("Failed to delete video:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to delete video",
            })
        } finally {
            setVideoToDelete(null)
        }
    }

    const handleEditFolder = (folder: VideoFolder) => {
        setSelectedFolderForEdit(folder)
        setEditFolderOpen(true)
    }

    const handleDeleteFolder = (folder: VideoFolder) => {
        setSelectedFolderForEdit(folder)
        setDeleteFolderOpen(true)
    }

    const handleMoveVideo = (video: Video) => {
        setSelectedVideoForMove(video)
        setMoveToFolderOpen(true)
    }

    const loadYouTubeAccounts = async () => {
        try {
            const accounts = await accountsApi.getAccounts()
            setYoutubeAccounts(accounts)
        } catch (error) {
            console.error("Failed to load YouTube accounts:", error)
        }
    }

    const handleDialogSuccess = () => {
        loadFolders()
        loadVideos()
    }

    const handleUploadToYouTube = (video: Video) => {
        setSelectedVideoForUpload(video)
        setUploadToYouTubeOpen(true)
    }

    const handleCreateStream = (video: Video) => {
        setSelectedVideoForStream(video)
        setCreateStreamOpen(true)
    }

    const handleStreamCreated = (streamJobId: string) => {
        addToast({
            type: "success",
            title: "Stream Created",
            description: "Redirecting to stream control panel...",
        })
        // Redirect to stream control page
        router.push(`/dashboard/streams/${streamJobId}`)
    }

    // Bulk selection handlers
    const toggleBulkSelection = () => {
        setBulkSelectionMode(!bulkSelectionMode)
        setSelectedVideoIds(new Set())
    }

    const toggleVideoSelection = (videoId: string) => {
        const newSelection = new Set(selectedVideoIds)
        if (newSelection.has(videoId)) {
            newSelection.delete(videoId)
        } else {
            newSelection.add(videoId)
        }
        setSelectedVideoIds(newSelection)
    }

    const toggleSelectAll = () => {
        if (selectedVideoIds.size === videos.length) {
            setSelectedVideoIds(new Set())
        } else {
            setSelectedVideoIds(new Set(videos.map((v) => v.id)))
        }
    }

    const clearSelection = () => {
        setSelectedVideoIds(new Set())
        setBulkSelectionMode(false)
    }

    const handleBulkUpload = () => {
        setBulkUploadOpen(true)
    }

    const handleBulkMove = () => {
        setBulkMoveOpen(true)
    }

    const handleBulkDelete = () => {
        setBulkDeleteOpen(true)
    }

    const handleBulkSuccess = () => {
        clearSelection()
        loadVideos()
    }

    const selectedVideos = videos.filter((v) => selectedVideoIds.has(v.id))

    // Drag and drop handlers
    const handleDragStart = (e: React.DragEvent, videoId: string) => {
        setDraggedVideoId(videoId)
        e.dataTransfer.effectAllowed = "move"
        e.dataTransfer.setData("text/plain", videoId)

        // Add visual feedback to the dragged element
        if (e.currentTarget instanceof HTMLElement) {
            e.currentTarget.style.opacity = "0.5"
        }
    }

    const handleDragEnd = (e: React.DragEvent) => {
        setDraggedVideoId(null)
        setDropTargetFolderId(null)

        // Reset visual feedback
        if (e.currentTarget instanceof HTMLElement) {
            e.currentTarget.style.opacity = "1"
        }
    }

    const handleDragOver = (e: React.DragEvent, folderId: string | null) => {
        e.preventDefault()
        e.dataTransfer.dropEffect = "move"
        setDropTargetFolderId(folderId)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        // Only clear if we're leaving the folder button itself
        if (e.currentTarget === e.target) {
            setDropTargetFolderId(null)
        }
    }

    const handleDrop = async (e: React.DragEvent, folderId: string | null) => {
        e.preventDefault()
        setDropTargetFolderId(null)

        const videoId = e.dataTransfer.getData("text/plain")
        if (!videoId || !draggedVideoId) return

        try {
            await videoLibraryApi.moveToFolder(videoId, folderId)
            loadVideos()
            addToast({
                type: "success",
                title: "Success",
                description: `Video moved to ${folderId ? folders.find(f => f.id === folderId)?.name || "folder" : "root"}`,
            })
        } catch (error) {
            console.error("Failed to move video:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to move video",
            })
        } finally {
            setDraggedVideoId(null)
        }
    }

    const formatDuration = (seconds: number | null | undefined) => {
        if (!seconds) return "N/A"
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, "0")}`
    }

    const formatFileSize = (bytes: number | null | undefined) => {
        if (!bytes) return "N/A"
        const mb = bytes / (1024 * 1024)
        if (mb < 1024) return `${mb.toFixed(1)} MB`
        return `${(mb / 1024).toFixed(1)} GB`
    }

    return (
        <DashboardLayout>
            <div className="flex h-full">
                {/* Sidebar - Folders */}
                <div className="w-64 border-r bg-muted/10 p-4">
                    <div className="mb-4 flex items-center justify-between">
                        <h3 className="font-semibold">Folders</h3>
                        <Button size="sm" variant="ghost" onClick={() => setCreateFolderOpen(true)}>
                            <FolderPlus className="h-4 w-4" />
                        </Button>
                    </div>

                    <div className="space-y-1">
                        <Button
                            variant={selectedFolder === null ? "secondary" : "ghost"}
                            className={`w-full justify-start transition-colors ${dropTargetFolderId === null && draggedVideoId ? "ring-2 ring-primary ring-offset-2" : ""
                                }`}
                            onClick={() => handleFolderSelect(null)}
                            onDragOver={(e) => handleDragOver(e, null)}
                            onDragLeave={handleDragLeave}
                            onDrop={(e) => handleDrop(e, null)}
                        >
                            <Folder className="mr-2 h-4 w-4" />
                            All Videos
                        </Button>

                        {folders.map((folder) => (
                            <div key={folder.id} className="group relative">
                                <Button
                                    variant={selectedFolder === folder.id ? "secondary" : "ghost"}
                                    className={`w-full justify-start pr-8 transition-colors ${dropTargetFolderId === folder.id ? "ring-2 ring-primary ring-offset-2" : ""
                                        }`}
                                    onClick={() => handleFolderSelect(folder.id)}
                                    onDragOver={(e) => handleDragOver(e, folder.id)}
                                    onDragLeave={handleDragLeave}
                                    onDrop={(e) => handleDrop(e, folder.id)}
                                >
                                    <Folder className="mr-2 h-4 w-4" style={{ color: folder.color || undefined }} />
                                    {folder.name}
                                </Button>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="absolute right-1 top-1 h-6 w-6 opacity-0 group-hover:opacity-100"
                                        >
                                            <MoreVertical className="h-3 w-3" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem onClick={() => handleEditFolder(folder)}>
                                            <Edit className="mr-2 h-4 w-4" />
                                            Edit
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            onClick={() => handleDeleteFolder(folder)}
                                            className="text-destructive"
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 p-6">
                    {/* Header */}
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold">Video Library</h1>
                            <p className="text-muted-foreground">
                                Manage your video library before uploading to YouTube
                            </p>
                        </div>
                        <Button onClick={() => router.push("/dashboard/videos/library/upload")}>
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Video
                        </Button>
                    </div>

                    {/* Filters */}
                    <div className="mb-6 space-y-4">
                        <div className="flex items-center gap-4">
                            <div className="flex-1">
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="Search videos..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                                        className="max-w-md"
                                    />
                                    <Button onClick={handleSearch}>
                                        <Search className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>

                            <Button
                                variant={bulkSelectionMode ? "secondary" : "outline"}
                                size="sm"
                                onClick={toggleBulkSelection}
                            >
                                {bulkSelectionMode ? (
                                    <>
                                        <CheckSquare className="mr-2 h-4 w-4" />
                                        Exit Selection
                                    </>
                                ) : (
                                    <>
                                        <Square className="mr-2 h-4 w-4" />
                                        Select Multiple
                                    </>
                                )}
                            </Button>

                            {bulkSelectionMode && videos.length > 0 && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={toggleSelectAll}
                                >
                                    {selectedVideoIds.size === videos.length ? "Deselect All" : "Select All"}
                                </Button>
                            )}

                            <Select
                                value={filters.sortBy}
                                onValueChange={(value) => setFilters({ ...filters, sortBy: value as any })}
                            >
                                <SelectTrigger className="w-40">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="created_at">Date</SelectItem>
                                    <SelectItem value="title">Title</SelectItem>
                                    <SelectItem value="duration">Duration</SelectItem>
                                    <SelectItem value="file_size">File Size</SelectItem>
                                </SelectContent>
                            </Select>

                            <div className="flex gap-1">
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

                        {/* Advanced Filters */}
                        <AdvancedFilterPanel
                            filters={advancedFilters}
                            onFiltersChange={setAdvancedFilters}
                            availableTags={[]} // TODO: Extract from videos
                        />
                    </div>

                    {/* Videos Grid/List */}
                    {loading ? (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {[...Array(6)].map((_, i) => (
                                <Card key={i}>
                                    <CardContent className="p-4">
                                        <Skeleton className="mb-2 h-40 w-full" />
                                        <Skeleton className="mb-2 h-4 w-3/4" />
                                        <Skeleton className="h-4 w-1/2" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : videos.length === 0 ? (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12">
                                <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
                                <h3 className="mb-2 text-lg font-semibold">No videos yet</h3>
                                <p className="mb-4 text-muted-foreground">
                                    Upload your first video to get started
                                </p>
                                <Button onClick={() => router.push("/dashboard/videos/library/upload")}>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload Video
                                </Button>
                            </CardContent>
                        </Card>
                    ) : viewMode === "grid" ? (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {videos.map((video) => (
                                <Card
                                    key={video.id}
                                    className={`overflow-hidden transition-opacity ${draggedVideoId === video.id ? "opacity-50" : ""
                                        }`}
                                >
                                    <div
                                        className="relative aspect-video bg-muted cursor-grab active:cursor-grabbing"
                                        draggable={!bulkSelectionMode}
                                        onDragStart={(e) => handleDragStart(e, video.id)}
                                        onDragEnd={handleDragEnd}
                                    >
                                        {bulkSelectionMode && (
                                            <div className="absolute top-2 left-2 z-10">
                                                <Button
                                                    variant={selectedVideoIds.has(video.id) ? "default" : "secondary"}
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={() => toggleVideoSelection(video.id)}
                                                >
                                                    {selectedVideoIds.has(video.id) ? (
                                                        <CheckSquare className="h-4 w-4" />
                                                    ) : (
                                                        <Square className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>
                                        )}
                                        {video.thumbnailUrl ? (
                                            <img
                                                src={video.thumbnailUrl}
                                                alt={video.title}
                                                className="h-full w-full object-cover"
                                            />
                                        ) : (
                                            <div className="flex h-full items-center justify-center">
                                                <Play className="h-12 w-12 text-muted-foreground" />
                                            </div>
                                        )}
                                        <div className="absolute bottom-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
                                            {formatDuration(video.duration)}
                                        </div>
                                    </div>
                                    <CardContent className="p-4">
                                        <div className="mb-2 flex items-start justify-between">
                                            <h3
                                                className="line-clamp-2 font-semibold cursor-pointer hover:text-primary transition-colors"
                                                onClick={() => router.push(`/dashboard/videos/library/${video.id}`)}
                                            >
                                                {video.title}
                                            </h3>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                        <MoreVertical className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    {/* TODO: Task 3.4 - Navigate to video detail page */}
                                                    <DropdownMenuItem onClick={() => router.push(`/dashboard/videos/library/${video.id}`)}>
                                                        <Edit className="mr-2 h-4 w-4" />
                                                        Edit
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleToggleFavorite(video.id)}>
                                                        <Star className="mr-2 h-4 w-4" />
                                                        {video.isFavorite ? "Unfavorite" : "Favorite"}
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleMoveVideo(video)}>
                                                        <Folder className="mr-2 h-4 w-4" />
                                                        Move to Folder
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleUploadToYouTube(video)}>
                                                        <Upload className="mr-2 h-4 w-4" />
                                                        Upload to YouTube
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleCreateStream(video)}>
                                                        <Radio className="mr-2 h-4 w-4" />
                                                        Create Stream
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem
                                                        onClick={() => handleDeleteVideo(video)}
                                                        className="text-destructive"
                                                    >
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        Delete
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <VideoUsageBadgeCompact video={video} />
                                            <span>•</span>
                                            <span>{formatFileSize(video.fileSize)}</span>
                                            {video.isFavorite && (
                                                <>
                                                    <span>•</span>
                                                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                                </>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {videos.map((video) => (
                                <Card
                                    key={video.id}
                                    className={`transition-opacity ${draggedVideoId === video.id ? "opacity-50" : ""
                                        }`}
                                >
                                    <CardContent className="flex items-center gap-4 p-4">
                                        {bulkSelectionMode && (
                                            <Button
                                                variant={selectedVideoIds.has(video.id) ? "default" : "secondary"}
                                                size="icon"
                                                className="h-8 w-8 flex-shrink-0"
                                                onClick={() => toggleVideoSelection(video.id)}
                                            >
                                                {selectedVideoIds.has(video.id) ? (
                                                    <CheckSquare className="h-4 w-4" />
                                                ) : (
                                                    <Square className="h-4 w-4" />
                                                )}
                                            </Button>
                                        )}
                                        <div
                                            className="h-20 w-32 flex-shrink-0 overflow-hidden rounded bg-muted cursor-grab active:cursor-grabbing"
                                            draggable={!bulkSelectionMode}
                                            onDragStart={(e) => handleDragStart(e, video.id)}
                                            onDragEnd={handleDragEnd}
                                        >
                                            {video.thumbnailUrl ? (
                                                <img
                                                    src={video.thumbnailUrl}
                                                    alt={video.title}
                                                    className="h-full w-full object-cover"
                                                />
                                            ) : (
                                                <div className="flex h-full items-center justify-center">
                                                    <Play className="h-8 w-8 text-muted-foreground" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <h3
                                                className="font-semibold cursor-pointer hover:text-primary transition-colors"
                                                onClick={() => router.push(`/dashboard/videos/library/${video.id}`)}
                                            >
                                                {video.title}
                                            </h3>
                                            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                                                <VideoUsageBadgeCompact video={video} />
                                                <span>•</span>
                                                <span>{formatDuration(video.duration)}</span>
                                                <span>•</span>
                                                <span>{formatFileSize(video.fileSize)}</span>
                                                {video.isFavorite && (
                                                    <>
                                                        <span>•</span>
                                                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon">
                                                    <MoreVertical className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                {/* TODO: Task 3.4 - Navigate to video detail page */}
                                                <DropdownMenuItem onClick={() => router.push(`/dashboard/videos/library/${video.id}`)}>
                                                    <Edit className="mr-2 h-4 w-4" />
                                                    Edit
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleToggleFavorite(video.id)}>
                                                    <Star className="mr-2 h-4 w-4" />
                                                    {video.isFavorite ? "Unfavorite" : "Favorite"}
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleMoveVideo(video)}>
                                                    <Folder className="mr-2 h-4 w-4" />
                                                    Move to Folder
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleUploadToYouTube(video)}>
                                                    <Upload className="mr-2 h-4 w-4" />
                                                    Upload to YouTube
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleCreateStream(video)}>
                                                    <Radio className="mr-2 h-4 w-4" />
                                                    Create Stream
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={() => handleDeleteVideo(video)}
                                                    className="text-destructive"
                                                >
                                                    <Trash2 className="mr-2 h-4 w-4" />
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {/* Pagination */}
                    {pagination.totalPages > 1 && (
                        <div className="mt-6 flex items-center justify-between">
                            <p className="text-sm text-muted-foreground">
                                Showing {(pagination.page - 1) * pagination.pageSize + 1} to{" "}
                                {Math.min(pagination.page * pagination.pageSize, pagination.total)} of{" "}
                                {pagination.total} videos
                            </p>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    disabled={pagination.page === 1}
                                    onClick={() => setFilters({ ...filters, page: pagination.page - 1 })}
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    disabled={pagination.page === pagination.totalPages}
                                    onClick={() => setFilters({ ...filters, page: pagination.page + 1 })}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Dialogs */}
            <CreateFolderDialog
                open={createFolderOpen}
                onOpenChange={setCreateFolderOpen}
                onSuccess={handleDialogSuccess}
                folders={folders}
            />
            <EditFolderDialog
                open={editFolderOpen}
                onOpenChange={setEditFolderOpen}
                onSuccess={handleDialogSuccess}
                folder={selectedFolderForEdit}
                folders={folders}
            />
            <DeleteFolderDialog
                open={deleteFolderOpen}
                onOpenChange={setDeleteFolderOpen}
                onSuccess={handleDialogSuccess}
                folder={selectedFolderForEdit}
                folders={folders}
                videoCount={selectedFolderForEdit ? videos.filter(v => v.folderId === selectedFolderForEdit.id).length : 0}
            />
            <MoveToFolderDialog
                open={moveToFolderOpen}
                onOpenChange={setMoveToFolderOpen}
                onSuccess={handleDialogSuccess}
                video={selectedVideoForMove}
                folders={folders}
            />
            <UploadToYouTubeDialog
                open={uploadToYouTubeOpen}
                onOpenChange={setUploadToYouTubeOpen}
                onSuccess={handleDialogSuccess}
                video={selectedVideoForUpload}
                accounts={youtubeAccounts}
            />
            <CreateStreamDialog
                open={createStreamOpen}
                onOpenChange={setCreateStreamOpen}
                onSuccess={handleStreamCreated}
                video={selectedVideoForStream}
                accounts={youtubeAccounts}
            />
            <BulkUploadDialog
                open={bulkUploadOpen}
                onOpenChange={setBulkUploadOpen}
                onSuccess={handleBulkSuccess}
                videos={selectedVideos}
                accounts={youtubeAccounts}
            />
            <BulkMoveDialog
                open={bulkMoveOpen}
                onOpenChange={setBulkMoveOpen}
                onSuccess={handleBulkSuccess}
                videos={selectedVideos}
                folders={folders}
            />
            <BulkDeleteDialog
                open={bulkDeleteOpen}
                onOpenChange={setBulkDeleteOpen}
                onSuccess={handleBulkSuccess}
                videos={selectedVideos}
            />

            {/* Delete Video Confirmation Dialog */}
            <ConfirmDialog
                open={deleteVideoOpen}
                onOpenChange={setDeleteVideoOpen}
                title="Delete Video"
                description={videoToDelete ? `Are you sure you want to delete "${videoToDelete.title}"? This action cannot be undone.` : ""}
                confirmText="Delete"
                cancelText="Cancel"
                variant="destructive"
                onConfirm={confirmDeleteVideo}
            />

            {/* Bulk Actions Bar */}
            <BulkActionsBar
                selectedCount={selectedVideoIds.size}
                onUploadToYouTube={handleBulkUpload}
                onMoveToFolder={handleBulkMove}
                onAddTags={() => { }} // TODO: Implement bulk add tags
                onDelete={handleBulkDelete}
                onClearSelection={clearSelection}
            />
        </DashboardLayout>
    )
}
