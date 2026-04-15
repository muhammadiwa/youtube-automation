"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    Download,
    RefreshCw,
    Check,
    X,
    Loader2,
    Youtube,
    AlertCircle,
    CheckCircle2,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toast"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

interface YouTubeVideo {
    id: string
    youtubeId: string
    title: string
    description: string
    thumbnailUrl: string
    publishedAt: string
    viewCount: number
    likeCount: number
    commentCount: number
    duration: string
    visibility: string
    isImported: boolean
}

export default function ImportVideosPage() {
    const router = useRouter()
    const { addToast } = useToast()
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [selectedAccount, setSelectedAccount] = useState<string>("")
    const [videos, setVideos] = useState<YouTubeVideo[]>([])
    const [loading, setLoading] = useState(false)
    const [importing, setImporting] = useState(false)
    const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set())
    const [importProgress, setImportProgress] = useState(0)
    const [importStatus, setImportStatus] = useState<"idle" | "importing" | "done">("idle")

    useEffect(() => {
        loadAccounts()
    }, [])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts({ status: "active" })
            const accountsList = Array.isArray(data) ? data : []
            setAccounts(accountsList)
            if (accountsList.length > 0) {
                setSelectedAccount(accountsList[0].id)
            }
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const fetchYouTubeVideos = async () => {
        if (!selectedAccount) return

        setLoading(true)
        setVideos([])
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/youtube/list?account_id=${selectedAccount}`,
                {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                    },
                }
            )

            if (response.ok) {
                const data = await response.json()
                setVideos(data.videos || [])
            } else {
                throw new Error("Failed to fetch videos")
            }
        } catch (error) {
            console.error("Failed to fetch YouTube videos:", error)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to fetch videos from YouTube",
            })
        } finally {
            setLoading(false)
        }
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
        const importableVideos = videos.filter((v) => !v.isImported)
        if (selectedVideos.size === importableVideos.length) {
            setSelectedVideos(new Set())
        } else {
            setSelectedVideos(new Set(importableVideos.map((v) => v.youtubeId)))
        }
    }

    const handleImport = async () => {
        if (selectedVideos.size === 0) return

        setImporting(true)
        setImportStatus("importing")
        setImportProgress(0)

        const videoIds = Array.from(selectedVideos)
        let imported = 0

        try {
            for (const videoId of videoIds) {
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/youtube/import`,
                    {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            account_id: selectedAccount,
                            youtube_video_id: videoId,
                        }),
                    }
                )

                if (response.ok) {
                    imported++
                    setImportProgress(Math.round((imported / videoIds.length) * 100))

                    // Update video status
                    setVideos((prev) =>
                        prev.map((v) =>
                            v.youtubeId === videoId ? { ...v, isImported: true } : v
                        )
                    )
                }
            }

            setImportStatus("done")
            addToast({
                type: "success",
                title: "Import Complete",
                description: `Successfully imported ${imported} video(s)`,
            })
            setSelectedVideos(new Set())
        } catch (error) {
            console.error("Failed to import videos:", error)
            addToast({
                type: "error",
                title: "Import Failed",
                description: "Some videos failed to import",
            })
        } finally {
            setImporting(false)
        }
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString()
    }

    const importableCount = videos.filter((v) => !v.isImported).length

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Videos", href: "/dashboard/videos" },
                { label: "Import from YouTube" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Import from YouTube</h1>
                        <p className="text-muted-foreground">
                            Import existing videos from your YouTube channel
                        </p>
                    </div>
                    <Button variant="outline" onClick={() => router.push("/dashboard/videos")}>
                        Back to Videos
                    </Button>
                </div>

                {/* Account Selection */}
                <Card>
                    <CardHeader>
                        <CardTitle>Select Channel</CardTitle>
                        <CardDescription>
                            Choose the YouTube channel to import videos from
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-4">
                            <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                                <SelectTrigger className="w-full max-w-md">
                                    <SelectValue placeholder="Select an account" />
                                </SelectTrigger>
                                <SelectContent>
                                    {accounts.map((account) => (
                                        <SelectItem key={account.id} value={account.id}>
                                            <div className="flex items-center gap-2">
                                                {account.thumbnailUrl && (
                                                    <img
                                                        src={account.thumbnailUrl}
                                                        alt={account.channelTitle}
                                                        className="w-6 h-6 rounded-full"
                                                    />
                                                )}
                                                {account.channelTitle}
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <Button
                                onClick={fetchYouTubeVideos}
                                disabled={!selectedAccount || loading}
                            >
                                {loading ? (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                ) : (
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                )}
                                Fetch Videos
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Import Progress */}
                {importStatus !== "idle" && (
                    <Card>
                        <CardContent className="py-4">
                            <div className="flex items-center gap-4">
                                {importStatus === "importing" ? (
                                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                ) : (
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                )}
                                <div className="flex-1">
                                    <p className="font-medium">
                                        {importStatus === "importing"
                                            ? "Importing videos..."
                                            : "Import complete!"}
                                    </p>
                                    <Progress value={importProgress} className="mt-2" />
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {importProgress}%
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Videos List */}
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3, 4].map((i) => (
                            <Card key={i}>
                                <CardContent className="p-4">
                                    <div className="flex gap-4">
                                        <Skeleton className="w-40 aspect-video rounded" />
                                        <div className="flex-1 space-y-2">
                                            <Skeleton className="h-5 w-3/4" />
                                            <Skeleton className="h-4 w-1/2" />
                                            <Skeleton className="h-4 w-1/4" />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : videos.length > 0 ? (
                    <div className="space-y-4">
                        {/* Bulk Actions */}
                        <Card>
                            <CardContent className="py-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <Checkbox
                                            checked={
                                                selectedVideos.size === importableCount &&
                                                importableCount > 0
                                            }
                                            onCheckedChange={handleSelectAll}
                                            disabled={importableCount === 0}
                                        />
                                        <span className="text-sm">
                                            {selectedVideos.size} of {importableCount} selected
                                        </span>
                                    </div>
                                    <Button
                                        onClick={handleImport}
                                        disabled={selectedVideos.size === 0 || importing}
                                    >
                                        {importing ? (
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        ) : (
                                            <Download className="h-4 w-4 mr-2" />
                                        )}
                                        Import Selected ({selectedVideos.size})
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Video List */}
                        {videos.map((video) => (
                            <Card
                                key={video.youtubeId}
                                className={video.isImported ? "opacity-60" : ""}
                            >
                                <CardContent className="p-4">
                                    <div className="flex items-start gap-4">
                                        {!video.isImported && (
                                            <Checkbox
                                                checked={selectedVideos.has(video.youtubeId)}
                                                onCheckedChange={() =>
                                                    handleSelectVideo(video.youtubeId)
                                                }
                                                className="mt-1"
                                            />
                                        )}
                                        <img
                                            src={video.thumbnailUrl}
                                            alt={video.title}
                                            className="w-40 aspect-video object-cover rounded"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2">
                                                <h3 className="font-semibold line-clamp-2">
                                                    {video.title}
                                                </h3>
                                                {video.isImported ? (
                                                    <Badge variant="secondary" className="shrink-0">
                                                        <Check className="h-3 w-3 mr-1" />
                                                        Imported
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="outline" className="shrink-0">
                                                        <Youtube className="h-3 w-3 mr-1" />
                                                        YouTube
                                                    </Badge>
                                                )}
                                            </div>
                                            <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                                                {video.description || "No description"}
                                            </p>
                                            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                                <span>{formatNumber(video.viewCount)} views</span>
                                                <span>{formatNumber(video.likeCount)} likes</span>
                                                <span>{formatDate(video.publishedAt)}</span>
                                                <Badge variant="outline" className="text-xs">
                                                    {video.visibility}
                                                </Badge>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : selectedAccount ? (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <Youtube className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No videos found</h3>
                            <p className="text-muted-foreground mb-4">
                                Click "Fetch Videos" to load videos from your YouTube channel
                            </p>
                            <Button onClick={fetchYouTubeVideos} disabled={loading}>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Fetch Videos
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <Card>
                        <CardContent className="py-12 text-center">
                            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">Select a channel</h3>
                            <p className="text-muted-foreground">
                                Please select a YouTube channel to import videos from
                            </p>
                        </CardContent>
                    </Card>
                )}
            </div>
        </DashboardLayout>
    )
}
