"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface CollapsibleContextValue {
    open: boolean
    onOpenChange: (open: boolean) => void
}

const CollapsibleContext = React.createContext<CollapsibleContextValue | undefined>(undefined)

interface CollapsibleProps {
    open?: boolean
    defaultOpen?: boolean
    onOpenChange?: (open: boolean) => void
    children: React.ReactNode
    className?: string
}

const Collapsible = React.forwardRef<HTMLDivElement, CollapsibleProps>(
    ({ open: controlledOpen, defaultOpen = false, onOpenChange, children, className, ...props }, ref) => {
        const [uncontrolledOpen, setUncontrolledOpen] = React.useState(defaultOpen)

        const isControlled = controlledOpen !== undefined
        const open = isControlled ? controlledOpen : uncontrolledOpen

        const handleOpenChange = React.useCallback((newOpen: boolean) => {
            if (!isControlled) {
                setUncontrolledOpen(newOpen)
            }
            onOpenChange?.(newOpen)
        }, [isControlled, onOpenChange])

        return (
            <CollapsibleContext.Provider value={{ open, onOpenChange: handleOpenChange }}>
                <div ref={ref} className={cn(className)} {...props}>
                    {children}
                </div>
            </CollapsibleContext.Provider>
        )
    }
)
Collapsible.displayName = "Collapsible"

const CollapsibleTrigger = React.forwardRef<
    HTMLButtonElement,
    React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }
>(({ className, children, asChild, onClick, ...props }, ref) => {
    const context = React.useContext(CollapsibleContext)

    if (!context) {
        throw new Error("CollapsibleTrigger must be used within a Collapsible")
    }

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        context.onOpenChange(!context.open)
        onClick?.(e)
    }

    if (asChild && React.isValidElement(children)) {
        return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, {
            onClick: () => context.onOpenChange(!context.open),
        })
    }

    return (
        <button
            ref={ref}
            type="button"
            className={cn(className)}
            onClick={handleClick}
            {...props}
        >
            {children}
        </button>
    )
})
CollapsibleTrigger.displayName = "CollapsibleTrigger"

const CollapsibleContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => {
    const context = React.useContext(CollapsibleContext)

    if (!context) {
        throw new Error("CollapsibleContent must be used within a Collapsible")
    }

    if (!context.open) {
        return null
    }

    return (
        <div
            ref={ref}
            className={cn(className)}
            {...props}
        >
            {children}
        </div>
    )
})
CollapsibleContent.displayName = "CollapsibleContent"

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
