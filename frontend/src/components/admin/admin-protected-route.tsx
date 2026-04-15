"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { useAdmin } from "@/hooks/use-admin"
import { Spinner } from "@/components/ui/spinner"
import { Shield, AlertTriangle } from "lucide-react"

const ADMIN_SESSION_KEY = "admin_session_token"
const ADMIN_SESSION_EXPIRY_KEY = "admin_session_expiry"
const ADMIN_VERIFIED_KEY = "admin_verified" // Cache admin verification

interface AdminProtectedRouteProps {
    children: React.ReactNode
    requiredPermission?: string
    requireSuperAdmin?: boolean
}

/**
 * Check if admin session is valid
 * Session is created after successful admin login with 2FA
 */
function isAdminSessionValid(): boolean {
    if (typeof window === "undefined") return false

    const sessionToken = localStorage.getItem(ADMIN_SESSION_KEY)
    const sessionExpiry = localStorage.getItem(ADMIN_SESSION_EXPIRY_KEY)

    if (!sessionToken || !sessionExpiry) return false

    const expiryDate = new Date(sessionExpiry)
    return expiryDate > new Date()
}

/**
 * Check if admin was previously verified (cached)
 * This prevents unnecessary API calls on refresh
 */
function isAdminVerifiedCached(): boolean {
    if (typeof window === "undefined") return false
    return localStorage.getItem(ADMIN_VERIFIED_KEY) === "true"
}

/**
 * Cache admin verification status
 */
function setAdminVerifiedCache(verified: boolean): void {
    if (typeof window === "undefined") return
    if (verified) {
        localStorage.setItem(ADMIN_VERIFIED_KEY, "true")
    } else {
        localStorage.removeItem(ADMIN_VERIFIED_KEY)
    }
}

/**
 * Protected route wrapper for admin pages
 * 
 * Logic:
 * 1. Check if user is authenticated (via auth token)
 * 2. Check if admin session is valid (created after 2FA login)
 * 3. If session valid, trust it - no need to re-verify admin status on every refresh
 * 4. Only verify admin status from API if not cached
 */
export function AdminProtectedRoute({
    children,
    requiredPermission,
    requireSuperAdmin = false,
}: AdminProtectedRouteProps) {
    const router = useRouter()
    const pathname = usePathname()
    const { isAuthenticated, isLoading: authLoading } = useAuth()
    const { admin, isAdmin, isLoading: adminLoading } = useAdmin()
    const [hasValidSession, setHasValidSession] = useState<boolean | null>(null)
    const [isVerified, setIsVerified] = useState<boolean | null>(null)
    const hasRedirected = useRef(false)

    // Check admin session on mount
    useEffect(() => {
        const sessionValid = isAdminSessionValid()
        setHasValidSession(sessionValid)

        // If session is valid, trust the cached verification
        if (sessionValid && isAdminVerifiedCached()) {
            setIsVerified(true)
        }
    }, [])

    // Update verification status when admin data loads
    useEffect(() => {
        if (!adminLoading && hasValidSession) {
            if (isAdmin) {
                setIsVerified(true)
                setAdminVerifiedCache(true)
            } else if (isVerified === null) {
                // Only set to false if we haven't verified yet
                // This prevents race conditions
                setIsVerified(false)
                setAdminVerifiedCache(false)
            }
        }
    }, [adminLoading, isAdmin, hasValidSession, isVerified])

    // Set up session expiry check interval (every 5 minutes instead of 1)
    useEffect(() => {
        const checkSession = () => {
            const valid = isAdminSessionValid()
            if (!valid && hasValidSession) {
                // Session expired
                setHasValidSession(false)
                setAdminVerifiedCache(false)
                const returnUrl = encodeURIComponent(pathname)
                router.push(`/admin/login?returnUrl=${returnUrl}&reason=session_expired`)
            }
        }

        // Check every 5 minutes
        const interval = setInterval(checkSession, 300000)
        return () => clearInterval(interval)
    }, [hasValidSession, pathname, router])

    // Determine if we're still loading
    const isLoading = authLoading || hasValidSession === null ||
        (hasValidSession && !isAdminVerifiedCached() && adminLoading)

    useEffect(() => {
        if (isLoading || hasRedirected.current) return

        // Redirect to login if not authenticated
        if (!isAuthenticated) {
            hasRedirected.current = true
            const returnUrl = encodeURIComponent(pathname)
            router.push(`/admin/login?returnUrl=${returnUrl}`)
            return
        }

        // Redirect to admin login if no valid session
        if (!hasValidSession) {
            hasRedirected.current = true
            const returnUrl = encodeURIComponent(pathname)
            router.push(`/admin/login?returnUrl=${returnUrl}`)
            return
        }

        // If we have valid session and cached verification, allow access
        // Only check API result if not cached
        if (!isAdminVerifiedCached() && !adminLoading && !isAdmin) {
            hasRedirected.current = true
            setAdminVerifiedCache(false)
            router.push("/dashboard")
            return
        }

        // Check super admin requirement
        if (requireSuperAdmin && admin?.role !== "super_admin") {
            hasRedirected.current = true
            router.push("/admin")
            return
        }

        // Check specific permission
        if (requiredPermission && admin && !admin.permissions.includes(requiredPermission)) {
            hasRedirected.current = true
            router.push("/admin")
            return
        }
    }, [isAuthenticated, isAdmin, admin, isLoading, adminLoading, hasValidSession, router, pathname, requiredPermission, requireSuperAdmin])

    // Show loading state only during initial load
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/30">
                <div className="text-center space-y-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30 mx-auto">
                        <Shield className="h-8 w-8 text-white animate-pulse" />
                    </div>
                    <Spinner className="h-6 w-6 mx-auto" />
                    <p className="text-muted-foreground">Loading...</p>
                </div>
            </div>
        )
    }

    // Show nothing if not authenticated (will redirect)
    if (!isAuthenticated) {
        return null
    }

    // Show nothing if session is invalid (will redirect)
    if (!hasValidSession) {
        return null
    }

    // If session is valid and we have cached verification, show content
    // This allows immediate render without waiting for API
    if (hasValidSession && (isAdminVerifiedCached() || isAdmin)) {
        return <>{children}</>
    }

    // Show access denied only if API confirmed user is not admin
    if (!adminLoading && !isAdmin && !isAdminVerifiedCached()) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/30">
                <div className="text-center space-y-4 max-w-md mx-auto p-8">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/30 mx-auto">
                        <AlertTriangle className="h-8 w-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold">Access Denied</h1>
                    <p className="text-muted-foreground">
                        You don&apos;t have permission to access the admin panel.
                        Please contact your administrator if you believe this is an error.
                    </p>
                </div>
            </div>
        )
    }

    return <>{children}</>
}

export default AdminProtectedRoute
