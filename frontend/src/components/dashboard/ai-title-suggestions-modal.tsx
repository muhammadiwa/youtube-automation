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
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { aiApi, type TitleSuggestion } from "@/lib/api/ai"

interface AITitleSuggestionsModalProps {
    currentTitle: string
    description?: string
    onApply: (title: string) => void
}

export function AITitleSuggestionsModal({
    currentTitle,
    description,
    onApply,
}: AITitleSuggestionsModalProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [suggestions, setSuggestions] = useState<TitleSuggestion[]>([])
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

    const generateSuggestions = async () => {
        try {
            setLoading(true)
            const response = await aiApi.generateTitles({
                video_content: description || currentTitle || "Video content",
                keywords: currentTitle ? currentTitle.split(' ').filter(w => w.length > 3) : [],
                style: "engaging",
            })
            setSuggestions(response.suggestions || [])
        } catch (error) {
            console.error("Failed to generate titles:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleOpen = (isOpen: boolean) => {
        setOpen(isOpen)
        if (isOpen && suggestions.length === 0) {
            generateSuggestions()
        }
    }

    const copyToClipboard = (text: string, index: number) => {
        navigator.clipboard.writeText(text)
        setCopiedIndex(index)
        setTimeout(() => setCopiedIndex(null), 2000)
    }

    const applyTitle = (title: string) => {
        onApply(title)
        setOpen(false)
    }

    return (
        <Dialog open={open} onOpenChange={handleOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <Sparkles className="h-4 w-4 text-yellow-500" />
                    AI Titles
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-yellow-500" />
                        AI Title Suggestions
                    </DialogTitle>
                    <DialogDescription>
                        Choose from 5 AI-generated title variations optimized for engagement and SEO
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-3 mt-4">
                    {loading ? (
                        <>
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="border rounded-xl p-4 space-y-3 animate-pulse">
                                    <Skeleton className="h-6 w-full" />
                                    <Skeleton className="h-4 w-3/4" />
                                    <div className="flex gap-2">
                                        <Skeleton className="h-5 w-16 rounded-full" />
                                        <Skeleton className="h-5 w-20 rounded-full" />
                                    </div>
                                </div>
                            ))}
                        </>
                    ) : suggestions.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p>Click regenerate to get AI suggestions</p>
                        </div>
                    ) : (
                        suggestions.map((suggestion, index) => (
                            <div
                                key={index}
                                className="group border rounded-xl p-4 hover:border-primary/50 hover:shadow-md transition-all duration-200"
                            >
                                <div className="flex items-start justify-between gap-3 mb-2">
                                    <h3 className="font-semibold flex-1 text-base leading-tight">
                                        {suggestion.title}
                                    </h3>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                        onClick={() => copyToClipboard(suggestion.title, index)}
                                    >
                                        {copiedIndex === index ? (
                                            <Check className="h-4 w-4 text-green-500" />
                                        ) : (
                                            <Copy className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>

                                <p className="text-sm text-muted-foreground mb-3">
                                    {suggestion.reasoning}
                                </p>

                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-muted-foreground">Confidence:</span>
                                            <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all"
                                                    style={{ width: `${suggestion.confidence_score * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-semibold text-green-600">
                                                {Math.round(suggestion.confidence_score * 100)}%
                                            </span>
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={() => applyTitle(suggestion.title)}
                                        className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700"
                                    >
                                        Apply
                                    </Button>
                                </div>

                                {suggestion.keywords && suggestion.keywords.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t">
                                        {suggestion.keywords.map((keyword) => (
                                            <Badge
                                                key={keyword}
                                                variant="secondary"
                                                className="text-xs bg-blue-500/10 text-blue-600 hover:bg-blue-500/20"
                                            >
                                                {keyword}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
                    <Button variant="outline" onClick={() => setOpen(false)}>
                        Cancel
                    </Button>
                    <Button
                        variant="outline"
                        onClick={generateSuggestions}
                        disabled={loading}
                        className="gap-2"
                    >
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Regenerate
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    )
}
