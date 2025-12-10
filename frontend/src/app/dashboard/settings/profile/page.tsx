"use client"

import { useState, useEffect, useRef } from "react"
import {
    User,
    Lock,
    Shield,
    Eye,
    EyeOff,
    Loader2,
    Check,
    Copy,
    Smartphone,
} from "lucide-react"
import QRCode from "qrcode"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Alert,
    AlertDescription,
} from "@/components/ui/alert"
import { authApi } from "@/lib/api/auth"
import type { AuthUser, TwoFactorSetup } from "@/types/auth"

export default function ProfileSettingsPage() {
    const [profile, setProfile] = useState<AuthUser | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saveSuccess, setSaveSuccess] = useState(false)

    // Profile form
    const [name, setName] = useState("")

    // Password form
    const [currentPassword, setCurrentPassword] = useState("")
    const [newPassword, setNewPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [showCurrentPassword, setShowCurrentPassword] = useState(false)
    const [showNewPassword, setShowNewPassword] = useState(false)
    const [changingPassword, setChangingPassword] = useState(false)
    const [passwordError, setPasswordError] = useState("")
    const [passwordSuccess, setPasswordSuccess] = useState(false)

    // 2FA state
    const [twoFactorSetup, setTwoFactorSetup] = useState<TwoFactorSetup | null>(null)
    const [twoFactorCode, setTwoFactorCode] = useState("")
    const [backupCodes, setBackupCodes] = useState<string[]>([])
    const [showBackupCodes, setShowBackupCodes] = useState(false)
    const [enabling2FA, setEnabling2FA] = useState(false)
    const [disabling2FA, setDisabling2FA] = useState(false)
    const [disable2FACode, setDisable2FACode] = useState("")
    const [show2FASetupDialog, setShow2FASetupDialog] = useState(false)
    const [show2FADisableDialog, setShow2FADisableDialog] = useState(false)
    const [twoFactorError, setTwoFactorError] = useState("")
    const qrCanvasRef = useRef<HTMLCanvasElement>(null)

    useEffect(() => {
        loadProfile()
    }, [])

    // Generate QR code when twoFactorSetup changes and dialog is open
    useEffect(() => {
        if (twoFactorSetup?.qrCodeUrl && show2FASetupDialog && !showBackupCodes) {
            // Small delay to ensure canvas is mounted
            const timer = setTimeout(() => {
                if (qrCanvasRef.current) {
                    QRCode.toCanvas(qrCanvasRef.current, twoFactorSetup.qrCodeUrl, {
                        width: 200,
                        margin: 2,
                        color: {
                            dark: "#000000",
                            light: "#ffffff",
                        },
                    }).catch(console.error)
                }
            }, 100)
            return () => clearTimeout(timer)
        }
    }, [twoFactorSetup, show2FASetupDialog, showBackupCodes])

    const loadProfile = async () => {
        try {
            setLoading(true)
            const data = await authApi.getCurrentUser()
            setProfile(data)
            setName(data.name)
        } catch (error) {
            console.error("Failed to load profile:", error)
            // Mock data for development
            const mockProfile: AuthUser = {
                id: "user-1",
                email: "user@example.com",
                name: "John Doe",
                is2FAEnabled: false,
                createdAt: new Date().toISOString(),
                lastLoginAt: new Date().toISOString(),
            }
            setProfile(mockProfile)
            setName(mockProfile.name)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveProfile = async () => {
        if (!name.trim()) return
        try {
            setSaving(true)
            setSaveSuccess(false)
            // API call would go here
            // await authApi.updateProfile({ name: name.trim() })
            setProfile((prev) => prev ? { ...prev, name: name.trim() } : null)
            setSaveSuccess(true)
            setTimeout(() => setSaveSuccess(false), 3000)
        } catch (error) {
            console.error("Failed to update profile:", error)
        } finally {
            setSaving(false)
        }
    }

    const handleChangePassword = async () => {
        setPasswordError("")
        setPasswordSuccess(false)

        if (!currentPassword || !newPassword || !confirmPassword) {
            setPasswordError("Please fill in all password fields")
            return
        }

        if (newPassword !== confirmPassword) {
            setPasswordError("New passwords do not match")
            return
        }

        if (newPassword.length < 8) {
            setPasswordError("Password must be at least 8 characters")
            return
        }

        try {
            setChangingPassword(true)
            await authApi.changePassword(currentPassword, newPassword)
            setPasswordSuccess(true)
            setCurrentPassword("")
            setNewPassword("")
            setConfirmPassword("")
        } catch (error: unknown) {
            const err = error as { message?: string }
            setPasswordError(err.message || "Failed to change password")
        } finally {
            setChangingPassword(false)
        }
    }

    const handleEnable2FA = async () => {
        try {
            setEnabling2FA(true)
            setTwoFactorError("")
            const setup = await authApi.enable2FA()
            setTwoFactorSetup(setup)
            setShow2FASetupDialog(true)
        } catch (error) {
            console.error("Failed to enable 2FA:", error)
        } finally {
            setEnabling2FA(false)
        }
    }

    const handleVerify2FASetup = async () => {
        if (!twoFactorCode || twoFactorCode.length !== 6) {
            setTwoFactorError("Please enter a valid 6-digit code")
            return
        }

        try {
            setEnabling2FA(true)
            setTwoFactorError("")
            const result = await authApi.verify2FASetup(twoFactorCode)
            setBackupCodes(result.backupCodes)
            setShowBackupCodes(true)
            setProfile((prev) => prev ? { ...prev, is2FAEnabled: true } : null)
            setTwoFactorCode("")
        } catch (error: unknown) {
            const err = error as { message?: string }
            setTwoFactorError(err.message || "Invalid verification code")
        } finally {
            setEnabling2FA(false)
        }
    }

    const handleDisable2FA = async () => {
        if (!disable2FACode || disable2FACode.length !== 6) {
            setTwoFactorError("Please enter a valid 6-digit code")
            return
        }

        try {
            setDisabling2FA(true)
            setTwoFactorError("")
            await authApi.disable2FA(disable2FACode)
            setProfile((prev) => prev ? { ...prev, is2FAEnabled: false } : null)
            setShow2FADisableDialog(false)
            setDisable2FACode("")
        } catch (error: unknown) {
            const err = error as { message?: string }
            setTwoFactorError(err.message || "Invalid verification code")
        } finally {
            setDisabling2FA(false)
        }
    }

    const copyBackupCodes = () => {
        navigator.clipboard.writeText(backupCodes.join("\n"))
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Settings", href: "/dashboard/settings" },
                    { label: "Profile" },
                ]}
            >
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Settings", href: "/dashboard/settings" },
                { label: "Profile" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <User className="h-8 w-8" />
                        Profile Settings
                    </h1>
                    <p className="text-muted-foreground">
                        Manage your account information and security settings
                    </p>
                </div>

                {/* Two Column Layout */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Profile Information - Left Column */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <User className="h-5 w-5" />
                                Profile Information
                            </CardTitle>
                            <CardDescription>
                                Update your personal information
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {saveSuccess && (
                                <Alert>
                                    <Check className="h-4 w-4" />
                                    <AlertDescription>Profile updated successfully!</AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={profile?.email || ""}
                                    disabled
                                    className="bg-muted"
                                />
                                <p className="text-xs text-muted-foreground">
                                    Email cannot be changed
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="name">Display Name</Label>
                                <Input
                                    id="name"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Enter your name"
                                />
                            </div>
                            <Button
                                onClick={handleSaveProfile}
                                disabled={saving || name === profile?.name}
                                className="w-full"
                            >
                                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Save Changes
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Change Password - Right Column */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Lock className="h-5 w-5" />
                                Change Password
                            </CardTitle>
                            <CardDescription>
                                Update your password to keep your account secure
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {passwordError && (
                                <Alert variant="destructive">
                                    <AlertDescription>{passwordError}</AlertDescription>
                                </Alert>
                            )}
                            {passwordSuccess && (
                                <Alert>
                                    <Check className="h-4 w-4" />
                                    <AlertDescription>Password changed successfully!</AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="currentPassword">Current Password</Label>
                                <div className="relative">
                                    <Input
                                        id="currentPassword"
                                        type={showCurrentPassword ? "text" : "password"}
                                        value={currentPassword}
                                        onChange={(e) => setCurrentPassword(e.target.value)}
                                        placeholder="Enter current password"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3"
                                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                    >
                                        {showCurrentPassword ? (
                                            <EyeOff className="h-4 w-4" />
                                        ) : (
                                            <Eye className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="newPassword">New Password</Label>
                                <div className="relative">
                                    <Input
                                        id="newPassword"
                                        type={showNewPassword ? "text" : "password"}
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        placeholder="Enter new password"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3"
                                        onClick={() => setShowNewPassword(!showNewPassword)}
                                    >
                                        {showNewPassword ? (
                                            <EyeOff className="h-4 w-4" />
                                        ) : (
                                            <Eye className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                                <Input
                                    id="confirmPassword"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="Confirm new password"
                                />
                            </div>
                            <Button
                                onClick={handleChangePassword}
                                disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
                                className="w-full"
                            >
                                {changingPassword && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Change Password
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* Two-Factor Authentication - Full Width */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5" />
                            Two-Factor Authentication
                        </CardTitle>
                        <CardDescription>
                            Add an extra layer of security to your account
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 border rounded-lg">
                            <div className="flex items-center gap-4">
                                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                    <Smartphone className="h-6 w-6 text-primary" />
                                </div>
                                <div>
                                    <p className="font-medium">Authenticator App</p>
                                    <p className="text-sm text-muted-foreground">
                                        Use an authenticator app like Google Authenticator or Authy to generate verification codes
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                {profile?.is2FAEnabled ? (
                                    <>
                                        <Badge variant="default" className="bg-green-500">Enabled</Badge>
                                        <Button
                                            variant="destructive"
                                            onClick={() => setShow2FADisableDialog(true)}
                                        >
                                            Disable
                                        </Button>
                                    </>
                                ) : (
                                    <>
                                        <Badge variant="secondary">Disabled</Badge>
                                        <Button onClick={handleEnable2FA} disabled={enabling2FA}>
                                            {enabling2FA && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                            Enable 2FA
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>


            {/* 2FA Setup Dialog */}
            <Dialog open={show2FASetupDialog} onOpenChange={setShow2FASetupDialog}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>
                            {showBackupCodes ? "Save Your Backup Codes" : "Set Up Two-Factor Authentication"}
                        </DialogTitle>
                        <DialogDescription>
                            {showBackupCodes
                                ? "Save these backup codes in a secure location. You can use them to access your account if you lose your authenticator device."
                                : "Scan the QR code with your authenticator app, then enter the verification code."}
                        </DialogDescription>
                    </DialogHeader>
                    {showBackupCodes ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-2 p-4 bg-muted rounded-lg font-mono text-sm">
                                {backupCodes.map((code, index) => (
                                    <div key={index} className="text-center py-1">
                                        {code}
                                    </div>
                                ))}
                            </div>
                            <Button
                                variant="outline"
                                className="w-full"
                                onClick={copyBackupCodes}
                            >
                                <Copy className="mr-2 h-4 w-4" />
                                Copy Codes
                            </Button>
                            <DialogFooter>
                                <Button
                                    onClick={() => {
                                        setShow2FASetupDialog(false)
                                        setShowBackupCodes(false)
                                        setTwoFactorSetup(null)
                                    }}
                                >
                                    Done
                                </Button>
                            </DialogFooter>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {twoFactorSetup && (
                                <>
                                    <div className="flex justify-center">
                                        <div className="p-4 bg-white rounded-lg shadow-sm border">
                                            <canvas ref={qrCanvasRef} className="w-[200px] h-[200px]" />
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-xs text-muted-foreground mb-1">
                                            Or enter this code manually:
                                        </p>
                                        <code className="text-sm bg-muted px-3 py-1.5 rounded font-mono break-all">
                                            {twoFactorSetup.secret}
                                        </code>
                                    </div>
                                </>
                            )}
                            {twoFactorError && (
                                <Alert variant="destructive">
                                    <AlertDescription>{twoFactorError}</AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label>Verification Code</Label>
                                <Input
                                    value={twoFactorCode}
                                    onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                                    placeholder="Enter 6-digit code"
                                    maxLength={6}
                                    className="text-center text-lg tracking-widest"
                                />
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setShow2FASetupDialog(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={handleVerify2FASetup} disabled={enabling2FA}>
                                    {enabling2FA && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Verify & Enable
                                </Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Disable 2FA Dialog */}
            <Dialog open={show2FADisableDialog} onOpenChange={setShow2FADisableDialog}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
                        <DialogDescription>
                            Enter your verification code to disable 2FA. This will make your account less secure.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        {twoFactorError && (
                            <Alert variant="destructive">
                                <AlertDescription>{twoFactorError}</AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label>Verification Code</Label>
                            <Input
                                value={disable2FACode}
                                onChange={(e) => setDisable2FACode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                                placeholder="Enter 6-digit code"
                                maxLength={6}
                                className="text-center text-lg tracking-widest"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShow2FADisableDialog(false)}>
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDisable2FA}
                            disabled={disabling2FA}
                        >
                            {disabling2FA && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Disable 2FA
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
