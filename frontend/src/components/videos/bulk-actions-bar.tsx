/**
 * Bulk Actions Bar Component
 * 
 * Fixed bar at bottom when videos are selected for bulk operations.
 * Requirements: 5.1, 5.2, 5.3 (Bulk Operations)
 */

"use client"

import { Upload, Folder, Trash2, X, Tag } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface BulkActionsBarProps {
    selectedCount: number
    onUploadToYouTube: () => void
    onMoveToFolder: () => void
    onAddTags: () => void
    onDelete: () => void
    onClearSelection: () => void
}

export function BulkActionsBar({
    selectedCount,
    onUploadToYouTube,
    onMoveToFolder,
    onAddTags,
    onDelete,
    onClearSelection,
}: BulkActionsBarProps) {
    if (selectedCount === 0) return null

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex items-center justify-between gap-4 py-4">
                <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="text-base">
                        {selectedCount} selected
                    </Badge>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onClearSelection}
                    >
                        <X className="mr-2 h-4 w-4" />
                        Clear
                    </Button>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onUploadToYouTube}
                    >
                        <Upload className="mr-2 h-4 w-4" />
                        Upload to YouTube
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onMoveToFolder}
                    >
                        <Folder className="mr-2 h-4 w-4" />
                        Move to Folder
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onAddTags}
                    >
                        <Tag className="mr-2 h-4 w-4" />
                        Add Tags
                    </Button>
                    <Button
                        variant="destructive"
                        size="sm"
                        onClick={onDelete}
                    >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                    </Button>
                </div>
            </div>
        </div>
    )
}
