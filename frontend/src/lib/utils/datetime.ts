/**
 * Datetime utilities for consistent timezone handling.
 * 
 * All datetime values from the backend are in UTC.
 * These utilities convert UTC to user's local timezone for display.
 * 
 * Usage:
 *   import { formatDateTime, formatDate, formatTime, getRelativeTime } from '@/lib/utils/datetime'
 *   
 *   // Display full datetime in user's timezone
 *   formatDateTime(stream.scheduled_start_at)  // "Jan 4, 2026, 7:30 PM"
 *   
 *   // Display relative time
 *   getRelativeTime(stream.scheduled_start_at)  // "in 2h 30m"
 */

/**
 * Parse ISO string to Date object.
 * Handles both ISO strings with and without timezone info.
 */
export function parseDateTime(isoString: string | null | undefined): Date | null {
    if (!isoString) return null

    try {
        const date = new Date(isoString)
        // Check if valid date
        if (isNaN(date.getTime())) return null
        return date
    } catch {
        return null
    }
}

/**
 * Format datetime in user's local timezone.
 * @param isoString - ISO datetime string from backend (UTC)
 * @param options - Intl.DateTimeFormat options
 * @returns Formatted datetime string in user's locale
 * 
 * @example
 * formatDateTime("2026-01-04T12:30:00Z")  // "Jan 4, 2026, 7:30 PM" (for UTC+7)
 */
export function formatDateTime(
    isoString: string | null | undefined,
    options?: Intl.DateTimeFormatOptions
): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    const defaultOptions: Intl.DateTimeFormatOptions = {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    }

    return date.toLocaleString(undefined, options || defaultOptions)
}

/**
 * Format date only in user's local timezone.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns Formatted date string
 * 
 * @example
 * formatDate("2026-01-04T12:30:00Z")  // "Jan 4, 2026"
 */
export function formatDate(isoString: string | null | undefined): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    return date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}

/**
 * Format time only in user's local timezone.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns Formatted time string
 * 
 * @example
 * formatTime("2026-01-04T12:30:00Z")  // "7:30 PM" (for UTC+7)
 */
export function formatTime(isoString: string | null | undefined): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    return date.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    })
}

/**
 * Format date with smart labels (Today, Tomorrow, etc.)
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns "Today", "Tomorrow", or formatted date
 * 
 * @example
 * formatSmartDate("2026-01-04T12:30:00Z")  // "Today" or "Tomorrow" or "Mon, Jan 5"
 */
export function formatSmartDate(isoString: string | null | undefined): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (date.toDateString() === today.toDateString()) {
        return "Today"
    }
    if (date.toDateString() === tomorrow.toDateString()) {
        return "Tomorrow"
    }

    return date.toLocaleDateString(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
    })
}

/**
 * Get relative time from now.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns Relative time string like "in 2h 30m" or "5m ago"
 * 
 * @example
 * getRelativeTime("2026-01-04T14:30:00Z")  // "in 2h 30m"
 * getRelativeTime("2026-01-04T10:00:00Z")  // "2h 30m ago"
 */
export function getRelativeTime(isoString: string | null | undefined): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffSeconds = Math.abs(Math.floor(diffMs / 1000))
    const isFuture = diffMs > 0

    const days = Math.floor(diffSeconds / 86400)
    const hours = Math.floor((diffSeconds % 86400) / 3600)
    const minutes = Math.floor((diffSeconds % 3600) / 60)

    let result = ""

    if (days > 0) {
        result = `${days}d ${hours}h`
    } else if (hours > 0) {
        result = `${hours}h ${minutes}m`
    } else if (minutes > 0) {
        result = `${minutes}m`
    } else {
        return isFuture ? "starting now" : "just now"
    }

    return isFuture ? `in ${result}` : `${result} ago`
}

/**
 * Get countdown from seconds.
 * @param seconds - Number of seconds until event
 * @returns Formatted countdown string
 * 
 * @example
 * formatCountdown(7200)  // "in 2h 0m"
 * formatCountdown(90)    // "in 1m"
 * formatCountdown(0)     // "Starting now"
 */
export function formatCountdown(seconds: number): string {
    if (seconds <= 0) return "Starting now"

    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (days > 0) {
        return `in ${days}d ${hours}h`
    }
    if (hours > 0) {
        return `in ${hours}h ${minutes}m`
    }
    return `in ${minutes}m`
}

/**
 * Format duration in HH:MM:SS or MM:SS format.
 * @param seconds - Duration in seconds
 * @returns Formatted duration string
 * 
 * @example
 * formatDuration(3661)  // "1:01:01"
 * formatDuration(125)   // "2:05"
 */
export function formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }
    return `${minutes}:${secs.toString().padStart(2, "0")}`
}

/**
 * Format time ago for alerts and notifications.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns Human-readable time ago string
 * 
 * @example
 * formatTimeAgo("2026-01-04T12:00:00Z")  // "just now", "5m ago", "2h ago", "3d ago"
 */
export function formatTimeAgo(isoString: string | null | undefined): string {
    const date = parseDateTime(isoString)
    if (!date) return "-"

    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return "just now"
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
}

/**
 * Check if datetime is within specified hours from now.
 * @param isoString - ISO datetime string from backend (UTC)
 * @param hours - Number of hours threshold
 * @returns True if datetime is within the specified hours
 * 
 * @example
 * isWithinHours("2026-01-04T13:00:00Z", 1)  // true if within 1 hour
 */
export function isWithinHours(isoString: string | null | undefined, hours: number): boolean {
    const date = parseDateTime(isoString)
    if (!date) return false

    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffHours = diffMs / (1000 * 60 * 60)

    return diffHours > 0 && diffHours <= hours
}

/**
 * Check if datetime is in the past.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns True if datetime is in the past
 */
export function isPast(isoString: string | null | undefined): boolean {
    const date = parseDateTime(isoString)
    if (!date) return false
    return date.getTime() < Date.now()
}

/**
 * Check if datetime is in the future.
 * @param isoString - ISO datetime string from backend (UTC)
 * @returns True if datetime is in the future
 */
export function isFuture(isoString: string | null | undefined): boolean {
    const date = parseDateTime(isoString)
    if (!date) return false
    return date.getTime() > Date.now()
}

/**
 * Convert local datetime to UTC ISO string for sending to backend.
 * @param date - Local Date object
 * @returns ISO string in UTC
 * 
 * @example
 * toUTCString(new Date())  // "2026-01-04T12:30:00.000Z"
 */
export function toUTCString(date: Date | null | undefined): string | null {
    if (!date) return null
    return date.toISOString()
}
