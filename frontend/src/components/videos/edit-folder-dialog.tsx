/**
 * Edit Folder Dialog Component
 * 
 * Dialog for editing existing video folders.
 * Requirements: 1.2 (Library Organization - Folders)
 * Design: EditFolderDialog component
 */

"use client"

import { useState, useEffect } from "react"
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
import { useToast } from "@/components/ui/toast"
import { videoLibraryApi, type VideoFolder } from "@/lib/api/video-library"

interface EditFolderDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    folder: VideoFolder | null
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

export function EditFolderDialog({
    open,
    onOpenChange,
    onSuccess,
    folder,
    folders,
}: EditFolderDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        color: "#3b82f6",
    })
    const [errors, setErrors] = useState<Record<string, string>>({})

    // Pre-fill form when folder changes
    useEffect(() => {
        if (folder) {
            setFormData({
                name: folder.name,
                description: folder.description || "",
                color: folder.color || "#3b82f6",
            })
            setErrors({})
        }
    }, [folder])

    const validateForm = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.name.trim()) {
            newErrors.name = "Folder name is required"
        } else if (formData.name.length > 255) {
            newErrors.name = "Folder name must be less than 255 characters"
        }

        // Check for duplicate names in same parent (excluding current folder)
        const duplicateExists = folders.some(
            (f) =>
                f.id !== folder?.id &&
                f.name.toLowerCase() === formData.name.toLowerCase() &&
                f.parentId === folder?.parentId
        )
        if (duplicateExists) {
            newErrors.name = "A folder with this name already exists in this location"
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!folder || !validateForm()) return

        try {
            setLoading(true)
            await videoLibraryApi.updateFolder(folder.id, {
                name: formData.name.trim(),
                description: formData.description.trim() || undefined,
                color: formData.color,
            })

            addToast({
                type: "success",
                title: "Success",
                description: "Folder updated successfully",
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to update folder:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to update folder",
            })
        } finally {
            setLoading(false)
        }
    }

    if (!folder) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle>Edit Folder</DialogTitle>
                        <DialogDescription>
                            Update folder name, description, and color
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
                            Save Changes
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
