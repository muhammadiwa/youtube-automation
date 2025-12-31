/**
 * Bulk Upload to YouTube Dialog
 * 
 * Dialog for uploading multiple videos to YouTube at once.
 * Requirements: 5.1 (Bulk Upload)
 */

"use client"

import { useState, useEffect } from "react"
import { Loader2, Youtube, CheckCircle2, XCircle } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi } from "@/lib/api/video-library"
import type { Video } from "@/types"

interface BulkUploadDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    videos: Video[]
    accounts: Array<{ id: string; channelTitle: string; thumbnailUrl?: string }>
}

interface UploadResult {
    videoId: string
    videoTitle: string
    status: "pending" | "uploading" | "success" | "error"
    jobId?: string
    error?: string
}

export function BulkUploadDialog({
    open,
    onOpenChange,
    onSuccess,
    videos,
    accounts,
}: BulkUploadDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [accountId, setAccountId] = useState("")
    const [uploadResults, setUploadResults] = useState<UploadResult[]>([])
    const [currentIndex, setCurrentIndex] = useState(0)

    useEffect(() => {
        if (videos.length > 0 && accounts.length > 0) {
            setAccountId(accounts[0].id)
            setUploadResults(
                videos.map((v) => ({
                    videoId: v.id,
                    videoTitle: v.title,
                    status: "pending",
                }))
            )
            setCurrentIndex(0)
        }
    }, [videos, accounts])

    const handleUpload = async () => {
        if (!accountId || videos.length === 0) return

        try {
            setLoading(true)

            const result = await videoLibraryApi.bulkUploadToYouTube({
                videoIds: videos.map((v) => v.id),
                accountId,
            })

            // Update results with job IDs
            const newResults = videos.map((video, index) => {
                const job = result.jobs.find((j) => j.videoId === video.id)
                const error = result.errors.find((e) => e.includes(video.id))

                return {
                    videoId: video.id,
                    videoTitle: video.title,
                    status: error ? "error" : "success",
                    jobId: job?.jobId,
                    error: error,
                } as UploadResult
            })

            setUploadResults(newResults)

            addToast({
                type: "success",
                title: "Bulk Upload Started",
                description: `${result.jobsCreated} videos queued for upload`,
            })

            setTimeout(() => {
                onSuccess()
                onOpenChange(false)
            }, 2000)
        } catch (error: any) {
            console.error("Failed to bulk upload:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to start bulk upload",
            })
        } finally {
            setLoading(false)
        }
    }

    const successCount = uploadResults.filter((r) => r.status === "success").length
    const errorCount = uploadResults.filter((r) => r.status === "error").length
    const progress = uploadResults.length > 0
        ? ((successCount + errorCount) / uploadResults.length) * 100
        : 0

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Youtube className="h-5 w-5 text-red-600" />
                        Bulk Upload to YouTube
                    </DialogTitle>
                    <DialogDescription>
                        Upload {videos.length} video{videos.length !== 1 ? "s" : ""} to YouTube
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Account Selector */}
                    <div className="space-y-2">
                        <Label htmlFor="accountId">
                            YouTube Account <span className="text-destructive">*</span>
                        </Label>
                        {accounts.length === 0 ? (
                            <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm">
                                No YouTube accounts connected. Please connect an account first.
                            </div>
                        ) : (
                            <Select
                                value={accountId}
                                onValueChange={setAccountId}
                                disabled={loading}
                            >
                                <SelectTrigger id="accountId">
                                    <SelectValue placeholder="Select account" />
                                </SelectTrigger>
                                <SelectContent>
                                    {accounts.map((account) => (
                                        <SelectItem key={account.id} value={account.id}>
                                            <div className="flex items-center gap-2">
                                                {account.thumbnailUrl && (
                                                    <img
                                                        src={account.thumbnailUrl}
                                                        alt={account.channelTitle}
                                                        className="h-6 w-6 rounded-full"
                                                    />
                                                )}
                                                <span>{account.channelTitle}</span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        )}
                    </div>

                    {/* Progress */}
                    {loading && (
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span>Uploading videos...</span>
                                <span>
                                    {successCount + errorCount} / {uploadResults.length}
                                </span>
                            </div>
                            <Progress value={progress} />
                        </div>
                    )}

                    {/* Results */}
                    {uploadResults.length > 0 && (
                        <div className="space-y-2">
                            <Label>Upload Status</Label>
                            <ScrollArea className="h-[300px] rounded-md border">
                                <div className="space-y-2 p-4">
                                    {uploadResults.map((result, index) => (
                                        <div
                                            key={result.videoId}
                                            className="flex items-center justify-between rounded-lg border p-3"
                                        >
                                            <div className="flex-1">
                                                <p className="font-medium">{result.videoTitle}</p>
                                                {result.error && (
                                                    <p className="text-sm text-destructive">
                                                        {result.error}
                                                    </p>
                                                )}
                                            </div>
                                            <div className="ml-4">
                                                {result.status === "pending" && (
                                                    <div className="h-5 w-5 rounded-full border-2 border-muted" />
                                                )}
                                                {result.status === "uploading" && (
                                                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                                )}
                                                {result.status === "success" && (
                                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                                )}
                                                {result.status === "error" && (
                                                    <XCircle className="h-5 w-5 text-destructive" />
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </ScrollArea>
                        </div>
                    )}

                    {/* Summary */}
                    {!loading && uploadResults.some((r) => r.status !== "pending") && (
                        <div className="rounded-lg border bg-muted/50 p-4">
                            <div className="flex items-center justify-between text-sm">
                                <span>Success:</span>
                                <span className="font-semibold text-green-600">{successCount}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <span>Failed:</span>
                                <span className="font-semibold text-destructive">{errorCount}</span>
                            </div>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={loading}
                    >
                        {loading ? "Close" : "Cancel"}
                    </Button>
                    {!loading && uploadResults.every((r) => r.status === "pending") && (
                        <Button
                            type="button"
                            onClick={handleUpload}
                            disabled={loading || accounts.length === 0 || !accountId}
                        >
                            Start Upload
                        </Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
