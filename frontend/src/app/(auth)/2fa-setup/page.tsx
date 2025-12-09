"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Loader2, Copy, Check, Download, Shield, Smartphone, Key } from "lucide-react"
import { Button, Input, Label, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui"
import authApi from "@/lib/api/auth"
import type { TwoFactorSetup } from "@/types/auth"

type SetupStep = "intro" | "qr" | "verify" | "backup" | "complete"

export default function TwoFactorSetupPage() {
    const router = useRouter()

    const [step, setStep] = useState<SetupStep>("intro")
    const [setupData, setSetupData] = useState<TwoFactorSetup | null>(null)
    const [verificationCode, setVerificationCode] = useState("")
    const [backupCodes, setBackupCodes] = useState<string[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [copiedSecret, setCopiedSecret] = useState(false)
    const [copiedBackup, setCopiedBackup] = useState(false)

    const startSetup = async () => {
        setIsLoading(true)
        setError("")

        try {
            const data = await authApi.enable2FA()
            setSetupData(data)
            setStep("qr")
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to start 2FA setup")
        } finally {
            setIsLoading(false)
        }
    }

    const verifyCode = async () => {
        if (verificationCode.length !== 6) return

        setIsLoading(true)
        setError("")

        try {
            const result = await authApi.verify2FASetup(verificationCode)
            setBackupCodes(result.backupCodes)
            setStep("backup")
        } catch (err) {
            setError(err instanceof Error ? err.message : "Invalid verification code")
        } finally {
            setIsLoading(false)
        }
    }

    const copySecret = async () => {
        if (!setupData?.secret) return
        await navigator.clipboard.writeText(setupData.secret)
        setCopiedSecret(true)
        setTimeout(() => setCopiedSecret(false), 2000)
    }

    const copyBackupCodes = async () => {
        const codesText = backupCodes.join("\n")
        await navigator.clipboard.writeText(codesText)
        setCopiedBackup(true)
        setTimeout(() => setCopiedBackup(false), 2000)
    }

    const downloadBackupCodes = () => {
        const codesText = `YouTube Automation Platform - Backup Codes\n${"=".repeat(50)}\n\nStore these codes in a safe place. Each code can only be used once.\n\n${backupCodes.map((code, i) => `${i + 1}. ${code}`).join("\n")}\n\nGenerated: ${new Date().toISOString()}`

        const blob = new Blob([codesText], { type: "text/plain" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = "backup-codes.txt"
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const completeSetup = () => {
        setStep("complete")
        setTimeout(() => {
            router.push("/dashboard")
        }, 2000)
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <Card className="w-full max-w-lg mx-auto">
                {/* Step: Introduction */}
                {step === "intro" && (
                    <>
                        <CardHeader className="text-center">
                            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                                <Shield className="h-6 w-6 text-primary" />
                            </div>
                            <CardTitle className="text-2xl">Enable Two-Factor Authentication</CardTitle>
                            <CardDescription>
                                Add an extra layer of security to your account
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-3">
                                <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                                    <Smartphone className="h-5 w-5 text-muted-foreground mt-0.5" />
                                    <div>
                                        <p className="font-medium text-sm">Authenticator App Required</p>
                                        <p className="text-sm text-muted-foreground">
                                            You&apos;ll need an authenticator app like Google Authenticator, Authy, or 1Password.
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                                    <Key className="h-5 w-5 text-muted-foreground mt-0.5" />
                                    <div>
                                        <p className="font-medium text-sm">Backup Codes</p>
                                        <p className="text-sm text-muted-foreground">
                                            You&apos;ll receive backup codes in case you lose access to your authenticator.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="flex flex-col gap-3">
                            <Button onClick={startSetup} className="w-full" disabled={isLoading}>
                                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Get Started
                            </Button>
                            <Button variant="ghost" onClick={() => router.back()} className="w-full">
                                Cancel
                            </Button>
                        </CardFooter>
                    </>
                )}

                {/* Step: QR Code */}
                {step === "qr" && setupData && (
                    <>
                        <CardHeader className="text-center">
                            <CardTitle>Scan QR Code</CardTitle>
                            <CardDescription>
                                Scan this QR code with your authenticator app
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {error && (
                                <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                                    {error}
                                </div>
                            )}

                            {/* QR Code Display */}
                            <div className="flex justify-center">
                                <div className="p-4 bg-white rounded-lg">
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                    <img
                                        src={setupData.qrCodeUrl}
                                        alt="2FA QR Code"
                                        className="w-48 h-48"
                                    />
                                </div>
                            </div>

                            {/* Manual Entry Option */}
                            <div className="space-y-2">
                                <p className="text-sm text-muted-foreground text-center">
                                    Can&apos;t scan? Enter this code manually:
                                </p>
                                <div className="flex items-center gap-2">
                                    <code className="flex-1 p-2 bg-muted rounded text-sm font-mono text-center break-all">
                                        {setupData.secret}
                                    </code>
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={copySecret}
                                    >
                                        {copiedSecret ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter>
                            <Button onClick={() => setStep("verify")} className="w-full">
                                Continue
                            </Button>
                        </CardFooter>
                    </>
                )}

                {/* Step: Verify */}
                {step === "verify" && (
                    <>
                        <CardHeader className="text-center">
                            <CardTitle>Verify Setup</CardTitle>
                            <CardDescription>
                                Enter the 6-digit code from your authenticator app
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {error && (
                                <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                                    {error}
                                </div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="code">Verification Code</Label>
                                <Input
                                    id="code"
                                    type="text"
                                    inputMode="numeric"
                                    pattern="[0-9]*"
                                    maxLength={6}
                                    placeholder="000000"
                                    value={verificationCode}
                                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))}
                                    className="text-center text-2xl tracking-widest"
                                    autoFocus
                                />
                            </div>
                        </CardContent>
                        <CardFooter className="flex flex-col gap-3">
                            <Button
                                onClick={verifyCode}
                                className="w-full"
                                disabled={isLoading || verificationCode.length !== 6}
                            >
                                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Verify
                            </Button>
                            <Button variant="ghost" onClick={() => setStep("qr")} className="w-full">
                                Back
                            </Button>
                        </CardFooter>
                    </>
                )}

                {/* Step: Backup Codes */}
                {step === "backup" && (
                    <>
                        <CardHeader className="text-center">
                            <CardTitle>Save Backup Codes</CardTitle>
                            <CardDescription>
                                Store these codes safely. Each can only be used once.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="p-4 bg-muted rounded-lg">
                                <div className="grid grid-cols-2 gap-2">
                                    {backupCodes.map((code, index) => (
                                        <code
                                            key={index}
                                            className="p-2 bg-background rounded text-sm font-mono text-center"
                                        >
                                            {code}
                                        </code>
                                    ))}
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    onClick={copyBackupCodes}
                                    className="flex-1"
                                >
                                    {copiedBackup ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
                                    Copy
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={downloadBackupCodes}
                                    className="flex-1"
                                >
                                    <Download className="mr-2 h-4 w-4" />
                                    Download
                                </Button>
                            </div>

                            <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg">
                                <p className="text-sm text-warning-foreground">
                                    <strong>Important:</strong> If you lose access to your authenticator app and don&apos;t have these codes, you won&apos;t be able to access your account.
                                </p>
                            </div>
                        </CardContent>
                        <CardFooter>
                            <Button onClick={completeSetup} className="w-full">
                                I&apos;ve saved my backup codes
                            </Button>
                        </CardFooter>
                    </>
                )}

                {/* Step: Complete */}
                {step === "complete" && (
                    <CardContent className="py-8">
                        <div className="text-center space-y-4">
                            <div className="mx-auto w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                                <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
                            </div>
                            <h2 className="text-xl font-semibold">2FA Enabled!</h2>
                            <p className="text-muted-foreground">
                                Your account is now more secure. Redirecting...
                            </p>
                        </div>
                    </CardContent>
                )}
            </Card>
        </motion.div>
    )
}
