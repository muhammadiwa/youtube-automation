"use client"

/**
 * Processing Status Badge Component
 * 
 * Displays video processing status with progress indicator.
 * Used for videos being processed in background (upload, conversion).
 * Uses existing columns: status, upload_progress, last_upload_error
 */

import { useEffect, useState } from "react"
import { Loader2, CheckCircle, XCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { videoLibraryApi } from "@/lib/api/video-library"

interface ProcessingStatusBadgeProps {
    videoId: string
    status: string
    uploadProgress?: number
    lastUploadError?: string | null
    onComplete?: () => void
}

export function ProcessingStatusBadge({
    videoId,
    status,
    uploadProgress: initialProgress,
    lastUploadError: initialError,
    onComplete,
}: ProcessingStatusBadgeProps) {
    const [progress, setProgress] = useState(initialProgress || 0)
    const [error, setError] = useState(initialError)
    const [isPolling, setIsPolling] = useState(false)

    // Poll for status updates if video is processing
    useEffect(() => {
        if (status !== "processing_upload") {
            return
        }

        setIsPolling(true)
        const pollInterval = setInterval(async () => {
            try {
                const statusData = await videoLibraryApi.getProcessingStatus(videoId)
                setProgress(statusData.uploadProgress)
                setError(statusData.uploadError)

                if (statusData.isReady) {
                    clearInterval(pollInterval)
                    setIsPolling(false)
                    onComplete?.()
                } else if (statusData.status === "failed") {
                    clearInterval(pollInterval)
                    setIsPolling(false)
                }
            } catch (err) {
                console.error("Failed to poll processing status:", err)
            }
        }, 2000) // Poll every 2 seconds

        return () => {
            clearInterval(pollInterval)
            setIsPolling(false)
        }
    }, [videoId, status, onComplete])

    // If not processing, don't show anything
    if (status !== "processing_upload" && status !== "in_library" && status !== "failed") {
        return null
    }

    // If ready, show ready badge
    if (status === "in_library") {
        return (
            <Badge variant="outline" className="gap-1 text-green-600 border-green-200 bg-green-50">
                <CheckCircle className="h-3 w-3" />
                Ready
            </Badge>
        )
    }

    // If failed, show error
    if (status === "failed" || error) {
        return (
            <Badge variant="destructive" className="gap-1">
                <XCircle className="h-3 w-3" />
                Failed
            </Badge>
        )
    }

    // Show processing status with progress
    return (
        <div className="flex flex-col gap-1">
            <Badge variant="secondary" className="gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processing {progress}%
            </Badge>
            {progress > 0 && progress < 100 && (
                <Progress value={progress} className="h-1 w-20" />
            )}
        </div>
    )
}

/**
 * Compact version for list/grid views
 */
export function ProcessingStatusBadgeCompact({
    videoId,
    status,
    uploadProgress,
    onComplete,
}: Omit<ProcessingStatusBadgeProps, "lastUploadError">) {
    const [currentProgress, setCurrentProgress] = useState(uploadProgress || 0)
    const [currentStatus, setCurrentStatus] = useState(status)

    // Poll for status updates
    useEffect(() => {
        if (status !== "processing_upload") {
            return
        }

        const pollInterval = setInterval(async () => {
            try {
                const statusData = await videoLibraryApi.getProcessingStatus(videoId)
                setCurrentProgress(statusData.uploadProgress)
                setCurrentStatus(statusData.status)

                if (statusData.isReady) {
                    clearInterval(pollInterval)
                    onComplete?.()
                } else if (statusData.status === "failed") {
                    clearInterval(pollInterval)
                }
            } catch (err) {
                console.error("Failed to poll processing status:", err)
            }
        }, 2000)

        return () => clearInterval(pollInterval)
    }, [videoId, status, onComplete])

    if (status !== "processing_upload") {
        return null
    }

    if (currentStatus === "failed") {
        return (
            <Badge variant="destructive" className="gap-1 text-xs">
                <XCircle className="h-3 w-3" />
                Failed
            </Badge>
        )
    }

    return (
        <Badge variant="secondary" className="gap-1 text-xs">
            <Loader2 className="h-3 w-3 animate-spin" />
            {currentProgress}%
        </Badge>
    )
}
