"use client"

import { useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { Mail, Loader2, ArrowLeft, Check, Play, KeyRound, Shield, Lock, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import authApi from "@/lib/api/auth"

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [isSubmitted, setIsSubmitted] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setIsLoading(true)

        try {
            await authApi.requestPasswordReset({ email })
            setIsSubmitted(true)
        } catch (err) {
            // Don't reveal if email exists or not for security
            setIsSubmitted(true)
        } finally {
            setIsLoading(false)
        }
    }

    if (isSubmitted) {
        return (
            <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100 dark:from-gray-950 dark:to-red-950 p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: "spring", duration: 0.6 }}
                    className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 sm:p-12 text-center max-w-md w-full"
                >
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1, rotate: 360 }}
                        transition={{ delay: 0.2, type: "spring" }}
                        className="mx-auto w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-red-500/30"
                    >
                        <Check className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                    </motion.div>
                    <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-3">Check your email</h2>
                    <p className="text-gray-600 dark:text-gray-400 text-base sm:text-lg mb-2">
                        If an account exists for <strong className="text-gray-900 dark:text-white">{email}</strong>, you'll receive a password reset link shortly.
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mb-8">
                        The link will expire in 1 hour.
                    </p>
                    <div className="space-y-3">
                        <Button
                            variant="outline"
                            onClick={() => {
                                setIsSubmitted(false)
                                setEmail("")
                            }}
                            className="w-full h-11 border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                            Try another email
                        </Button>
                        <Link href="/login" className="block">
                            <Button variant="ghost" className="w-full h-11 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                                <ArrowLeft className="mr-2 h-4 w-4" />
                                Back to login
                            </Button>
                        </Link>
                    </div>
                </motion.div>
            </div>
        )
    }

    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row">
            {/* Left Side - Form (Mobile First) */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12 bg-white dark:bg-gray-950 order-2 lg:order-1">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-md"
                >
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/30">
                            <Play className="w-5 h-5 sm:w-6 sm:h-6 text-white fill-white" />
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">YouTube Auto</h1>
                            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Reset your password</p>
                        </div>
                    </div>

                    {/* Welcome Text */}
                    <div className="mb-8">
                        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">Forgot password?</h2>
                        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">No worries, we'll send you reset instructions</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm"
                            >
                                {error}
                            </motion.div>
                        )}

                        <div>
                            <Label htmlFor="email" className="text-gray-700 dark:text-gray-300 mb-2 block text-sm sm:text-base">
                                Email Address
                            </Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="name@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="pl-9 sm:pl-10 h-10 sm:h-11 text-sm sm:text-base bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 focus:border-red-500 focus:ring-red-500"
                                    required
                                    autoComplete="email"
                                    autoFocus
                                />
                            </div>
                            <p className="mt-2 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                                Enter the email associated with your account
                            </p>
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-10 sm:h-11 text-sm sm:text-base bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-medium shadow-lg shadow-red-500/30"
                            disabled={isLoading || !email}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                                    Sending reset link...
                                </>
                            ) : (
                                <>
                                    <KeyRound className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                                    Send reset link
                                </>
                            )}
                        </Button>

                        <Link href="/login" className="block">
                            <Button
                                type="button"
                                variant="ghost"
                                className="w-full h-10 sm:h-11 text-sm sm:text-base text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                            >
                                <ArrowLeft className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                                Back to login
                            </Button>
                        </Link>
                    </form>

                    <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg">
                        <div className="flex items-start gap-3">
                            <Shield className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Security tip</h3>
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                    For security reasons, we won't reveal whether an email exists in our system. Check your inbox and spam folder.
                                </p>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Right Side - Hero (Hidden on Mobile) */}
            <div className="hidden lg:flex w-full lg:w-1/2 bg-gradient-to-br from-red-500 via-red-600 to-red-700 p-12 items-center justify-center relative overflow-hidden order-1 lg:order-2">
                {/* Animated Background */}
                <div className="absolute inset-0">
                    <motion.div
                        className="absolute top-20 right-20 w-96 h-96 bg-white/10 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.2, 1],
                            x: [0, 50, 0],
                            y: [0, 30, 0],
                        }}
                        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute bottom-20 left-20 w-96 h-96 bg-red-400/20 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.3, 1],
                            x: [0, -50, 0],
                            y: [0, -30, 0],
                        }}
                        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-red-800/20 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.4, 1],
                        }}
                        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    />
                </div>

                {/* Floating Icons */}
                <motion.div
                    className="absolute top-10 left-10 text-white/30"
                    animate={{ y: [0, -20, 0], rotate: [0, 10, 0] }}
                    transition={{ duration: 5, repeat: Infinity }}
                >
                    <Lock className="w-12 h-12" />
                </motion.div>
                <motion.div
                    className="absolute top-20 right-16 text-white/30"
                    animate={{ y: [0, 15, 0], rotate: [0, -10, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                >
                    <KeyRound className="w-10 h-10" />
                </motion.div>
                <motion.div
                    className="absolute bottom-20 left-16 text-white/30"
                    animate={{ y: [0, -15, 0], x: [0, 10, 0] }}
                    transition={{ duration: 6, repeat: Infinity }}
                >
                    <Sparkles className="w-14 h-14" />
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.7 }}
                    className="relative z-10 text-white max-w-lg"
                >
                    <div className="mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl backdrop-blur-sm mb-6">
                            <Shield className="w-8 h-8" />
                        </div>
                    </div>
                    <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                        Secure Password Recovery
                    </h2>
                    <p className="text-lg lg:text-xl text-white/90 mb-8">
                        We take your account security seriously. Follow the simple steps to regain access to your account safely.
                    </p>
                    <div className="space-y-4">
                        {[
                            "Instant email verification",
                            "Secure reset link generation",
                            "One-time use tokens",
                            "24/7 support available",
                        ].map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3 + index * 0.1 }}
                                className="flex items-center gap-3"
                            >
                                <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                </div>
                                <span className="text-base lg:text-lg">{feature}</span>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
