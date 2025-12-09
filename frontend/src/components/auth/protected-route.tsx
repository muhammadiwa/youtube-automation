"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/components/providers/auth-provider"
import { Spinner } from "@/components/ui"

interface ProtectedRouteProps {
    children: React.ReactNode
    requireAuth?: boolean
    require2FA?: boolean
    redirectTo?: string
}

/**
 * Protected route wrapper that handles authentication state
 * 
 * @param requireAuth - If true, redirects unauthenticated users to login
 * @param require2FA - If true, requires 2FA to be enabled
 * @param redirectTo - Custom redirect path for unauthenticated users
 */
export function ProtectedRoute({
    children,
    requireAuth = true,
    require2FA = false,
    redirectTo = "/login",
}: ProtectedRouteProps) {
    const router = useRouter()
    const pathname = usePathname()
    const { isAuthenticated, isLoading, user } = useAuth()

    useEffect(() => {
        if (isLoading) return

        if (requireAuth && !isAuthenticated) {
            // Store the intended destination for redirect after login
            const returnUrl = encodeURIComponent(pathname)
            router.push(`${redirectTo}?returnUrl=${returnUrl}`)
            return
        }

        if (require2FA && user && !user.is2FAEnabled) {
            router.push("/2fa-setup")
            return
        }
    }, [isAuthenticated, isLoading, requireAuth, require2FA, user, router, pathname, redirectTo])

    // Show loading state while checking auth
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center space-y-4">
                    <Spinner className="h-8 w-8 mx-auto" />
                    <p className="text-muted-foreground">Loading...</p>
                </div>
            </div>
        )
    }

    // Don't render children if auth requirements aren't met
    if (requireAuth && !isAuthenticated) {
        return null
    }

    if (require2FA && user && !user.is2FAEnabled) {
        return null
    }

    return <>{children}</>
}

/**
 * HOC version of ProtectedRoute for wrapping page components
 */
export function withAuth<P extends object>(
    Component: React.ComponentType<P>,
    options?: Omit<ProtectedRouteProps, "children">
) {
    return function AuthenticatedComponent(props: P) {
        return (
            <ProtectedRoute {...options}>
                <Component {...props} />
            </ProtectedRoute>
        )
    }
}

export default ProtectedRoute
