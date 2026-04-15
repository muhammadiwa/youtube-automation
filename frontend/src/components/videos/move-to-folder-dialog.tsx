/**
 * Move to Folder Dialog Component
 * 
 * Dialog for moving videos to different folders.
 * Requirements: 1.2 (Library Organization - Folders)
 * Design: MoveToFolderDialog component
 */

"use client"

import { useState, useEffect } from "react"
import { Loader2, Folder, FolderOpen } from "lucide-react"
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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"
import type { Video } from "@/types"

interface MoveToFolderDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    video: Video | null
    folders: VideoFolder[]
}

export function MoveToFolderDialog({
    open,
    onOpenChange,
    onSuccess,
    video,
    folders,
}: MoveToFolderDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)

    // Initialize selected folder when dialog opens or video changes
    useEffect(() => {
        if (video && open) {
            setSelectedFolderId(video.folderId || null)
        }
    }, [video, open])

    const handleMove = async () => {
        if (!video) return

        try {
            setLoading(true)
            // Convert undefined to null for API
            const targetFolderId = selectedFolderId === undefined ? null : selectedFolderId
            await videoLibraryApi.moveToFolder(video.id, targetFolderId)

            addToast({
                type: "success",
                title: "Success",
                description: selectedFolderId
                    ? "Video moved to folder successfully"
                    : "Video moved to root successfully",
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to move video:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to move video",
            })
        } finally {
            setLoading(false)
        }
    }

    // Get current folder name
    const currentFolder = video?.folderId
        ? folders.find((f) => f.id === video.folderId)
        : null

    if (!video) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Move Video to Folder</DialogTitle>
                    <DialogDescription>
                        Select a folder to move &quot;{video.title}&quot; to
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Current Location */}
                    <div className="rounded-lg border bg-muted/50 p-3">
                        <p className="text-sm font-medium mb-1">Current Location:</p>
                        <div className="flex items-center gap-2 text-sm">
                            <Folder className="h-4 w-4" />
                            <span>
                                {currentFolder ? currentFolder.name : "Root (No Folder)"}
                            </span>
                        </div>
                    </div>

                    {/* Folder Selection */}
                    <div className="space-y-2">
                        <Label>Select Destination:</Label>
                        <ScrollArea className="h-[300px] rounded-md border p-4">
                            <RadioGroup
                                value={selectedFolderId || "root"}
                                onValueChange={(value) =>
                                    setSelectedFolderId(value === "root" ? null : value)
                                }
                            >
                                {/* Root Option */}
                                <div className="flex items-center space-x-2 py-2">
                                    <RadioGroupItem value="root" id="root" />
                                    <Label
                                        htmlFor="root"
                                        className="flex items-center gap-2 cursor-pointer flex-1"
                                    >
                                        <FolderOpen className="h-4 w-4" />
                                        <span>Root (No Folder)</span>
                                    </Label>
                                </div>

                                {/* Folder Options */}
                                {folders.map((folder) => (
                                    <div
                                        key={folder.id}
                                        className="flex items-center space-x-2 py-2"
                                    >
                                        <RadioGroupItem value={folder.id} id={folder.id} />
                                        <Label
                                            htmlFor={folder.id}
                                            className="flex items-center gap-2 cursor-pointer flex-1"
                                        >
                                            <Folder
                                                className="h-4 w-4"
                                                style={{ color: folder.color || undefined }}
                                            />
                                            <div className="flex-1">
                                                <p className="font-medium">{folder.name}</p>
                                                {folder.description && (
                                                    <p className="text-xs text-muted-foreground">
                                                        {folder.description}
                                                    </p>
                                                )}
                                            </div>
                                        </Label>
                                    </div>
                                ))}

                                {folders.length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        No folders available. Create a folder first.
                                    </p>
                                )}
                            </RadioGroup>
                        </ScrollArea>
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
                        onClick={handleMove}
                        disabled={loading || selectedFolderId === (video.folderId || null)}
                    >
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Move Video
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
