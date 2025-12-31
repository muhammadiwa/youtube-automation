/**
 * Delete Folder Dialog Component
 * 
 * Confirmation dialog for deleting video folders with validation.
 * Requirements: 1.2 (Library Organization - Folders)
 * Design: DeleteFolderDialog component
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
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"

interface DeleteFolderDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    folder: VideoFolder | null
    folders: VideoFolder[]
    videoCount?: number // Number of videos in this folder
}

export function DeleteFolderDialog({
    open,
    onOpenChange,
    onSuccess,
    folder,
    folders,
    videoCount = 0,
}: DeleteFolderDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)

    // Check if folder has subfolders
    const hasSubfolders = folder
        ? folders.some((f) => f.parentId === folder.id)
        : false

    // Check if folder has videos
    const hasVideos = videoCount > 0

    // Can delete only if folder is empty (no videos and no subfolders)
    const canDelete = !hasVideos && !hasSubfolders

    const handleDelete = async () => {
        if (!folder || !canDelete) return

        try {
            setLoading(true)
            await videoLibraryApi.deleteFolder(folder.id)

            addToast({
                type: "success",
                title: "Success",
                description: "Folder deleted successfully",
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to delete folder:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to delete folder",
            })
        } finally {
            setLoading(false)
        }
    }

    if (!folder) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Delete Folder</DialogTitle>
                    <DialogDescription>
                        Are you sure you want to delete this folder?
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Folder Info */}
                    <div className="rounded-lg border p-4">
                        <div className="flex items-center gap-3">
                            <div
                                className="h-10 w-10 rounded-full"
                                style={{ backgroundColor: folder.color || "#3b82f6" }}
                            />
                            <div>
                                <p className="font-semibold">{folder.name}</p>
                                {folder.description && (
                                    <p className="text-sm text-muted-foreground">
                                        {folder.description}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Validation Errors */}
                    {!canDelete && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                                <p className="font-semibold mb-2">Cannot delete this folder:</p>
                                <ul className="list-disc list-inside space-y-1">
                                    {hasVideos && (
                                        <li>
                                            Folder contains {videoCount} video{videoCount !== 1 ? "s" : ""}
                                        </li>
                                    )}
                                    {hasSubfolders && (
                                        <li>Folder contains subfolders</li>
                                    )}
                                </ul>
                                <p className="mt-2 text-sm">
                                    Please move or delete all contents before deleting this folder.
                                </p>
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Warning */}
                    {canDelete && (
                        <Alert>
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                                This action cannot be undone. The folder will be permanently deleted.
                            </AlertDescription>
                        </Alert>
                    )}
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
                        disabled={loading || !canDelete}
                    >
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Delete Folder
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
