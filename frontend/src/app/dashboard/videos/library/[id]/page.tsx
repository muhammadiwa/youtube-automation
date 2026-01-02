/**
 * Video Detail Page
 * 
 * Detailed view of a single video with player, metadata editor, and actions.
 * Requirements: 1.1, 1.3, 2.1, 3.1, 4.2
 * Design: VideoDetailPage component
 */

"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import {
    ArrowLeft,
    Play,
    Upload,
    Radio,
    Trash2,
    Star,
    Folder,
    Loader2,
    Youtube,
    ExternalLink,
    Clock,
    HardDrive,
    Film,
    Eye
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toast"
import { VideoUsageBadgeFull } from "@/components/videos/video-usage-badge"
import { UploadToYouTubeDialog } from "@/components/videos/upload-to-youtube-dialog"
import { CreateStreamDialog } from "@/components/videos/create-stream-dialog"
import { MoveToFolderDialog } from "@/components/videos/move-to-folder-dialog"
import { VideoPlayer } from "@/components/videos/video-player"
import { VideoUsageHistory } from "@/components/videos/video-usage-history"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"
import { accountsApi } from "@/lib/api/accounts"
import type { Video, YouTubeAccount } from "@/types"

export default function VideoDetailPage() {
    const router = useRouter()
    const params = useParams()
    const videoId = params.id as string
    const { addToast } = useToast()

    // State
    const [video, setVideo] = useState<Video | null>(null)
    const [folders, setFolders] = useState<VideoFolder[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [editing, setEditing] = useState(false)
    const [streamUrl, setStreamUrl] = useState<string | null>(null)

    // Form data
    const [formData, setFormData] = useState({
        title: "",
        description: "",
        tags: [] as string[],
        notes: "",
    })
    const [tagInput, setTagInput] = useState("")

    // Dialogs
    const [uploadToYouTubeOpen, setUploadToYouTubeOpen] = useState(false)
    const [createStreamOpen, setCreateStreamOpen] = useState(false)
    const [moveToFolderOpen, setMoveToFolderOpen] = useState(false)
    const [youtubeAccounts, setYoutubeAccounts] = useState<YouTubeAccount[]>([])

    // Load data
    useEffect(() => {
        loadVideo()
        loadFolders()
        loadYouTubeAccounts()
    }, [videoId])

    // Load stream URL after video is loaded
    useEffect(() => {
        if (video) {
            loadStreamUrl()
        }
    }, [video?.id, video?.filePath])

    const loadStreamUrl = async () => {
        // Only set stream URL if video has a local file
        // Videos imported from YouTube won't have a local file
        if (!video?.filePath) {
            setStreamUrl(null)
            return
        }

        // For local storage, we use the stream endpoint directly
        // The endpoint returns the video file directly
        // We need to add auth token as query parameter for video element to access
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

        // Get token from localStorage - key is "auth_access_token" as defined in auth-provider
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_access_token') : null

        if (token) {
            setStreamUrl(`${apiUrl}/videos/library/${videoId}/stream?token=${encodeURIComponent(token)}`)
        } else {
            // Try without token - will fail if auth required
            setStreamUrl(`${apiUrl}/videos/library/${videoId}/stream`)
        }
    }

    const loadVideo = async () => {
        try {
            setLoading(true)
            const data = await videoLibraryApi.getLibraryVideo(videoId)
            setVideo(data)
            setFormData({
                title: data.title,
                description: data.description || "",
                tags: data.tags || [],
                notes: data.notes || "",
            })
        } catch (error) {
            console.error("Failed to load video:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to load video",
            })
            router.push("/dashboard/videos/library")
        } finally {
            setLoading(false)
        }
    }

    const loadFolders = async () => {
        try {
            const data = await videoLibraryApi.getAllFolders()
            setFolders(data)
        } catch (error) {
            console.error("Failed to load folders:", error)
        }
    }

    const loadYouTubeAccounts = async () => {
        try {
            const accounts = await accountsApi.getAccounts()
            setYoutubeAccounts(accounts)
        } catch (error) {
            console.error("Failed to load YouTube accounts:", error)
        }
    }

    const handleSave = async () => {
        if (!video) return

        try {
            setSaving(true)
            await videoLibraryApi.updateMetadata(video.id, {
                title: formData.title,
                description: formData.description || undefined,
                tags: formData.tags.length > 0 ? formData.tags : undefined,
                notes: formData.notes || undefined,
            })

            addToast({
                type: "success",
                title: "Success",
                description: "Video metadata updated",
            })

            setEditing(false)
            loadVideo()
        } catch (error: any) {
            console.error("Failed to update metadata:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to update metadata",
            })
        } finally {
            setSaving(false)
        }
    }

    const handleCancel = () => {
        if (video) {
            setFormData({
                title: video.title,
                description: video.description || "",
                tags: video.tags || [],
                notes: video.notes || "",
            })
        }
        setEditing(false)
    }

    const handleToggleFavorite = async () => {
        if (!video) return

        try {
            await videoLibraryApi.toggleFavorite(video.id)
            loadVideo()
            addToast({
                type: "success",
                title: "Success",
                description: video.isFavorite ? "Removed from favorites" : "Added to favorites",
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

    const handleDelete = async () => {
        if (!video || !confirm("Are you sure you want to delete this video? This action cannot be undone.")) return

        try {
            await videoLibraryApi.deleteFromLibrary(video.id)
            addToast({
                type: "success",
                title: "Success",
                description: "Video deleted successfully",
            })
            router.push("/dashboard/videos/library")
        } catch (error) {
            console.error("Failed to delete video:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to delete video",
            })
        }
    }

    const handleAddTag = () => {
        const tag = tagInput.trim()
        if (tag && !formData.tags.includes(tag)) {
            setFormData({ ...formData, tags: [...formData.tags, tag] })
            setTagInput("")
        }
    }

    const handleRemoveTag = (tagToRemove: string) => {
        setFormData({
            ...formData,
            tags: formData.tags.filter((tag) => tag !== tagToRemove),
        })
    }

    const formatDuration = (seconds: number | null | undefined) => {
        if (!seconds) return "N/A"
        const hours = Math.floor(seconds / 3600)
        const mins = Math.floor((seconds % 3600) / 60)
        const secs = seconds % 60
        if (hours > 0) {
            return `${hours}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
        }
        return `${mins}:${secs.toString().padStart(2, "0")}`
    }

    const formatFileSize = (bytes: number | null | undefined) => {
        if (!bytes) return "N/A"
        const gb = bytes / (1024 * 1024 * 1024)
        if (gb >= 1) return `${gb.toFixed(2)} GB`
        const mb = bytes / (1024 * 1024)
        return `${mb.toFixed(2)} MB`
    }

    const formatDate = (date: string | null | undefined) => {
        if (!date) return "N/A"
        return new Date(date).toLocaleString()
    }

    if (loading) {
        return (
            <DashboardLayout>
                <div className="p-6">
                    <Skeleton className="mb-4 h-8 w-64" />
                    <div className="grid gap-6 lg:grid-cols-3">
                        <div className="lg:col-span-2">
                            <Skeleton className="mb-4 h-96 w-full" />
                            <Skeleton className="h-64 w-full" />
                        </div>
                        <div>
                            <Skeleton className="h-96 w-full" />
                        </div>
                    </div>
                </div>
            </DashboardLayout>
        )
    }

    if (!video) return null

    const currentFolder = video.folderId ? folders.find((f) => f.id === video.folderId) : null

    return (
        <DashboardLayout>
            <div className="p-6">
                {/* Header */}
                <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push("/dashboard/videos/library")}
                        >
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                        <div>
                            <h1 className="text-3xl font-bold">{video.title}</h1>
                            <div className="mt-1 flex items-center gap-2">
                                <VideoUsageBadgeFull video={video} />
                                {video.isFavorite && (
                                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={handleToggleFavorite}
                        >
                            <Star
                                className={`h-4 w-4 ${video.isFavorite ? "fill-yellow-400 text-yellow-400" : ""
                                    }`}
                            />
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => setUploadToYouTubeOpen(true)}
                        >
                            <Upload className="mr-2 h-4 w-4" />
                            Upload to YouTube
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => setCreateStreamOpen(true)}
                        >
                            <Radio className="mr-2 h-4 w-4" />
                            Create Stream
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDelete}
                        >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                        </Button>
                    </div>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Main Content */}
                    <div className="space-y-6 lg:col-span-2">
                        {/* Video Player */}
                        <Card>
                            <CardContent className="p-0">
                                {streamUrl && video.filePath ? (
                                    <VideoPlayer
                                        videoUrl={streamUrl}
                                        poster={video.thumbnailUrl}
                                        className="aspect-video"
                                        onError={(error) => {
                                            console.error("Video player error:", error)
                                            addToast({
                                                type: "error",
                                                title: "Playback Error",
                                                description: error.message,
                                            })
                                        }}
                                    />
                                ) : video.youtubeId ? (
                                    // Show YouTube embed for videos imported from YouTube
                                    <div className="aspect-video">
                                        <iframe
                                            src={`https://www.youtube.com/embed/${video.youtubeId}`}
                                            title={video.title}
                                            className="w-full h-full"
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                            allowFullScreen
                                        />
                                    </div>
                                ) : (
                                    <div className="aspect-video bg-muted flex items-center justify-center">
                                        <div className="text-center text-muted-foreground">
                                            <Play className="h-12 w-12 mx-auto mb-2" />
                                            <p>Video preview not available</p>
                                            <p className="text-sm">No local file or YouTube video linked</p>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Metadata Editor */}
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle>Video Information</CardTitle>
                                    {!editing ? (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setEditing(true)}
                                        >
                                            Edit
                                        </Button>
                                    ) : (
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={handleCancel}
                                                disabled={saving}
                                            >
                                                Cancel
                                            </Button>
                                            <Button
                                                size="sm"
                                                onClick={handleSave}
                                                disabled={saving}
                                            >
                                                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                Save
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Title */}
                                <div className="space-y-2">
                                    <Label htmlFor="title">Title</Label>
                                    {editing ? (
                                        <Input
                                            id="title"
                                            value={formData.title}
                                            onChange={(e) =>
                                                setFormData({ ...formData, title: e.target.value })
                                            }
                                            disabled={saving}
                                        />
                                    ) : (
                                        <p className="text-sm">{video.title}</p>
                                    )}
                                </div>

                                {/* Description */}
                                <div className="space-y-2">
                                    <Label htmlFor="description">Description</Label>
                                    {editing ? (
                                        <Textarea
                                            id="description"
                                            value={formData.description}
                                            onChange={(e) =>
                                                setFormData({ ...formData, description: e.target.value })
                                            }
                                            rows={4}
                                            disabled={saving}
                                        />
                                    ) : (
                                        <p className="text-sm text-muted-foreground">
                                            {video.description || "No description"}
                                        </p>
                                    )}
                                </div>

                                {/* Tags */}
                                <div className="space-y-2">
                                    <Label>Tags</Label>
                                    {editing ? (
                                        <>
                                            <div className="flex gap-2">
                                                <Input
                                                    value={tagInput}
                                                    onChange={(e) => setTagInput(e.target.value)}
                                                    onKeyDown={(e) => {
                                                        if (e.key === "Enter") {
                                                            e.preventDefault()
                                                            handleAddTag()
                                                        }
                                                    }}
                                                    placeholder="Add tag"
                                                    disabled={saving}
                                                />
                                                <Button
                                                    type="button"
                                                    variant="outline"
                                                    onClick={handleAddTag}
                                                    disabled={saving || !tagInput.trim()}
                                                >
                                                    Add
                                                </Button>
                                            </div>
                                            {formData.tags.length > 0 && (
                                                <div className="flex flex-wrap gap-2">
                                                    {formData.tags.map((tag) => (
                                                        <div
                                                            key={tag}
                                                            className="flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-sm"
                                                        >
                                                            <span>{tag}</span>
                                                            <button
                                                                type="button"
                                                                onClick={() => handleRemoveTag(tag)}
                                                                className="text-muted-foreground hover:text-foreground"
                                                                disabled={saving}
                                                            >
                                                                ×
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </>
                                    ) : (
                                        <div className="flex flex-wrap gap-2">
                                            {video.tags && video.tags.length > 0 ? (
                                                video.tags.map((tag) => (
                                                    <Badge key={tag} variant="secondary">
                                                        {tag}
                                                    </Badge>
                                                ))
                                            ) : (
                                                <p className="text-sm text-muted-foreground">No tags</p>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Notes */}
                                <div className="space-y-2">
                                    <Label htmlFor="notes">Internal Notes</Label>
                                    {editing ? (
                                        <Textarea
                                            id="notes"
                                            value={formData.notes}
                                            onChange={(e) =>
                                                setFormData({ ...formData, notes: e.target.value })
                                            }
                                            rows={3}
                                            placeholder="Private notes (not uploaded to YouTube)"
                                            disabled={saving}
                                        />
                                    ) : (
                                        <p className="text-sm text-muted-foreground">
                                            {video.notes || "No notes"}
                                        </p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* File Info */}
                        <Card>
                            <CardHeader>
                                <CardTitle>File Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3 text-sm">
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        <Clock className="h-4 w-4" />
                                        Duration
                                    </span>
                                    <span className="font-medium">{formatDuration(video.duration)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        <HardDrive className="h-4 w-4" />
                                        File Size
                                    </span>
                                    <span className="font-medium">{formatFileSize(video.fileSize)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        <Film className="h-4 w-4" />
                                        Resolution
                                    </span>
                                    <span className="font-medium">{video.resolution || "N/A"}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">Format</span>
                                    <span className="font-medium">{video.format || "N/A"}</span>
                                </div>
                                <Separator />
                                <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">Created</span>
                                    <span className="font-medium">{formatDate(video.createdAt)}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">Updated</span>
                                    <span className="font-medium">{formatDate(video.updatedAt)}</span>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Folder */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Organization</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <div className="space-y-2">
                                    <Label>Folder</Label>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Folder
                                                className="h-4 w-4"
                                                style={{ color: currentFolder?.color || undefined }}
                                            />
                                            <span className="text-sm">
                                                {currentFolder ? currentFolder.name : "Root"}
                                            </span>
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setMoveToFolderOpen(true)}
                                        >
                                            Move
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* YouTube Info */}
                        {video.youtubeId && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Youtube className="h-5 w-5 text-red-600" />
                                        YouTube
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3 text-sm">
                                    <div className="flex items-center justify-between">
                                        <span className="flex items-center gap-2 text-muted-foreground">
                                            <Eye className="h-4 w-4" />
                                            Views
                                        </span>
                                        <span className="font-medium">{video.viewCount.toLocaleString()}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">Likes</span>
                                        <span className="font-medium">{video.likeCount.toLocaleString()}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">Comments</span>
                                        <span className="font-medium">{video.commentCount.toLocaleString()}</span>
                                    </div>
                                    <Separator />
                                    <Button
                                        variant="outline"
                                        className="w-full"
                                        onClick={() =>
                                            window.open(`https://youtube.com/watch?v=${video.youtubeId}`, "_blank")
                                        }
                                    >
                                        <ExternalLink className="mr-2 h-4 w-4" />
                                        View on YouTube
                                    </Button>
                                </CardContent>
                            </Card>
                        )}

                        {/* Streaming Info */}
                        {video.isUsedForStreaming && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Radio className="h-5 w-5 text-red-600" />
                                        Streaming
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3 text-sm">
                                    <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">Sessions</span>
                                        <span className="font-medium">{video.streamingCount}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">Total Duration</span>
                                        <span className="font-medium">
                                            {formatDuration(video.totalStreamingDuration || 0)}
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Usage History */}
                        <VideoUsageHistory videoId={videoId} onUpdate={loadVideo} />
                    </div>
                </div>
            </div>

            {/* Dialogs */}
            <UploadToYouTubeDialog
                open={uploadToYouTubeOpen}
                onOpenChange={setUploadToYouTubeOpen}
                onSuccess={loadVideo}
                video={video}
                accounts={youtubeAccounts}
            />
            <CreateStreamDialog
                open={createStreamOpen}
                onOpenChange={setCreateStreamOpen}
                onSuccess={(streamJobId) => {
                    addToast({
                        type: "success",
                        title: "Stream Created",
                        description: "Redirecting to stream control panel...",
                    })
                    router.push(`/dashboard/streams/${streamJobId}/control`)
                }}
                video={video}
                accounts={youtubeAccounts}
            />
            <MoveToFolderDialog
                open={moveToFolderOpen}
                onOpenChange={setMoveToFolderOpen}
                onSuccess={loadVideo}
                video={video}
                folders={folders}
            />
        </DashboardLayout>
    )
}
