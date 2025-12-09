"use client"

import { useState, useMemo, Suspense } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import { Lock, Loader2, Eye, EyeOff, Check, X, ArrowLeft, AlertCircle } from "lucide-react"
import { Button, Input, Label, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui"
import authApi from "@/lib/api/auth"
import { calculatePasswordStrength, getStrengthColor, getStrengthLabel } from "@/lib/utils/password"

function ResetPasswordForm() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const token = searchParams.get("token")

    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [isSuccess, setIsSuccess] = useState(false)

    const passwordStrength = useMemo(() => calculatePasswordStrength(password), [password])
    const passwordsMatch = password === confirmPassword && confirmPassword.length > 0

    const isFormValid = useMemo(() => {
        return passwordStrength.isValid && passwordsMatch
    }, [passwordStrength.isValid, passwordsMatch])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!token) {
            setError("Invalid or missing reset token")
            return
        }

        if (!isFormValid) {
            setError("Please ensure your password meets all requirements")
            return
        }

        setError("")
        setIsLoading(true)

        try {
            await authApi.confirmPasswordReset({ token, newPassword: password })
            setIsSuccess(true)
            setTimeout(() => {
                router.push("/login")
            }, 3000)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to reset password. The link may have expired.")
        } finally {
            setIsLoading(false)
        }
    }

    // No token provided
    if (!token) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center space-y-4">
                            <div className="mx-auto w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center">
                                <AlertCircle className="h-6 w-6 text-destructive" />
                            </div>
                            <h2 className="text-xl font-semibold">Invalid Reset Link</h2>
                            <p className="text-muted-foreground">
                                This password reset link is invalid or has expired.
                            </p>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-3">
                        <Link href="/forgot-password" className="w-full">
                            <Button className="w-full">
                                Request new reset link
                            </Button>
                        </Link>
                        <Link href="/login" className="w-full">
                            <Button variant="ghost" className="w-full">
                                <ArrowLeft className="mr-2 h-4 w-4" />
                                Back to login
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>
            </motion.div>
        )
    }

    // Success state
    if (isSuccess) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
            >
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center space-y-4">
                            <div className="mx-auto w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                                <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
                            </div>
                            <h2 className="text-xl font-semibold">Password Reset!</h2>
                            <p className="text-muted-foreground">
                                Your password has been successfully reset. Redirecting to login...
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <Card>
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold">Reset your password</CardTitle>
                    <CardDescription>
                        Enter your new password below
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-4">
                        {error && (
                            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="password">New Password</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="pl-10 pr-10"
                                    required
                                    autoComplete="new-password"
                                    autoFocus
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>

                            {/* Password strength indicator */}
                            {password && (
                                <div className="space-y-2">
                                    <div className="flex gap-1">
                                        {[0, 1, 2, 3].map((index) => (
                                            <div
                                                key={index}
                                                className={`h-1 flex-1 rounded-full transition-colors ${index < passwordStrength.score
                                                        ? getStrengthColor(passwordStrength.score)
                                                        : "bg-muted"
                                                    }`}
                                            />
                                        ))}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Password strength: <span className="font-medium">{getStrengthLabel(passwordStrength.score)}</span>
                                    </p>
                                    {passwordStrength.feedback.length > 0 && (
                                        <ul className="text-xs text-muted-foreground space-y-1">
                                            {passwordStrength.feedback.map((item, index) => (
                                                <li key={index} className="flex items-center gap-1">
                                                    <X className="h-3 w-3 text-destructive" />
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">Confirm New Password</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="confirmPassword"
                                    type={showConfirmPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="pl-10 pr-10"
                                    required
                                    autoComplete="new-password"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                                >
                                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {confirmPassword && (
                                <p className={`text-xs flex items-center gap-1 ${passwordsMatch ? "text-green-600" : "text-destructive"}`}>
                                    {passwordsMatch ? (
                                        <>
                                            <Check className="h-3 w-3" />
                                            Passwords match
                                        </>
                                    ) : (
                                        <>
                                            <X className="h-3 w-3" />
                                            Passwords do not match
                                        </>
                                    )}
                                </p>
                            )}
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-3">
                        <Button type="submit" className="w-full" disabled={isLoading || !isFormValid}>
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Reset password
                        </Button>
                        <Link href="/login" className="w-full">
                            <Button variant="ghost" className="w-full">
                                <ArrowLeft className="mr-2 h-4 w-4" />
                                Back to login
                            </Button>
                        </Link>
                    </CardFooter>
                </form>
            </Card>
        </motion.div>
    )
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={
            <Card>
                <CardContent className="pt-6">
                    <div className="flex justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                </CardContent>
            </Card>
        }>
            <ResetPasswordForm />
        </Suspense>
    )
}
