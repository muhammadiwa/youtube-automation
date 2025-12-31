/**
 * Bulk Move to Folder Dialog
 * 
 * Dialog for moving multiple videos to a folder at once.
 * Requirements: 5.2 (Bulk Operations)
 */

"use client"

import { useState } from "react"
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

interface BulkMoveDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    videos: Video[]
    folders: VideoFolder[]
}

export function BulkMoveDialog({
    open,
    onOpenChange,
    onSuccess,
    videos,
    folders,
}: BulkMoveDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)

    const handleMove = async () => {
        if (videos.length === 0) return

        try {
            setLoading(true)

            // Move each video
            const promises = videos.map((video) =>
                videoLibraryApi.moveToFolder(video.id, selectedFolderId)
            )

            await Promise.all(promises)

            addToast({
                type: "success",
                title: "Success",
                description: `${videos.length} video${videos.length !== 1 ? "s" : ""} moved successfully`,
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to move videos:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to move videos",
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Move Videos to Folder</DialogTitle>
                    <DialogDescription>
                        Move {videos.length} video{videos.length !== 1 ? "s" : ""} to a folder
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
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
                        disabled={loading}
                    >
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Move Videos
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
