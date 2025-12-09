"use client"

import { useState } from "react"
import { Sparkles, Copy, Check, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
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
            return
        }

        try {
            setLoading(true)
            const response = await aiApi.generateDescription({
                video_title: title,
                video_content: currentDescription || title,
                keywords: title.split(' ').filter(w => w.length > 3),
                include_timestamps: false,
                include_cta: true,
            })
            setSuggestion(response.suggestion || null)
        } catch (error) {
            console.error("Failed to generate description:", error)
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
                <Button variant="outline" size="sm" className="gap-2">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    AI Description
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-purple-500" />
                        AI Description Generator
                    </DialogTitle>
                    <DialogDescription>
                        Generate an SEO-optimized description with keywords and CTAs
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                    {loading ? (
                        <div className="space-y-3 animate-pulse">
                            <Skeleton className="h-40 w-full rounded-xl" />
                            <div className="flex gap-2">
                                <Skeleton className="h-6 w-20 rounded-full" />
                                <Skeleton className="h-6 w-24 rounded-full" />
                                <Skeleton className="h-6 w-16 rounded-full" />
                            </div>
                        </div>
                    ) : suggestion ? (
                        <>
                            <div className="border rounded-xl p-4 space-y-4">
                                <Textarea
                                    value={suggestion.description}
                                    readOnly
                                    rows={10}
                                    className="resize-none bg-muted/30 border-0 focus-visible:ring-0"
                                />

                                <div className="flex items-center justify-between pt-3 border-t">
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-muted-foreground">SEO Score:</span>
                                            <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                                                    style={{ width: `${suggestion.seo_score * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-semibold text-purple-600">
                                                {Math.round(suggestion.seo_score * 100)}%
                                            </span>
                                        </div>
                                        {suggestion.estimated_read_time && (
                                            <span className="text-xs text-muted-foreground">
                                                ~{suggestion.estimated_read_time}s read
                                            </span>
                                        )}
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={copyToClipboard} className="gap-2">
                                        {copied ? (
                                            <>
                                                <Check className="h-4 w-4 text-green-500" />
                                                Copied
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="h-4 w-4" />
                                                Copy
                                            </>
                                        )}
                                    </Button>
                                </div>

                                {suggestion.has_cta && (
                                    <p className="text-sm text-muted-foreground bg-green-500/10 p-3 rounded-lg border border-green-500/20">
                                        ✅ Includes Call-to-Action elements
                                    </p>
                                )}

                                {suggestion.keywords_used && suggestion.keywords_used.length > 0 && (
                                    <div className="space-y-2">
                                        <span className="text-xs font-medium text-muted-foreground">Keywords Used:</span>
                                        <div className="flex flex-wrap gap-1.5">
                                            {suggestion.keywords_used.map((keyword) => (
                                                <Badge
                                                    key={keyword}
                                                    variant="secondary"
                                                    className="text-xs bg-purple-500/10 text-purple-600"
                                                >
                                                    {keyword}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex justify-end gap-2 pt-2">
                                <Button variant="outline" onClick={() => setOpen(false)}>
                                    Cancel
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={generateDescription}
                                    disabled={loading}
                                    className="gap-2"
                                >
                                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                                    Regenerate
                                </Button>
                                <Button
                                    onClick={applyDescription}
                                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                                >
                                    Apply Description
                                </Button>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-12 text-muted-foreground">
                            <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p>Click regenerate to get AI description</p>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
