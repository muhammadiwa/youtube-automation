"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import {
    Eye,
    EyeOff,
    Mail,
    Lock,
    Loader2,
    Shield,
    ArrowRight,
    KeyRound,
    AlertTriangle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/use-auth"
import adminApi from "@/lib/api/admin"
import type { AdminAccessVerification, AdminLoginState } from "@/types/admin"

const ADMIN_SESSION_KEY = "admin_session_token"
const ADMIN_SESSION_EXPIRY_KEY = "admin_session_expiry"

export default function AdminLoginPage() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const { isAuthenticated, isLoading: authLoading, login } = useAuth()

    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [totpCode, setTotpCode] = useState("")
    const [showPassword, setShowPassword] = useState(false)

    const [state, setState] = useState<AdminLoginState>({
        step: "credentials",
        isLoading: false,
        error: null,
        adminInfo: null,
    })

    const returnUrl = searchParams.get("returnUrl") || "/admin"

    // Check if user is already authenticated and has admin access
    useEffect(() => {
        if (authLoading) return

        const checkAdminAccess = async () => {
            if (!isAuthenticated) return

            try {
                const adminInfo = await adminApi.verifyAdminAccess()
                if (adminInfo.isAdmin) {
                    // If 2FA is not required, redirect directly to admin
                    if (!adminInfo.requires2FA) {
                        // Create a simple session marker for non-2FA admins
                        const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
                        localStorage.setItem(ADMIN_SESSION_KEY, "no-2fa-session")
                        localStorage.setItem(ADMIN_SESSION_EXPIRY_KEY, expiresAt.toISOString())
                        router.push(returnUrl)
                        return
                    }

                    // Check if we have a valid admin session (for 2FA users)
                    const sessionToken = localStorage.getItem(ADMIN_SESSION_KEY)
                    const sessionExpiry = localStorage.getItem(ADMIN_SESSION_EXPIRY_KEY)

                    if (sessionToken && sessionExpiry) {
                        const expiryDate = new Date(sessionExpiry)
                        if (expiryDate > new Date()) {
                            // Valid session exists, redirect to admin
                            router.push(returnUrl)
                            return
                        }
                    }

                    // Need 2FA verification
                    setState((prev) => ({
                        ...prev,
                        step: "2fa",
                        adminInfo,
                    }))
                }
            } catch {
                // Not an admin, stay on login page
            }
        }

        checkAdminAccess()
    }, [isAuthenticated, authLoading, router, returnUrl])

    const handleCredentialsSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setState((prev) => ({ ...prev, isLoading: true, error: null }))

        try {
            // First, login with credentials
            await login({ email, password, rememberMe: false })

            // Then verify admin access
            const adminInfo = await adminApi.verifyAdminAccess()

            if (!adminInfo.isAdmin) {
                setState((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: "You do not have admin privileges.",
                }))
                return
            }

            // If 2FA is not required, redirect directly to admin
            if (!adminInfo.requires2FA) {
                // Create a simple session marker for non-2FA admins
                const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
                localStorage.setItem(ADMIN_SESSION_KEY, "no-2fa-session")
                localStorage.setItem(ADMIN_SESSION_EXPIRY_KEY, expiresAt.toISOString())
                router.push(returnUrl)
                return
            }

            // Move to 2FA step (only if 2FA is enabled)
            setState((prev) => ({
                ...prev,
                step: "2fa",
                isLoading: false,
                adminInfo,
            }))
        } catch (err) {
            setState((prev) => ({
                ...prev,
                isLoading: false,
                error:
                    err instanceof Error
                        ? err.message
                        : "Invalid credentials. Please try again.",
            }))
        }
    }

    const handle2FASubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setState((prev) => ({ ...prev, isLoading: true, error: null }))

        try {
            const response = await adminApi.verify2FA(totpCode)

            if (response.verified) {
                // Store admin session token
                localStorage.setItem(ADMIN_SESSION_KEY, response.adminSessionToken)
                localStorage.setItem(ADMIN_SESSION_EXPIRY_KEY, response.expiresAt)

                // Redirect to admin panel
                router.push(returnUrl)
            }
        } catch (err) {
            setState((prev) => ({
                ...prev,
                isLoading: false,
                error:
                    err instanceof Error
                        ? err.message
                        : "Invalid 2FA code. Please try again.",
            }))
        }
    }

    const handleBackToCredentials = () => {
        setState({
            step: "credentials",
            isLoading: false,
            error: null,
            adminInfo: null,
        })
        setTotpCode("")
    }

    if (authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                <div className="text-center space-y-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30 mx-auto">
                        <Shield className="h-8 w-8 text-white animate-pulse" />
                    </div>
                    <Loader2 className="h-6 w-6 mx-auto animate-spin text-blue-400" />
                    <p className="text-slate-400">Loading...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row">
            {/* Left Side - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12 bg-white dark:bg-slate-950 order-2 lg:order-1">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-md"
                >
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                            <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                                Admin Panel
                            </h1>
                            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                                Secure administrative access
                            </p>
                        </div>
                    </div>

                    <AnimatePresence mode="wait">
                        {state.step === "credentials" ? (
                            <motion.div
                                key="credentials"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.3 }}
                            >
                                {/* Welcome Text */}
                                <div className="mb-8">
                                    <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
                                        Admin Sign In
                                    </h2>
                                    <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                                        Enter your credentials to access the admin panel
                                    </p>
                                </div>

                                {/* Credentials Form */}
                                <form onSubmit={handleCredentialsSubmit} className="space-y-5">
                                    {state.error && (
                                        <motion.div
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3"
                                        >
                                            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                                            <span className="text-red-600 dark:text-red-400 text-sm">
                                                {state.error}
                                            </span>
                                        </motion.div>
                                    )}

                                    <div>
                                        <Label
                                            htmlFor="email"
                                            className="text-slate-700 dark:text-slate-300 mb-2 block text-sm sm:text-base"
                                        >
                                            Email Address
                                        </Label>
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-slate-400" />
                                            <Input
                                                id="email"
                                                type="email"
                                                placeholder="admin@example.com"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                className="pl-9 sm:pl-10 h-10 sm:h-11 text-sm sm:text-base bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 focus:border-blue-500 focus:ring-blue-500"
                                                required
                                                autoComplete="email"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <Label
                                            htmlFor="password"
                                            className="text-slate-700 dark:text-slate-300 mb-2 block text-sm sm:text-base"
                                        >
                                            Password
                                        </Label>
                                        <div className="relative">
                                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-slate-400" />
                                            <Input
                                                id="password"
                                                type={showPassword ? "text" : "password"}
                                                placeholder="••••••••"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="pl-9 sm:pl-10 pr-9 sm:pr-10 h-10 sm:h-11 text-sm sm:text-base bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 focus:border-blue-500 focus:ring-blue-500"
                                                required
                                                autoComplete="current-password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                                            >
                                                {showPassword ? (
                                                    <EyeOff className="h-4 w-4 sm:h-5 sm:w-5" />
                                                ) : (
                                                    <Eye className="h-4 w-4 sm:h-5 sm:w-5" />
                                                )}
                                            </button>
                                        </div>
                                    </div>

                                    <Button
                                        type="submit"
                                        className="w-full h-10 sm:h-11 text-sm sm:text-base bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium shadow-lg shadow-blue-500/30"
                                        disabled={state.isLoading}
                                    >
                                        {state.isLoading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                                                Verifying...
                                            </>
                                        ) : (
                                            <>
                                                Continue
                                                <ArrowRight className="ml-2 h-4 w-4 sm:h-5 sm:w-5" />
                                            </>
                                        )}
                                    </Button>
                                </form>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="2fa"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.3 }}
                            >
                                {/* 2FA Step */}
                                <div className="mb-8">
                                    <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
                                        Two-Factor Authentication
                                    </h2>
                                    <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
                                        Enter the 6-digit code from your authenticator app
                                    </p>
                                </div>

                                {/* Security Notice */}
                                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                    <div className="flex items-start gap-3">
                                        <Shield className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                                                Enhanced Security Required
                                            </p>
                                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                                All admin access requires 2FA verification for security
                                                purposes.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* 2FA Form */}
                                <form onSubmit={handle2FASubmit} className="space-y-5">
                                    {state.error && (
                                        <motion.div
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3"
                                        >
                                            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                                            <span className="text-red-600 dark:text-red-400 text-sm">
                                                {state.error}
                                            </span>
                                        </motion.div>
                                    )}

                                    <div>
                                        <Label
                                            htmlFor="totp"
                                            className="text-slate-700 dark:text-slate-300 mb-2 block text-sm sm:text-base"
                                        >
                                            Authentication Code
                                        </Label>
                                        <div className="relative">
                                            <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-slate-400" />
                                            <Input
                                                id="totp"
                                                type="text"
                                                inputMode="numeric"
                                                pattern="[0-9]*"
                                                maxLength={6}
                                                placeholder="000000"
                                                value={totpCode}
                                                onChange={(e) =>
                                                    setTotpCode(e.target.value.replace(/\D/g, ""))
                                                }
                                                className="pl-9 sm:pl-10 h-10 sm:h-11 text-sm sm:text-base text-center tracking-[0.5em] font-mono bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 focus:border-blue-500 focus:ring-blue-500"
                                                required
                                                autoComplete="one-time-code"
                                                autoFocus
                                            />
                                        </div>
                                    </div>

                                    <Button
                                        type="submit"
                                        className="w-full h-10 sm:h-11 text-sm sm:text-base bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium shadow-lg shadow-blue-500/30"
                                        disabled={state.isLoading || totpCode.length !== 6}
                                    >
                                        {state.isLoading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                                                Verifying...
                                            </>
                                        ) : (
                                            <>
                                                Verify & Sign In
                                                <Shield className="ml-2 h-4 w-4 sm:h-5 sm:w-5" />
                                            </>
                                        )}
                                    </Button>

                                    <Button
                                        type="button"
                                        variant="ghost"
                                        className="w-full text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                                        onClick={handleBackToCredentials}
                                    >
                                        ← Back to login
                                    </Button>
                                </form>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <p className="mt-8 text-center text-xs text-slate-500 dark:text-slate-500">
                        This is a secure admin area. All access is logged and monitored.
                    </p>
                </motion.div>
            </div>

            {/* Right Side - Hero */}
            <div className="hidden lg:flex w-full lg:w-1/2 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 p-12 items-center justify-center relative overflow-hidden order-1 lg:order-2">
                {/* Animated Background */}
                <div className="absolute inset-0">
                    <motion.div
                        className="absolute top-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.2, 1],
                            x: [0, 50, 0],
                            y: [0, 30, 0],
                        }}
                        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute bottom-20 left-20 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.3, 1],
                            x: [0, -50, 0],
                            y: [0, -30, 0],
                        }}
                        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                    />
                </div>

                {/* Grid Pattern */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.7 }}
                    className="relative z-10 text-white max-w-lg"
                >
                    <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30 mb-8">
                        <Shield className="h-10 w-10 text-white" />
                    </div>

                    <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                        Administrative Control Center
                    </h2>
                    <p className="text-lg lg:text-xl text-slate-300 mb-8">
                        Manage users, monitor system health, configure settings, and access
                        comprehensive analytics from a single secure dashboard.
                    </p>
                    <div className="space-y-4">
                        {[
                            "User & subscription management",
                            "Real-time system monitoring",
                            "Content moderation tools",
                            "Comprehensive audit logs",
                        ].map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3 + index * 0.1 }}
                                className="flex items-center gap-3"
                            >
                                <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                                    <svg
                                        className="w-4 h-4"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M5 13l4 4L19 7"
                                        />
                                    </svg>
                                </div>
                                <span className="text-base lg:text-lg text-slate-200">
                                    {feature}
                                </span>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
