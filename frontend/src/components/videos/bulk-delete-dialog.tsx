/**
 * Bulk Delete Dialog
 * 
 * Confirmation dialog for deleting multiple videos.
 * Requirements: 5.3 (Bulk Operations)
 */

"use client"

import { useState } from "react"
import { Loader2, AlertTriangle } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi } from "@/lib/api/video-library"
import type { Video } from "@/types"

interface BulkDeleteDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    videos: Video[]
}

export function BulkDeleteDialog({
    open,
    onOpenChange,
    onSuccess,
    videos,
}: BulkDeleteDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState(0)

    const handleDelete = async () => {
        if (videos.length === 0) return

        try {
            setLoading(true)
            setProgress(0)

            // Delete each video with progress tracking
            for (let i = 0; i < videos.length; i++) {
                await videoLibraryApi.deleteFromLibrary(videos[i].id)
                setProgress(((i + 1) / videos.length) * 100)
            }

            addToast({
                type: "success",
                title: "Success",
                description: `${videos.length} video${videos.length !== 1 ? "s" : ""} deleted successfully`,
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to delete videos:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to delete videos",
            })
        } finally {
            setLoading(false)
            setProgress(0)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Delete Videos</DialogTitle>
                    <DialogDescription>
                        Are you sure you want to delete {videos.length} video{videos.length !== 1 ? "s" : ""}?
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Warning */}
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                            <p className="font-semibold mb-2">This action cannot be undone!</p>
                            <p className="text-sm">
                                All selected videos will be permanently deleted from your library.
                                {videos.some((v) => v.youtubeId) && (
                                    <span className="block mt-1">
                                        Note: Videos already uploaded to YouTube will remain on YouTube.
                                    </span>
                                )}
                            </p>
                        </AlertDescription>
                    </Alert>

                    {/* Progress */}
                    {loading && (
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span>Deleting videos...</span>
                                <span>{Math.round(progress)}%</span>
                            </div>
                            <Progress value={progress} />
                        </div>
                    )}

                    {/* Video List */}
                    <div className="rounded-lg border bg-muted/50 p-4">
                        <p className="text-sm font-medium mb-2">Videos to delete:</p>
                        <ul className="space-y-1 text-sm text-muted-foreground max-h-[200px] overflow-y-auto">
                            {videos.slice(0, 10).map((video) => (
                                <li key={video.id} className="truncate">
                                    • {video.title}
                                </li>
                            ))}
                            {videos.length > 10 && (
                                <li className="text-xs italic">
                                    ... and {videos.length - 10} more
                                </li>
                            )}
                        </ul>
                    </div>
                </div>

                <DialogFooter>
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        variant="destructive"
                        onClick={handleDelete}
                        disabled={loading}
                    >
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Delete {videos.length} Video{videos.length !== 1 ? "s" : ""}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
