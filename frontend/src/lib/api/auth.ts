import apiClient from "./client"
import type {
    LoginCredentials,
    RegisterData,
    AuthTokens,
    TwoFactorSetup,
    TwoFactorVerification,
    PasswordResetRequest,
    PasswordResetConfirm,
    AuthUser,
} from "@/types/auth"

export const authApi = {
    /**
     * Login with email and password
     */
    async login(credentials: LoginCredentials): Promise<AuthTokens & { requires2FA?: boolean; tempToken?: string }> {
        return apiClient.post("/auth/login", credentials)
    },

    /**
     * Register a new user
     */
    async register(data: RegisterData): Promise<AuthUser> {
        return apiClient.post("/auth/register", data)
    },

    /**
     * Refresh access token
     */
    async refreshToken(refreshToken: string): Promise<AuthTokens> {
        return apiClient.post("/auth/refresh", { refreshToken })
    },

    /**
     * Logout and invalidate tokens
     */
    async logout(): Promise<void> {
        return apiClient.post("/auth/logout")
    },

    /**
     * Get current user profile
     */
    async getCurrentUser(): Promise<AuthUser> {
        return apiClient.get("/auth/me")
    },

    /**
     * Enable 2FA for current user
     */
    async enable2FA(): Promise<TwoFactorSetup> {
        return apiClient.post("/auth/2fa/enable")
    },

    /**
     * Verify 2FA code during setup
     */
    async verify2FASetup(code: string): Promise<{ backupCodes: string[] }> {
        return apiClient.post("/auth/2fa/verify-setup", { code })
    },

    /**
     * Verify 2FA code during login
     */
    async verify2FALogin(data: TwoFactorVerification & { tempToken: string }): Promise<AuthTokens> {
        return apiClient.post("/auth/2fa/verify", data)
    },

    /**
     * Disable 2FA
     */
    async disable2FA(code: string): Promise<void> {
        return apiClient.post("/auth/2fa/disable", { code })
    },

    /**
     * Request password reset email
     */
    async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
        return apiClient.post("/auth/password/reset-request", data)
    },

    /**
     * Confirm password reset with token
     */
    async confirmPasswordReset(data: PasswordResetConfirm): Promise<void> {
        return apiClient.post("/auth/password/reset-confirm", data)
    },

    /**
     * Change password (when logged in)
     */
    async changePassword(currentPassword: string, newPassword: string): Promise<void> {
        return apiClient.post("/auth/password/change", { currentPassword, newPassword })
    },

    /**
     * Initiate Google OAuth login
     */
    getGoogleOAuthUrl(): string {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
        return `${baseUrl}/auth/oauth/google`
    },
}

export default authApi
