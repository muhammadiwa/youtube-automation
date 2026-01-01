"use client"

import { useState, useEffect, useCallback } from "react"
import { usePathname } from "next/navigation"
import adminApi from "@/lib/api/admin"
import { isAdminSessionValid } from "@/hooks/use-admin-session"
import type { AdminUser, AdminAuthState } from "@/types/admin"

// Cache key for admin status
const ADMIN_STATUS_CACHE_KEY = "admin_status_cache"
const ADMIN_STATUS_CACHE_TTL = 5 * 60 * 1000 // 5 minutes

interface AdminStatusCache {
    admin: AdminUser | null
    timestamp: number
}

function getAdminStatusFromCache(): AdminUser | null | undefined {
    if (typeof window === "undefined") return undefined

    try {
        const cached = localStorage.getItem(ADMIN_STATUS_CACHE_KEY)
        if (!cached) return undefined

        const { admin, timestamp }: AdminStatusCache = JSON.parse(cached)

        // Check if cache is still valid
        if (Date.now() - timestamp > ADMIN_STATUS_CACHE_TTL) {
            localStorage.removeItem(ADMIN_STATUS_CACHE_KEY)
            return undefined
        }

        return admin
    } catch {
        return undefined
    }
}

function setAdminStatusCache(admin: AdminUser | null): void {
    if (typeof window === "undefined") return

    try {
        const cache: AdminStatusCache = {
            admin,
            timestamp: Date.now(),
        }
        localStorage.setItem(ADMIN_STATUS_CACHE_KEY, JSON.stringify(cache))
    } catch {
        // Ignore storage errors
    }
}

/**
 * Hook to check and manage admin authentication state
 * 
 * IMPORTANT: This hook only calls the admin API when on admin pages (/admin/*)
 * On client dashboard pages, it returns isAdmin: false without making API calls
 * to avoid unnecessary 403 errors for non-admin users.
 */
export function useAdmin(): AdminAuthState & { refreshAdmin: () => Promise<void> } {
    const pathname = usePathname()
    const isOnAdminPage = pathname?.startsWith("/admin")

    const [state, setState] = useState<AdminAuthState>({
        admin: null,
        isAdmin: false,
        isLoading: isOnAdminPage ?? false, // Only loading if on admin page
        is2FAVerified: false,
    })

    const checkAdminStatus = useCallback(async (forceRefresh = false) => {
        // Don't check admin status on non-admin pages
        // This prevents 403 errors for regular users on client dashboard
        if (!isOnAdminPage) {
            setState({
                admin: null,
                isAdmin: false,
                isLoading: false,
                is2FAVerified: false,
            })
            return
        }

        setState(prev => ({ ...prev, isLoading: true }))

        // Check cache first (unless force refresh)
        if (!forceRefresh) {
            const cachedAdmin = getAdminStatusFromCache()
            if (cachedAdmin !== undefined) {
                const is2FAVerified = isAdminSessionValid()
                setState({
                    admin: cachedAdmin,
                    isAdmin: cachedAdmin !== null && cachedAdmin.isActive,
                    isLoading: false,
                    is2FAVerified,
                })
                return
            }
        }

        try {
            const admin = await adminApi.checkAdminStatus()
            const is2FAVerified = isAdminSessionValid()

            // Cache the result
            setAdminStatusCache(admin)

            setState({
                admin,
                isAdmin: admin !== null && admin.isActive,
                isLoading: false,
                is2FAVerified,
            })
        } catch {
            // Cache the negative result to avoid repeated 403 errors
            setAdminStatusCache(null)

            setState({
                admin: null,
                isAdmin: false,
                isLoading: false,
                is2FAVerified: false,
            })
        }
    }, [isOnAdminPage])

    useEffect(() => {
        checkAdminStatus()
    }, [checkAdminStatus])

    return {
        ...state,
        refreshAdmin: () => checkAdminStatus(true),
    }
}

/**
 * Clear admin status cache (call on logout)
 */
export function clearAdminStatusCache(): void {
    if (typeof window === "undefined") return
    localStorage.removeItem(ADMIN_STATUS_CACHE_KEY)
}

/**
 * Check if admin has specific permission
 */
export function hasPermission(admin: AdminUser | null, permission: string): boolean {
    if (!admin || !admin.isActive) return false
    return admin.permissions.includes(permission)
}

/**
 * Check if admin is super admin
 */
export function isSuperAdmin(admin: AdminUser | null): boolean {
    if (!admin || !admin.isActive) return false
    return admin.role === "super_admin"
}
