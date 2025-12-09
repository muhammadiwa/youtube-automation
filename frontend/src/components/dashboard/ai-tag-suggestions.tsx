"use client"

import { useState } from "react"
import { Sparkles, Plus } from "lucide-react"
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
import { aiApi, type TagSuggestion } from "@/lib/api/ai"

interface AITagSuggestionsProps {
    title: string
    description?: string
    currentTags: string[]
    onAddTag: (tag: string) => void
}

export function AITagSuggestions({
    title,
    description,
    currentTags,
    onAddTag,
}: AITagSuggestionsProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [suggestions, setSuggestions] = useState<TagSuggestion[]>([])

    const generateTags = async () => {
        if (!title.trim()) {
            alert("Please enter a video title first")
            return
        }

        try {
            setLoading(true)
            const results = await aiApi.generateTags({
                videoTitle: title,
                videoDescription: description,
            })
            setSuggestions(results)
        } catch (error) {
            console.error("Failed to generate tags:", error)
            alert("Failed to generate tag suggestions")
        } finally {
            setLoading(false)
        }
    }

    const handleOpen = (isOpen: boolean) => {
        setOpen(isOpen)
        if (isOpen && suggestions.length === 0) {
            generateTags()
        }
    }

    const handleAddTag = (tag: string) => {
        if (!currentTags.includes(tag)) {
            onAddTag(tag)
        }
    }

    const isTagAdded = (tag: string) => currentTags.includes(tag)

    return (
        <Dialog open={open} onOpenChange={handleOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                    <Sparkles className="mr-2 h-4 w-4" />
                    Suggest Tags
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>AI Tag Suggestions</DialogTitle>
                    <DialogDescription>
                        Discover relevant tags to improve your video's discoverability
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                    {loading ? (
                        <div className="space-y-2">
                            {[...Array(10)].map((_, i) => (
                                <Skeleton key={i} className="h-8 w-full" />
                            ))}
                        </div>
                    ) : suggestions.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <p>No tag suggestions generated yet</p>
                        </div>
                    ) : (
                        <>
                            <div className="grid grid-cols-2 gap-3">
                                {suggestions.map((suggestion, index) => (
                                    <div
                                        key={index}
                                        className="border rounded-lg p-3 hover:border-primary transition-colors"
                                    >
                                        <div className="flex items-center justify-between gap-2 mb-2">
                                            <span className="font-medium">{suggestion.tag}</span>
                                            <Button
                                                size="sm"
                                                variant={isTagAdded(suggestion.tag) ? "secondary" : "default"}
                                                onClick={() => handleAddTag(suggestion.tag)}
                                                disabled={isTagAdded(suggestion.tag)}
                                            >
                                                {isTagAdded(suggestion.tag) ? (
                                                    "Added"
                                                ) : (
                                                    <>
                                                        <Plus className="mr-1 h-3 w-3" />
                                                        Add
                                                    </>
                                                )}
                                            </Button>
                                        </div>
                                        <div className="flex items-center justify-between text-xs">
                                            <Badge variant="outline" className="text-xs">
                                                {suggestion.category}
                                            </Badge>
                                            <span className="text-muted-foreground">
                                                {Math.round(suggestion.relevance * 100)}% relevant
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="flex justify-end gap-2 mt-4">
                                <Button variant="outline" onClick={generateTags}>
                                    Regenerate
                                </Button>
                                <Button onClick={() => setOpen(false)}>Done</Button>
                            </div>
                        </>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
