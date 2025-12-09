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
            const results = await aiApi.generateTitles({
                videoTitle: currentTitle,
                videoDescription: description,
            })
            setSuggestions(results)
        } catch (error) {
            console.error("Failed to generate titles:", error)
            alert("Failed to generate title suggestions")
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
                <Button variant="outline" size="sm">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Titles
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>AI Title Suggestions</DialogTitle>
                    <DialogDescription>
                        Choose from 5 AI-generated title variations optimized for engagement
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                    {loading ? (
                        <>
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="border rounded-lg p-4 space-y-2">
                                    <Skeleton className="h-6 w-full" />
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-2 w-24" />
                                </div>
                            ))}
                        </>
                    ) : suggestions.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <p>No suggestions generated yet</p>
                        </div>
                    ) : (
                        suggestions.map((suggestion, index) => (
                            <div
                                key={index}
                                className="border rounded-lg p-4 hover:border-primary transition-colors"
                            >
                                <div className="flex items-start justify-between gap-3 mb-2">
                                    <h3 className="font-semibold flex-1">{suggestion.title}</h3>
                                    <div className="flex gap-1">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => copyToClipboard(suggestion.title, index)}
                                        >
                                            {copiedIndex === index ? (
                                                <Check className="h-4 w-4 text-green-500" />
                                            ) : (
                                                <Copy className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </div>
                                </div>

                                <p className="text-sm text-muted-foreground mb-3">
                                    {suggestion.reasoning}
                                </p>

                                <div className="flex items-center justify-between">
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
                                    <Button size="sm" onClick={() => applyTitle(suggestion.title)}>
                                        Apply
                                    </Button>
                                </div>

                                {suggestion.keywords.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-3">
                                        {suggestion.keywords.map((keyword) => (
                                            <Badge key={keyword} variant="secondary" className="text-xs">
                                                {keyword}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {!loading && suggestions.length > 0 && (
                    <div className="flex justify-end gap-2 mt-4">
                        <Button variant="outline" onClick={generateSuggestions}>
                            Regenerate
                        </Button>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}
