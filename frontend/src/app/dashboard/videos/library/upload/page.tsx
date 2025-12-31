"use client"

/**
 * Video Library Upload Page
 * 
 * Upload videos to library (not YouTube). Simplified upload flow.
 * Requirements: 1.1, Task 3.3
 */

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Upload, X, FileVideo, AlertCircle, CheckCircle2, Folder } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"

interface UploadFile {
    id: string
    file: File
    progress: number
    status: "pending" | "uploading" | "completed" | "error"
    error?: string
    videoId?: string
    title: string
    description: string
    tags: string[]
    folderId: string | null
}

const MAX_FILES = 10
const MAX_FILE_SIZE = 128 * 1024 * 1024 * 1024 // 128GB (YouTube limit)
const ALLOWED_FORMATS = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv", "video/webm", "video/x-matroska"]

export default function LibraryUploadPage() {
    const router = useRouter()
    const { addToast } = useToast()
    const [folders, setFolders] = useState<VideoFolder[]>([])
    const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
    const [isDragging, setIsDragging] = useState(false)
    const [activeFileId, setActiveFileId] = useState<string | null>(null)
    const [isUploading, setIsUploading] = useState(false)
    const [tagInput, setTagInput] = useState("")

    const loadFolders = useCallback(async () => {
        try {
            const data = await videoLibraryApi.getAllFolders()
            setFolders(data)
        } catch (error) {
            console.error("Failed to load folders:", error)
        }
    }, [])

    // Load folders on mount
    useEffect(() => {
        loadFolders()
    }, [loadFolders])

    const validateFile = (file: File): string | null => {
        if (!ALLOWED_FORMATS.includes(file.type)) {
            return "Invalid file format. Please upload a video file."
        }
        if (file.size > MAX_FILE_SIZE) {
            return "File size exceeds 128GB limit."
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
                folderId: null,
            })
        }

        if (errors.length > 0) {
            addToast({ type: "error", title: "Upload Error", description: errors.join(", ") })
        }

        setUploadFiles((prev) => [...prev, ...newFiles])
        if (newFiles.length > 0 && !activeFileId) {
            setActiveFileId(newFiles[0].id)
        }
    }

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
    }, [uploadFiles])

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
        setUploadFiles((prev) => prev.map((f) => (f.id === id ? { ...f, ...updates } : f)))
    }

    const addTag = (fileId: string) => {
        if (!tagInput.trim()) return
        const file = uploadFiles.find((f) => f.id === fileId)
        if (file && !file.tags.includes(tagInput.trim())) {
            updateFileMetadata(fileId, { tags: [...file.tags, tagInput.trim()] })
        }
        setTagInput("")
    }

    const removeTag = (fileId: string, tag: string) => {
        const file = uploadFiles.find((f) => f.id === fileId)
        if (file) {
            updateFileMetadata(fileId, { tags: file.tags.filter((t) => t !== tag) })
        }
    }

    const uploadFile = async (uploadFile: UploadFile) => {
        try {
            updateFileMetadata(uploadFile.id, { status: "uploading", progress: 0 })

            // Simulate progress (real implementation would track actual upload progress)
            const progressInterval = setInterval(() => {
                setUploadFiles((prev) =>
                    prev.map((f) =>
                        f.id === uploadFile.id && f.progress < 90
                            ? { ...f, progress: f.progress + 10 }
                            : f
                    )
                )
            }, 500)

            const video = await videoLibraryApi.uploadToLibrary(uploadFile.file, {
                title: uploadFile.title,
                description: uploadFile.description || undefined,
                tags: uploadFile.tags.length > 0 ? uploadFile.tags : undefined,
                folderId: uploadFile.folderId,
            })

            clearInterval(progressInterval)
            updateFileMetadata(uploadFile.id, {
                status: "completed",
                progress: 100,
                videoId: video.id,
            })

            addToast({
                type: "success",
                title: "Upload Complete",
                description: `${uploadFile.title} uploaded successfully`,
            })
        } catch (error: any) {
            updateFileMetadata(uploadFile.id, {
                status: "error",
                error: error.message || "Upload failed",
            })
            addToast({
                type: "error",
                title: "Upload Failed",
                description: error.message || "Failed to upload video",
            })
        }
    }

    const handleUploadAll = async () => {
        setIsUploading(true)
        const pendingFiles = uploadFiles.filter((f) => f.status === "pending")

        for (const file of pendingFiles) {
            await uploadFile(file)
        }

        setIsUploading(false)

        // Check if all completed
        const allCompleted = uploadFiles.every((f) => f.status === "completed")
        if (allCompleted) {
            addToast({
                type: "success",
                title: "All Uploads Complete",
                description: "All videos uploaded to library successfully",
            })
            setTimeout(() => router.push("/dashboard/videos/library"), 2000)
        }
    }

    const activeFile = uploadFiles.find((f) => f.id === activeFileId)

    const getStatusIcon = (status: UploadFile["status"]) => {
        switch (status) {
            case "pending":
                return <FileVideo className="h-4 w-4 text-muted-foreground" />
            case "uploading":
                return <Upload className="h-4 w-4 text-blue-500 animate-pulse" />
            case "completed":
                return <CheckCircle2 className="h-4 w-4 text-green-500" />
            case "error":
                return <AlertCircle className="h-4 w-4 text-red-500" />
        }
    }

    const getStatusBadge = (status: UploadFile["status"]) => {
        const variants: Record<UploadFile["status"], "default" | "secondary" | "destructive" | "outline"> = {
            pending: "secondary",
            uploading: "default",
            completed: "outline",
            error: "destructive",
        }
        return <Badge variant={variants[status]}>{status}</Badge>
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Upload to Library</h1>
                        <p className="text-muted-foreground">
                            Upload videos to your library. You can upload to YouTube later.
                        </p>
                    </div>
                    <Button variant="outline" onClick={() => router.push("/dashboard/videos/library")}>
                        Back to Library
                    </Button>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* File List */}
                    <div className="lg:col-span-1">
                        <Card>
                            <CardHeader>
                                <CardTitle>Files ({uploadFiles.length})</CardTitle>
                                <CardDescription>
                                    {uploadFiles.filter((f) => f.status === "completed").length} completed
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {uploadFiles.map((file) => (
                                    <div
                                        key={file.id}
                                        className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted ${activeFileId === file.id ? "bg-muted" : ""
                                            }`}
                                        onClick={() => setActiveFileId(file.id)}
                                    >
                                        {getStatusIcon(file.status)}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{file.title}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {(file.file.size / (1024 * 1024)).toFixed(1)} MB
                                            </p>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-6 w-6"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                removeFile(file.id)
                                            }}
                                            disabled={file.status === "uploading"}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}

                                {uploadFiles.length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        No files selected
                                    </p>
                                )}
                            </CardContent>
                        </Card>

                        {uploadFiles.length > 0 && (
                            <Button
                                className="w-full mt-4"
                                onClick={handleUploadAll}
                                disabled={isUploading || uploadFiles.every((f) => f.status !== "pending")}
                            >
                                <Upload className="mr-2 h-4 w-4" />
                                Upload All ({uploadFiles.filter((f) => f.status === "pending").length})
                            </Button>
                        )}
                    </div>

                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Drop Zone */}
                        {uploadFiles.length === 0 && (
                            <Card
                                className={`border-2 border-dashed transition-colors ${isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25"
                                    }`}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                            >
                                <CardContent className="flex flex-col items-center justify-center py-12">
                                    <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                                    <h3 className="text-lg font-semibold mb-2">Drop videos here</h3>
                                    <p className="text-muted-foreground mb-4">or</p>
                                    <Button asChild>
                                        <label>
                                            <input
                                                type="file"
                                                multiple
                                                accept="video/*"
                                                className="hidden"
                                                onChange={handleFileInput}
                                            />
                                            Browse Files
                                        </label>
                                    </Button>
                                    <p className="text-xs text-muted-foreground mt-4">
                                        Max {MAX_FILES} files, up to 128GB each
                                    </p>
                                </CardContent>
                            </Card>
                        )}

                        {/* File Details */}
                        {activeFile && (
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <CardTitle>Video Details</CardTitle>
                                        {getStatusBadge(activeFile.status)}
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {activeFile.status === "uploading" && (
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between text-sm">
                                                <span>Uploading...</span>
                                                <span>{activeFile.progress}%</span>
                                            </div>
                                            <Progress value={activeFile.progress} />
                                        </div>
                                    )}

                                    {activeFile.status === "error" && (
                                        <div className="flex items-center gap-2 p-3 rounded bg-red-500/10 text-red-500">
                                            <AlertCircle className="h-4 w-4" />
                                            <p className="text-sm">{activeFile.error}</p>
                                        </div>
                                    )}

                                    {activeFile.status === "completed" && (
                                        <div className="flex items-center gap-2 p-3 rounded bg-green-500/10 text-green-500">
                                            <CheckCircle2 className="h-4 w-4" />
                                            <p className="text-sm">Upload completed successfully</p>
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <Label>Title *</Label>
                                        <Input
                                            value={activeFile.title}
                                            onChange={(e) =>
                                                updateFileMetadata(activeFile.id, { title: e.target.value })
                                            }
                                            disabled={activeFile.status !== "pending"}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Description</Label>
                                        <Textarea
                                            value={activeFile.description}
                                            onChange={(e) =>
                                                updateFileMetadata(activeFile.id, { description: e.target.value })
                                            }
                                            rows={4}
                                            disabled={activeFile.status !== "pending"}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Folder</Label>
                                        <Select
                                            value={activeFile.folderId || "none"}
                                            onValueChange={(value) =>
                                                updateFileMetadata(activeFile.id, {
                                                    folderId: value === "none" ? null : value,
                                                })
                                            }
                                            disabled={activeFile.status !== "pending"}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="none">
                                                    <div className="flex items-center gap-2">
                                                        <Folder className="h-4 w-4" />
                                                        No Folder
                                                    </div>
                                                </SelectItem>
                                                {folders.map((folder) => (
                                                    <SelectItem key={folder.id} value={folder.id}>
                                                        <div className="flex items-center gap-2">
                                                            <Folder
                                                                className="h-4 w-4"
                                                                style={{ color: folder.color || undefined }}
                                                            />
                                                            {folder.name}
                                                        </div>
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Tags</Label>
                                        <div className="flex gap-2">
                                            <Input
                                                value={tagInput}
                                                onChange={(e) => setTagInput(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") {
                                                        e.preventDefault()
                                                        addTag(activeFile.id)
                                                    }
                                                }}
                                                placeholder="Add tag and press Enter"
                                                disabled={activeFile.status !== "pending"}
                                            />
                                            <Button
                                                type="button"
                                                variant="outline"
                                                onClick={() => addTag(activeFile.id)}
                                                disabled={activeFile.status !== "pending"}
                                            >
                                                Add
                                            </Button>
                                        </div>
                                        {activeFile.tags.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                                {activeFile.tags.map((tag) => (
                                                    <Badge
                                                        key={tag}
                                                        variant="secondary"
                                                        className="cursor-pointer"
                                                        onClick={() =>
                                                            activeFile.status === "pending" &&
                                                            removeTag(activeFile.id, tag)
                                                        }
                                                    >
                                                        {tag}
                                                        {activeFile.status === "pending" && (
                                                            <span className="ml-1">×</span>
                                                        )}
                                                    </Badge>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Add More Files */}
                        {uploadFiles.length > 0 && uploadFiles.length < MAX_FILES && (
                            <Card className="border-dashed">
                                <CardContent className="py-6">
                                    <Button variant="outline" className="w-full" asChild>
                                        <label>
                                            <input
                                                type="file"
                                                multiple
                                                accept="video/*"
                                                className="hidden"
                                                onChange={handleFileInput}
                                            />
                                            <Upload className="mr-2 h-4 w-4" />
                                            Add More Files
                                        </label>
                                    </Button>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    )
}
