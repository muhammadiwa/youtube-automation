"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Save, Upload, X, Clock, ChevronRight, ChevronDown, History } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { videosApi } from "@/lib/api/videos"
import type { Video } from "@/types"
import { AITitleSuggestionsModal } from "@/components/dashboard/ai-title-suggestions-modal"
import { AIDescriptionGenerator } from "@/components/dashboard/ai-description-generator"
import { AITagSuggestions } from "@/components/dashboard/ai-tag-suggestions"
import { AIThumbnailGenerator } from "@/components/dashboard/ai-thumbnail-generator"

interface MetadataVersion {
    id: string
    version: number
    title: string
    description: string
    tags: string[]
    visibility: string
    createdAt: string
    createdBy: string
}

const YOUTUBE_CATEGORIES = [
    { id: "1", name: "Film & Animation" },
    { id: "2", name: "Autos & Vehicles" },
    { id: "10", name: "Music" },
    { id: "15", name: "Pets & Animals" },
    { id: "17", name: "Sports" },
    { id: "19", name: "Travel & Events" },
    { id: "20", name: "Gaming" },
    { id: "22", name: "People & Blogs" },
    { id: "23", name: "Comedy" },
    { id: "24", name: "Entertainment" },
    { id: "25", name: "News & Politics" },
    { id: "26", name: "Howto & Style" },
    { id: "27", name: "Education" },
    { id: "28", name: "Science & Technology" },
]

export default function VideoEditPage() {
    const router = useRouter()
    const params = useParams()
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
    const [scheduledPublishAt, setScheduledPublishAt] = useState("")
    const [thumbnailPreview, setThumbnailPreview] = useState<string>("")

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
            setDescription(data.description)
            setTags(data.tags)
            setCategoryId(data.categoryId)
            setVisibility(data.visibility)
            setScheduledPublishAt(data.scheduledPublishAt || "")
            setThumbnailPreview(data.thumbnailUrl)
        } catch (error) {
            console.error("Failed to load video:", error)
            alert("Failed to load video")
            router.push("/dashboard/videos")
        } finally {
            setLoading(false)
        }
    }

    const loadVersionHistory = async () => {
        // Mock version history - in real implementation, fetch from API
        setVersions([
            {
                id: "v1",
                version: 1,
                title: "Original Title",
                description: "Original description",
                tags: ["original", "tags"],
                visibility: "private",
                createdAt: new Date(Date.now() - 86400000).toISOString(),
                createdBy: "user@example.com",
            },
        ])
    }

    const handleThumbnailUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            if (!file.type.startsWith("image/")) {
                alert("Please upload an image file")
                return
            }
            if (file.size > 2 * 1024 * 1024) {
                alert("Image size must be less than 2MB")
                return
            }
            const reader = new FileReader()
            reader.onload = (ev) => {
                setThumbnailPreview(ev.target?.result as string)
            }
            reader.readAsDataURL(file)
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
            alert("Title is required")
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
                scheduledPublishAt: scheduledPublishAt || undefined,
            })
            alert("Video updated successfully!")
            router.push("/dashboard/videos")
        } catch (error) {
            console.error("Failed to update video:", error)
            alert("Failed to update video")
        } finally {
            setSaving(false)
        }
    }

    const restoreVersion = (version: MetadataVersion) => {
        if (confirm(`Restore version ${version.version}?`)) {
            setTitle(version.title)
            setDescription(version.description)
            setTags(version.tags)
            setVisibility(version.visibility as any)
        }
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
                                        <AITitleSuggestionsModal
                                            currentTitle={title}
                                            description={description}
                                            onApply={setTitle}
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
                                        <AIDescriptionGenerator
                                            title={title}
                                            currentDescription={description}
                                            onApply={setDescription}
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
                                        <AITagSuggestions
                                            title={title}
                                            description={description}
                                            currentTags={tags}
                                            onAddTag={(tag) => setTags([...tags, tag])}
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <Input
                                            id="tags"
                                            value={tagInput}
                                            onChange={(e) => setTagInput(e.target.value)}
                                            onKeyPress={(e) => {
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
                                    <Label htmlFor="category">Category</Label>
                                    <Select value={categoryId} onValueChange={setCategoryId}>
                                        <SelectTrigger id="category">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {YOUTUBE_CATEGORIES.map((cat) => (
                                                <SelectItem key={cat.id} value={cat.id}>
                                                    {cat.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
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
                                    <RadioGroup value={visibility} onValueChange={(v: any) => setVisibility(v)}>
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

                                <div>
                                    <Label htmlFor="schedule">Schedule Publish (Optional)</Label>
                                    <div className="flex gap-2">
                                        <Clock className="h-4 w-4 text-muted-foreground mt-3" />
                                        <Input
                                            id="schedule"
                                            type="datetime-local"
                                            value={scheduledPublishAt}
                                            onChange={(e) => setScheduledPublishAt(e.target.value)}
                                        />
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Leave empty to publish immediately
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Thumbnail */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Thumbnail</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex gap-4">
                                    {thumbnailPreview && (
                                        <img
                                            src={thumbnailPreview}
                                            alt="Thumbnail"
                                            className="w-48 aspect-video object-cover rounded border"
                                        />
                                    )}
                                    <div className="flex-1 space-y-2">
                                        <input
                                            type="file"
                                            id="thumbnail-upload"
                                            className="hidden"
                                            accept="image/*"
                                            onChange={handleThumbnailUpload}
                                        />
                                        <Button asChild variant="outline" className="w-full">
                                            <label htmlFor="thumbnail-upload" className="cursor-pointer">
                                                <Upload className="mr-2 h-4 w-4" />
                                                Upload New Thumbnail
                                            </label>
                                        </Button>
                                        <AIThumbnailGenerator
                                            videoId={videoId}
                                            onApply={setThumbnailPreview}
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            Recommended: 1280x720px, max 2MB
                                        </p>
                                    </div>
                                </div>
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
                                    {versions.length === 0 ? (
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
                                                        onClick={() => restoreVersion(version)}
                                                    >
                                                        Restore
                                                    </Button>
                                                </div>
                                                <p className="text-xs text-muted-foreground line-clamp-2">
                                                    {version.title}
                                                </p>
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
