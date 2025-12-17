"use client"

import { useState } from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
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
    minDate = new Date(),
    disabled = false,
}: SchedulePickerProps) {
    const [isScheduled, setIsScheduled] = useState(!!value)
    const [selectedDate, setSelectedDate] = useState<Date | undefined>(value || undefined)
    const [selectedHour, setSelectedHour] = useState(value ? format(value, "HH") : "12")
    const [selectedMinute, setSelectedMinute] = useState(value ? format(value, "mm") : "00")

    const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, "0"))
    const minutes = ["00", "15", "30", "45"]

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
    }

    const handleTimeChange = (hour: string, minute: string) => {
        setSelectedHour(hour)
        setSelectedMinute(minute)
        if (selectedDate && isScheduled) {
            updateDateTime(selectedDate, hour, minute)
        }
    }

    const updateDateTime = (date: Date, hour: string, minute: string) => {
        const newDate = new Date(date)
        newDate.setHours(parseInt(hour), parseInt(minute), 0, 0)
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
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    variant="outline"
                                    className={cn(
                                        "w-full justify-start text-left font-normal",
                                        !selectedDate && "text-muted-foreground"
                                    )}
                                    disabled={disabled}
                                >
                                    <CalendarIcon className="mr-2 h-4 w-4" />
                                    {selectedDate ? format(selectedDate, "PPP") : "Pick a date"}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                    mode="single"
                                    selected={selectedDate}
                                    onSelect={handleDateSelect}
                                    disabled={(date) => date < minDate}
                                    initialFocus
                                />
                            </PopoverContent>
                        </Popover>
                    </div>

                    {/* Time Picker */}
                    <div className="space-y-2">
                        <Label>Time</Label>
                        <div className="flex gap-2">
                            <Select
                                value={selectedHour}
                                onValueChange={(h) => handleTimeChange(h, selectedMinute)}
                                disabled={disabled}
                            >
                                <SelectTrigger className="w-full">
                                    <Clock className="mr-2 h-4 w-4" />
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {hours.map((hour) => (
                                        <SelectItem key={hour} value={hour}>
                                            {hour}:00
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <Select
                                value={selectedMinute}
                                onValueChange={(m) => handleTimeChange(selectedHour, m)}
                                disabled={disabled}
                            >
                                <SelectTrigger className="w-20">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {minutes.map((minute) => (
                                        <SelectItem key={minute} value={minute}>
                                            :{minute}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </div>
            )}

            {isScheduled && selectedDate && (
                <p className="text-sm text-muted-foreground">
                    Video will be published on{" "}
                    <span className="font-medium text-foreground">
                        {format(
                            new Date(
                                selectedDate.getFullYear(),
                                selectedDate.getMonth(),
                                selectedDate.getDate(),
                                parseInt(selectedHour),
                                parseInt(selectedMinute)
                            ),
                            "PPP 'at' p"
                        )}
                    </span>
                </p>
            )}
        </div>
    )
}

export default SchedulePicker
