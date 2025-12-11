"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

export type ToastType = "success" | "error" | "warning" | "info"

export interface Toast {
    id: string
    type: ToastType
    title: string
    description?: string
    duration?: number
}

interface ToastContextValue {
    toasts: Toast[]
    addToast: (toast: Omit<Toast, "id">) => void
    removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined)

export function useToast() {
    const context = React.useContext(ToastContext)
    if (!context) {
        throw new Error("useToast must be used within a ToastProvider")
    }
    return context
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = React.useState<Toast[]>([])

    const addToast = React.useCallback((toast: Omit<Toast, "id">) => {
        const id = Math.random().toString(36).substring(2, 9)
        const newToast = { ...toast, id }
        setToasts((prev) => [...prev, newToast])

        // Auto-remove after duration
        const duration = toast.duration ?? 5000
        if (duration > 0) {
            setTimeout(() => {
                setToasts((prev) => prev.filter((t) => t.id !== id))
            }, duration)
        }
    }, [])

    const removeToast = React.useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    )
}

function ToastContainer({
    toasts,
    onRemove,
}: {
    toasts: Toast[]
    onRemove: (id: string) => void
}) {
    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
            <AnimatePresence mode="popLayout">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
                ))}
            </AnimatePresence>
        </div>
    )
}

function ToastItem({
    toast,
    onRemove,
}: {
    toast: Toast
    onRemove: (id: string) => void
}) {
    const icons = {
        success: <CheckCircle className="h-5 w-5 text-green-500" />,
        error: <XCircle className="h-5 w-5 text-red-500" />,
        warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
        info: <Info className="h-5 w-5 text-blue-500" />,
    }

    const bgColors = {
        success: "bg-green-500/10 border-green-500/20",
        error: "bg-red-500/10 border-red-500/20",
        warning: "bg-yellow-500/10 border-yellow-500/20",
        info: "bg-blue-500/10 border-blue-500/20",
    }

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
            className={cn(
                "flex items-start gap-3 p-4 rounded-lg border shadow-lg bg-background",
                bgColors[toast.type]
            )}
        >
            {icons[toast.type]}
            <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{toast.title}</p>
                {toast.description && (
                    <p className="text-sm text-muted-foreground mt-1">{toast.description}</p>
                )}
            </div>
            <button
                onClick={() => onRemove(toast.id)}
                className="p-1 rounded-full hover:bg-muted transition-colors"
            >
                <X className="h-4 w-4 text-muted-foreground" />
            </button>
        </motion.div>
    )
}

// Convenience functions for common toast types
export function toast(_options: Omit<Toast, "id">) {
    // This is a placeholder - actual implementation requires context
    console.warn("Toast called outside of ToastProvider context")
}
