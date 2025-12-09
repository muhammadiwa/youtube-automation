// Authentication related types

export interface LoginCredentials {
    email: string
    password: string
    rememberMe?: boolean
}

export interface RegisterData {
    email: string
    password: string
    name: string
    acceptTerms: boolean
}

export interface AuthTokens {
    accessToken: string
    refreshToken: string
    expiresIn: number
    tokenType: string
}

export interface TwoFactorSetup {
    secret: string
    qrCodeUrl: string
    backupCodes: string[]
}

export interface TwoFactorVerification {
    code: string
}

export interface PasswordResetRequest {
    email: string
}

export interface PasswordResetConfirm {
    token: string
    newPassword: string
}

export interface AuthUser {
    id: string
    email: string
    name: string
    is2FAEnabled: boolean
    createdAt: string
    lastLoginAt: string
}

export interface AuthState {
    user: AuthUser | null
    isAuthenticated: boolean
    isLoading: boolean
    requires2FA: boolean
    tempToken?: string
}

export interface PasswordStrength {
    score: number // 0-4
    feedback: string[]
    isValid: boolean
}
