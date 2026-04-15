"use client"

import * as React from "react"
import { format, startOfDay, endOfDay } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface DatePickerProps {
    value?: Date
    onChange?: (date: Date | undefined) => void
    placeholder?: string
    disabled?: boolean
    minDate?: Date
    maxDate?: Date
    className?: string
    formatStr?: string
}

export function DatePicker({
    value,
    onChange,
    placeholder = "Pick a date",
    disabled = false,
    minDate,
    maxDate,
    className,
    formatStr = "PPP",
}: DatePickerProps) {
    const [open, setOpen] = React.useState(false)

    const handleSelect = (date: Date | undefined) => {
        onChange?.(date)
        setOpen(false)
    }

    // Use startOfDay for minDate and endOfDay for maxDate to include the full day
    const isDateDisabled = (date: Date) => {
        const dateStart = startOfDay(date)
        if (minDate && dateStart < startOfDay(minDate)) return true
        if (maxDate && dateStart > endOfDay(maxDate)) return true
        return false
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    className={cn(
                        "w-full justify-start text-left font-normal h-10",
                        !value && "text-muted-foreground",
                        className
                    )}
                    disabled={disabled}
                >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {value ? format(value, formatStr) : placeholder}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start" sideOffset={4}>
                <Calendar
                    mode="single"
                    selected={value}
                    onSelect={handleSelect}
                    disabled={isDateDisabled}
                    autoFocus
                />
            </PopoverContent>
        </Popover>
    )
}

interface DateRangePickerProps {
    startDate?: Date
    endDate?: Date
    onStartDateChange?: (date: Date | undefined) => void
    onEndDateChange?: (date: Date | undefined) => void
    startPlaceholder?: string
    endPlaceholder?: string
    disabled?: boolean
    minDate?: Date
    maxDate?: Date
    className?: string
}

export function DateRangePicker({
    startDate,
    endDate,
    onStartDateChange,
    onEndDateChange,
    startPlaceholder = "Start date",
    endPlaceholder = "End date",
    disabled = false,
    minDate,
    maxDate,
    className,
}: DateRangePickerProps) {
    return (
        <div className={cn("flex items-center gap-2", className)}>
            <DatePicker
                value={startDate}
                onChange={onStartDateChange}
                placeholder={startPlaceholder}
                disabled={disabled}
                minDate={minDate}
                maxDate={endDate || maxDate}
                className="flex-1"
            />
            <span className="text-muted-foreground">to</span>
            <DatePicker
                value={endDate}
                onChange={onEndDateChange}
                placeholder={endPlaceholder}
                disabled={disabled}
                minDate={startDate || minDate}
                maxDate={maxDate}
                className="flex-1"
            />
        </div>
    )
}

export default DatePicker
