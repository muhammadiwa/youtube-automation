// Admin related types

export type AdminRole = "admin" | "super_admin"

export interface AdminUser {
    id: string
    userId: string
    role: AdminRole
    permissions: string[]
    isActive: boolean
    lastLoginAt: string | null
    createdAt: string
}

export interface AdminAuthState {
    admin: AdminUser | null
    isAdmin: boolean
    isLoading: boolean
    is2FAVerified?: boolean
}

export interface AdminAccessVerification {
    isAdmin: boolean
    adminId: string
    role: AdminRole
    permissions: string[]
    requires2FA: boolean
}

export interface Admin2FAResponse {
    verified: boolean
    adminSessionToken: string
    expiresAt: string
}

export interface AdminLoginState {
    step: "credentials" | "2fa"
    isLoading: boolean
    error: string | null
    adminInfo: AdminAccessVerification | null
}

// Admin navigation item
export interface AdminNavItem {
    name: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string | number
}

// Admin sidebar section
export interface AdminNavSection {
    title: string
    items: AdminNavItem[]
}
