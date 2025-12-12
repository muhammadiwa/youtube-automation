"use client"

import { useState, useEffect, useCallback } from "react"
import adminApi from "@/lib/api/admin"
import { isAdminSessionValid } from "@/hooks/use-admin-session"
import type { AdminUser, AdminAuthState } from "@/types/admin"

/**
 * Hook to check and manage admin authentication state
 */
export function useAdmin(): AdminAuthState & { refreshAdmin: () => Promise<void> } {
    const [state, setState] = useState<AdminAuthState>({
        admin: null,
        isAdmin: false,
        isLoading: true,
        is2FAVerified: false,
    })

    const checkAdminStatus = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true }))
        try {
            const admin = await adminApi.checkAdminStatus()
            const is2FAVerified = isAdminSessionValid()
            setState({
                admin,
                isAdmin: admin !== null && admin.isActive,
                isLoading: false,
                is2FAVerified,
            })
        } catch {
            setState({
                admin: null,
                isAdmin: false,
                isLoading: false,
                is2FAVerified: false,
            })
        }
    }, [])

    useEffect(() => {
        checkAdminStatus()
    }, [checkAdminStatus])

    return {
        ...state,
        refreshAdmin: checkAdminStatus,
    }
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
