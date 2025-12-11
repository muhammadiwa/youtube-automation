"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface TooltipContextValue {
    open: boolean
    setOpen: (open: boolean) => void
}

const TooltipContext = React.createContext<TooltipContextValue | undefined>(undefined)

export function TooltipProvider({ children }: { children: React.ReactNode }) {
    return <>{children}</>
}

export function Tooltip({ children }: { children: React.ReactNode }) {
    const [open, setOpen] = React.useState(false)

    return (
        <TooltipContext.Provider value={{ open, setOpen }}>
            <div className="relative inline-flex">
                {children}
            </div>
        </TooltipContext.Provider>
    )
}

export function TooltipTrigger({
    children,
    asChild
}: {
    children: React.ReactNode
    asChild?: boolean
}) {
    const context = React.useContext(TooltipContext)

    if (!context) {
        throw new Error("TooltipTrigger must be used within a Tooltip")
    }

    const handleMouseEnter = () => context.setOpen(true)
    const handleMouseLeave = () => context.setOpen(false)
    const handleFocus = () => context.setOpen(true)
    const handleBlur = () => context.setOpen(false)

    if (asChild && React.isValidElement(children)) {
        return React.cloneElement(children as React.ReactElement<{
            onMouseEnter?: () => void
            onMouseLeave?: () => void
            onFocus?: () => void
            onBlur?: () => void
        }>, {
            onMouseEnter: handleMouseEnter,
            onMouseLeave: handleMouseLeave,
            onFocus: handleFocus,
            onBlur: handleBlur,
        })
    }

    return (
        <span
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onFocus={handleFocus}
            onBlur={handleBlur}
        >
            {children}
        </span>
    )
}

export function TooltipContent({
    children,
    className,
    side = "top",
    sideOffset = 4,
}: {
    children: React.ReactNode
    className?: string
    side?: "top" | "bottom" | "left" | "right"
    sideOffset?: number
}) {
    const context = React.useContext(TooltipContext)

    if (!context) {
        throw new Error("TooltipContent must be used within a Tooltip")
    }

    if (!context.open) {
        return null
    }

    const positionClasses = {
        top: `bottom-full left-1/2 -translate-x-1/2 mb-${sideOffset}`,
        bottom: `top-full left-1/2 -translate-x-1/2 mt-${sideOffset}`,
        left: `right-full top-1/2 -translate-y-1/2 mr-${sideOffset}`,
        right: `left-full top-1/2 -translate-y-1/2 ml-${sideOffset}`,
    }

    return (
        <div
            className={cn(
                "absolute z-50 px-3 py-1.5 text-sm rounded-md shadow-md",
                "bg-popover text-popover-foreground border",
                "animate-in fade-in-0 zoom-in-95",
                positionClasses[side],
                className
            )}
            style={{ marginBottom: side === "top" ? `${sideOffset}px` : undefined }}
        >
            {children}
        </div>
    )
}
