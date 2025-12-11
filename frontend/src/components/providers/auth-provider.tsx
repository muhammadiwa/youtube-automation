"use client"

import React, { createContext, useContext, useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import apiClient from "@/lib/api/client"
import authApi from "@/lib/api/auth"
import type { AuthUser, AuthState, LoginCredentials, RegisterData, AuthTokens } from "@/types/auth"

const TOKEN_KEY = "auth_access_token"
const REFRESH_TOKEN_KEY = "auth_refresh_token"

interface AuthContextType extends AuthState {
    login: (credentials: LoginCredentials) => Promise<{ requires2FA: boolean; tempToken?: string }>
    register: (data: RegisterData) => Promise<void>
    logout: () => Promise<void>
    verify2FA: (code: string, tempToken: string) => Promise<void>
    refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const router = useRouter()
    const [state, setState] = useState<AuthState>({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        requires2FA: false,
    })

    const setTokens = useCallback((tokens: AuthTokens) => {
        localStorage.setItem(TOKEN_KEY, tokens.accessToken)
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
        apiClient.setAccessToken(tokens.accessToken)
    }, [])

    const clearTokens = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        apiClient.setAccessToken(null)
    }, [])

    const fetchUser = useCallback(async () => {
        try {
            const user = await authApi.getCurrentUser()
            // Store user ID in apiClient for X-User-ID header
            apiClient.setUserId(user.id)
            setState(prev => ({
                ...prev,
                user,
                isAuthenticated: true,
                isLoading: false,
            }))
        } catch {
            clearTokens()
            apiClient.setUserId(null)
            setState(prev => ({
                ...prev,
                user: null,
                isAuthenticated: false,
                isLoading: false,
            }))
        }
    }, [clearTokens])

    const refreshAuth = useCallback(async () => {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
        if (!refreshToken) {
            setState(prev => ({ ...prev, isLoading: false }))
            return
        }

        try {
            const tokens = await authApi.refreshToken(refreshToken)
            setTokens(tokens)
            await fetchUser()
        } catch {
            clearTokens()
            setState(prev => ({
                ...prev,
                user: null,
                isAuthenticated: false,
                isLoading: false,
            }))
        }
    }, [setTokens, clearTokens, fetchUser])

    useEffect(() => {
        const accessToken = localStorage.getItem(TOKEN_KEY)
        if (accessToken) {
            apiClient.setAccessToken(accessToken)
            // Also restore user ID from localStorage if available
            const storedUserId = localStorage.getItem("user_id")
            if (storedUserId) {
                apiClient.setUserId(storedUserId)
            }
            fetchUser()
        } else {
            setState(prev => ({ ...prev, isLoading: false }))
        }
    }, [fetchUser])

    const login = async (credentials: LoginCredentials): Promise<{ requires2FA: boolean; tempToken?: string }> => {
        const response = await authApi.login(credentials)

        if (response.requires2FA && response.tempToken) {
            setState(prev => ({
                ...prev,
                requires2FA: true,
                tempToken: response.tempToken,
            }))
            return { requires2FA: true, tempToken: response.tempToken }
        }

        setTokens(response as AuthTokens)
        await fetchUser()
        return { requires2FA: false }
    }

    const register = async (data: RegisterData): Promise<void> => {
        await authApi.register(data)
    }

    const logout = async (): Promise<void> => {
        try {
            await authApi.logout()
        } finally {
            clearTokens()
            apiClient.setUserId(null)
            setState({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                requires2FA: false,
            })
            router.push("/login")
        }
    }

    const verify2FA = async (code: string, tempToken: string): Promise<void> => {
        const tokens = await authApi.verify2FALogin({ code, tempToken })
        setTokens(tokens)
        setState(prev => ({ ...prev, requires2FA: false, tempToken: undefined }))
        await fetchUser()
    }

    return (
        <AuthContext.Provider
            value={{
                ...state,
                login,
                register,
                logout,
                verify2FA,
                refreshAuth,
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider")
    }
    return context
}

export default AuthProvider
