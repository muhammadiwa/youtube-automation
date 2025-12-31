/**
 * Advanced Filter Panel Component
 * 
 * Expandable panel with advanced filtering options for video library.
 * Requirements: 1.2 (Library Organization - Filters)
 * Design: FilterPanel component
 */

"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, X, Calendar, Clock, HardDrive, Tag as TagIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"

export interface AdvancedFilters {
    tags?: string[]
    dateRange?: {
        from?: Date
        to?: Date
        preset?: "today" | "week" | "month" | "custom"
    }
    durationRange?: {
        min?: number // in seconds
        max?: number
        preset?: "short" | "medium" | "long" | "custom"
    }
    fileSizeRange?: {
        min?: number // in MB
        max?: number
        preset?: "small" | "medium" | "large" | "custom"
    }
}

interface AdvancedFilterPanelProps {
    filters: AdvancedFilters
    onFiltersChange: (filters: AdvancedFilters) => void
    availableTags?: string[]
}

export function AdvancedFilterPanel({
    filters,
    onFiltersChange,
    availableTags = [],
}: AdvancedFilterPanelProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [tagInput, setTagInput] = useState("")

    // Count active filters
    const activeFilterCount = [
        filters.tags?.length,
        filters.dateRange?.from || filters.dateRange?.to,
        filters.durationRange?.min !== undefined || filters.durationRange?.max !== undefined,
        filters.fileSizeRange?.min !== undefined || filters.fileSizeRange?.max !== undefined,
    ].filter(Boolean).length

    const handleClearAll = () => {
        onFiltersChange({})
    }

    const handleAddTag = (tag: string) => {
        if (!tag.trim()) return
        const currentTags = filters.tags || []
        if (!currentTags.includes(tag)) {
            onFiltersChange({
                ...filters,
                tags: [...currentTags, tag],
            })
        }
        setTagInput("")
    }

    const handleRemoveTag = (tag: string) => {
        onFiltersChange({
            ...filters,
            tags: (filters.tags || []).filter((t) => t !== tag),
        })
    }

    const handleDatePreset = (preset: "today" | "week" | "month") => {
        const now = new Date()
        const from = new Date()

        switch (preset) {
            case "today":
                from.setHours(0, 0, 0, 0)
                break
            case "week":
                from.setDate(now.getDate() - 7)
                break
            case "month":
                from.setMonth(now.getMonth() - 1)
                break
        }

        onFiltersChange({
            ...filters,
            dateRange: { from, to: now, preset },
        })
    }

    const handleDurationPreset = (preset: "short" | "medium" | "long") => {
        let min: number | undefined
        let max: number | undefined

        switch (preset) {
            case "short":
                max = 300 // 5 minutes
                break
            case "medium":
                min = 300
                max = 1200 // 20 minutes
                break
            case "long":
                min = 1200
                break
        }

        onFiltersChange({
            ...filters,
            durationRange: { min, max, preset },
        })
    }

    const handleFileSizePreset = (preset: "small" | "medium" | "large") => {
        let min: number | undefined
        let max: number | undefined

        switch (preset) {
            case "small":
                max = 100 // 100MB
                break
            case "medium":
                min = 100
                max = 1024 // 1GB
                break
            case "large":
                min = 1024
                break
        }

        onFiltersChange({
            ...filters,
            fileSizeRange: { min, max, preset },
        })
    }

    return (
        <div className="border rounded-lg bg-card">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <span className="font-medium">Advanced Filters</span>
                    {activeFilterCount > 0 && (
                        <Badge variant="secondary" className="ml-2">
                            {activeFilterCount}
                        </Badge>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {activeFilterCount > 0 && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation()
                                handleClearAll()
                            }}
                        >
                            Clear All
                        </Button>
                    )}
                    {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                    ) : (
                        <ChevronDown className="h-4 w-4" />
                    )}
                </div>
            </button>

            {/* Filter Content */}
            {isExpanded && (
                <div className="p-4 pt-0 space-y-6 border-t">
                    {/* Tags Filter */}
                    <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                            <TagIcon className="h-4 w-4" />
                            Filter by Tags
                        </Label>
                        <div className="flex gap-2">
                            <Input
                                placeholder="Add tag..."
                                value={tagInput}
                                onChange={(e) => setTagInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleAddTag(tagInput)
                                    }
                                }}
                                list="available-tags"
                            />
                            <datalist id="available-tags">
                                {availableTags.map((tag) => (
                                    <option key={tag} value={tag} />
                                ))}
                            </datalist>
                            <Button
                                type="button"
                                onClick={() => handleAddTag(tagInput)}
                            >
                                Add
                            </Button>
                        </div>
                        {filters.tags && filters.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-2">
                                {filters.tags.map((tag) => (
                                    <Badge
                                        key={tag}
                                        variant="secondary"
                                        className="cursor-pointer"
                                    >
                                        {tag}
                                        <X
                                            className="h-3 w-3 ml-1"
                                            onClick={() => handleRemoveTag(tag)}
                                        />
                                    </Badge>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Date Range Filter */}
                    <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                            <Calendar className="h-4 w-4" />
                            Filter by Date
                        </Label>
                        <div className="flex gap-2">
                            <Button
                                variant={filters.dateRange?.preset === "today" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDatePreset("today")}
                            >
                                Today
                            </Button>
                            <Button
                                variant={filters.dateRange?.preset === "week" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDatePreset("week")}
                            >
                                This Week
                            </Button>
                            <Button
                                variant={filters.dateRange?.preset === "month" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDatePreset("month")}
                            >
                                This Month
                            </Button>
                        </div>
                        {filters.dateRange && (
                            <div className="text-sm text-muted-foreground">
                                {filters.dateRange.from && (
                                    <span>From: {filters.dateRange.from.toLocaleDateString()}</span>
                                )}
                                {filters.dateRange.to && (
                                    <span className="ml-2">To: {filters.dateRange.to.toLocaleDateString()}</span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Duration Range Filter */}
                    <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                            <Clock className="h-4 w-4" />
                            Filter by Duration
                        </Label>
                        <div className="flex gap-2">
                            <Button
                                variant={filters.durationRange?.preset === "short" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDurationPreset("short")}
                            >
                                Short (&lt;5min)
                            </Button>
                            <Button
                                variant={filters.durationRange?.preset === "medium" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDurationPreset("medium")}
                            >
                                Medium (5-20min)
                            </Button>
                            <Button
                                variant={filters.durationRange?.preset === "long" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleDurationPreset("long")}
                            >
                                Long (&gt;20min)
                            </Button>
                        </div>
                    </div>

                    {/* File Size Range Filter */}
                    <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                            <HardDrive className="h-4 w-4" />
                            Filter by File Size
                        </Label>
                        <div className="flex gap-2">
                            <Button
                                variant={filters.fileSizeRange?.preset === "small" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleFileSizePreset("small")}
                            >
                                Small (&lt;100MB)
                            </Button>
                            <Button
                                variant={filters.fileSizeRange?.preset === "medium" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleFileSizePreset("medium")}
                            >
                                Medium (100MB-1GB)
                            </Button>
                            <Button
                                variant={filters.fileSizeRange?.preset === "large" ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleFileSizePreset("large")}
                            >
                                Large (&gt;1GB)
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
