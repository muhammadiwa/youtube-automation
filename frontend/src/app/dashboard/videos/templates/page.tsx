"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    Plus,
    FileText,
    MoreVertical,
    Pencil,
    Trash2,
    Star,
    Copy,
    Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toast"
import { videoTemplatesApi, VideoTemplate, CreateTemplateData } from "@/lib/api/video-templates"
import { CategorySelect, getCategoryName } from "@/components/videos/category-select"

export default function VideoTemplatesPage() {
    const router = useRouter()
    const { addToast } = useToast()
    const [templates, setTemplates] = useState<VideoTemplate[]>([])
    const [loading, setLoading] = useState(true)
    const [isCreateOpen, setIsCreateOpen] = useState(false)
    const [isEditOpen, setIsEditOpen] = useState(false)
    const [isDeleteOpen, setIsDeleteOpen] = useState(false)
    const [selectedTemplate, setSelectedTemplate] = useState<VideoTemplate | null>(null)
    const [saving, setSaving] = useState(false)

    // Form state
    const [formData, setFormData] = useState<CreateTemplateData>({
        name: "",
        description: "",
        titleTemplate: "",
        descriptionTemplate: "",
        tags: [],
        categoryId: "22",
        visibility: "private",
        isDefault: false,
    })
    const [tagInput, setTagInput] = useState("")

    useEffect(() => {
        loadTemplates()
    }, [])

    const loadTemplates = async () => {
        try {
            setLoading(true)
            const data = await videoTemplatesApi.getTemplates()
            setTemplates(data)
        } catch (error) {
            console.error("Failed to load templates:", error)
            addToast({ type: "error", title: "Error", description: "Failed to load templates" })
        } finally {
            setLoading(false)
        }
    }

    const resetForm = () => {
        setFormData({
            name: "",
            description: "",
            titleTemplate: "",
            descriptionTemplate: "",
            tags: [],
            categoryId: "22",
            visibility: "private",
            isDefault: false,
        })
        setTagInput("")
    }

    const handleCreate = async () => {
        if (!formData.name.trim()) {
            addToast({ type: "error", title: "Validation Error", description: "Template name is required" })
            return
        }

        try {
            setSaving(true)
            await videoTemplatesApi.createTemplate(formData)
            addToast({ type: "success", title: "Success", description: "Template created successfully" })
            setIsCreateOpen(false)
            resetForm()
            loadTemplates()
        } catch (error) {
            console.error("Failed to create template:", error)
            addToast({ type: "error", title: "Error", description: "Failed to create template" })
        } finally {
            setSaving(false)
        }
    }

    const handleEdit = async () => {
        if (!selectedTemplate || !formData.name.trim()) return

        try {
            setSaving(true)
            await videoTemplatesApi.updateTemplate(selectedTemplate.id, formData)
            addToast({ type: "success", title: "Success", description: "Template updated successfully" })
            setIsEditOpen(false)
            setSelectedTemplate(null)
            resetForm()
            loadTemplates()
        } catch (error) {
            console.error("Failed to update template:", error)
            addToast({ type: "error", title: "Error", description: "Failed to update template" })
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async () => {
        if (!selectedTemplate) return

        try {
            await videoTemplatesApi.deleteTemplate(selectedTemplate.id)
            addToast({ type: "success", title: "Success", description: "Template deleted successfully" })
            setIsDeleteOpen(false)
            setSelectedTemplate(null)
            loadTemplates()
        } catch (error) {
            console.error("Failed to delete template:", error)
            addToast({ type: "error", title: "Error", description: "Failed to delete template" })
        }
    }

    const handleDuplicate = async (template: VideoTemplate) => {
        try {
            await videoTemplatesApi.createTemplate({
                name: `${template.name} (Copy)`,
                description: template.description,
                titleTemplate: template.titleTemplate,
                descriptionTemplate: template.descriptionTemplate,
                tags: template.tags,
                categoryId: template.categoryId,
                visibility: template.visibility,
                isDefault: false,
            })
            addToast({ type: "success", title: "Success", description: "Template duplicated successfully" })
            loadTemplates()
        } catch (error) {
            console.error("Failed to duplicate template:", error)
            addToast({ type: "error", title: "Error", description: "Failed to duplicate template" })
        }
    }

    const openEditDialog = (template: VideoTemplate) => {
        setSelectedTemplate(template)
        setFormData({
            name: template.name,
            description: template.description || "",
            titleTemplate: template.titleTemplate || "",
            descriptionTemplate: template.descriptionTemplate || "",
            tags: template.tags || [],
            categoryId: template.categoryId || "22",
            visibility: template.visibility || "private",
            isDefault: template.isDefault,
        })
        setIsEditOpen(true)
    }

    const openDeleteDialog = (template: VideoTemplate) => {
        setSelectedTemplate(template)
        setIsDeleteOpen(true)
    }

    const addTag = () => {
        if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
            setFormData({ ...formData, tags: [...(formData.tags || []), tagInput.trim()] })
            setTagInput("")
        }
    }

    const removeTag = (tag: string) => {
        setFormData({ ...formData, tags: formData.tags?.filter((t) => t !== tag) })
    }

    const TemplateForm = () => (
        <div className="space-y-4">
            <div className="space-y-2">
                <Label htmlFor="name">Template Name *</Label>
                <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Gaming Video Template"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Brief description of this template"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="titleTemplate">Title Template</Label>
                <Input
                    id="titleTemplate"
                    value={formData.titleTemplate}
                    onChange={(e) => setFormData({ ...formData, titleTemplate: e.target.value })}
                    placeholder="e.g., {{game}} - Episode {{number}}"
                />
                <p className="text-xs text-muted-foreground">
                    Use {"{{variable}}"} for placeholders
                </p>
            </div>

            <div className="space-y-2">
                <Label htmlFor="descriptionTemplate">Description Template</Label>
                <Textarea
                    id="descriptionTemplate"
                    value={formData.descriptionTemplate}
                    onChange={(e) => setFormData({ ...formData, descriptionTemplate: e.target.value })}
                    placeholder="Enter your description template..."
                    rows={4}
                />
            </div>

            <div className="space-y-2">
                <Label>Default Tags</Label>
                <div className="flex gap-2">
                    <Input
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                e.preventDefault()
                                addTag()
                            }
                        }}
                        placeholder="Add tag and press Enter"
                    />
                    <Button type="button" onClick={addTag} variant="outline">
                        Add
                    </Button>
                </div>
                {formData.tags && formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {formData.tags.map((tag) => (
                            <Badge
                                key={tag}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => removeTag(tag)}
                            >
                                {tag}
                                <span className="ml-1">×</span>
                            </Badge>
                        ))}
                    </div>
                )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                    <Label>Category</Label>
                    <CategorySelect
                        value={formData.categoryId}
                        onValueChange={(value) => setFormData({ ...formData, categoryId: value })}
                    />
                </div>
                <div className="space-y-2">
                    <Label>Default Visibility</Label>
                    <select
                        className="w-full h-10 px-3 rounded-md border border-input bg-background"
                        value={formData.visibility}
                        onChange={(e) => setFormData({ ...formData, visibility: e.target.value as any })}
                    >
                        <option value="private">Private</option>
                        <option value="unlisted">Unlisted</option>
                        <option value="public">Public</option>
                    </select>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                    <Label>Set as Default</Label>
                    <p className="text-xs text-muted-foreground">
                        Auto-apply this template to new uploads
                    </p>
                </div>
                <Switch
                    checked={formData.isDefault}
                    onCheckedChange={(checked) => setFormData({ ...formData, isDefault: checked })}
                />
            </div>
        </div>
    )

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Videos", href: "/dashboard/videos" },
                { label: "Templates" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Video Templates</h1>
                        <p className="text-muted-foreground">
                            Create reusable templates for video metadata
                        </p>
                    </div>
                    <Button onClick={() => { resetForm(); setIsCreateOpen(true) }}>
                        <Plus className="h-4 w-4 mr-2" />
                        Create Template
                    </Button>
                </div>

                {/* Templates Grid */}
                {loading ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <Card key={i}>
                                <CardHeader>
                                    <Skeleton className="h-6 w-32" />
                                    <Skeleton className="h-4 w-48" />
                                </CardHeader>
                                <CardContent>
                                    <Skeleton className="h-20 w-full" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : templates.length === 0 ? (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No templates yet</h3>
                            <p className="text-muted-foreground text-center mb-4">
                                Create your first template to speed up video uploads
                            </p>
                            <Button onClick={() => { resetForm(); setIsCreateOpen(true) }}>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Template
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {templates.map((template) => (
                            <Card key={template.id} className="relative">
                                <CardHeader className="pb-3">
                                    <div className="flex items-start justify-between">
                                        <div className="space-y-1">
                                            <CardTitle className="flex items-center gap-2">
                                                {template.name}
                                                {template.isDefault && (
                                                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                                                )}
                                            </CardTitle>
                                            {template.description && (
                                                <CardDescription>{template.description}</CardDescription>
                                            )}
                                        </div>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                                    <MoreVertical className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={() => openEditDialog(template)}>
                                                    <Pencil className="h-4 w-4 mr-2" />
                                                    Edit
                                                </DropdownMenuItem>
                                                <DropdownMenuItem onClick={() => handleDuplicate(template)}>
                                                    <Copy className="h-4 w-4 mr-2" />
                                                    Duplicate
                                                </DropdownMenuItem>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    onClick={() => openDeleteDialog(template)}
                                                    className="text-destructive"
                                                >
                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    {template.titleTemplate && (
                                        <div>
                                            <p className="text-xs text-muted-foreground mb-1">Title Template</p>
                                            <p className="text-sm font-mono bg-muted px-2 py-1 rounded truncate">
                                                {template.titleTemplate}
                                            </p>
                                        </div>
                                    )}
                                    <div className="flex flex-wrap gap-2">
                                        <Badge variant="outline">
                                            {getCategoryName(template.categoryId || "22")}
                                        </Badge>
                                        <Badge variant="secondary">{template.visibility}</Badge>
                                    </div>
                                    {template.tags && template.tags.length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                            {template.tags.slice(0, 3).map((tag) => (
                                                <Badge key={tag} variant="outline" className="text-xs">
                                                    {tag}
                                                </Badge>
                                            ))}
                                            {template.tags.length > 3 && (
                                                <Badge variant="outline" className="text-xs">
                                                    +{template.tags.length - 3}
                                                </Badge>
                                            )}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Dialog */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Create Template</DialogTitle>
                        <DialogDescription>
                            Create a reusable template for video metadata
                        </DialogDescription>
                    </DialogHeader>
                    <TemplateForm />
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleCreate} disabled={saving}>
                            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Create Template
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Edit Dialog */}
            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Edit Template</DialogTitle>
                        <DialogDescription>
                            Update template settings
                        </DialogDescription>
                    </DialogHeader>
                    <TemplateForm />
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsEditOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleEdit} disabled={saving}>
                            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Save Changes
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Template</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete "{selectedTemplate?.name}"? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </DashboardLayout>
    )
}
