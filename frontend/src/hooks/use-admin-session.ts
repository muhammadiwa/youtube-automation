"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"

const ADMIN_SESSION_KEY = "admin_session_token"
const ADMIN_SESSION_EXPIRY_KEY = "admin_session_expiry"
const SESSION_CHECK_INTERVAL = 60000 // Check every minute

export interface AdminSession {
    token: string
    expiresAt: Date
}

export interface AdminSessionState {
    session: AdminSession | null
    isValid: boolean
    isLoading: boolean
    timeRemaining: number | null // seconds until expiry
}

/**
 * Hook to manage admin session state
 * Handles session storage, validation, and auto-logout
 */
export function useAdminSession() {
    const router = useRouter()
    const [state, setState] = useState<AdminSessionState>({
        session: null,
        isValid: false,
        isLoading: true,
        timeRemaining: null,
    })

    /**
     * Load session from localStorage
     */
    const loadSession = useCallback((): AdminSession | null => {
        if (typeof window === "undefined") return null

        const token = localStorage.getItem(ADMIN_SESSION_KEY)
        const expiryStr = localStorage.getItem(ADMIN_SESSION_EXPIRY_KEY)

        if (!token || !expiryStr) return null

        const expiresAt = new Date(expiryStr)
        return { token, expiresAt }
    }, [])

    /**
     * Check if session is valid
     */
    const isSessionValid = useCallback((session: AdminSession | null): boolean => {
        if (!session) return false
        return session.expiresAt > new Date()
    }, [])

    /**
     * Calculate time remaining in seconds
     */
    const calculateTimeRemaining = useCallback((session: AdminSession | null): number | null => {
        if (!session) return null
        const remaining = Math.floor((session.expiresAt.getTime() - Date.now()) / 1000)
        return remaining > 0 ? remaining : 0
    }, [])

    /**
     * Save session to localStorage
     */
    const saveSession = useCallback((token: string, expiresAt: string) => {
        if (typeof window === "undefined") return

        localStorage.setItem(ADMIN_SESSION_KEY, token)
        localStorage.setItem(ADMIN_SESSION_EXPIRY_KEY, expiresAt)

        const session = { token, expiresAt: new Date(expiresAt) }
        setState({
            session,
            isValid: isSessionValid(session),
            isLoading: false,
            timeRemaining: calculateTimeRemaining(session),
        })
    }, [isSessionValid, calculateTimeRemaining])

    /**
     * Clear session from localStorage
     */
    const clearSession = useCallback(() => {
        if (typeof window === "undefined") return

        localStorage.removeItem(ADMIN_SESSION_KEY)
        localStorage.removeItem(ADMIN_SESSION_EXPIRY_KEY)

        setState({
            session: null,
            isValid: false,
            isLoading: false,
            timeRemaining: null,
        })
    }, [])

    /**
     * Logout and redirect to admin login
     */
    const logout = useCallback((returnUrl?: string) => {
        clearSession()
        const url = returnUrl
            ? `/admin/login?returnUrl=${encodeURIComponent(returnUrl)}`
            : "/admin/login"
        router.push(url)
    }, [clearSession, router])

    /**
     * Check session validity and update state
     */
    const checkSession = useCallback(() => {
        const session = loadSession()
        const valid = isSessionValid(session)
        const timeRemaining = calculateTimeRemaining(session)

        setState({
            session,
            isValid: valid,
            isLoading: false,
            timeRemaining,
        })

        return valid
    }, [loadSession, isSessionValid, calculateTimeRemaining])

    // Initial load
    useEffect(() => {
        checkSession()
    }, [checkSession])

    // Set up periodic session check
    useEffect(() => {
        const interval = setInterval(() => {
            const valid = checkSession()

            // Auto-logout if session expired
            if (!valid && state.session) {
                logout(window.location.pathname)
            }
        }, SESSION_CHECK_INTERVAL)

        return () => clearInterval(interval)
    }, [checkSession, logout, state.session])

    // Update time remaining every second when session is valid
    useEffect(() => {
        if (!state.isValid || !state.session) return

        const interval = setInterval(() => {
            const timeRemaining = calculateTimeRemaining(state.session)

            if (timeRemaining !== null && timeRemaining <= 0) {
                // Session expired
                logout(window.location.pathname)
            } else {
                setState(prev => ({ ...prev, timeRemaining }))
            }
        }, 1000)

        return () => clearInterval(interval)
    }, [state.isValid, state.session, calculateTimeRemaining, logout])

    return {
        ...state,
        saveSession,
        clearSession,
        logout,
        checkSession,
    }
}

/**
 * Get admin session token for API requests
 */
export function getAdminSessionToken(): string | null {
    if (typeof window === "undefined") return null
    return localStorage.getItem(ADMIN_SESSION_KEY)
}

/**
 * Check if admin session is valid (utility function)
 */
export function isAdminSessionValid(): boolean {
    if (typeof window === "undefined") return false

    const token = localStorage.getItem(ADMIN_SESSION_KEY)
    const expiryStr = localStorage.getItem(ADMIN_SESSION_EXPIRY_KEY)

    if (!token || !expiryStr) return false

    const expiresAt = new Date(expiryStr)
    return expiresAt > new Date()
}
