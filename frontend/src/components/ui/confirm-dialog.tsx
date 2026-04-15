"use client"

import { useState } from "react"
import { AlertTriangle, Trash2, Loader2 } from "lucide-react"
import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogHeader,
    AlertDialogFooter,
    AlertDialogTitle,
    AlertDialogDescription,
    AlertDialogAction,
    AlertDialogCancel,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

export interface ConfirmDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    title: string
    description: string
    confirmText?: string
    cancelText?: string
    variant?: "default" | "destructive"
    icon?: React.ReactNode
    onConfirm: () => void | Promise<void>
    loading?: boolean
}

export function ConfirmDialog({
    open,
    onOpenChange,
    title,
    description,
    confirmText = "Confirm",
    cancelText = "Cancel",
    variant = "default",
    icon,
    onConfirm,
    loading = false,
}: ConfirmDialogProps) {
    const [isLoading, setIsLoading] = useState(false)

    const handleConfirm = async () => {
        setIsLoading(true)
        try {
            await onConfirm()
            onOpenChange(false)
        } finally {
            setIsLoading(false)
        }
    }

    const isProcessing = loading || isLoading

    return (
        <AlertDialog open={open} onOpenChange={onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <div className="flex items-start gap-4">
                        {icon || (variant === "destructive" ? (
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-destructive/10">
                                <AlertTriangle className="h-5 w-5 text-destructive" />
                            </div>
                        ) : null)}
                        <div className="space-y-2">
                            <AlertDialogTitle>{title}</AlertDialogTitle>
                            <AlertDialogDescription>{description}</AlertDialogDescription>
                        </div>
                    </div>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={isProcessing}>
                        {cancelText}
                    </AlertDialogCancel>
                    <Button
                        variant={variant}
                        onClick={handleConfirm}
                        disabled={isProcessing}
                    >
                        {isProcessing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {confirmText}
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}

// Hook for easier usage
export function useConfirmDialog() {
    const [state, setState] = useState<{
        open: boolean
        title: string
        description: string
        confirmText?: string
        variant?: "default" | "destructive"
        onConfirm: () => void | Promise<void>
    }>({
        open: false,
        title: "",
        description: "",
        onConfirm: () => { },
    })

    const confirm = (options: {
        title: string
        description: string
        confirmText?: string
        variant?: "default" | "destructive"
        onConfirm: () => void | Promise<void>
    }) => {
        setState({ ...options, open: true })
    }

    const close = () => {
        setState((prev) => ({ ...prev, open: false }))
    }

    return {
        confirm,
        close,
        dialogProps: {
            open: state.open,
            onOpenChange: (open: boolean) => setState((prev) => ({ ...prev, open })),
            title: state.title,
            description: state.description,
            confirmText: state.confirmText,
            variant: state.variant,
            onConfirm: state.onConfirm,
        },
    }
}

export default ConfirmDialog
