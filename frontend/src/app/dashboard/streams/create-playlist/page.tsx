"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    ArrowLeft,
    Plus,
    Trash2,
    GripVertical,
    Play,
    Clock,
    Repeat,
    Settings,
    Video,
    Check,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { streamsApi, type CreateLiveEventRequest } from "@/lib/api/streams"
import { videosApi } from "@/lib/api/videos"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount, Video as VideoType } from "@/types"

interface PlaylistItem {
    id: string
    videoId: string
    title: string
    thumbnailUrl: string
    duration: number
    transition: "cut" | "fade" | "crossfade"
}

const TRANSITIONS = [
    { value: "cut", label: "Cut (Instant)" },
    { value: "fade", label: "Fade (1s)" },
    { value: "crossfade", label: "Crossfade (2s)" },
]

function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
}

function VideoSelector({
    videos,
    selectedIds,
    onSelect,
    loading,
}: {
    videos: VideoType[]
    selectedIds: Set<string>
    onSelect: (video: VideoType) => void
    loading: boolean
}) {
    const [search, setSearch] = useState("")

    const filteredVideos = videos.filter((v) =>
        v.title.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="space-y-4">
            <Input
                placeholder="Search videos..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
            />
            <div className="max-h-[400px] overflow-y-auto space-y-2">
                {loading ? (
                    [...Array(5)].map((_, i) => (
                        <div key={i} className="flex items-center gap-3 p-2">
                            <Skeleton className="w-24 h-14" />
                            <div className="flex-1">
                                <Skeleton className="h-4 w-3/4 mb-2" />
                                <Skeleton className="h-3 w-1/4" />
                            </div>
                        </div>
                    ))
                ) : filteredVideos.length === 0 ? (
                    <p className="text-center text-muted-foreground py-8">No videos found</p>
                ) : (
                    filteredVideos.map((video) => (
                        <div
                            key={video.id}
                            onClick={() => onSelect(video)}
                            className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${selectedIds.has(video.id)
                                ? "bg-primary/10 border-2 border-primary"
                                : "hover:bg-muted border-2 border-transparent"
                                }`}
                        >
                            <img
                                src={video.thumbnailUrl || "/placeholder-thumbnail.jpg"}
                                alt={video.title}
                                className="w-24 h-14 object-cover rounded"
                            />
                            <div className="flex-1 min-w-0">
                                <p className="font-medium truncate">{video.title}</p>
                                <p className="text-sm text-muted-foreground">
                                    {video.viewCount.toLocaleString()} views
                                </p>
                            </div>
                            {selectedIds.has(video.id) && (
                                <Check className="h-5 w-5 text-primary" />
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default function CreatePlaylistStreamPage() {
    const router = useRouter()
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [videos, setVideos] = useState<VideoType[]>([])
    const [loading, setLoading] = useState(true)
    const [videosLoading, setVideosLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [videoSelectorOpen, setVideoSelectorOpen] = useState(false)

    // Form state
    const [accountId, setAccountId] = useState("")
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [playlist, setPlaylist] = useState<PlaylistItem[]>([])
    const [loopEnabled, setLoopEnabled] = useState(true)
    const [loopCount, setLoopCount] = useState<number | "infinite">("infinite")
    const [defaultTransition, setDefaultTransition] = useState<PlaylistItem["transition"]>("cut")

    useEffect(() => {
        loadAccounts()
    }, [])

    useEffect(() => {
        if (accountId) {
            loadVideos()
        }
    }, [accountId])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            const accountList = Array.isArray(data) ? data : []
            setAccounts(accountList.filter((a) => a.hasLiveStreamingEnabled))
        } catch (error) {
            console.error("Failed to load accounts:", error)
        } finally {
            setLoading(false)
        }
    }

    const loadVideos = async () => {
        try {
            setVideosLoading(true)
            const response = await videosApi.getVideos({ accountId, pageSize: 100 })
            setVideos(response.items || [])
        } catch (error) {
            console.error("Failed to load videos:", error)
        } finally {
            setVideosLoading(false)
        }
    }

    const addVideoToPlaylist = (video: VideoType) => {
        if (playlist.some((item) => item.videoId === video.id)) {
            // Remove if already in playlist
            setPlaylist((prev) => prev.filter((item) => item.videoId !== video.id))
        } else {
            // Add to playlist
            const newItem: PlaylistItem = {
                id: `${Date.now()}-${video.id}`,
                videoId: video.id,
                title: video.title,
                thumbnailUrl: video.thumbnailUrl,
                duration: 0, // Would come from video metadata
                transition: defaultTransition,
            }
            setPlaylist((prev) => [...prev, newItem])
        }
    }

    const removeFromPlaylist = (itemId: string) => {
        setPlaylist((prev) => prev.filter((item) => item.id !== itemId))
    }

    const updateItemTransition = (itemId: string, transition: PlaylistItem["transition"]) => {
        setPlaylist((prev) =>
            prev.map((item) => (item.id === itemId ? { ...item, transition } : item))
        )
    }

    const moveItem = (fromIndex: number, toIndex: number) => {
        if (toIndex < 0 || toIndex >= playlist.length) return
        const newPlaylist = [...playlist]
        const [removed] = newPlaylist.splice(fromIndex, 1)
        newPlaylist.splice(toIndex, 0, removed)
        setPlaylist(newPlaylist)
    }

    const handleSubmit = async () => {
        if (!accountId || !title.trim() || playlist.length === 0) {
            alert("Please fill in all required fields and add at least one video")
            return
        }

        try {
            setSubmitting(true)
            const request: CreateLiveEventRequest = {
                account_id: accountId,
                title,
                description: description || undefined,
                scheduled_start: new Date().toISOString(),
                enable_dvr: true,
                enable_auto_start: true,
            }

            const event = await streamsApi.createEvent(request)

            // Add playlist items
            for (const item of playlist) {
                await streamsApi.addPlaylistItem(event.id, {
                    video_url: item.videoId,
                    title: item.title,
                    duration: item.duration,
                })
            }

            router.push(`/dashboard/streams/${event.id}/control`)
        } catch (error) {
            console.error("Failed to create playlist stream:", error)
            alert("Failed to create playlist stream. Please try again.")
        } finally {
            setSubmitting(false)
        }
    }

    const selectedVideoIds = new Set(playlist.map((item) => item.videoId))
    const totalDuration = playlist.reduce((sum, item) => sum + item.duration, 0)

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: "Create Playlist Stream" },
            ]}
        >
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/streams")}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold">Create Playlist Stream</h1>
                        <p className="text-muted-foreground">
                            Stream videos from your library in a continuous loop
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Form */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Basic Info */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle>Stream Details</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="account">YouTube Account *</Label>
                                    <Select value={accountId} onValueChange={setAccountId}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accounts.map((account) => (
                                                <SelectItem key={account.id} value={account.id}>
                                                    {account.channelTitle}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="title">Stream Title *</Label>
                                    <Input
                                        id="title"
                                        placeholder="Enter stream title"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        maxLength={100}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="description">Description</Label>
                                    <Textarea
                                        id="description"
                                        placeholder="Describe your stream..."
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        rows={3}
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Playlist Builder */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle>Playlist</CardTitle>
                                        <CardDescription>
                                            Drag to reorder videos. {playlist.length} video(s) added.
                                        </CardDescription>
                                    </div>
                                    <Dialog open={videoSelectorOpen} onOpenChange={setVideoSelectorOpen}>
                                        <DialogTrigger asChild>
                                            <Button disabled={!accountId}>
                                                <Plus className="mr-2 h-4 w-4" />
                                                Add Videos
                                            </Button>
                                        </DialogTrigger>
                                        <DialogContent className="max-w-2xl">
                                            <DialogHeader>
                                                <DialogTitle>Select Videos</DialogTitle>
                                            </DialogHeader>
                                            <VideoSelector
                                                videos={videos}
                                                selectedIds={selectedVideoIds}
                                                onSelect={addVideoToPlaylist}
                                                loading={videosLoading}
                                            />
                                            <div className="flex justify-end">
                                                <Button onClick={() => setVideoSelectorOpen(false)}>
                                                    Done ({playlist.length} selected)
                                                </Button>
                                            </div>
                                        </DialogContent>
                                    </Dialog>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {playlist.length === 0 ? (
                                    <div className="text-center py-8 border-2 border-dashed rounded-lg">
                                        <Video className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                                        <p className="text-muted-foreground">
                                            {accountId
                                                ? "Click 'Add Videos' to build your playlist"
                                                : "Select an account first"}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        {playlist.map((item, index) => (
                                            <div
                                                key={item.id}
                                                className="flex items-center gap-3 p-3 bg-muted rounded-lg group"
                                            >
                                                <div className="flex flex-col gap-1">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-6 w-6"
                                                        onClick={() => moveItem(index, index - 1)}
                                                        disabled={index === 0}
                                                    >
                                                        ↑
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-6 w-6"
                                                        onClick={() => moveItem(index, index + 1)}
                                                        disabled={index === playlist.length - 1}
                                                    >
                                                        ↓
                                                    </Button>
                                                </div>
                                                <GripVertical className="h-5 w-5 text-muted-foreground cursor-grab" />
                                                <span className="text-sm font-medium w-6">{index + 1}</span>
                                                <img
                                                    src={item.thumbnailUrl || "/placeholder-thumbnail.jpg"}
                                                    alt={item.title}
                                                    className="w-20 h-12 object-cover rounded"
                                                />
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium truncate">{item.title}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {formatDuration(item.duration)}
                                                    </p>
                                                </div>
                                                <Select
                                                    value={item.transition}
                                                    onValueChange={(value) =>
                                                        updateItemTransition(item.id, value as PlaylistItem["transition"])
                                                    }
                                                >
                                                    <SelectTrigger className="w-32">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {TRANSITIONS.map((t) => (
                                                            <SelectItem key={t.value} value={t.value}>
                                                                {t.label}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => removeFromPlaylist(item.id)}
                                                    className="opacity-0 group-hover:opacity-100"
                                                >
                                                    <Trash2 className="h-4 w-4 text-destructive" />
                                                </Button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Loop Settings */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Repeat className="h-5 w-5" />
                                    Loop Settings
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label>Enable Loop</Label>
                                    <Switch checked={loopEnabled} onCheckedChange={setLoopEnabled} />
                                </div>

                                {loopEnabled && (
                                    <div className="space-y-2">
                                        <Label>Loop Count</Label>
                                        <Select
                                            value={loopCount.toString()}
                                            onValueChange={(value) =>
                                                setLoopCount(value === "infinite" ? "infinite" : parseInt(value))
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="infinite">Infinite</SelectItem>
                                                <SelectItem value="1">1 time</SelectItem>
                                                <SelectItem value="2">2 times</SelectItem>
                                                <SelectItem value="3">3 times</SelectItem>
                                                <SelectItem value="5">5 times</SelectItem>
                                                <SelectItem value="10">10 times</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Default Transition */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Settings className="h-5 w-5" />
                                    Default Transition
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <Select
                                    value={defaultTransition}
                                    onValueChange={(value) =>
                                        setDefaultTransition(value as PlaylistItem["transition"])
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {TRANSITIONS.map((t) => (
                                            <SelectItem key={t.value} value={t.value}>
                                                {t.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-muted-foreground mt-2">
                                    Applied to newly added videos
                                </p>
                            </CardContent>
                        </Card>

                        {/* Summary */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-lg">Summary</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Videos</span>
                                    <span className="font-medium">{playlist.length}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Total Duration</span>
                                    <span className="font-medium">{formatDuration(totalDuration)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Loop</span>
                                    <span className="font-medium">
                                        {loopEnabled ? (loopCount === "infinite" ? "∞" : `${loopCount}x`) : "Off"}
                                    </span>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t">
                    <Button variant="outline" onClick={() => router.push("/dashboard/streams")}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!accountId || !title.trim() || playlist.length === 0 || submitting}
                        className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                    >
                        <Play className="mr-2 h-4 w-4" />
                        {submitting ? "Creating..." : "Create Playlist Stream"}
                    </Button>
                </div>
            </div>
        </DashboardLayout>
    )
}
