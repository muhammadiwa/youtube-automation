"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
    Mail,
    Edit2,
    Eye,
    X,
    Save,
    Loader2,
    Code,
    FileText,
    Tag,
    CheckCircle,
    XCircle,
} from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/components/ui/toast"
import { configApi, type EmailTemplate, type EmailTemplatePreviewResponse } from "@/lib/api/admin"

const defaultTemplates: EmailTemplate[] = [
    {
        template_id: "welcome",
        template_name: "Welcome Email",
        subject: "Welcome to {{platform_name}}!",
        body_html: "<h1>Welcome, {{user_name}}!</h1><p>Thank you for joining us.</p>",
        body_text: "Welcome, {{user_name}}! Thank you for joining us.",
        variables: ["platform_name", "user_name", "user_email"],
        is_active: true,
        category: "onboarding",
    },
]

export default function EmailTemplatesPage() {
    const [templates, setTemplates] = useState<EmailTemplate[]>(defaultTemplates)
    const [isLoading, setIsLoading] = useState(true)
    const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
    const [previewData, setPreviewData] = useState<EmailTemplatePreviewResponse | null>(null)
    const [isPreviewOpen, setIsPreviewOpen] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [isLoadingPreview, setIsLoadingPreview] = useState(false)
    const { addToast } = useToast()

    const fetchTemplates = useCallback(async () => {
        try {
            const data = await configApi.getEmailTemplates()
            setTemplates(data.templates)
        } catch (error) {
            console.error("Failed to fetch templates:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchTemplates()
    }, [fetchTemplates])

    const handleSaveTemplate = async () => {
        if (!editingTemplate) return
        setIsSaving(true)
        try {
            await configApi.updateEmailTemplate(editingTemplate.template_id, editingTemplate)
            setTemplates((prev) =>
                prev.map((t) =>
                    t.template_id === editingTemplate.template_id ? editingTemplate : t
                )
            )
            setEditingTemplate(null)
            addToast({
                type: "success",
                title: "Template updated",
                description: `${editingTemplate.template_name} has been updated successfully.`,
            })
        } catch (error) {
            console.error("Failed to update template:", error)
            addToast({
                type: "error",
                title: "Failed to update",
                description: "An error occurred while updating the template.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    const handlePreview = async (template: EmailTemplate) => {
        setIsLoadingPreview(true)
        setIsPreviewOpen(true)
        try {
            // Create sample data from variables
            const sampleData: Record<string, string> = {}
            template.variables.forEach((v) => {
                sampleData[v] = `[${v}]`
            })
            const preview = await configApi.previewEmailTemplate(template.template_id, sampleData)
            setPreviewData(preview)
        } catch (error) {
            console.error("Failed to preview template:", error)
            // Fallback to local preview
            setPreviewData({
                subject: template.subject,
                body_html: template.body_html,
                body_text: template.body_text,
            })
        } finally {
            setIsLoadingPreview(false)
        }
    }

    const updateEditingTemplate = <K extends keyof EmailTemplate>(
        key: K,
        value: EmailTemplate[K]
    ) => {
        if (!editingTemplate) return
        setEditingTemplate((prev) => (prev ? { ...prev, [key]: value } : null))
    }

    const getCategoryColor = (category: string) => {
        const colors: Record<string, string> = {
            onboarding: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
            billing: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
            notification: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
            security: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
            general: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
        }
        return colors[category] || colors.general
    }

    return (
        <ConfigFormWrapper
            title="Email Templates"
            description="Manage email templates with HTML/text editors and preview functionality."
            icon={<Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={async () => { }}
            onReset={() => { }}
            isDirty={false}
            isLoading={isLoading}
        >
            <div className="space-y-4">
                {/* Template List */}
                {templates.map((template) => (
                    <motion.div
                        key={template.template_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <Card>
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <CardTitle className="text-base">
                                            {template.template_name}
                                        </CardTitle>
                                        <Badge className={getCategoryColor(template.category)}>
                                            {template.category}
                                        </Badge>
                                        {template.is_active ? (
                                            <Badge variant="outline" className="text-green-600">
                                                <CheckCircle className="h-3 w-3 mr-1" />
                                                Active
                                            </Badge>
                                        ) : (
                                            <Badge variant="outline" className="text-slate-500">
                                                <XCircle className="h-3 w-3 mr-1" />
                                                Inactive
                                            </Badge>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handlePreview(template)}
                                        >
                                            <Eye className="h-4 w-4 mr-1" />
                                            Preview
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setEditingTemplate(template)}
                                        >
                                            <Edit2 className="h-4 w-4 mr-1" />
                                            Edit
                                        </Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    <p className="text-sm text-slate-600 dark:text-slate-400">
                                        <span className="font-medium">Subject:</span> {template.subject}
                                    </p>
                                    <div className="flex flex-wrap gap-1">
                                        {template.variables.map((v) => (
                                            <Badge key={v} variant="secondary" className="text-xs">
                                                <Tag className="h-3 w-3 mr-1" />
                                                {`{{${v}}}`}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Edit Template Dialog */}
            <AnimatePresence>
                {editingTemplate && (
                    <Dialog open={!!editingTemplate} onOpenChange={() => setEditingTemplate(null)}>
                        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                            <DialogHeader>
                                <DialogTitle>Edit {editingTemplate.template_name}</DialogTitle>
                                <DialogDescription>
                                    Edit the email template content and settings.
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-6 py-4">
                                {/* Basic Info */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Template Name</Label>
                                        <Input
                                            value={editingTemplate.template_name}
                                            onChange={(e) =>
                                                updateEditingTemplate("template_name", e.target.value)
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Category</Label>
                                        <Input
                                            value={editingTemplate.category}
                                            onChange={(e) =>
                                                updateEditingTemplate("category", e.target.value)
                                            }
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label>Subject Line</Label>
                                    <Input
                                        value={editingTemplate.subject}
                                        onChange={(e) =>
                                            updateEditingTemplate("subject", e.target.value)
                                        }
                                    />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                    <div>
                                        <Label>Active</Label>
                                        <p className="text-xs text-slate-500">
                                            Enable or disable this template
                                        </p>
                                    </div>
                                    <Switch
                                        checked={editingTemplate.is_active}
                                        onCheckedChange={(checked) =>
                                            updateEditingTemplate("is_active", checked)
                                        }
                                    />
                                </div>

                                <Separator />

                                {/* Content Editors */}
                                <Tabs defaultValue="html">
                                    <TabsList>
                                        <TabsTrigger value="html">
                                            <Code className="h-4 w-4 mr-2" />
                                            HTML
                                        </TabsTrigger>
                                        <TabsTrigger value="text">
                                            <FileText className="h-4 w-4 mr-2" />
                                            Plain Text
                                        </TabsTrigger>
                                    </TabsList>
                                    <TabsContent value="html" className="mt-4">
                                        <div className="space-y-2">
                                            <Label>HTML Body</Label>
                                            <Textarea
                                                value={editingTemplate.body_html}
                                                onChange={(e) =>
                                                    updateEditingTemplate("body_html", e.target.value)
                                                }
                                                className="font-mono text-sm min-h-[300px]"
                                            />
                                        </div>
                                    </TabsContent>
                                    <TabsContent value="text" className="mt-4">
                                        <div className="space-y-2">
                                            <Label>Plain Text Body</Label>
                                            <Textarea
                                                value={editingTemplate.body_text}
                                                onChange={(e) =>
                                                    updateEditingTemplate("body_text", e.target.value)
                                                }
                                                className="font-mono text-sm min-h-[300px]"
                                            />
                                        </div>
                                    </TabsContent>
                                </Tabs>

                                <Separator />

                                {/* Variables */}
                                <div>
                                    <Label className="mb-2 block">Available Variables</Label>
                                    <div className="flex flex-wrap gap-2">
                                        {editingTemplate.variables.map((v) => (
                                            <Badge key={v} variant="outline">
                                                <Tag className="h-3 w-3 mr-1" />
                                                {`{{${v}}}`}
                                            </Badge>
                                        ))}
                                    </div>
                                    <p className="text-xs text-slate-500 mt-2">
                                        Use these variables in your template content.
                                    </p>
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-4 border-t">
                                <Button
                                    variant="outline"
                                    onClick={() => setEditingTemplate(null)}
                                    disabled={isSaving}
                                >
                                    <X className="h-4 w-4 mr-2" />
                                    Cancel
                                </Button>
                                <Button onClick={handleSaveTemplate} disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="h-4 w-4 mr-2" />
                                            Save Changes
                                        </>
                                    )}
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                )}
            </AnimatePresence>

            {/* Preview Dialog */}
            <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Email Preview</DialogTitle>
                        <DialogDescription>
                            Preview how the email will look to recipients.
                        </DialogDescription>
                    </DialogHeader>

                    {isLoadingPreview ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                        </div>
                    ) : previewData ? (
                        <div className="space-y-4 py-4">
                            <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                                <p className="text-sm font-medium">Subject:</p>
                                <p className="text-slate-700 dark:text-slate-300">
                                    {previewData.subject}
                                </p>
                            </div>

                            <Tabs defaultValue="html">
                                <TabsList>
                                    <TabsTrigger value="html">HTML Preview</TabsTrigger>
                                    <TabsTrigger value="text">Plain Text</TabsTrigger>
                                </TabsList>
                                <TabsContent value="html" className="mt-4">
                                    <div
                                        className="p-4 bg-white dark:bg-slate-900 border rounded-lg min-h-[300px]"
                                        dangerouslySetInnerHTML={{ __html: previewData.body_html }}
                                    />
                                </TabsContent>
                                <TabsContent value="text" className="mt-4">
                                    <pre className="p-4 bg-slate-100 dark:bg-slate-800 rounded-lg whitespace-pre-wrap text-sm min-h-[300px]">
                                        {previewData.body_text}
                                    </pre>
                                </TabsContent>
                            </Tabs>
                        </div>
                    ) : null}
                </DialogContent>
            </Dialog>
        </ConfigFormWrapper>
    )
}
