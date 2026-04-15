"use client"

import { useState, useEffect } from "react"
import { X, AlertCircle, CheckCircle2, AlertTriangle, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface Announcement {
    id: string
    title: string
    content: string
    announcement_type: "info" | "warning" | "success" | "error"
    is_dismissible: boolean
}

const typeConfig = {
    info: {
        bg: "bg-blue-500/10 border-blue-500/20",
        text: "text-blue-700 dark:text-blue-300",
        icon: AlertCircle,
    },
    warning: {
        bg: "bg-amber-500/10 border-amber-500/20",
        text: "text-amber-700 dark:text-amber-300",
        icon: AlertTriangle,
    },
    success: {
        bg: "bg-emerald-500/10 border-emerald-500/20",
        text: "text-emerald-700 dark:text-emerald-300",
        icon: CheckCircle2,
    },
    error: {
        bg: "bg-red-500/10 border-red-500/20",
        text: "text-red-700 dark:text-red-300",
        icon: XCircle,
    },
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export function AnnouncementBanner() {
    const [announcements, setAnnouncements] = useState<Announcement[]>([])
    const [dismissedIds, setDismissedIds] = useState<string[]>([])

    useEffect(() => {
        // Load dismissed announcements from localStorage
        const stored = localStorage.getItem("dismissed_announcements")
        if (stored) {
            try {
                setDismissedIds(JSON.parse(stored))
            } catch {
                // Ignore parse errors
            }
        }

        // Fetch active announcements
        const fetchAnnouncements = async () => {
            try {
                const token = localStorage.getItem("access_token")
                const response = await fetch(`${API_BASE}/announcements/active`, {
                    headers: token ? { Authorization: `Bearer ${token}` } : {},
                })
                if (response.ok) {
                    const data = await response.json()
                    setAnnouncements(data.items || data)
                }
            } catch {
                // Silently fail - announcements are not critical
            }
        }

        fetchAnnouncements()
    }, [])

    const handleDismiss = (id: string) => {
        const newDismissed = [...dismissedIds, id]
        setDismissedIds(newDismissed)
        localStorage.setItem("dismissed_announcements", JSON.stringify(newDismissed))
    }

    const visibleAnnouncements = announcements.filter(a => !dismissedIds.includes(a.id))

    if (visibleAnnouncements.length === 0) return null

    return (
        <div className="space-y-2 mb-4">
            {visibleAnnouncements.map((announcement) => {
                const config = typeConfig[announcement.announcement_type]
                const Icon = config.icon

                return (
                    <div
                        key={announcement.id}
                        className={cn(
                            "flex items-start gap-3 p-3 rounded-lg border",
                            config.bg
                        )}
                    >
                        <Icon className={cn("h-5 w-5 mt-0.5 shrink-0", config.text)} />
                        <div className="flex-1 min-w-0">
                            <p className={cn("font-medium text-sm", config.text)}>
                                {announcement.title}
                            </p>
                            <p className={cn("text-sm mt-0.5 opacity-90", config.text)}>
                                {announcement.content}
                            </p>
                        </div>
                        {announcement.is_dismissible && (
                            <Button
                                variant="ghost"
                                size="icon"
                                className={cn("h-6 w-6 shrink-0", config.text)}
                                onClick={() => handleDismiss(announcement.id)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        )}
                    </div>
                )
            })}
        </div>
    )
}
