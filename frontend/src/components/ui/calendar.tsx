"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { DayPicker } from "react-day-picker"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({
    className,
    classNames,
    showOutsideDays = true,
    ...props
}: CalendarProps) {
    return (
        <DayPicker
            showOutsideDays={showOutsideDays}
            className={cn("p-4", className)}
            classNames={{
                months: "flex flex-col sm:flex-row gap-4",
                month: "flex flex-col gap-4",
                month_caption: "flex justify-center pt-1 relative items-center h-10",
                caption_label: "text-sm font-semibold",
                nav: "flex items-center gap-1",
                button_previous: cn(
                    buttonVariants({ variant: "outline" }),
                    "absolute left-1 h-8 w-8 bg-transparent p-0 opacity-70 hover:opacity-100 rounded-md border"
                ),
                button_next: cn(
                    buttonVariants({ variant: "outline" }),
                    "absolute right-1 h-8 w-8 bg-transparent p-0 opacity-70 hover:opacity-100 rounded-md border"
                ),
                month_grid: "w-full border-collapse",
                weekdays: "flex",
                weekday: "text-muted-foreground rounded-md w-10 font-medium text-[0.8rem] h-10 flex items-center justify-center",
                week: "flex w-full mt-1",
                day: "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-accent [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected].day-range-end)]:rounded-r-md first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md",
                day_button: cn(
                    buttonVariants({ variant: "ghost" }),
                    "h-10 w-10 p-0 font-normal aria-selected:opacity-100 hover:bg-accent hover:text-accent-foreground rounded-md transition-colors"
                ),
                range_end: "day-range-end",
                selected: "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground rounded-md",
                today: "bg-accent text-accent-foreground rounded-md font-semibold",
                outside: "day-outside text-muted-foreground opacity-50 aria-selected:bg-accent/50 aria-selected:text-muted-foreground",
                disabled: "text-muted-foreground opacity-50 cursor-not-allowed",
                range_middle: "aria-selected:bg-accent aria-selected:text-accent-foreground",
                hidden: "invisible",
                ...classNames,
            }}
            components={{
                Chevron: ({ orientation }) =>
                    orientation === "left" ? (
                        <ChevronLeft className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    ),
            }}
            {...props}
        />
    )
}
Calendar.displayName = "Calendar"

export { Calendar }
