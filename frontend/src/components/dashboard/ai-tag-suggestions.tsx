"use client"

import { useState } from "react"
import { Sparkles, Plus, Tag, TrendingUp, Star, Hash } from "lucide-react"
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
import { cn } from "@/lib/utils"

interface AITagSuggestionsProps {
    title: string
    description?: string
    currentTags: string[]
    onAddTag: (tag: string) => void
}

const categoryConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
    primary: { icon: Star, color: "text-yellow-500 bg-yellow-500/10 border-yellow-500/30", label: "Primary" },
    secondary: { icon: Tag, color: "text-blue-500 bg-blue-500/10 border-blue-500/30", label: "Secondary" },
    trending: { icon: TrendingUp, color: "text-green-500 bg-green-500/10 border-green-500/30", label: "Trending" },
    long_tail: { icon: Hash, color: "text-purple-500 bg-purple-500/10 border-purple-500/30", label: "Long Tail" },
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
            const response = await aiApi.generateTags({
                video_title: title,
                video_description: description,
            })
            setSuggestions(response.suggestions)
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

    const getCategoryInfo = (category: string) => {
        return categoryConfig[category] || categoryConfig.secondary
    }

    return (
        <Dialog open={open} onOpenChange={handleOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="group hover:border-primary/50 transition-all duration-300">
                    <Sparkles className="mr-2 h-4 w-4 group-hover:text-primary transition-colors" />
                    Suggest Tags
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5">
                            <Tag className="h-5 w-5 text-primary" />
                        </div>
                        AI Tag Suggestions
                    </DialogTitle>
                    <DialogDescription>
                        Discover relevant tags to improve your video's discoverability
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto space-y-4 mt-4 pr-2">
                    {loading ? (
                        <div className="grid grid-cols-2 gap-3">
                            {[...Array(8)].map((_, i) => (
                                <Skeleton key={i} className="h-20 w-full rounded-xl" />
                            ))}
                        </div>
                    ) : suggestions.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <Tag className="h-12 w-12 mx-auto mb-4 opacity-30" />
                            <p>No tag suggestions generated yet</p>
                            <Button variant="outline" className="mt-4" onClick={generateTags}>
                                Generate Tags
                            </Button>
                        </div>
                    ) : (
                        <>
                            <div className="grid grid-cols-2 gap-3">
                                {suggestions.map((suggestion, index) => {
                                    const categoryInfo = getCategoryInfo(suggestion.category)
                                    const CategoryIcon = categoryInfo.icon
                                    const added = isTagAdded(suggestion.tag)

                                    return (
                                        <div
                                            key={index}
                                            className={cn(
                                                "border rounded-xl p-4 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5",
                                                added ? "bg-muted/50 border-muted" : "hover:border-primary/50 bg-card"
                                            )}
                                        >
                                            <div className="flex items-start justify-between gap-2 mb-3">
                                                <span className={cn(
                                                    "font-medium text-sm truncate flex-1",
                                                    added && "text-muted-foreground"
                                                )}>
                                                    #{suggestion.tag}
                                                </span>
                                                <Button
                                                    size="sm"
                                                    variant={added ? "secondary" : "default"}
                                                    onClick={() => handleAddTag(suggestion.tag)}
                                                    disabled={added}
                                                    className={cn(
                                                        "h-7 text-xs transition-all",
                                                        !added && "bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70"
                                                    )}
                                                >
                                                    {added ? (
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
                                                <Badge
                                                    variant="outline"
                                                    className={cn("text-xs gap-1", categoryInfo.color)}
                                                >
                                                    <CategoryIcon className="h-3 w-3" />
                                                    {categoryInfo.label}
                                                </Badge>
                                                <div className="flex items-center gap-1">
                                                    <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-primary to-primary/60 rounded-full transition-all"
                                                            style={{ width: `${suggestion.relevance_score * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-muted-foreground">
                                                        {Math.round(suggestion.relevance_score * 100)}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </>
                    )}
                </div>

                {suggestions.length > 0 && (
                    <div className="flex justify-between items-center gap-2 pt-4 border-t mt-4">
                        <p className="text-xs text-muted-foreground">
                            {suggestions.filter(s => isTagAdded(s.tag)).length} of {suggestions.length} tags added
                        </p>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={generateTags} disabled={loading}>
                                {loading ? "Generating..." : "Regenerate"}
                            </Button>
                            <Button onClick={() => setOpen(false)}>Done</Button>
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}
