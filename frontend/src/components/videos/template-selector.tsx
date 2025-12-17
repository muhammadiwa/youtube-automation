"use client"

import { useState, useEffect } from "react"
import { FileText, Check, ChevronDown, Star, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { videoTemplatesApi, VideoTemplate } from "@/lib/api/video-templates"

interface TemplateSelectorProps {
    onSelect: (template: VideoTemplate) => void
    disabled?: boolean
}

export function TemplateSelector({ onSelect, disabled = false }: TemplateSelectorProps) {
    const [templates, setTemplates] = useState<VideoTemplate[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedTemplate, setSelectedTemplate] = useState<VideoTemplate | null>(null)
    const [loaded, setLoaded] = useState(false)

    useEffect(() => {
        if (!loaded) {
            loadTemplates()
        }
    }, [loaded])

    const loadTemplates = async () => {
        try {
            setLoading(true)
            const data = await videoTemplatesApi.getTemplates()
            setTemplates(data)
            setLoaded(true)

            // Auto-select default template
            const defaultTemplate = data.find((t) => t.isDefault)
            if (defaultTemplate) {
                setSelectedTemplate(defaultTemplate)
            }
        } catch (error) {
            console.error("Failed to load templates:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSelect = (template: VideoTemplate) => {
        setSelectedTemplate(template)
        onSelect(template)
    }

    if (loading) {
        return (
            <Button variant="outline" disabled className="gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading templates...
            </Button>
        )
    }

    if (templates.length === 0) {
        return (
            <Button variant="outline" disabled className="gap-2">
                <FileText className="h-4 w-4" />
                No templates
            </Button>
        )
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" disabled={disabled} className="gap-2">
                    <FileText className="h-4 w-4" />
                    {selectedTemplate ? selectedTemplate.name : "Apply Template"}
                    <ChevronDown className="h-4 w-4 ml-auto" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
                {templates.map((template) => (
                    <DropdownMenuItem
                        key={template.id}
                        onClick={() => handleSelect(template)}
                        className="flex items-center justify-between"
                    >
                        <div className="flex items-center gap-2">
                            {template.isDefault && (
                                <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                            )}
                            <span className="truncate">{template.name}</span>
                        </div>
                        {selectedTemplate?.id === template.id && (
                            <Check className="h-4 w-4 text-primary" />
                        )}
                    </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() => window.open("/dashboard/videos/templates", "_blank")}
                    className="text-muted-foreground"
                >
                    Manage Templates...
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}

export default TemplateSelector
