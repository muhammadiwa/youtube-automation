/**
 * Create Folder Dialog Component
 * 
 * Dialog for creating new video folders with validation.
 * Requirements: 1.2 (Library Organization - Folders)
 * Design: CreateFolderDialog component
 */

"use client"

import { useState } from "react"
import { Loader2 } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"

interface CreateFolderDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    folders: VideoFolder[]
}

const FOLDER_COLORS = [
    { value: "#ef4444", label: "Red" },
    { value: "#f97316", label: "Orange" },
    { value: "#eab308", label: "Yellow" },
    { value: "#22c55e", label: "Green" },
    { value: "#3b82f6", label: "Blue" },
    { value: "#8b5cf6", label: "Purple" },
    { value: "#ec4899", label: "Pink" },
    { value: "#64748b", label: "Gray" },
]

export function CreateFolderDialog({
    open,
    onOpenChange,
    onSuccess,
    folders,
}: CreateFolderDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        name: "",
        parentId: null as string | null,
        description: "",
        color: "#3b82f6",
    })
    const [errors, setErrors] = useState<Record<string, string>>({})

    const validateForm = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.name.trim()) {
            newErrors.name = "Folder name is required"
        } else if (formData.name.length > 255) {
            newErrors.name = "Folder name must be less than 255 characters"
        }

        // Check for duplicate names in same parent
        const duplicateExists = folders.some(
            (folder) =>
                folder.name.toLowerCase() === formData.name.toLowerCase() &&
                folder.parentId === formData.parentId
        )
        if (duplicateExists) {
            newErrors.name = "A folder with this name already exists in this location"
        }

        // Check max depth (5 levels)
        if (formData.parentId) {
            const depth = getFolderDepth(formData.parentId, folders)
            if (depth >= 5) {
                newErrors.parentId = "Maximum folder depth (5 levels) reached"
            }
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm()) return

        try {
            setLoading(true)
            await videoLibraryApi.createFolder({
                name: formData.name.trim(),
                parentId: formData.parentId || undefined,
                description: formData.description.trim() || undefined,
                color: formData.color,
            })

            addToast({
                type: "success",
                title: "Success",
                description: "Folder created successfully",
            })

            // Reset form
            setFormData({
                name: "",
                parentId: null,
                description: "",
                color: "#3b82f6",
            })
            setErrors({})

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to create folder:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to create folder",
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Create New Folder</DialogTitle>
                        <DialogDescription>
                            Create a folder to organize your video library
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        {/* Folder Name */}
                        <div className="space-y-2">
                            <Label htmlFor="name">
                                Folder Name <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) =>
                                    setFormData({ ...formData, name: e.target.value })
                                }
                                placeholder="e.g., Tutorials, Gaming, Vlogs"
                                disabled={loading}
                                className={errors.name ? "border-destructive" : ""}
                            />
                            {errors.name && (
                                <p className="text-sm text-destructive">{errors.name}</p>
                            )}
                        </div>

                        {/* Parent Folder */}
                        <div className="space-y-2">
                            <Label htmlFor="parentId">Parent Folder (Optional)</Label>
                            <Select
                                value={formData.parentId || "root"}
                                onValueChange={(value) =>
                                    setFormData({
                                        ...formData,
                                        parentId: value === "root" ? null : value,
                                    })
                                }
                                disabled={loading}
                            >
                                <SelectTrigger id="parentId">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="root">Root (No Parent)</SelectItem>
                                    {folders
                                        .filter((f) => !f.parentId) // Only show root folders
                                        .map((folder) => (
                                            <SelectItem key={folder.id} value={folder.id}>
                                                {folder.name}
                                            </SelectItem>
                                        ))}
                                </SelectContent>
                            </Select>
                            {errors.parentId && (
                                <p className="text-sm text-destructive">{errors.parentId}</p>
                            )}
                            <p className="text-xs text-muted-foreground">
                                Maximum depth: 5 levels
                            </p>
                        </div>

                        {/* Description */}
                        <div className="space-y-2">
                            <Label htmlFor="description">Description (Optional)</Label>
                            <Textarea
                                id="description"
                                value={formData.description}
                                onChange={(e) =>
                                    setFormData({ ...formData, description: e.target.value })
                                }
                                placeholder="Add a description for this folder"
                                rows={3}
                                disabled={loading}
                            />
                        </div>

                        {/* Color Picker */}
                        <div className="space-y-2">
                            <Label htmlFor="color">Folder Color</Label>
                            <div className="flex gap-2">
                                {FOLDER_COLORS.map((color) => (
                                    <button
                                        key={color.value}
                                        type="button"
                                        onClick={() =>
                                            setFormData({ ...formData, color: color.value })
                                        }
                                        className={`h-8 w-8 rounded-full border-2 transition-all ${formData.color === color.value
                                                ? "scale-110 border-foreground"
                                                : "border-transparent hover:scale-105"
                                            }`}
                                        style={{ backgroundColor: color.value }}
                                        title={color.label}
                                        disabled={loading}
                                    />
                                ))}
                            </div>
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
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Folder
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}

/**
 * Helper function to calculate folder depth
 */
function getFolderDepth(folderId: string, folders: VideoFolder[]): number {
    const folder = folders.find((f) => f.id === folderId)
    if (!folder || !folder.parentId) return 1

    return 1 + getFolderDepth(folder.parentId, folders)
}
