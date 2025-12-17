"use client"

import { useState } from "react"
import { format, startOfDay } from "date-fns"
import { Calendar as CalendarIcon, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

interface SchedulePickerProps {
    value?: Date | null
    onChange: (date: Date | null) => void
    minDate?: Date
    disabled?: boolean
}

export function SchedulePicker({
    value,
    onChange,
    minDate,
    disabled = false,
}: SchedulePickerProps) {
    const [isScheduled, setIsScheduled] = useState(!!value)
    const [selectedDate, setSelectedDate] = useState<Date | undefined>(value || undefined)
    const [selectedHour, setSelectedHour] = useState(value ? format(value, "HH") : "12")
    const [selectedMinute, setSelectedMinute] = useState(value ? format(value, "mm") : "00")
    const [calendarOpen, setCalendarOpen] = useState(false)

    // Generate hours 00-23
    const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, "0"))

    // Use start of today as minimum date (allows selecting today)
    const effectiveMinDate = minDate ? startOfDay(minDate) : startOfDay(new Date())

    const handleScheduleToggle = (checked: boolean) => {
        setIsScheduled(checked)
        if (!checked) {
            onChange(null)
        } else if (selectedDate) {
            updateDateTime(selectedDate, selectedHour, selectedMinute)
        }
    }

    const handleDateSelect = (date: Date | undefined) => {
        setSelectedDate(date)
        if (date && isScheduled) {
            updateDateTime(date, selectedHour, selectedMinute)
        }
        setCalendarOpen(false)
    }

    const handleHourChange = (hour: string) => {
        setSelectedHour(hour)
        if (selectedDate && isScheduled) {
            updateDateTime(selectedDate, hour, selectedMinute)
        }
    }

    const handleMinuteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value

        // Allow empty or partial input while typing
        if (value === "") {
            setSelectedMinute("")
            return
        }

        // Only allow numbers
        if (!/^\d*$/.test(value)) return

        // Limit to 2 digits
        if (value.length > 2) return

        setSelectedMinute(value)
    }

    const handleMinuteBlur = () => {
        // On blur, validate and format the minute
        let minute = parseInt(selectedMinute) || 0
        if (minute > 59) minute = 59
        if (minute < 0) minute = 0

        const paddedMinute = minute.toString().padStart(2, "0")
        setSelectedMinute(paddedMinute)

        if (selectedDate && isScheduled) {
            updateDateTime(selectedDate, selectedHour, paddedMinute)
        }
    }

    const updateDateTime = (date: Date, hour: string, minute: string) => {
        const newDate = new Date(date)
        const h = parseInt(hour) || 0
        const m = parseInt(minute) || 0
        newDate.setHours(h, m, 0, 0)
        onChange(newDate)
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                    <Label>Schedule for later</Label>
                    <p className="text-sm text-muted-foreground">
                        Set a specific date and time to publish
                    </p>
                </div>
                <Switch
                    checked={isScheduled}
                    onCheckedChange={handleScheduleToggle}
                    disabled={disabled}
                />
            </div>

            {isScheduled && (
                <div className="grid gap-4 sm:grid-cols-2">
                    {/* Date Picker */}
                    <div className="space-y-2">
                        <Label>Date</Label>
                        <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
                            <PopoverTrigger asChild>
                                <Button
                                    variant="outline"
                                    className={cn(
                                        "w-full justify-start text-left font-normal h-10",
                                        !selectedDate && "text-muted-foreground"
                                    )}
                                    disabled={disabled}
                                >
                                    <CalendarIcon className="mr-2 h-4 w-4" />
                                    {selectedDate ? format(selectedDate, "PPP") : "Pick a date"}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start" sideOffset={4}>
                                <Calendar
                                    mode="single"
                                    selected={selectedDate}
                                    onSelect={handleDateSelect}
                                    disabled={(date) => date < effectiveMinDate}
                                    autoFocus
                                />
                            </PopoverContent>
                        </Popover>
                    </div>

                    {/* Time Picker - Hour dropdown + Minute input */}
                    <div className="space-y-2">
                        <Label>Time</Label>
                        <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4 text-muted-foreground mr-1" />
                            {/* Hour Select */}
                            <Select
                                value={selectedHour}
                                onValueChange={handleHourChange}
                                disabled={disabled}
                            >
                                <SelectTrigger className="w-[70px] h-10">
                                    <SelectValue placeholder="HH" />
                                </SelectTrigger>
                                <SelectContent className="max-h-[200px]">
                                    {hours.map((hour) => (
                                        <SelectItem key={hour} value={hour}>
                                            {hour}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            <span className="text-lg font-medium px-1">:</span>

                            {/* Minute Input */}
                            <Input
                                type="text"
                                inputMode="numeric"
                                value={selectedMinute}
                                onChange={handleMinuteChange}
                                onBlur={handleMinuteBlur}
                                disabled={disabled}
                                className="w-[70px] h-10 text-center"
                                placeholder="00"
                                maxLength={2}
                            />
                        </div>
                    </div>
                </div>
            )}

            {isScheduled && selectedDate && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <CalendarIcon className="h-4 w-4 text-primary shrink-0" />
                    <p className="text-sm">
                        Video will be published on{" "}
                        <span className="font-semibold text-primary">
                            {format(
                                new Date(
                                    selectedDate.getFullYear(),
                                    selectedDate.getMonth(),
                                    selectedDate.getDate(),
                                    parseInt(selectedHour) || 0,
                                    parseInt(selectedMinute) || 0
                                ),
                                "EEEE, MMMM d, yyyy 'at' h:mm a"
                            )}
                        </span>
                    </p>
                </div>
            )}
        </div>
    )
}

export default SchedulePicker
