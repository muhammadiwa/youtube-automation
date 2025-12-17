"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
    Upload,
    X,
    FileVideo,
    AlertCircle,
    CheckCircle2,
    Eye,
    EyeOff,
    Globe,
    Image as ImageIcon,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

import { videosApi } from "@/lib/api/videos"
import { accountsApi } from "@/lib/api/accounts"
import { VideoTemplate } from "@/lib/api/video-templates"
import { useToast } from "@/components/ui/toast"
import { AIGenerateButton } from "@/components/ai/ai-generate-button"
import { CategorySelect } from "@/components/videos/category-select"
import { SchedulePicker } from "@/components/videos/schedule-picker"
import { TemplateSelector } from "@/components/videos/template-selector"
import type { YouTubeAccount } from "@/types"

interface UploadFile {
    id: string
    file: File
    progress: number
    status: "pending" | "uploading" | "processing" | "completed" | "error"
    error?: string
    jobId?: string
    videoId?: string
    // Metadata
    title: string
    description: string
    tags: string[]
    categoryId: string
    visibility: "public" | "unlisted" | "private"
    scheduledPublishAt: Date | null
    // Thumbnail
    thumbnail?: File
    thumbnailPreview?: string
}

const MAX_FILES = 10
const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024 // 5GB
const ALLOWED_FORMATS = [
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/webm",
]

export default function VideoUploadPage() {
    const router = useRouter()
    const { addToast } = useToast()
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [selectedAccount, setSelectedAccount] = useState<string>("")
    const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
    const [isDragging, setIsDragging] = useState(false)
    const [activeFileId, setActiveFileId] = useState<string | null>(null)
    const [isUploading, setIsUploading] = useState(false)

    useEffect(() => {
        loadAccounts()
    }, [])

    // Set active file when files change
    useEffect(() => {
        if (uploadFiles.length > 0 && !activeFileId) {
            setActiveFileId(uploadFiles[0].id)
        } else if (uploadFiles.length === 0) {
            setActiveFileId(null)
        }
    }, [uploadFiles, activeFileId])

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
            setAccounts([])
        }
    }

    const validateFile = (file: File): string | null => {
        if (!ALLOWED_FORMATS.includes(file.type)) {
            return "Invalid file format. Please upload a video file."
        }
        if (file.size > MAX_FILE_SIZE) {
            return "File size exceeds 5GB limit."
        }
        return null
    }

    const handleFiles = (files: FileList | null) => {
        if (!files) return

        const newFiles: UploadFile[] = []
        const errors: string[] = []

        for (let i = 0; i < files.length; i++) {
            const file = files[i]

            if (uploadFiles.length + newFiles.length >= MAX_FILES) {
                errors.push(`Maximum ${MAX_FILES} files allowed`)
                break
            }

            const error = validateFile(file)
            if (error) {
                errors.push(`${file.name}: ${error}`)
                continue
            }

            const title = file.name.replace(/\.[^/.]+$/, "") // Remove extension

            newFiles.push({
                id: `${Date.now()}-${i}`,
                file,
                progress: 0,
                status: "pending",
                title,
                description: "",
                tags: [],
                categoryId: "22", // Default: People & Blogs
                visibility: "private",
                scheduledPublishAt: null,
            })
        }

        if (errors.length > 0) {
            addToast({ type: "error", title: "Upload Error", description: errors.join(", ") })
        }

        setUploadFiles((prev) => [...prev, ...newFiles])
    }

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault()
            setIsDragging(false)
            handleFiles(e.dataTransfer.files)
        },
        [uploadFiles]
    )

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files)
        e.target.value = ""
    }

    const removeFile = (id: string) => {
        setUploadFiles((prev) => prev.filter((f) => f.id !== id))
        if (activeFileId === id) {
            const remaining = uploadFiles.filter((f) => f.id !== id)
            setActiveFileId(remaining.length > 0 ? remaining[0].id : null)
        }
    }

    const updateFileMetadata = (id: string, updates: Partial<UploadFile>) => {
        setUploadFiles((prev) =>
            prev.map((f) => (f.id === id ? { ...f, ...updates } : f))
        )
    }

    // Poll for upload progress
    const pollProgress = useCallback(
        async (fileId: string, videoId: string) => {
            try {
                const progress = await videosApi.getUploadProgress(videoId)

                setUploadFiles((prev) =>
                    prev.map((f) => {
                        if (f.id !== fileId) return f

                        if (progress.status === "published" || progress.status === "processing") {
                            return { ...f, status: "processing", progress: 100 }
                        } else if (progress.status === "failed") {
                            return { ...f, status: "error", error: progress.error || "Upload failed" }
                        } else if (progress.status === "uploading") {
                            return { ...f, progress: progress.progress }
                        }
                        return f
                    })
                )

                if (progress.status === "uploading") {
                    setTimeout(() => pollProgress(fileId, videoId), 2000)
                } else if (progress.status === "processing") {
                    addToast({
                        type: "success",
                        title: "Upload Complete",
                        description: "Video is now processing on YouTube",
                    })
                    setUploadFiles((prev) =>
                        prev.map((f) => (f.id === fileId ? { ...f, status: "completed" } : f))
                    )
                }
            } catch (error) {
                console.error("Failed to poll progress:", error)
            }
        },
        [addToast]
    )

    const uploadFile = async (uploadFile: UploadFile) => {
        if (!selectedAccount) {
            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id
                        ? { ...f, status: "error", error: "Please select an account" }
                        : f
                )
            )
            return
        }

        setUploadFiles((prev) =>
            prev.map((f) =>
                f.id === uploadFile.id ? { ...f, status: "uploading", progress: 0 } : f
            )
        )

        try {
            const result = await videosApi.uploadVideo(
                {
                    accountId: selectedAccount,
                    title: uploadFile.title,
                    description: uploadFile.description,
                    tags: uploadFile.tags,
                    categoryId: uploadFile.categoryId,
                    visibility: uploadFile.visibility,
                    scheduledPublishAt: uploadFile.scheduledPublishAt?.toISOString(),
                },
                uploadFile.file,
                uploadFile.thumbnail
            )

            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id
                        ? { ...f, jobId: result.jobId, videoId: result.videoId, progress: 10 }
                        : f
                )
            )

            if (result.videoId) {
                pollProgress(uploadFile.id, result.videoId)
            } else {
                setUploadFiles((prev) =>
                    prev.map((f) =>
                        f.id === uploadFile.id ? { ...f, status: "completed", progress: 100 } : f
                    )
                )
            }
        } catch (error: any) {
            const errorMessage = error?.detail || error?.message || "Upload failed"
            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id ? { ...f, status: "error", error: errorMessage } : f
                )
            )
            addToast({ type: "error", title: "Upload Failed", description: errorMessage })
        }
    }

    const uploadAll = async () => {
        setIsUploading(true)
        const pendingFiles = uploadFiles.filter((f) => f.status === "pending")
        for (const file of pendingFiles) {
            await uploadFile(file)
        }
        setIsUploading(false)
    }

    const getStatusIcon = (status: UploadFile["status"]) => {
        switch (status) {
            case "completed":
                return <CheckCircle2 className="h-5 w-5 text-green-500" />
            case "error":
                return <AlertCircle className="h-5 w-5 text-destructive" />
            case "uploading":
                return <Upload className="h-5 w-5 text-primary animate-pulse" />
            case "processing":
                return <FileVideo className="h-5 w-5 text-blue-500 animate-pulse" />
            default:
                return <FileVideo className="h-5 w-5 text-muted-foreground" />
        }
    }

    const getVisibilityIcon = (visibility: string) => {
        switch (visibility) {
            case "public":
                return <Globe className="h-4 w-4" />
            case "unlisted":
                return <Eye className="h-4 w-4" />
            case "private":
                return <EyeOff className="h-4 w-4" />
            default:
                return null
        }
    }

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return "0 Bytes"
        const k = 1024
        const sizes = ["Bytes", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
    }

    const applyTemplate = (template: VideoTemplate) => {
        if (!activeFileId) return

        const updates: Partial<UploadFile> = {}

        // Apply template values
        if (template.titleTemplate) {
            // Replace placeholders with actual values
            const activeFile = uploadFiles.find((f) => f.id === activeFileId)
            let title = template.titleTemplate
            if (activeFile) {
                title = title.replace(/\{\{filename\}\}/gi, activeFile.file.name.replace(/\.[^/.]+$/, ""))
                title = title.replace(/\{\{date\}\}/gi, new Date().toLocaleDateString())
            }
            updates.title = title
        }
        if (template.descriptionTemplate) {
            updates.description = template.descriptionTemplate
        }
        if (template.tags && template.tags.length > 0) {
            updates.tags = template.tags
        }
        if (template.categoryId) {
            updates.categoryId = template.categoryId
        }
        if (template.visibility) {
            updates.visibility = template.visibility
        }

        updateFileMetadata(activeFileId, updates)
        addToast({ type: "success", title: "Template Applied", description: `Applied "${template.name}" template` })
    }

    const activeFile = uploadFiles.find((f) => f.id === activeFileId)
    const pendingCount = uploadFiles.filter((f) => f.status === "pending").length
    const uploadingCount = uploadFiles.filter((f) => f.status === "uploading").length
    const completedCount = uploadFiles.filter((f) => f.status === "completed").length

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Videos", href: "/dashboard/videos" },
                { label: "Upload" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Upload Videos</h1>
                        <p className="text-muted-foreground">
                            Upload up to {MAX_FILES} videos at once with AI-powered metadata
                        </p>
                    </div>
                    <Button variant="outline" onClick={() => router.push("/dashboard/videos")}>
                        Back to Videos
                    </Button>
                </div>

                {/* Account Selection */}
                <Card>
                    <CardHeader>
                        <CardTitle>YouTube Account</CardTitle>
                        <CardDescription>Select the channel to upload videos to</CardDescription>
                    </CardHeader>
                    <CardContent>
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
                        {accounts.length === 0 && (
                            <p className="text-sm text-muted-foreground mt-2">
                                No active accounts found.{" "}
                                <a href="/dashboard/accounts" className="text-primary hover:underline">
                                    Connect a YouTube account
                                </a>
                            </p>
                        )}
                    </CardContent>
                </Card>

                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Left Column - File Selection & Queue */}
                    <div className="space-y-6">
                        {/* Upload Zone */}
                        <Card>
                            <CardContent className="pt-6">
                                <div
                                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging
                                        ? "border-primary bg-primary/5"
                                        : "border-muted-foreground/25 hover:border-primary/50"
                                        }`}
                                    onDrop={handleDrop}
                                    onDragOver={handleDragOver}
                                    onDragLeave={handleDragLeave}
                                >
                                    <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
                                    <h3 className="text-lg font-semibold mb-1">
                                        Drag and drop video files
                                    </h3>
                                    <p className="text-sm text-muted-foreground mb-3">
                                        or click to browse (max {MAX_FILES} files, 5GB each)
                                    </p>
                                    <input
                                        type="file"
                                        id="file-upload"
                                        className="hidden"
                                        multiple
                                        accept={ALLOWED_FORMATS.join(",")}
                                        onChange={handleFileInput}
                                        disabled={uploadFiles.length >= MAX_FILES}
                                    />
                                    <Button asChild disabled={uploadFiles.length >= MAX_FILES}>
                                        <label htmlFor="file-upload" className="cursor-pointer">
                                            Browse Files
                                        </label>
                                    </Button>
                                    <p className="text-xs text-muted-foreground mt-3">
                                        MP4, MOV, AVI, WMV, WebM, MPEG
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* File Queue */}
                        {uploadFiles.length > 0 && (
                            <Card>
                                <CardHeader className="pb-3">
                                    <div className="flex items-center justify-between">
                                        <CardTitle>Upload Queue ({uploadFiles.length})</CardTitle>
                                        {pendingCount > 0 && (
                                            <Button
                                                onClick={uploadAll}
                                                disabled={!selectedAccount || isUploading}
                                            >
                                                Upload All ({pendingCount})
                                            </Button>
                                        )}
                                    </div>
                                    <div className="flex gap-3 text-sm text-muted-foreground">
                                        {pendingCount > 0 && <span>{pendingCount} pending</span>}
                                        {uploadingCount > 0 && <span>{uploadingCount} uploading</span>}
                                        {completedCount > 0 && <span>{completedCount} completed</span>}
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {uploadFiles.map((file) => (
                                        <div
                                            key={file.id}
                                            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${activeFileId === file.id
                                                ? "border-primary bg-primary/5"
                                                : "hover:bg-accent"
                                                }`}
                                            onClick={() => setActiveFileId(file.id)}
                                        >
                                            {getStatusIcon(file.status)}
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium truncate text-sm">
                                                    {file.title}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {formatFileSize(file.file.size)}
                                                </p>
                                                {file.status === "uploading" && (
                                                    <Progress value={file.progress} className="h-1 mt-1" />
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {getVisibilityIcon(file.visibility)}
                                                {file.status === "pending" && (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-8 w-8"
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            removeFile(file.id)
                                                        }}
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        )}
                    </div>

                    {/* Right Column - Metadata Editor */}
                    {activeFile && activeFile.status === "pending" && (
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle>Video Details</CardTitle>
                                        <CardDescription>
                                            Edit metadata for: {activeFile.file.name}
                                        </CardDescription>
                                    </div>
                                    <TemplateSelector onSelect={applyTemplate} />
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* Title */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="title">Title</Label>
                                        <AIGenerateButton
                                            type="title"
                                            context={{ videoContent: activeFile.title }}
                                            onSelect={(value) =>
                                                updateFileMetadata(activeFile.id, {
                                                    title: value as string,
                                                })
                                            }
                                        />
                                    </div>
                                    <Input
                                        id="title"
                                        value={activeFile.title}
                                        onChange={(e) =>
                                            updateFileMetadata(activeFile.id, { title: e.target.value })
                                        }
                                        maxLength={100}
                                        placeholder="Enter video title"
                                    />
                                    <p className="text-xs text-muted-foreground text-right">
                                        {activeFile.title.length}/100
                                    </p>
                                </div>

                                {/* Description */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Label htmlFor="description">Description</Label>
                                        <AIGenerateButton
                                            type="description"
                                            context={{
                                                videoTitle: activeFile.title,
                                                videoContent: activeFile.title,
                                            }}
                                            onSelect={(value) =>
                                                updateFileMetadata(activeFile.id, {
                                                    description: value as string,
                                                })
                                            }
                                        />
                                    </div>
                                    <Textarea
                                        id="description"
                                        value={activeFile.description}
                                        onChange={(e) =>
                                            updateFileMetadata(activeFile.id, {
                                                description: e.target.value,
                                            })
                                        }
                                        maxLength={5000}
                                        rows={5}
                                        placeholder="Enter video description"
                                    />
                                    <p className="text-xs text-muted-foreground text-right">
                                        {activeFile.description.length}/5000
                                    </p>
                                </div>

                                {/* Tags */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Label>Tags</Label>
                                        <AIGenerateButton
                                            type="tags"
                                            context={{
                                                videoTitle: activeFile.title,
                                                videoDescription: activeFile.description,
                                                existingTags: activeFile.tags,
                                            }}
                                            onSelect={(value) =>
                                                updateFileMetadata(activeFile.id, {
                                                    tags: [
                                                        ...activeFile.tags,
                                                        ...(value as string[]),
                                                    ].filter((v, i, a) => a.indexOf(v) === i),
                                                })
                                            }
                                        />
                                    </div>
                                    <Input
                                        placeholder="Add tags (press Enter)"
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                e.preventDefault()
                                                const value = e.currentTarget.value.trim()
                                                if (value && !activeFile.tags.includes(value)) {
                                                    updateFileMetadata(activeFile.id, {
                                                        tags: [...activeFile.tags, value],
                                                    })
                                                    e.currentTarget.value = ""
                                                }
                                            }
                                        }}
                                    />
                                    {activeFile.tags.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-2">
                                            {activeFile.tags.map((tag, index) => (
                                                <Badge
                                                    key={index}
                                                    variant="secondary"
                                                    className="cursor-pointer"
                                                    onClick={() =>
                                                        updateFileMetadata(activeFile.id, {
                                                            tags: activeFile.tags.filter((_, i) => i !== index),
                                                        })
                                                    }
                                                >
                                                    {tag}
                                                    <X className="h-3 w-3 ml-1" />
                                                </Badge>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Category & Visibility */}
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label>Category</Label>
                                        <CategorySelect
                                            value={activeFile.categoryId}
                                            onValueChange={(value) =>
                                                updateFileMetadata(activeFile.id, { categoryId: value })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Visibility</Label>
                                        <Select
                                            value={activeFile.visibility}
                                            onValueChange={(value: "public" | "unlisted" | "private") =>
                                                updateFileMetadata(activeFile.id, { visibility: value })
                                            }
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="private">
                                                    <div className="flex items-center gap-2">
                                                        <EyeOff className="h-4 w-4" />
                                                        Private
                                                    </div>
                                                </SelectItem>
                                                <SelectItem value="unlisted">
                                                    <div className="flex items-center gap-2">
                                                        <Eye className="h-4 w-4" />
                                                        Unlisted
                                                    </div>
                                                </SelectItem>
                                                <SelectItem value="public">
                                                    <div className="flex items-center gap-2">
                                                        <Globe className="h-4 w-4" />
                                                        Public
                                                    </div>
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                {/* Schedule */}
                                <SchedulePicker
                                    value={activeFile.scheduledPublishAt}
                                    onChange={(date) =>
                                        updateFileMetadata(activeFile.id, { scheduledPublishAt: date })
                                    }
                                />

                                {/* Thumbnail */}
                                <div className="space-y-2">
                                    <Label>Thumbnail (Optional)</Label>
                                    {activeFile.thumbnailPreview ? (
                                        <div className="relative">
                                            <div className="relative aspect-video rounded-lg overflow-hidden border bg-muted max-w-xs">
                                                <img
                                                    src={activeFile.thumbnailPreview}
                                                    alt="Thumbnail preview"
                                                    className="w-full h-full object-cover"
                                                />
                                            </div>
                                            <div className="flex gap-2 mt-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        const input = document.createElement("input")
                                                        input.type = "file"
                                                        input.accept = "image/jpeg,image/png,image/gif"
                                                        input.onchange = (e) => {
                                                            const file = (e.target as HTMLInputElement).files?.[0]
                                                            if (file) {
                                                                if (file.size > 2 * 1024 * 1024) {
                                                                    addToast({ type: "error", title: "File too large", description: "Thumbnail must be under 2MB" })
                                                                    return
                                                                }
                                                                const preview = URL.createObjectURL(file)
                                                                updateFileMetadata(activeFile.id, {
                                                                    thumbnail: file,
                                                                    thumbnailPreview: preview,
                                                                })
                                                            }
                                                        }
                                                        input.click()
                                                    }}
                                                >
                                                    Change
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        if (activeFile.thumbnailPreview) {
                                                            URL.revokeObjectURL(activeFile.thumbnailPreview)
                                                        }
                                                        updateFileMetadata(activeFile.id, {
                                                            thumbnail: undefined,
                                                            thumbnailPreview: undefined,
                                                        })
                                                    }}
                                                >
                                                    <X className="h-4 w-4 mr-1" />
                                                    Remove
                                                </Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div
                                            className="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:border-primary/50 transition-colors"
                                            onClick={() => {
                                                const input = document.createElement("input")
                                                input.type = "file"
                                                input.accept = "image/jpeg,image/png,image/gif"
                                                input.onchange = (e) => {
                                                    const file = (e.target as HTMLInputElement).files?.[0]
                                                    if (file) {
                                                        if (file.size > 2 * 1024 * 1024) {
                                                            addToast({ type: "error", title: "File too large", description: "Thumbnail must be under 2MB" })
                                                            return
                                                        }
                                                        const preview = URL.createObjectURL(file)
                                                        updateFileMetadata(activeFile.id, {
                                                            thumbnail: file,
                                                            thumbnailPreview: preview,
                                                        })
                                                    }
                                                }
                                                input.click()
                                            }}
                                        >
                                            <ImageIcon className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
                                            <p className="text-sm text-muted-foreground">
                                                Click to add thumbnail
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                JPG, PNG, GIF • Max 2MB • 1280x720px recommended
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* Upload Button */}
                                <Button
                                    className="w-full"
                                    onClick={() => uploadFile(activeFile)}
                                    disabled={!selectedAccount || isUploading}
                                >
                                    <Upload className="h-4 w-4 mr-2" />
                                    Upload This Video
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {/* Status display for non-pending files */}
                    {activeFile && activeFile.status !== "pending" && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Upload Status</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(activeFile.status)}
                                    <div>
                                        <p className="font-medium">{activeFile.title}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {activeFile.status === "uploading" &&
                                                `Uploading... ${activeFile.progress}%`}
                                            {activeFile.status === "processing" &&
                                                "Processing on YouTube..."}
                                            {activeFile.status === "completed" &&
                                                "Upload completed!"}
                                            {activeFile.status === "error" && activeFile.error}
                                        </p>
                                    </div>
                                </div>
                                {activeFile.status === "uploading" && (
                                    <Progress value={activeFile.progress} />
                                )}
                                {activeFile.status === "completed" && (
                                    <Button
                                        variant="outline"
                                        onClick={() => router.push("/dashboard/videos")}
                                    >
                                        View All Videos
                                    </Button>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Empty state */}
                    {!activeFile && (
                        <Card>
                            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                                <FileVideo className="h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No video selected</h3>
                                <p className="text-muted-foreground">
                                    Add video files to start editing metadata
                                </p>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </DashboardLayout>
    )
}
