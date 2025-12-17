"use client"

import { useState, useEffect } from "react"
import { History, RotateCcw, ChevronDown, ChevronRight, Loader2, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { useToast } from "@/components/ui/toast"
import { getCategoryName } from "@/components/videos/category-select"

interface MetadataVersion {
    id: string
    version: number
    title: string
    description: string
    tags: string[]
    categoryId?: string
    visibility: string
    thumbnailUrl?: string
    createdAt: string
    changedBy?: string
    changeReason?: string
}

interface VersionHistoryProps {
    videoId: string
    currentTitle?: string
    onRollback?: () => void
}

export function VersionHistory({
    videoId,
    currentTitle,
    onRollback,
}: VersionHistoryProps) {
    const { addToast } = useToast()
    const [versions, setVersions] = useState<MetadataVersion[]>([])
    const [loading, setLoading] = useState(true)
    const [isOpen, setIsOpen] = useState(false)
    const [selectedVersion, setSelectedVersion] = useState<MetadataVersion | null>(null)
    const [isPreviewOpen, setIsPreviewOpen] = useState(false)
    const [isRollbackOpen, setIsRollbackOpen] = useState(false)
    const [isRollingBack, setIsRollingBack] = useState(false)

    useEffect(() => {
        if (isOpen) {
            loadVersions()
        }
    }, [isOpen, videoId])

    const loadVersions = async () => {
        try {
            setLoading(true)
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/${videoId}/versions`,
                {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                    },
                }
            )
            if (response.ok) {
                const data = await response.json()
                // Map backend snake_case to frontend camelCase
                const mappedVersions = (Array.isArray(data) ? data : data.versions || []).map((v: any) => ({
                    id: v.id,
                    version: v.version_number,
                    title: v.title,
                    description: v.description,
                    tags: v.tags || [],
                    categoryId: v.category_id,
                    visibility: v.visibility,
                    thumbnailUrl: v.thumbnail_url,
                    createdAt: v.created_at,
                    changedBy: v.changed_by,
                    changeReason: v.change_reason,
                }))
                setVersions(mappedVersions)
            }
        } catch (error) {
            console.error("Failed to load versions:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleRollback = async () => {
        if (!selectedVersion) return

        try {
            setIsRollingBack(true)
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/videos/${videoId}/rollback/${selectedVersion.version}`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                        "Content-Type": "application/json",
                    },
                }
            )

            if (response.ok) {
                addToast({
                    type: "success",
                    title: "Rollback Successful",
                    description: `Restored to version ${selectedVersion.version}`,
                })
                setIsRollbackOpen(false)
                setSelectedVersion(null)
                loadVersions()
                onRollback?.()
            } else {
                throw new Error("Failed to rollback")
            }
        } catch (error) {
            addToast({
                type: "error",
                title: "Rollback Failed",
                description: "Could not restore to this version",
            })
        } finally {
            setIsRollingBack(false)
        }
    }

    const openPreview = (version: MetadataVersion) => {
        setSelectedVersion(version)
        setIsPreviewOpen(true)
    }

    const openRollbackConfirm = (version: MetadataVersion) => {
        setSelectedVersion(version)
        setIsRollbackOpen(true)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString()
    }

    return (
        <>
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <CollapsibleTrigger asChild>
                    <Button variant="ghost" className="w-full justify-between p-0 h-auto">
                        <div className="flex items-center gap-2">
                            <History className="h-4 w-4" />
                            <span className="font-semibold">Version History</span>
                        </div>
                        {isOpen ? (
                            <ChevronDown className="h-4 w-4" />
                        ) : (
                            <ChevronRight className="h-4 w-4" />
                        )}
                    </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-4">
                    {loading ? (
                        <div className="space-y-2">
                            <Skeleton className="h-16 w-full" />
                            <Skeleton className="h-16 w-full" />
                        </div>
                    ) : versions.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-4">
                            No version history available
                        </p>
                    ) : (
                        <div className="space-y-2">
                            {versions.map((version) => (
                                <div
                                    key={version.id}
                                    className="border rounded-lg p-3 space-y-2"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="outline">v{version.version}</Badge>
                                            <span className="text-sm font-medium truncate max-w-[150px]">
                                                {version.title}
                                            </span>
                                        </div>
                                        <div className="flex gap-1">
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => openPreview(version)}
                                            >
                                                <Eye className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => openRollbackConfirm(version)}
                                            >
                                                <RotateCcw className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                    {version.changeReason && (
                                        <p className="text-xs text-muted-foreground">
                                            {version.changeReason}
                                        </p>
                                    )}
                                    <p className="text-xs text-muted-foreground">
                                        {formatDate(version.createdAt)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </CollapsibleContent>
            </Collapsible>

            {/* Preview Dialog */}
            <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Version {selectedVersion?.version} Details</DialogTitle>
                        <DialogDescription>
                            {selectedVersion && formatDate(selectedVersion.createdAt)}
                        </DialogDescription>
                    </DialogHeader>
                    {selectedVersion && (
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium">Title</label>
                                <p className="mt-1 p-2 bg-muted rounded text-sm">
                                    {selectedVersion.title}
                                </p>
                                {currentTitle && currentTitle !== selectedVersion.title && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Current: {currentTitle}
                                    </p>
                                )}
                            </div>
                            <div>
                                <label className="text-sm font-medium">Description</label>
                                <p className="mt-1 p-2 bg-muted rounded text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
                                    {selectedVersion.description || "(empty)"}
                                </p>
                            </div>
                            <div>
                                <label className="text-sm font-medium">Tags</label>
                                <div className="mt-1 flex flex-wrap gap-1">
                                    {selectedVersion.tags && selectedVersion.tags.length > 0 ? (
                                        selectedVersion.tags.map((tag) => (
                                            <Badge key={tag} variant="secondary">
                                                {tag}
                                            </Badge>
                                        ))
                                    ) : (
                                        <span className="text-sm text-muted-foreground">(no tags)</span>
                                    )}
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium">Category</label>
                                    <p className="mt-1 text-sm">
                                        {getCategoryName(selectedVersion.categoryId || "22")}
                                    </p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium">Visibility</label>
                                    <p className="mt-1 text-sm capitalize">
                                        {selectedVersion.visibility}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsPreviewOpen(false)}>
                            Close
                        </Button>
                        <Button onClick={() => {
                            setIsPreviewOpen(false)
                            if (selectedVersion) openRollbackConfirm(selectedVersion)
                        }}>
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Restore This Version
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Rollback Confirmation */}
            <AlertDialog open={isRollbackOpen} onOpenChange={setIsRollbackOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Restore Version {selectedVersion?.version}?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will restore the video metadata to version {selectedVersion?.version}.
                            The current metadata will be saved as a new version.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isRollingBack}>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleRollback} disabled={isRollingBack}>
                            {isRollingBack && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Restore
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    )
}

export default VersionHistory
