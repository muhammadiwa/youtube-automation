/**
 * Multi-Date Picker Component
 * 
 * Calendar component that allows selecting multiple dates.
 * Used for scheduling streams on specific dates.
 */

"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface MultiDatePickerProps {
    selectedDates: Date[]
    onDatesChange: (dates: Date[]) => void
    minDate?: Date
    maxDate?: Date
    disabled?: boolean
    className?: string
}

const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
const MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

export function MultiDatePicker({
    selectedDates,
    onDatesChange,
    minDate,
    maxDate,
    disabled = false,
    className,
}: MultiDatePickerProps) {
    const [currentMonth, setCurrentMonth] = React.useState(() => {
        const now = new Date()
        return new Date(now.getFullYear(), now.getMonth(), 1)
    })

    // Get days in month
    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear()
        const month = date.getMonth()
        const firstDay = new Date(year, month, 1)
        const lastDay = new Date(year, month + 1, 0)
        const daysInMonth = lastDay.getDate()
        const startingDay = firstDay.getDay()

        const days: (Date | null)[] = []

        // Add empty slots for days before the first day of month
        for (let i = 0; i < startingDay; i++) {
            days.push(null)
        }

        // Add all days of the month
        for (let i = 1; i <= daysInMonth; i++) {
            days.push(new Date(year, month, i))
        }

        return days
    }

    const days = getDaysInMonth(currentMonth)

    // Check if a date is selected
    const isSelected = (date: Date) => {
        return selectedDates.some(d =>
            d.getFullYear() === date.getFullYear() &&
            d.getMonth() === date.getMonth() &&
            d.getDate() === date.getDate()
        )
    }

    // Check if date is disabled
    const isDisabledDate = (date: Date) => {
        if (minDate && date < new Date(minDate.setHours(0, 0, 0, 0))) return true
        if (maxDate && date > new Date(maxDate.setHours(23, 59, 59, 999))) return true
        return false
    }

    // Check if date is today
    const isToday = (date: Date) => {
        const today = new Date()
        return date.getFullYear() === today.getFullYear() &&
            date.getMonth() === today.getMonth() &&
            date.getDate() === today.getDate()
    }

    // Check if date is in the past
    const isPast = (date: Date) => {
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        return date < today
    }

    // Toggle date selection
    const toggleDate = (date: Date) => {
        if (disabled || isDisabledDate(date) || isPast(date)) return

        if (isSelected(date)) {
            onDatesChange(selectedDates.filter(d =>
                !(d.getFullYear() === date.getFullYear() &&
                    d.getMonth() === date.getMonth() &&
                    d.getDate() === date.getDate())
            ))
        } else {
            onDatesChange([...selectedDates, date].sort((a, b) => a.getTime() - b.getTime()))
        }
    }

    // Remove a specific date
    const removeDate = (date: Date) => {
        onDatesChange(selectedDates.filter(d =>
            !(d.getFullYear() === date.getFullYear() &&
                d.getMonth() === date.getMonth() &&
                d.getDate() === date.getDate())
        ))
    }

    // Navigate months
    const prevMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
    }

    const nextMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
    }

    // Format date for display
    const formatDate = (date: Date) => {
        return `${date.getDate()} ${MONTHS[date.getMonth()].slice(0, 3)}`
    }

    return (
        <div className={cn("space-y-3", className)}>
            {/* Calendar */}
            <div className="rounded-lg border p-3">
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={prevMonth}
                        disabled={disabled}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="font-medium text-sm">
                        {MONTHS[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                    </span>
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={nextMonth}
                        disabled={disabled}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>

                {/* Day headers */}
                <div className="grid grid-cols-7 gap-1 mb-1">
                    {DAYS.map(day => (
                        <div
                            key={day}
                            className="text-center text-xs font-medium text-muted-foreground py-1"
                        >
                            {day}
                        </div>
                    ))}
                </div>

                {/* Days grid */}
                <div className="grid grid-cols-7 gap-1">
                    {days.map((date, index) => (
                        <div key={index} className="aspect-square">
                            {date ? (
                                <button
                                    type="button"
                                    onClick={() => toggleDate(date)}
                                    disabled={disabled || isDisabledDate(date) || isPast(date)}
                                    className={cn(
                                        "w-full h-full rounded-md text-sm transition-colors",
                                        "hover:bg-accent hover:text-accent-foreground",
                                        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
                                        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent",
                                        isSelected(date) && "bg-primary text-primary-foreground hover:bg-primary/90",
                                        isToday(date) && !isSelected(date) && "border border-primary",
                                        isPast(date) && "text-muted-foreground/50"
                                    )}
                                >
                                    {date.getDate()}
                                </button>
                            ) : (
                                <div />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected dates display */}
            {selectedDates.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                            {selectedDates.length} date{selectedDates.length > 1 ? "s" : ""} selected
                        </span>
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => onDatesChange([])}
                            disabled={disabled}
                        >
                            Clear all
                        </Button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {selectedDates.map((date, index) => (
                            <Badge
                                key={index}
                                variant="secondary"
                                className="text-xs pr-1"
                            >
                                {formatDate(date)}
                                <button
                                    type="button"
                                    onClick={() => removeDate(date)}
                                    disabled={disabled}
                                    className="ml-1 hover:text-destructive"
                                >
                                    <X className="h-3 w-3" />
                                </button>
                            </Badge>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
