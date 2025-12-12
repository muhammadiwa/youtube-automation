"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { useAdmin } from "@/hooks/use-admin"
import { Spinner } from "@/components/ui/spinner"
import { Shield, AlertTriangle } from "lucide-react"

const ADMIN_SESSION_KEY = "admin_session_token"
const ADMIN_SESSION_EXPIRY_KEY = "admin_session_expiry"

interface AdminProtectedRouteProps {
    children: React.ReactNode
    requiredPermission?: string
    requireSuperAdmin?: boolean
}

/**
 * Check if admin session is valid
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
 * Protected route wrapper for admin pages
 * Checks both authentication, admin role, and 2FA session
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

    const isLoading = authLoading || adminLoading || hasValidSession === null

    // Check admin session on mount
    useEffect(() => {
        setHasValidSession(isAdminSessionValid())
    }, [])

    // Set up session expiry check interval
    useEffect(() => {
        const checkSession = () => {
            const valid = isAdminSessionValid()
            setHasValidSession(valid)

            if (!valid && isAdmin) {
                // Session expired, redirect to admin login
                const returnUrl = encodeURIComponent(pathname)
                router.push(`/admin/login?returnUrl=${returnUrl}`)
            }
        }

        // Check every minute
        const interval = setInterval(checkSession, 60000)
        return () => clearInterval(interval)
    }, [isAdmin, pathname, router])

    useEffect(() => {
        if (isLoading) return

        // Redirect to admin login if not authenticated
        if (!isAuthenticated) {
            const returnUrl = encodeURIComponent(pathname)
            router.push(`/admin/login?returnUrl=${returnUrl}`)
            return
        }

        // Redirect to dashboard if not admin
        if (!isAdmin) {
            router.push("/dashboard")
            return
        }

        // Redirect to admin login if no valid 2FA session
        if (!hasValidSession) {
            const returnUrl = encodeURIComponent(pathname)
            router.push(`/admin/login?returnUrl=${returnUrl}`)
            return
        }

        // Check super admin requirement
        if (requireSuperAdmin && admin?.role !== "super_admin") {
            router.push("/admin")
            return
        }

        // Check specific permission
        if (requiredPermission && admin && !admin.permissions.includes(requiredPermission)) {
            router.push("/admin")
            return
        }
    }, [isAuthenticated, isAdmin, admin, isLoading, hasValidSession, router, pathname, requiredPermission, requireSuperAdmin])

    // Show loading state
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/30">
                <div className="text-center space-y-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30 mx-auto">
                        <Shield className="h-8 w-8 text-white animate-pulse" />
                    </div>
                    <Spinner className="h-6 w-6 mx-auto" />
                    <p className="text-muted-foreground">Verifying admin access...</p>
                </div>
            </div>
        )
    }

    // Show access denied if not authenticated
    if (!isAuthenticated) {
        return null
    }

    // Show access denied if not admin
    if (!isAdmin) {
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

    // Show nothing if session is invalid (will redirect)
    if (!hasValidSession) {
        return null
    }

    return <>{children}</>
}

export default AdminProtectedRoute
