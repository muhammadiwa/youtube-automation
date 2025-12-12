"use client"

import { useState } from "react"
import { Calendar, ChevronDown, ArrowLeftRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { format, subDays, subMonths, startOfDay, endOfDay } from "date-fns"

export type DatePreset = "7d" | "30d" | "90d" | "custom"

export interface DateRange {
    startDate: Date
    endDate: Date
    preset: DatePreset
}

interface DateRangeFilterProps {
    value: DateRange
    onChange: (range: DateRange) => void
    showComparison?: boolean
    comparisonEnabled?: boolean
    onComparisonChange?: (enabled: boolean) => void
}

const presets: { label: string; value: DatePreset; getDates: () => { start: Date; end: Date } }[] = [
    {
        label: "Last 7 days",
        value: "7d",
        getDates: () => ({
            start: startOfDay(subDays(new Date(), 7)),
            end: endOfDay(new Date()),
        }),
    },
    {
        label: "Last 30 days",
        value: "30d",
        getDates: () => ({
            start: startOfDay(subDays(new Date(), 30)),
            end: endOfDay(new Date()),
        }),
    },
    {
        label: "Last 90 days",
        value: "90d",
        getDates: () => ({
            start: startOfDay(subDays(new Date(), 90)),
            end: endOfDay(new Date()),
        }),
    },
]

export function DateRangeFilter({
    value,
    onChange,
    showComparison = true,
    comparisonEnabled = false,
    onComparisonChange,
}: DateRangeFilterProps) {
    const [isCustomOpen, setIsCustomOpen] = useState(false)
    const [customStart, setCustomStart] = useState(format(value.startDate, "yyyy-MM-dd"))
    const [customEnd, setCustomEnd] = useState(format(value.endDate, "yyyy-MM-dd"))

    const handlePresetSelect = (preset: DatePreset) => {
        if (preset === "custom") {
            setIsCustomOpen(true)
            return
        }

        const presetConfig = presets.find((p) => p.value === preset)
        if (presetConfig) {
            const { start, end } = presetConfig.getDates()
            onChange({
                startDate: start,
                endDate: end,
                preset,
            })
        }
    }

    const handleCustomApply = () => {
        const start = new Date(customStart)
        const end = new Date(customEnd)

        if (start <= end) {
            onChange({
                startDate: startOfDay(start),
                endDate: endOfDay(end),
                preset: "custom",
            })
            setIsCustomOpen(false)
        }
    }

    const getDisplayLabel = () => {
        if (value.preset === "custom") {
            return `${format(value.startDate, "MMM d, yyyy")} - ${format(value.endDate, "MMM d, yyyy")}`
        }
        const preset = presets.find((p) => p.value === value.preset)
        return preset?.label ?? "Select date range"
    }

    return (
        <div className="flex items-center gap-4">
            <DropdownMenu open={isCustomOpen} onOpenChange={setIsCustomOpen}>
                <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="gap-2">
                        <Calendar className="h-4 w-4" />
                        <span>{getDisplayLabel()}</span>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-[280px]">
                    {presets.map((preset) => (
                        <DropdownMenuItem
                            key={preset.value}
                            onClick={() => handlePresetSelect(preset.value)}
                            className={cn(value.preset === preset.value && "bg-muted")}
                        >
                            {preset.label}
                        </DropdownMenuItem>
                    ))}
                    <DropdownMenuSeparator />
                    <div className="p-3 space-y-3">
                        <p className="text-sm font-medium">Custom Range</p>
                        <div className="grid gap-2">
                            <div className="grid gap-1">
                                <Label htmlFor="start-date" className="text-xs">Start Date</Label>
                                <Input
                                    id="start-date"
                                    type="date"
                                    value={customStart}
                                    onChange={(e) => setCustomStart(e.target.value)}
                                    className="h-8"
                                />
                            </div>
                            <div className="grid gap-1">
                                <Label htmlFor="end-date" className="text-xs">End Date</Label>
                                <Input
                                    id="end-date"
                                    type="date"
                                    value={customEnd}
                                    onChange={(e) => setCustomEnd(e.target.value)}
                                    className="h-8"
                                />
                            </div>
                        </div>
                        <Button size="sm" className="w-full" onClick={handleCustomApply}>
                            Apply
                        </Button>
                    </div>
                </DropdownMenuContent>
            </DropdownMenu>

            {showComparison && onComparisonChange && (
                <div className="flex items-center gap-2">
                    <Switch
                        id="comparison"
                        checked={comparisonEnabled}
                        onCheckedChange={onComparisonChange}
                    />
                    <Label htmlFor="comparison" className="text-sm text-muted-foreground flex items-center gap-1 cursor-pointer">
                        <ArrowLeftRight className="h-3 w-3" />
                        Compare
                    </Label>
                </div>
            )}
        </div>
    )
}

// Helper to get default date range
export function getDefaultDateRange(): DateRange {
    return {
        startDate: startOfDay(subDays(new Date(), 30)),
        endDate: endOfDay(new Date()),
        preset: "30d",
    }
}
