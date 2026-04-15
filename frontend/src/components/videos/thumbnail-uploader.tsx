"use client"

import { useState, useRef, useCallback } from "react"
import { Upload, X, Image as ImageIcon, Loader2, Check, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/toast"
import { videosApi } from "@/lib/api/videos"

interface ThumbnailUploaderProps {
    videoId: string
    currentThumbnail?: string | null
    onUploadComplete?: (thumbnailUrl: string) => void
    disabled?: boolean
}

const MAX_FILE_SIZE = 2 * 1024 * 1024 // 2MB
const ALLOWED_FORMATS = ["image/jpeg", "image/png", "image/gif"]
const RECOMMENDED_WIDTH = 1280
const RECOMMENDED_HEIGHT = 720

export function ThumbnailUploader({
    videoId,
    currentThumbnail,
    onUploadComplete,
    disabled = false,
}: ThumbnailUploaderProps) {
    const { addToast } = useToast()
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [preview, setPreview] = useState<string | null>(currentThumbnail || null)
    const [isUploading, setIsUploading] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)
    const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle")
    const [error, setError] = useState<string | null>(null)

    const validateFile = (file: File): string | null => {
        if (!ALLOWED_FORMATS.includes(file.type)) {
            return "Invalid format. Please use JPG, PNG, or GIF."
        }
        if (file.size > MAX_FILE_SIZE) {
            return "File size exceeds 2MB limit."
        }
        return null
    }

    const validateDimensions = (file: File): Promise<{ width: number; height: number } | null> => {
        return new Promise((resolve) => {
            const img = new Image()
            img.onload = () => {
                resolve({ width: img.width, height: img.height })
                URL.revokeObjectURL(img.src)
            }
            img.onerror = () => {
                resolve(null)
                URL.revokeObjectURL(img.src)
            }
            img.src = URL.createObjectURL(file)
        })
    }

    const handleFile = async (file: File) => {
        setError(null)

        // Validate file type and size
        const validationError = validateFile(file)
        if (validationError) {
            setError(validationError)
            addToast({ type: "error", title: "Invalid File", description: validationError })
            return
        }

        // Validate dimensions
        const dimensions = await validateDimensions(file)
        if (!dimensions) {
            setError("Could not read image dimensions")
            return
        }

        // Warn about non-optimal dimensions
        if (dimensions.width < RECOMMENDED_WIDTH || dimensions.height < RECOMMENDED_HEIGHT) {
            addToast({
                type: "warning",
                title: "Low Resolution",
                description: `Recommended size is ${RECOMMENDED_WIDTH}x${RECOMMENDED_HEIGHT}px. Your image is ${dimensions.width}x${dimensions.height}px.`,
            })
        }

        // Create preview
        const previewUrl = URL.createObjectURL(file)
        setPreview(previewUrl)

        // Upload
        await uploadThumbnail(file)
    }

    const uploadThumbnail = async (file: File) => {
        setIsUploading(true)
        setUploadStatus("uploading")
        setUploadProgress(0)

        // Simulate progress since we don't have real progress tracking
        const progressInterval = setInterval(() => {
            setUploadProgress((prev) => Math.min(prev + 10, 90))
        }, 200)

        try {
            const result = await videosApi.uploadThumbnail(videoId, file)

            clearInterval(progressInterval)
            setUploadProgress(100)
            setUploadStatus("success")

            addToast({
                type: "success",
                title: "Thumbnail Uploaded",
                description: "Your thumbnail has been uploaded successfully.",
            })

            if (onUploadComplete) {
                onUploadComplete(preview || "")
            }
        } catch (err: any) {
            clearInterval(progressInterval)
            setUploadStatus("error")
            const errorMessage = err?.detail || err?.message || "Failed to upload thumbnail"
            setError(errorMessage)
            addToast({ type: "error", title: "Upload Failed", description: errorMessage })
        } finally {
            setIsUploading(false)
        }
    }

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)

        const file = e.dataTransfer.files[0]
        if (file) {
            handleFile(file)
        }
    }, [])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            handleFile(file)
        }
        e.target.value = ""
    }

    const handleRemove = () => {
        setPreview(null)
        setUploadStatus("idle")
        setError(null)
    }

    const handleBrowseClick = () => {
        fileInputRef.current?.click()
    }

    return (
        <div className="space-y-4">
            <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_FORMATS.join(",")}
                onChange={handleFileInput}
                className="hidden"
                disabled={disabled || isUploading}
            />

            {preview ? (
                <div className="relative">
                    <div className="relative aspect-video rounded-lg overflow-hidden border bg-muted">
                        <img
                            src={preview}
                            alt="Thumbnail preview"
                            className="w-full h-full object-cover"
                        />
                        {uploadStatus === "uploading" && (
                            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                                <div className="text-center text-white">
                                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                                    <p className="text-sm">Uploading...</p>
                                    <Progress value={uploadProgress} className="w-32 mt-2" />
                                </div>
                            </div>
                        )}
                        {uploadStatus === "success" && (
                            <div className="absolute top-2 right-2">
                                <div className="bg-green-500 text-white rounded-full p-1">
                                    <Check className="h-4 w-4" />
                                </div>
                            </div>
                        )}
                    </div>
                    {!isUploading && (
                        <div className="flex gap-2 mt-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleBrowseClick}
                                disabled={disabled}
                            >
                                Change
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleRemove}
                                disabled={disabled}
                            >
                                <X className="h-4 w-4 mr-1" />
                                Remove
                            </Button>
                        </div>
                    )}
                </div>
            ) : (
                <div
                    className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${isDragging
                            ? "border-primary bg-primary/5"
                            : "border-muted-foreground/25 hover:border-primary/50"
                        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={disabled ? undefined : handleBrowseClick}
                >
                    <ImageIcon className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
                    <h3 className="text-sm font-medium mb-1">
                        Upload custom thumbnail
                    </h3>
                    <p className="text-xs text-muted-foreground mb-2">
                        Drag and drop or click to browse
                    </p>
                    <p className="text-xs text-muted-foreground">
                        JPG, PNG, or GIF • Max 2MB • {RECOMMENDED_WIDTH}x{RECOMMENDED_HEIGHT}px recommended
                    </p>
                </div>
            )}

            {error && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                </div>
            )}
        </div>
    )
}

export default ThumbnailUploader
