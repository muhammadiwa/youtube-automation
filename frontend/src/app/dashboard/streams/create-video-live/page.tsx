"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    ArrowLeft,
    Video,
    Settings,
    Clock,
    Key,
    Play,
    Repeat,
    Infinity,
    Info,
    Eye,
    EyeOff,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Separator } from "@/components/ui/separator"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { useToast } from "@/components/ui/toast"
import { accountsApi } from "@/lib/api/accounts"
import { videosApi } from "@/lib/api/videos"
import { streamJobsApi, type CreateStreamJobRequest, type LoopMode, type Resolution, type EncodingMode } from "@/lib/api/stream-jobs"
import type { YouTubeAccount, Video as VideoType } from "@/types"

export default function CreateVideoToLivePage() {
    const router = useRouter()
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [videos, setVideos] = useState<VideoType[]>([])
    const [loadingVideos, setLoadingVideos] = useState(false)
    const [showStreamKey, setShowStreamKey] = useState(false)

    // Form state
    const [formData, setFormData] = useState({
        accountId: "",
        videoId: "",
        videoPath: "",
        title: "",
        description: "",
        // Loop settings
        loopMode: "infinite" as LoopMode,
        loopCount: 10,
        // Output settings
        resolution: "1080p" as Resolution,
        targetBitrate: 6000,
        encodingMode: "cbr" as EncodingMode,
        targetFps: 30,
        // Schedule settings
        scheduleEnabled: false,
        scheduledStartAt: "",
        scheduledEndAt: "",
        // Stream key
        rtmpUrl: "rtmp://a.rtmp.youtube.com/live2",
        streamKey: "",
        // Chat moderation
        enableChatModeration: true,
        // Auto-restart
        enableAutoRestart: true,
        maxRestarts: 5,
    })

    useEffect(() => {
        loadAccounts()
        loadVideos() // Load all videos from library on mount
    }, [])

    useEffect(() => {
        if (formData.accountId) {
            loadStreamKey(formData.accountId)
        }
    }, [formData.accountId])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadVideos = async () => {
        try {
            setLoadingVideos(true)
            // Get ALL videos from user's library (includes videos without accountId)
            const response = await videosApi.getLibraryVideos({ limit: 100 })
            // Filter only videos that have file_path (uploaded to server)
            const availableVideos = (response.items || []).filter((v) => v.filePath)
            setVideos(availableVideos)
        } catch (error) {
            console.error("Failed to load videos:", error)
        } finally {
            setLoadingVideos(false)
        }
    }

    const loadStreamKey = async (accountId: string) => {
        try {
            // First check if account already has stream key info
            const account = accounts.find((a) => a.id === accountId)
            if (account?.rtmpUrl) {
                setFormData((prev) => ({
                    ...prev,
                    rtmpUrl: account.rtmpUrl || "rtmp://a.rtmp.youtube.com/live2",
                }))
            }

            // Get full stream key status (includes actual key if synced)
            const status = await accountsApi.getStreamKeyStatus(accountId)

            // Auto-fill RTMP URL
            if (status.rtmpUrl) {
                setFormData((prev) => ({
                    ...prev,
                    rtmpUrl: status.rtmpUrl || prev.rtmpUrl,
                }))
            }

            // Auto-fill stream key if available
            if (status.streamKey) {
                setFormData((prev) => ({
                    ...prev,
                    streamKey: status.streamKey || "",
                }))
                addToast({
                    type: "success",
                    title: "Stream Key Loaded",
                    description: "Stream key auto-filled from your account settings.",
                })
            } else if (status.hasStreamKey && status.streamKeyMasked) {
                // Has key but couldn't decrypt (shouldn't happen normally)
                addToast({
                    type: "info",
                    title: "Stream Key Available",
                    description: `Stream key found (${status.streamKeyMasked}). Please enter it manually if not auto-filled.`,
                })
            }
        } catch (error) {
            console.error("Failed to load stream key:", error)
        }
    }

    const handleVideoSelect = (videoId: string) => {
        const video = videos.find((v) => v.id === videoId)
        if (video && video.filePath) {
            setFormData((prev) => ({
                ...prev,
                videoId,
                videoPath: video.filePath || "",
                title: prev.title || video.title,
                description: prev.description || video.description || "",
            }))
        }
    }

    // Get selected video details
    const selectedVideo = videos.find((v) => v.id === formData.videoId)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.accountId) {
            addToast({ type: "error", title: "Error", description: "Please select a YouTube account" })
            return
        }

        if (!formData.videoId || !formData.videoPath) {
            addToast({ type: "error", title: "Error", description: "Please select a video from your library" })
            return
        }

        if (!formData.streamKey) {
            addToast({ type: "error", title: "Error", description: "Please enter your YouTube stream key. Get it from YouTube Studio → Go Live → Stream" })
            return
        }

        if (!formData.title) {
            addToast({ type: "error", title: "Error", description: "Please enter a stream title" })
            return
        }

        try {
            setLoading(true)

            const request: CreateStreamJobRequest = {
                accountId: formData.accountId,
                videoId: formData.videoId || undefined,
                videoPath: formData.videoPath,
                title: formData.title,
                description: formData.description || undefined,
                loopMode: formData.loopMode,
                loopCount: formData.loopMode === "count" ? formData.loopCount : undefined,
                resolution: formData.resolution,
                targetBitrate: formData.targetBitrate,
                encodingMode: formData.encodingMode,
                targetFps: formData.targetFps,
                rtmpUrl: formData.rtmpUrl,
                streamKey: formData.streamKey,
                enableChatModeration: formData.enableChatModeration,
                scheduledStartAt: formData.scheduleEnabled && formData.scheduledStartAt
                    ? new Date(formData.scheduledStartAt).toISOString()
                    : undefined,
                scheduledEndAt: formData.scheduleEnabled && formData.scheduledEndAt
                    ? new Date(formData.scheduledEndAt).toISOString()
                    : undefined,
                enableAutoRestart: formData.enableAutoRestart,
                maxRestarts: formData.maxRestarts,
            }

            const job = await streamJobsApi.createStreamJob(request)

            addToast({
                type: "success",
                title: "Created",
                description: "Video-to-Live stream created successfully",
            })

            router.push(`/dashboard/streams/${job.id}/control`)
        } catch (error: unknown) {
            const err = error as { message?: string; detail?: string }
            console.error("Failed to create stream:", error)
            addToast({
                type: "error",
                title: "Error",
                description: err.detail || err.message || "Failed to create stream",
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: "Create Video-to-Live" },
            ]}
        >
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold">Create Video-to-Live Stream</h1>
                        <p className="text-muted-foreground">
                            Stream pre-recorded videos as live content 24/7
                        </p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Video Selection */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Video className="h-5 w-5" />
                                Video Source
                            </CardTitle>
                            <CardDescription>
                                Select a video from your library to stream as live content
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Info Box */}
                            <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                                <div className="flex gap-3">
                                    <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                                    <div className="text-sm">
                                        <p className="font-medium text-blue-700 dark:text-blue-300">What is Video-to-Live?</p>
                                        <p className="text-blue-600 dark:text-blue-400 mt-1">
                                            Stream pre-recorded videos as live content on YouTube. Perfect for 24/7 music streams,
                                            lofi channels, or re-streaming content. The video will appear as a live broadcast to viewers.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label>YouTube Account</Label>
                                    <Select
                                        value={formData.accountId}
                                        onValueChange={(value) =>
                                            setFormData((prev) => ({ ...prev, accountId: value, videoId: "", videoPath: "" }))
                                        }
                                    >
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
                                    <Label>Video from Library</Label>
                                    <Select
                                        value={formData.videoId}
                                        onValueChange={handleVideoSelect}
                                        disabled={loadingVideos}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder={
                                                loadingVideos
                                                    ? "Loading..."
                                                    : videos.length === 0
                                                        ? "No videos available"
                                                        : "Select video"
                                            } />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {videos.map((video) => (
                                                <SelectItem key={video.id} value={video.id}>
                                                    {video.title}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    {!loadingVideos && videos.length === 0 && (
                                        <p className="text-xs text-amber-600 dark:text-amber-400">
                                            No videos with local files found. Upload videos first to use Video-to-Live.
                                        </p>
                                    )}
                                </div>
                            </div>

                            {/* Selected Video Preview */}
                            {selectedVideo && (
                                <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                                    <div className="flex items-start gap-4">
                                        {selectedVideo.thumbnailUrl && (
                                            <img
                                                src={selectedVideo.thumbnailUrl}
                                                alt={selectedVideo.title}
                                                className="w-32 h-20 object-cover rounded"
                                            />
                                        )}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium truncate">{selectedVideo.title}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {selectedVideo.duration ? `Duration: ${Math.floor(selectedVideo.duration / 60)}:${(selectedVideo.duration % 60).toString().padStart(2, '0')}` : 'Duration unknown'}
                                            </p>
                                            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                                                ✓ Video file ready for streaming
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <Separator />

                            <div className="space-y-2">
                                <Label>Stream Title</Label>
                                <Input
                                    value={formData.title}
                                    onChange={(e) =>
                                        setFormData((prev) => ({ ...prev, title: e.target.value }))
                                    }
                                    placeholder="My 24/7 Live Stream"
                                />
                                <p className="text-xs text-muted-foreground">
                                    This title will appear on your YouTube live stream
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label>Description (optional)</Label>
                                <Textarea
                                    value={formData.description}
                                    onChange={(e) =>
                                        setFormData((prev) => ({ ...prev, description: e.target.value }))
                                    }
                                    placeholder="Stream description..."
                                    rows={3}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Loop Configuration */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Repeat className="h-5 w-5" />
                                Loop Settings
                            </CardTitle>
                            <CardDescription>
                                Configure how the video should loop
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <RadioGroup
                                value={formData.loopMode}
                                onValueChange={(value) =>
                                    setFormData((prev) => ({ ...prev, loopMode: value as LoopMode }))
                                }
                                className="space-y-3"
                            >
                                <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                                    <RadioGroupItem value="infinite" id="infinite" />
                                    <Label htmlFor="infinite" className="flex-1 cursor-pointer">
                                        <div className="flex items-center gap-2">
                                            <Infinity className="h-4 w-4" />
                                            <span className="font-medium">Infinite Loop (24/7)</span>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            Stream continuously until manually stopped
                                        </p>
                                    </Label>
                                </div>

                                <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                                    <RadioGroupItem value="count" id="count" />
                                    <Label htmlFor="count" className="flex-1 cursor-pointer">
                                        <div className="flex items-center gap-2">
                                            <Repeat className="h-4 w-4" />
                                            <span className="font-medium">Loop Count</span>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            Loop a specific number of times
                                        </p>
                                    </Label>
                                </div>

                                <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                                    <RadioGroupItem value="none" id="none" />
                                    <Label htmlFor="none" className="flex-1 cursor-pointer">
                                        <div className="flex items-center gap-2">
                                            <Play className="h-4 w-4" />
                                            <span className="font-medium">Play Once</span>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            Play the video once and stop
                                        </p>
                                    </Label>
                                </div>
                            </RadioGroup>

                            {formData.loopMode === "count" && (
                                <div className="space-y-2 pl-8">
                                    <Label>Number of Loops</Label>
                                    <Input
                                        type="number"
                                        min={1}
                                        max={1000}
                                        value={formData.loopCount}
                                        onChange={(e) =>
                                            setFormData((prev) => ({
                                                ...prev,
                                                loopCount: parseInt(e.target.value) || 1,
                                            }))
                                        }
                                        className="w-32"
                                    />
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Output Settings */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                Output Settings
                            </CardTitle>
                            <CardDescription>
                                Configure video quality and encoding
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label>Resolution</Label>
                                    <Select
                                        value={formData.resolution}
                                        onValueChange={(value) =>
                                            setFormData((prev) => ({ ...prev, resolution: value as Resolution }))
                                        }
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="720p">720p (HD)</SelectItem>
                                            <SelectItem value="1080p">1080p (Full HD)</SelectItem>
                                            <SelectItem value="1440p">1440p (2K)</SelectItem>
                                            <SelectItem value="4k">4K (Ultra HD)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label>Frame Rate</Label>
                                    <Select
                                        value={formData.targetFps.toString()}
                                        onValueChange={(value) =>
                                            setFormData((prev) => ({ ...prev, targetFps: parseInt(value) }))
                                        }
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="24">24 fps</SelectItem>
                                            <SelectItem value="30">30 fps</SelectItem>
                                            <SelectItem value="60">60 fps</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label>Bitrate: {formData.targetBitrate} kbps</Label>
                                    <TooltipProvider>
                                        <Tooltip>
                                            <TooltipTrigger>
                                                <Info className="h-4 w-4 text-muted-foreground" />
                                            </TooltipTrigger>
                                            <TooltipContent>
                                                <p>Recommended: 4500-9000 kbps for 1080p</p>
                                            </TooltipContent>
                                        </Tooltip>
                                    </TooltipProvider>
                                </div>
                                <Slider
                                    value={[formData.targetBitrate]}
                                    onValueChange={([value]) =>
                                        setFormData((prev) => ({ ...prev, targetBitrate: value }))
                                    }
                                    min={1000}
                                    max={10000}
                                    step={500}
                                />
                                <div className="flex justify-between text-xs text-muted-foreground">
                                    <span>1000 kbps</span>
                                    <span>10000 kbps</span>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label>Encoding Mode</Label>
                                <RadioGroup
                                    value={formData.encodingMode}
                                    onValueChange={(value) =>
                                        setFormData((prev) => ({ ...prev, encodingMode: value as EncodingMode }))
                                    }
                                    className="flex gap-4"
                                >
                                    <div className="flex items-center space-x-2">
                                        <RadioGroupItem value="cbr" id="cbr" />
                                        <Label htmlFor="cbr">CBR (Constant)</Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <RadioGroupItem value="vbr" id="vbr" />
                                        <Label htmlFor="vbr">VBR (Variable)</Label>
                                    </div>
                                </RadioGroup>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Schedule Settings */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Clock className="h-5 w-5" />
                                Schedule (Optional)
                            </CardTitle>
                            <CardDescription>
                                Schedule when the stream should start and end
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center space-x-2">
                                <Switch
                                    checked={formData.scheduleEnabled}
                                    onCheckedChange={(checked) =>
                                        setFormData((prev) => ({ ...prev, scheduleEnabled: checked }))
                                    }
                                />
                                <Label>Enable scheduling</Label>
                            </div>

                            {formData.scheduleEnabled && (
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label>Start Time</Label>
                                        <Input
                                            type="datetime-local"
                                            value={formData.scheduledStartAt}
                                            onChange={(e) =>
                                                setFormData((prev) => ({
                                                    ...prev,
                                                    scheduledStartAt: e.target.value,
                                                }))
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>End Time (optional)</Label>
                                        <Input
                                            type="datetime-local"
                                            value={formData.scheduledEndAt}
                                            onChange={(e) =>
                                                setFormData((prev) => ({
                                                    ...prev,
                                                    scheduledEndAt: e.target.value,
                                                }))
                                            }
                                        />
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Stream Key */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Key className="h-5 w-5" />
                                Stream Key
                            </CardTitle>
                            <CardDescription>
                                Enter your YouTube stream key
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>RTMP URL</Label>
                                <Input
                                    value={formData.rtmpUrl}
                                    onChange={(e) =>
                                        setFormData((prev) => ({ ...prev, rtmpUrl: e.target.value }))
                                    }
                                    placeholder="rtmp://a.rtmp.youtube.com/live2"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label>Stream Key</Label>
                                <div className="relative">
                                    <Input
                                        type={showStreamKey ? "text" : "password"}
                                        value={formData.streamKey}
                                        onChange={(e) =>
                                            setFormData((prev) => ({ ...prev, streamKey: e.target.value }))
                                        }
                                        placeholder="xxxx-xxxx-xxxx-xxxx-xxxx"
                                        className="pr-10"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                        onClick={() => setShowStreamKey(!showStreamKey)}
                                    >
                                        {showStreamKey ? (
                                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                                        ) : (
                                            <Eye className="h-4 w-4 text-muted-foreground" />
                                        )}
                                    </Button>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Get your stream key from YouTube Studio → Go Live → Stream
                                </p>
                            </div>

                            <Separator />

                            <div className="flex items-center space-x-2">
                                <Switch
                                    checked={formData.enableChatModeration}
                                    onCheckedChange={(checked) =>
                                        setFormData((prev) => ({ ...prev, enableChatModeration: checked }))
                                    }
                                />
                                <Label>Enable live chat moderation</Label>
                            </div>
                            {formData.enableChatModeration && (
                                <p className="text-xs text-muted-foreground pl-8">
                                    Chat moderation will auto-start when your stream goes live.
                                    The system will automatically detect your YouTube broadcast.
                                </p>
                            )}

                            <Separator />

                            <div className="space-y-4">
                                <div className="flex items-center space-x-2">
                                    <Switch
                                        checked={formData.enableAutoRestart}
                                        onCheckedChange={(checked) =>
                                            setFormData((prev) => ({ ...prev, enableAutoRestart: checked }))
                                        }
                                    />
                                    <Label>Enable auto-restart on failure</Label>
                                </div>

                                {formData.enableAutoRestart && (
                                    <div className="space-y-2 pl-8">
                                        <Label>Max restart attempts</Label>
                                        <Input
                                            type="number"
                                            min={1}
                                            max={10}
                                            value={formData.maxRestarts}
                                            onChange={(e) =>
                                                setFormData((prev) => ({
                                                    ...prev,
                                                    maxRestarts: parseInt(e.target.value) || 5,
                                                }))
                                            }
                                            className="w-24"
                                        />
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Submit */}
                    <div className="flex justify-end gap-4">
                        <Button type="button" variant="outline" onClick={() => router.back()}>
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={loading}
                            className="bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 text-white"
                        >
                            {loading ? "Creating..." : "Create Stream"}
                        </Button>
                    </div>
                </form>
            </div>
        </DashboardLayout>
    )
}
