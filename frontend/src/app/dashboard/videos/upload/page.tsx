"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Upload, X, FileVideo, AlertCircle, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { videosApi } from "@/lib/api/videos"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

interface UploadFile {
    id: string
    file: File
    progress: number
    status: "pending" | "uploading" | "completed" | "error"
    error?: string
    jobId?: string
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
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [selectedAccount, setSelectedAccount] = useState<string>("")
    const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
    const [isDragging, setIsDragging] = useState(false)

    useEffect(() => {
        loadAccounts()
    }, [])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts({ status: "active" })
            setAccounts(data)
            if (data.length > 0) {
                setSelectedAccount(data[0].id)
            }
        } catch (error) {
            console.error("Failed to load accounts:", error)
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

            newFiles.push({
                id: `${Date.now()}-${i}`,
                file,
                progress: 0,
                status: "pending",
            })
        }

        if (errors.length > 0) {
            alert(errors.join("\n"))
        }

        setUploadFiles((prev) => [...prev, ...newFiles])
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
        e.target.value = "" // Reset input
    }

    const removeFile = (id: string) => {
        setUploadFiles((prev) => prev.filter((f) => f.id !== id))
    }

    const cancelUpload = (id: string) => {
        // In a real implementation, this would cancel the actual upload
        setUploadFiles((prev) =>
            prev.map((f) => (f.id === id ? { ...f, status: "error", error: "Cancelled by user" } : f))
        )
    }

    const uploadFile = async (uploadFile: UploadFile) => {
        if (!selectedAccount) {
            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id ? { ...f, status: "error", error: "Please select an account" } : f
                )
            )
            return
        }

        setUploadFiles((prev) =>
            prev.map((f) => (f.id === uploadFile.id ? { ...f, status: "uploading", progress: 0 } : f))
        )

        try {
            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setUploadFiles((prev) =>
                    prev.map((f) => {
                        if (f.id === uploadFile.id && f.progress < 90) {
                            return { ...f, progress: f.progress + 10 }
                        }
                        return f
                    })
                )
            }, 500)

            const result = await videosApi.uploadVideo(
                {
                    accountId: selectedAccount,
                    title: uploadFile.file.name.replace(/\.[^/.]+$/, ""), // Remove extension
                    visibility: "private",
                },
                uploadFile.file
            )

            clearInterval(progressInterval)

            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id
                        ? { ...f, status: "completed", progress: 100, jobId: result.jobId }
                        : f
                )
            )
        } catch (error: any) {
            setUploadFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id
                        ? { ...f, status: "error", error: error.message || "Upload failed" }
                        : f
                )
            )
        }
    }

    const uploadAll = async () => {
        const pendingFiles = uploadFiles.filter((f) => f.status === "pending")
        for (const file of pendingFiles) {
            await uploadFile(file)
        }
    }

    const getStatusIcon = (status: UploadFile["status"]) => {
        switch (status) {
            case "completed":
                return <CheckCircle2 className="h-5 w-5 text-green-500" />
            case "error":
                return <AlertCircle className="h-5 w-5 text-destructive" />
            case "uploading":
                return <Upload className="h-5 w-5 text-primary animate-pulse" />
            default:
                return <FileVideo className="h-5 w-5 text-muted-foreground" />
        }
    }

    const getStatusBadge = (status: UploadFile["status"]) => {
        const variants: Record<UploadFile["status"], { variant: any; label: string }> = {
            pending: { variant: "secondary", label: "Pending" },
            uploading: { variant: "default", label: "Uploading" },
            completed: { variant: "default", label: "Completed" },
            error: { variant: "destructive", label: "Error" },
        }
        const config = variants[status]
        return <Badge variant={config.variant}>{config.label}</Badge>
    }

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return "0 Bytes"
        const k = 1024
        const sizes = ["Bytes", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i]
    }

    const pendingCount = uploadFiles.filter((f) => f.status === "pending").length
    const uploadingCount = uploadFiles.filter((f) => f.status === "uploading").length
    const completedCount = uploadFiles.filter((f) => f.status === "completed").length
    const errorCount = uploadFiles.filter((f) => f.status === "error").length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Upload Videos</h1>
                    <p className="text-muted-foreground">Upload up to {MAX_FILES} videos at once</p>
                </div>
                <Button variant="outline" onClick={() => router.push("/dashboard/videos")}>
                    Back to Videos
                </Button>
            </div>

            {/* Account Selection */}
            <Card>
                <CardHeader>
                    <CardTitle>Select YouTube Account</CardTitle>
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
                                        <img
                                            src={account.thumbnailUrl}
                                            alt={account.channelTitle}
                                            className="w-6 h-6 rounded-full"
                                        />
                                        {account.channelTitle}
                                    </div>
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    {accounts.length === 0 && (
                        <p className="text-sm text-muted-foreground mt-2">
                            No active accounts found. Please connect a YouTube account first.
                        </p>
                    )}
                </CardContent>
            </Card>

            {/* Upload Zone */}
            <Card>
                <CardContent className="pt-6">
                    <div
                        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${isDragging
                                ? "border-primary bg-primary/5"
                                : "border-muted-foreground/25 hover:border-primary/50"
                            }`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                    >
                        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">Drag and drop video files here</h3>
                        <p className="text-sm text-muted-foreground mb-4">
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
                        <p className="text-xs text-muted-foreground mt-4">
                            Supported formats: MP4, MOV, AVI, WMV, WebM, MPEG
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Upload Queue */}
            {uploadFiles.length > 0 && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Upload Queue ({uploadFiles.length})</CardTitle>
                            <div className="flex gap-2">
                                {pendingCount > 0 && (
                                    <Button onClick={uploadAll} disabled={!selectedAccount || uploadingCount > 0}>
                                        Upload All ({pendingCount})
                                    </Button>
                                )}
                                {completedCount === uploadFiles.length && (
                                    <Button onClick={() => router.push("/dashboard/videos")}>
                                        View Videos
                                    </Button>
                                )}
                            </div>
                        </div>
                        {(pendingCount > 0 || uploadingCount > 0 || errorCount > 0) && (
                            <div className="flex gap-4 text-sm text-muted-foreground mt-2">
                                {pendingCount > 0 && <span>{pendingCount} pending</span>}
                                {uploadingCount > 0 && <span>{uploadingCount} uploading</span>}
                                {completedCount > 0 && <span>{completedCount} completed</span>}
                                {errorCount > 0 && <span className="text-destructive">{errorCount} failed</span>}
                            </div>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {uploadFiles.map((uploadFile) => (
                            <div key={uploadFile.id} className="border rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    {getStatusIcon(uploadFile.status)}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2 mb-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium truncate">{uploadFile.file.name}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {formatFileSize(uploadFile.file.size)}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {getStatusBadge(uploadFile.status)}
                                                {uploadFile.status === "pending" && (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => removeFile(uploadFile.id)}
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                )}
                                                {uploadFile.status === "uploading" && (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => cancelUpload(uploadFile.id)}
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                        {uploadFile.status === "uploading" && (
                                            <div className="space-y-1">
                                                <Progress value={uploadFile.progress} />
                                                <p className="text-xs text-muted-foreground">
                                                    {uploadFile.progress}% uploaded
                                                </p>
                                            </div>
                                        )}
                                        {uploadFile.status === "error" && (
                                            <div className="flex items-center gap-2 text-sm text-destructive">
                                                <AlertCircle className="h-4 w-4" />
                                                {uploadFile.error}
                                            </div>
                                        )}
                                        {uploadFile.status === "completed" && uploadFile.jobId && (
                                            <p className="text-sm text-muted-foreground">
                                                Upload complete. Processing video...
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
