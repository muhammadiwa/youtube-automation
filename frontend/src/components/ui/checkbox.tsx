"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

export interface CheckboxProps {
    checked?: boolean
    onCheckedChange?: (checked: boolean) => void
    disabled?: boolean
    id?: string
    className?: string
    name?: string
}

const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
    ({ className, checked = false, onCheckedChange, disabled, id, name }, ref) => {
        return (
            <button
                ref={ref}
                type="button"
                role="checkbox"
                aria-checked={checked}
                disabled={disabled}
                id={id}
                data-state={checked ? "checked" : "unchecked"}
                onClick={() => onCheckedChange?.(!checked)}
                className={cn(
                    "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    "data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
                    "flex items-center justify-center transition-colors",
                    className
                )}
            >
                {checked && <Check className="h-3 w-3" />}
                <input type="hidden" name={name} value={checked ? "true" : "false"} />
            </button>
        )
    }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
