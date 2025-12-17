"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Save, X, ChevronRight, ChevronDown, History } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Skeleton } from "@/components/ui/skeleton"
import { videosApi } from "@/lib/api/videos"
import { useToast } from "@/components/ui/toast"
import type { Video } from "@/types"
import { AIGenerateButton } from "@/components/ai/ai-generate-button"
import { CategorySelect } from "@/components/videos/category-select"
import { SchedulePicker } from "@/components/videos/schedule-picker"
import { ThumbnailUploader } from "@/components/videos/thumbnail-uploader"

interface MetadataVersion {
    id: string
    version: number
    title: string
    description: string
    tags: string[]
    visibility: string
    categoryId?: string
    createdAt: string
    changedBy?: string
    changeReason?: string
}

export default function VideoEditPage() {
    const router = useRouter()
    const params = useParams()
    const { addToast } = useToast()
    const videoId = params.id as string

    const [video, setVideo] = useState<Video | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [showVersionHistory, setShowVersionHistory] = useState(false)
    const [versions, setVersions] = useState<MetadataVersion[]>([])

    // Form state
    const [title, setTitle] = useState("")
    const [description, setDescription] = useState("")
    const [tags, setTags] = useState<string[]>([])
    const [tagInput, setTagInput] = useState("")
    const [categoryId, setCategoryId] = useState("22")
    const [visibility, setVisibility] = useState<"public" | "unlisted" | "private">("private")
    const [scheduledPublishAt, setScheduledPublishAt] = useState<Date | null>(null)
    const [thumbnailUrl, setThumbnailUrl] = useState<string>("")
    const [loadingVersions, setLoadingVersions] = useState(false)

    useEffect(() => {
        loadVideo()
        loadVersionHistory()
    }, [videoId])

    const loadVideo = async () => {
        try {
            setLoading(true)
            const data = await videosApi.getVideo(videoId)
            setVideo(data)
            setTitle(data.title)
            setDescription(data.description || "")
            setTags(data.tags || [])
            setCategoryId(data.categoryId || "22")
            setVisibility(data.visibility || "private")
            setScheduledPublishAt(data.scheduledPublishAt ? new Date(data.scheduledPublishAt) : null)
            setThumbnailUrl(data.thumbnailUrl || "")
        } catch (error) {
            console.error("Failed to load video:", error)
            addToast({ type: "error", title: "Error", description: "Failed to load video" })
            router.push("/dashboard/videos")
        } finally {
            setLoading(false)
        }
    }

    const loadVersionHistory = async () => {
        try {
            setLoadingVersions(true)
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/${videoId}/versions`,
                {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                    },
                }
            )
            if (response.ok) {
                const data = await response.json()
                // Backend returns array directly, map snake_case to camelCase
                const rawVersions = Array.isArray(data) ? data : data.versions || []
                const mappedVersions = rawVersions.map((v: any) => ({
                    id: v.id,
                    version: v.version_number,
                    title: v.title,
                    description: v.description,
                    tags: v.tags || [],
                    categoryId: v.category_id,
                    visibility: v.visibility,
                    createdAt: v.created_at,
                    changedBy: v.changed_by,
                    changeReason: v.change_reason,
                }))
                setVersions(mappedVersions)
            }
        } catch (error) {
            console.error("Failed to load version history:", error)
        } finally {
            setLoadingVersions(false)
        }
    }

    const addTag = () => {
        if (tagInput.trim() && !tags.includes(tagInput.trim())) {
            setTags([...tags, tagInput.trim()])
            setTagInput("")
        }
    }

    const removeTag = (tag: string) => {
        setTags(tags.filter((t) => t !== tag))
    }

    const handleSave = async () => {
        if (!title.trim()) {
            addToast({ type: "error", title: "Validation Error", description: "Title is required" })
            return
        }

        try {
            setSaving(true)
            await videosApi.updateVideo(videoId, {
                title,
                description,
                tags,
                categoryId,
                visibility,
                scheduledPublishAt: scheduledPublishAt?.toISOString(),
            })
            addToast({ type: "success", title: "Success", description: "Video updated successfully!" })
            router.push("/dashboard/videos")
        } catch (error) {
            console.error("Failed to update video:", error)
            addToast({ type: "error", title: "Error", description: "Failed to update video" })
        } finally {
            setSaving(false)
        }
    }

    const handleRollback = async (version: MetadataVersion) => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/${videoId}/rollback/${version.version}`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                        "Content-Type": "application/json",
                    },
                }
            )
            if (response.ok) {
                addToast({ type: "success", title: "Success", description: `Restored to version ${version.version}` })
                loadVideo()
                loadVersionHistory()
            } else {
                throw new Error("Failed to rollback")
            }
        } catch (error) {
            addToast({ type: "error", title: "Error", description: "Failed to restore version" })
        }
    }

    const handleThumbnailUploadComplete = (url: string) => {
        setThumbnailUrl(url)
    }

    if (loading) {
        return (
            <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Videos", href: "/dashboard/videos" }, { label: "Edit" }]}>
                <div className="space-y-6">
                    <Skeleton className="h-10 w-64" />
                    <Card>
                        <CardContent className="pt-6 space-y-4">
                            <Skeleton className="h-10 w-full" />
                            <Skeleton className="h-32 w-full" />
                            <Skeleton className="h-10 w-full" />
                        </CardContent>
                    </Card>
                </div>
            </DashboardLayout>
        )
    }

    if (!video) {
        return null
    }

    return (
        <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Videos", href: "/dashboard/videos" }, { label: video.title }]}>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Edit Video</h1>
                        <p className="text-muted-foreground">Update video metadata and settings</p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={() => router.push("/dashboard/videos")}>
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            <Save className="mr-2 h-4 w-4" />
                            {saving ? "Saving..." : "Save Changes"}
                        </Button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Form */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Basic Information */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Basic Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <Label htmlFor="title">
                                            Title <span className="text-destructive">*</span>
                                        </Label>
                                        <AIGenerateButton
                                            type="title"
                                            context={{ videoContent: title, videoTitle: title }}
                                            onSelect={(value) => setTitle(value as string)}
                                        />
                                    </div>
                                    <Input
                                        id="title"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        placeholder="Enter video title"
                                        maxLength={100}
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {title.length}/100 characters
                                    </p>
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <Label htmlFor="description">Description</Label>
                                        <AIGenerateButton
                                            type="description"
                                            context={{ videoTitle: title, videoContent: description }}
                                            onSelect={(value) => setDescription(value as string)}
                                        />
                                    </div>
                                    <Textarea
                                        id="description"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        placeholder="Enter video description"
                                        rows={6}
                                        maxLength={5000}
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {description.length}/5000 characters
                                    </p>
                                </div>

                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <Label htmlFor="tags">Tags</Label>
                                        <AIGenerateButton
                                            type="tags"
                                            context={{
                                                videoTitle: title,
                                                videoDescription: description,
                                                existingTags: tags,
                                            }}
                                            onSelect={(value) =>
                                                setTags([...tags, ...(value as string[])].filter(
                                                    (v, i, a) => a.indexOf(v) === i
                                                ))
                                            }
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <Input
                                            id="tags"
                                            value={tagInput}
                                            onChange={(e) => setTagInput(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") {
                                                    e.preventDefault()
                                                    addTag()
                                                }
                                            }}
                                            placeholder="Add a tag and press Enter"
                                        />
                                        <Button type="button" onClick={addTag}>
                                            Add
                                        </Button>
                                    </div>
                                    {tags.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {tags.map((tag) => (
                                                <Badge key={tag} variant="secondary">
                                                    {tag}
                                                    <button
                                                        onClick={() => removeTag(tag)}
                                                        className="ml-2 hover:text-destructive"
                                                    >
                                                        <X className="h-3 w-3" />
                                                    </button>
                                                </Badge>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <div>
                                    <Label>Category</Label>
                                    <CategorySelect
                                        value={categoryId}
                                        onValueChange={setCategoryId}
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Visibility & Publishing */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Visibility & Publishing</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <Label>Visibility</Label>
                                    <RadioGroup value={visibility} onValueChange={(v: "public" | "unlisted" | "private") => setVisibility(v)}>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="public" id="public" />
                                            <Label htmlFor="public" className="font-normal cursor-pointer">
                                                Public - Anyone can search for and view
                                            </Label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="unlisted" id="unlisted" />
                                            <Label htmlFor="unlisted" className="font-normal cursor-pointer">
                                                Unlisted - Anyone with the link can view
                                            </Label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="private" id="private" />
                                            <Label htmlFor="private" className="font-normal cursor-pointer">
                                                Private - Only you can view
                                            </Label>
                                        </div>
                                    </RadioGroup>
                                </div>

                                <SchedulePicker
                                    value={scheduledPublishAt}
                                    onChange={setScheduledPublishAt}
                                />
                            </CardContent>
                        </Card>

                        {/* Thumbnail */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Thumbnail</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ThumbnailUploader
                                    videoId={videoId}
                                    currentThumbnail={thumbnailUrl}
                                    onUploadComplete={handleThumbnailUploadComplete}
                                />
                            </CardContent>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Video Status */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Video Status</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Status</span>
                                    <Badge>{video.status}</Badge>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Views</span>
                                    <span className="text-sm font-medium">{video.viewCount.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Likes</span>
                                    <span className="text-sm font-medium">{video.likeCount.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Comments</span>
                                    <span className="text-sm font-medium">{video.commentCount.toLocaleString()}</span>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Version History */}
                        <Card>
                            <CardHeader>
                                <button
                                    className="flex items-center justify-between w-full"
                                    onClick={() => setShowVersionHistory(!showVersionHistory)}
                                >
                                    <CardTitle className="flex items-center gap-2">
                                        <History className="h-4 w-4" />
                                        Version History
                                    </CardTitle>
                                    {showVersionHistory ? (
                                        <ChevronDown className="h-4 w-4" />
                                    ) : (
                                        <ChevronRight className="h-4 w-4" />
                                    )}
                                </button>
                            </CardHeader>
                            {showVersionHistory && (
                                <CardContent className="space-y-3">
                                    {loadingVersions ? (
                                        <div className="space-y-2">
                                            <Skeleton className="h-16 w-full" />
                                            <Skeleton className="h-16 w-full" />
                                        </div>
                                    ) : versions.length === 0 ? (
                                        <p className="text-sm text-muted-foreground">No version history</p>
                                    ) : (
                                        versions.map((version) => (
                                            <div key={version.id} className="border rounded p-3 space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm font-medium">
                                                        Version {version.version}
                                                    </span>
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        onClick={() => handleRollback(version)}
                                                    >
                                                        Restore
                                                    </Button>
                                                </div>
                                                <p className="text-xs font-medium line-clamp-1">
                                                    {version.title}
                                                </p>
                                                {version.changeReason && (
                                                    <p className="text-xs text-muted-foreground">
                                                        {version.changeReason}
                                                    </p>
                                                )}
                                                <p className="text-xs text-muted-foreground">
                                                    {new Date(version.createdAt).toLocaleString()}
                                                </p>
                                            </div>
                                        ))
                                    )}
                                </CardContent>
                            )}
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    )
}
