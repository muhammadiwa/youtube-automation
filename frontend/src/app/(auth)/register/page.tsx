"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Eye, EyeOff, Mail, Lock, User, Loader2, Check, X, Play, ArrowRight, Sparkles, Shield, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { useAuth } from "@/hooks/use-auth"
import { calculatePasswordStrength, getStrengthLabel } from "@/lib/utils/password"

export default function RegisterPage() {
    const router = useRouter()
    const { register } = useAuth()

    const [name, setName] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [acceptTerms, setAcceptTerms] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState(false)

    const passwordStrength = useMemo(() => calculatePasswordStrength(password), [password])
    const passwordsMatch = password === confirmPassword && confirmPassword.length > 0

    const isFormValid = useMemo(() => {
        return (
            name.trim().length >= 2 &&
            email.includes("@") &&
            passwordStrength.isValid &&
            passwordsMatch &&
            acceptTerms
        )
    }, [name, email, passwordStrength.isValid, passwordsMatch, acceptTerms])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")

        if (!isFormValid) {
            setError("Please fill in all fields correctly")
            return
        }

        setIsLoading(true)

        try {
            await register({ email, password, name, acceptTerms })
            setSuccess(true)
            setTimeout(() => {
                router.push("/login")
            }, 2000)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Registration failed. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    if (success) {
        return (
            <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-orange-50 to-red-50 dark:from-gray-950 dark:to-orange-950 p-4">
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
                        className="mx-auto w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-orange-500/30"
                    >
                        <Check className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                    </motion.div>
                    <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-3">Account Created!</h2>
                    <p className="text-gray-600 dark:text-gray-400 text-base sm:text-lg mb-6">
                        Welcome aboard! Redirecting you to login...
                    </p>
                    <div className="flex justify-center gap-2">
                        {[0, 1, 2].map((i) => (
                            <motion.div
                                key={i}
                                className="w-2 h-2 bg-orange-500 rounded-full"
                                animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                                transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                            />
                        ))}
                    </div>
                </motion.div>
            </div>
        )
    }

    return (
        <div className="min-h-screen w-full flex flex-col lg:flex-row">
            {/* Left Side - Hero (Hidden on Mobile) */}
            <div className="hidden lg:flex w-full lg:w-1/2 bg-gradient-to-br from-orange-500 via-orange-600 to-red-500 p-12 items-center justify-center relative overflow-hidden">
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
                        className="absolute bottom-20 left-20 w-96 h-96 bg-yellow-500/20 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.3, 1],
                            x: [0, -50, 0],
                            y: [0, -30, 0],
                        }}
                        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-red-500/20 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.4, 1],
                        }}
                        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    />
                </div>

                {/* Floating Icons */}
                <motion.div
                    className="absolute top-10 right-10 text-white/30"
                    animate={{ y: [0, -20, 0], rotate: [0, 15, 0] }}
                    transition={{ duration: 5, repeat: Infinity }}
                >
                    <Sparkles className="w-12 h-12" />
                </motion.div>
                <motion.div
                    className="absolute bottom-10 left-10 text-white/30"
                    animate={{ y: [0, 20, 0], rotate: [0, -15, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                >
                    <Zap className="w-10 h-10" />
                </motion.div>
                <motion.div
                    className="absolute top-1/3 left-10 text-white/30"
                    animate={{ y: [0, 15, 0], x: [0, 10, 0] }}
                    transition={{ duration: 6, repeat: Infinity }}
                >
                    <Shield className="w-14 h-14" />
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.7 }}
                    className="relative z-10 text-white max-w-lg"
                >
                    <h2 className="text-4xl lg:text-5xl font-bold mb-6">
                        Start Your Journey Today
                    </h2>
                    <p className="text-lg lg:text-xl text-white/90 mb-8">
                        Join thousands of creators who are automating their YouTube success with our powerful platform.
                    </p>
                    <div className="space-y-4">
                        {[
                            "Free to start, upgrade anytime",
                            "No credit card required",
                            "24/7 customer support",
                            "Cancel anytime",
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

            {/* Right Side - Form (Mobile First) */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 lg:p-12 bg-white dark:bg-gray-950 min-h-screen lg:min-h-0">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-md"
                >
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/30">
                            <Play className="w-5 h-5 sm:w-6 sm:h-6 text-white fill-white" />
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">YouTube Auto</h1>
                            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Create your account</p>
                        </div>
                    </div>

                    {/* Welcome Text */}
                    <div className="mb-6">
                        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">Get started free</h2>
                        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">Create your account and start managing your channels</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
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
                            <Label htmlFor="name" className="text-gray-700 dark:text-gray-300 mb-2 block text-sm sm:text-base">
                                Full Name
                            </Label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                                <Input
                                    id="name"
                                    type="text"
                                    placeholder="John Doe"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="pl-9 sm:pl-10 h-10 sm:h-11 text-sm sm:text-base bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 focus:border-orange-500 focus:ring-orange-500"
                                    required
                                />
                            </div>
                        </div>

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
                                    className="pl-9 sm:pl-10 h-10 sm:h-11 text-sm sm:text-base bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 focus:border-orange-500 focus:ring-orange-500"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <Label htmlFor="password" className="text-gray-700 dark:text-gray-300 mb-2 block text-sm sm:text-base">
                                Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="pl-9 sm:pl-10 pr-9 sm:pr-10 h-10 sm:h-11 text-sm sm:text-base bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 focus:border-orange-500 focus:ring-orange-500"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4 sm:h-5 sm:w-5" /> : <Eye className="h-4 w-4 sm:h-5 sm:w-5" />}
                                </button>
                            </div>

                            {password && (
                                <div className="mt-2 space-y-2">
                                    <div className="flex gap-1">
                                        {[0, 1, 2, 3].map((index) => (
                                            <div
                                                key={index}
                                                className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${index < passwordStrength.score
                                                    ? passwordStrength.score === 1
                                                        ? "bg-red-500"
                                                        : passwordStrength.score === 2
                                                            ? "bg-yellow-500"
                                                            : passwordStrength.score === 3
                                                                ? "bg-orange-500"
                                                                : "bg-green-500"
                                                    : "bg-gray-200 dark:bg-gray-800"
                                                    }`}
                                            />
                                        ))}
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">
                                        Strength: <span className="font-semibold">{getStrengthLabel(passwordStrength.score)}</span>
                                    </p>
                                    {passwordStrength.feedback.length > 0 && (
                                        <ul className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                                            {passwordStrength.feedback.slice(0, 2).map((item, index) => (
                                                <li key={index} className="flex items-center gap-1">
                                                    <X className="h-3 w-3 text-red-500 flex-shrink-0" />
                                                    <span className="line-clamp-1">{item}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            )}
                        </div>

                        <div>
                            <Label htmlFor="confirmPassword" className="text-gray-700 dark:text-gray-300 mb-2 block text-sm sm:text-base">
                                Confirm Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                                <Input
                                    id="confirmPassword"
                                    type={showConfirmPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="pl-9 sm:pl-10 pr-9 sm:pr-10 h-10 sm:h-11 text-sm sm:text-base bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 focus:border-orange-500 focus:ring-orange-500"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                >
                                    {showConfirmPassword ? <EyeOff className="h-4 w-4 sm:h-5 sm:w-5" /> : <Eye className="h-4 w-4 sm:h-5 sm:w-5" />}
                                </button>
                            </div>
                            {confirmPassword && (
                                <p
                                    className={`text-xs flex items-center gap-1 mt-2 ${passwordsMatch ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                                        }`}
                                >
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

                        <div className="flex items-start space-x-3 pt-2">
                            <Checkbox
                                id="terms"
                                checked={acceptTerms}
                                onCheckedChange={setAcceptTerms}
                                className="mt-0.5 border-gray-300 data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
                            />
                            <Label htmlFor="terms" className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 leading-tight cursor-pointer">
                                I agree to the{" "}
                                <Link href="/terms" className="text-orange-600 dark:text-orange-400 hover:underline">
                                    Terms of Service
                                </Link>{" "}
                                and{" "}
                                <Link href="/privacy" className="text-orange-600 dark:text-orange-400 hover:underline">
                                    Privacy Policy
                                </Link>
                            </Label>
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-10 sm:h-11 text-sm sm:text-base bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-medium shadow-lg shadow-orange-500/30"
                            disabled={isLoading || !isFormValid}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    Create Account
                                    <ArrowRight className="ml-2 h-4 w-4 sm:h-5 sm:w-5" />
                                </>
                            )}
                        </Button>

                        <div className="relative my-4">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-200 dark:border-gray-800"></div>
                            </div>
                            <div className="relative flex justify-center text-xs sm:text-sm">
                                <span className="px-4 bg-white dark:bg-gray-950 text-gray-500">Or continue with</span>
                            </div>
                        </div>

                        <Button
                            type="button"
                            variant="outline"
                            className="w-full h-10 sm:h-11 text-sm sm:text-base border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900"
                        >
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 mr-2" viewBox="0 0 24 24">
                                <path
                                    fill="#4285F4"
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                />
                                <path
                                    fill="#34A853"
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                />
                                <path
                                    fill="#FBBC05"
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                />
                                <path
                                    fill="#EA4335"
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                />
                            </svg>
                            Continue with Google
                        </Button>
                    </form>

                    <p className="mt-6 text-center text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                        Already have an account?{" "}
                        <Link href="/login" className="text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 font-semibold">
                            Sign in
                        </Link>
                    </p>
                </motion.div>
            </div>
        </div>
    )
}
