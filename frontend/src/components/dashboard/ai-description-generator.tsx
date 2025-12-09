"use client"

import { useState } from "react"
import { Sparkles, Copy, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { aiApi, type DescriptionSuggestion } from "@/lib/api/ai"

interface AIDescriptionGeneratorProps {
    title: string
    currentDescription?: string
    onApply: (description: string) => void
}

export function AIDescriptionGenerator({
    title,
    currentDescription,
    onApply,
}: AIDescriptionGeneratorProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [suggestion, setSuggestion] = useState<DescriptionSuggestion | null>(null)
    const [copied, setCopied] = useState(false)

    const generateDescription = async () => {
        if (!title.trim()) {
            alert("Please enter a video title first")
            return
        }

        try {
            setLoading(true)
            const result = await aiApi.generateDescription({
                videoTitle: title,
                includeHashtags: true,
            })
            setSuggestion(result)
        } catch (error) {
            console.error("Failed to generate description:", error)
            alert("Failed to generate description")
        } finally {
            setLoading(false)
        }
    }

    const handleOpen = (isOpen: boolean) => {
        setOpen(isOpen)
        if (isOpen && !suggestion) {
            generateDescription()
        }
    }

    const copyToClipboard = () => {
        if (suggestion) {
            navigator.clipboard.writeText(suggestion.description)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    const applyDescription = () => {
        if (suggestion) {
            onApply(suggestion.description)
            setOpen(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={handleOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Description
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>AI Description Generator</DialogTitle>
                    <DialogDescription>
                        Generate an SEO-optimized description for your video
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                    {loading ? (
                        <div className="space-y-3">
                            <Skeleton className="h-32 w-full" />
                            <Skeleton className="h-4 w-3/4" />
                            <Skeleton className="h-2 w-24" />
                        </div>
                    ) : suggestion ? (
                        <>
                            <div className="border rounded-lg p-4 space-y-3">
                                <div className="flex items-start justify-between gap-2">
                                    <Textarea
                                        value={suggestion.description}
                                        readOnly
                                        rows={8}
                                        className="resize-none"
                                    />
                                </div>

                                <div className="flex items-center justify-between pt-2 border-t">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">Confidence:</span>
                                        <Progress
                                            value={suggestion.confidenceScore * 100}
                                            className="w-24 h-2"
                                        />
                                        <span className="text-xs font-medium">
                                            {Math.round(suggestion.confidenceScore * 100)}%
                                        </span>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={copyToClipboard}>
                                        {copied ? (
                                            <>
                                                <Check className="mr-2 h-4 w-4 text-green-500" />
                                                Copied
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="mr-2 h-4 w-4" />
                                                Copy
                                            </>
                                        )}
                                    </Button>
                                </div>

                                <p className="text-sm text-muted-foreground">{suggestion.reasoning}</p>
                            </div>

                            <div className="flex justify-end gap-2">
                                <Button variant="outline" onClick={generateDescription}>
                                    Regenerate
                                </Button>
                                <Button onClick={applyDescription}>Apply Description</Button>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <p>No description generated yet</p>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
