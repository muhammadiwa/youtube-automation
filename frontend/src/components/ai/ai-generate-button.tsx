"use client"

import { useState } from "react"
import { Sparkles, Loader2, ChevronDown, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { aiApi, TitleSuggestion, TagSuggestion } from "@/lib/api/ai"

interface AIGenerateButtonProps {
    type: "title" | "description" | "tags"
    context: {
        videoContent?: string
        videoTitle?: string
        videoDescription?: string
        existingTags?: string[]
    }
    onSelect: (value: string | string[]) => void
    disabled?: boolean
}

export function AIGenerateButton({ type, context, onSelect, disabled }: AIGenerateButtonProps) {
    const [isLoading, setIsLoading] = useState(false)
    const [isOpen, setIsOpen] = useState(false)
    const [suggestions, setSuggestions] = useState<TitleSuggestion[] | TagSuggestion[] | null>(null)
    const [descriptionSuggestion, setDescriptionSuggestion] = useState<string | null>(null)

    const handleGenerate = async () => {
        setIsLoading(true)
        try {
            if (type === "title") {
                const result = await aiApi.generateTitles({
                    video_content: context.videoContent || context.videoTitle || "Video content",
                    style: "engaging",
                })
                setSuggestions(result.suggestions)
                setIsOpen(true)
            } else if (type === "description") {
                const result = await aiApi.generateDescription({
                    video_title: context.videoTitle || "Video Title",
                    video_content: context.videoContent || context.videoTitle || "Video content",
                    include_cta: true,
                })
                setDescriptionSuggestion(result.suggestion.description)
                setIsOpen(true)
            } else if (type === "tags") {
                const result = await aiApi.generateTags({
                    video_title: context.videoTitle || "Video Title",
                    video_description: context.videoDescription,
                    existing_tags: context.existingTags,
                    max_tags: 15,
                })
                setSuggestions(result.suggestions)
                setIsOpen(true)
            }
        } catch (error) {
            console.error("Failed to generate:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleSelectTitle = (title: string) => {
        onSelect(title)
        setIsOpen(false)
    }

    const handleSelectDescription = () => {
        if (descriptionSuggestion) {
            onSelect(descriptionSuggestion)
            setIsOpen(false)
        }
    }

    const handleSelectTags = (tags: string[]) => {
        onSelect(tags)
        setIsOpen(false)
    }

    const getButtonLabel = () => {
        switch (type) {
            case "title": return "Generate Title"
            case "description": return "Generate Description"
            case "tags": return "Suggest Tags"
        }
    }

    return (
        <>
            <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={disabled || isLoading}
                className="gap-2"
            >
                {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                    <Sparkles className="h-4 w-4" />
                )}
                {getButtonLabel()}
            </Button>

            <Dialog open={isOpen} onOpenChange={setIsOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-primary" />
                            AI {type === "title" ? "Title" : type === "description" ? "Description" : "Tag"} Suggestions
                        </DialogTitle>
                        <DialogDescription>
                            {type === "title" && "Select a title suggestion or use it as inspiration"}
                            {type === "description" && "Review and use the generated description"}
                            {type === "tags" && "Select tags to add to your video"}
                        </DialogDescription>
                    </DialogHeader>

                    <ScrollArea className="max-h-[400px]">
                        {type === "title" && suggestions && (
                            <div className="space-y-3">
                                {(suggestions as TitleSuggestion[]).map((suggestion, index) => (
                                    <div
                                        key={index}
                                        className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                                        onClick={() => handleSelectTitle(suggestion.title)}
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                <p className="font-medium">{suggestion.title}</p>
                                                <p className="text-sm text-muted-foreground mt-1">
                                                    {suggestion.reasoning}
                                                </p>
                                                <div className="flex gap-1 mt-2">
                                                    {suggestion.keywords.map((kw, i) => (
                                                        <Badge key={i} variant="secondary" className="text-xs">
                                                            {kw}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                            <Badge variant="outline">
                                                {Math.round(suggestion.confidence_score * 100)}%
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {type === "description" && descriptionSuggestion && (
                            <div className="space-y-4">
                                <div className="p-4 border rounded-lg bg-muted/50">
                                    <pre className="whitespace-pre-wrap text-sm font-sans">
                                        {descriptionSuggestion}
                                    </pre>
                                </div>
                                <Button onClick={handleSelectDescription} className="w-full">
                                    <Check className="h-4 w-4 mr-2" />
                                    Use This Description
                                </Button>
                            </div>
                        )}

                        {type === "tags" && suggestions && (
                            <TagSelector
                                suggestions={suggestions as TagSuggestion[]}
                                onSelect={handleSelectTags}
                            />
                        )}
                    </ScrollArea>
                </DialogContent>
            </Dialog>
        </>
    )
}

interface TagSelectorProps {
    suggestions: TagSuggestion[]
    onSelect: (tags: string[]) => void
}

function TagSelector({ suggestions, onSelect }: TagSelectorProps) {
    const [selectedTags, setSelectedTags] = useState<string[]>([])

    const toggleTag = (tag: string) => {
        setSelectedTags(prev =>
            prev.includes(tag)
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        )
    }

    const getCategoryColor = (category: string) => {
        switch (category) {
            case "primary": return "bg-blue-100 text-blue-800 border-blue-200"
            case "secondary": return "bg-green-100 text-green-800 border-green-200"
            case "trending": return "bg-orange-100 text-orange-800 border-orange-200"
            case "long_tail": return "bg-purple-100 text-purple-800 border-purple-200"
            default: return ""
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                    <Badge
                        key={index}
                        variant="outline"
                        className={`cursor-pointer transition-all ${getCategoryColor(suggestion.category)} ${selectedTags.includes(suggestion.tag) ? "ring-2 ring-primary" : ""
                            }`}
                        onClick={() => toggleTag(suggestion.tag)}
                    >
                        {selectedTags.includes(suggestion.tag) && (
                            <Check className="h-3 w-3 mr-1" />
                        )}
                        {suggestion.tag}
                        <span className="ml-1 opacity-60">
                            {Math.round(suggestion.relevance_score * 100)}%
                        </span>
                    </Badge>
                ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                    {selectedTags.length} tags selected
                </p>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedTags(suggestions.map(s => s.tag))}
                    >
                        Select All
                    </Button>
                    <Button
                        size="sm"
                        onClick={() => onSelect(selectedTags)}
                        disabled={selectedTags.length === 0}
                    >
                        Add Selected Tags
                    </Button>
                </div>
            </div>
        </div>
    )
}

export default AIGenerateButton
