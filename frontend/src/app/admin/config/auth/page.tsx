"use client"

import { useState, useEffect, useCallback } from "react"
import { Shield, Key, Lock, Clock } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { configApi, type AuthConfig } from "@/lib/api/admin"

const defaultConfig: AuthConfig = {
    jwt_access_token_expire_minutes: 15,
    jwt_refresh_token_expire_days: 7,
    password_min_length: 8,
    password_require_uppercase: true,
    password_require_lowercase: true,
    password_require_digit: true,
    password_require_special: true,
    max_login_attempts: 5,
    lockout_duration_minutes: 30,
    require_email_verification: true,
    allow_social_login: true,
    admin_require_2fa: true,
    session_timeout_minutes: 60,
}

export default function AuthConfigPage() {
    const [config, setConfig] = useState<AuthConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<AuthConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getAuthConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch auth config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateAuthConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof AuthConfig>(key: K, value: AuthConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    return (
        <ConfigFormWrapper
            title="Authentication Configuration"
            description="Configure JWT settings, password policies, and login security options."
            icon={<Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* JWT Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Key className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">JWT Settings</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="jwt_access_token_expire_minutes">
                                Access Token Expiry (minutes)
                            </Label>
                            <Input
                                id="jwt_access_token_expire_minutes"
                                type="number"
                                min={1}
                                max={60}
                                value={config.jwt_access_token_expire_minutes}
                                onChange={(e) =>
                                    updateConfig("jwt_access_token_expire_minutes", parseInt(e.target.value) || 15)
                                }
                            />
                            <p className="text-xs text-slate-500">1-60 minutes</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="jwt_refresh_token_expire_days">
                                Refresh Token Expiry (days)
                            </Label>
                            <Input
                                id="jwt_refresh_token_expire_days"
                                type="number"
                                min={1}
                                max={30}
                                value={config.jwt_refresh_token_expire_days}
                                onChange={(e) =>
                                    updateConfig("jwt_refresh_token_expire_days", parseInt(e.target.value) || 7)
                                }
                            />
                            <p className="text-xs text-slate-500">1-30 days</p>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Password Policy */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Lock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Password Policy</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="password_min_length">Minimum Password Length</Label>
                            <Input
                                id="password_min_length"
                                type="number"
                                min={6}
                                max={32}
                                value={config.password_min_length}
                                onChange={(e) =>
                                    updateConfig("password_min_length", parseInt(e.target.value) || 8)
                                }
                                className="max-w-[200px]"
                            />
                            <p className="text-xs text-slate-500">6-32 characters</p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="password_require_uppercase">Require Uppercase</Label>
                                    <p className="text-xs text-slate-500">At least one uppercase letter</p>
                                </div>
                                <Switch
                                    id="password_require_uppercase"
                                    checked={config.password_require_uppercase}
                                    onCheckedChange={(checked) =>
                                        updateConfig("password_require_uppercase", checked)
                                    }
                                />
                            </div>
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="password_require_lowercase">Require Lowercase</Label>
                                    <p className="text-xs text-slate-500">At least one lowercase letter</p>
                                </div>
                                <Switch
                                    id="password_require_lowercase"
                                    checked={config.password_require_lowercase}
                                    onCheckedChange={(checked) =>
                                        updateConfig("password_require_lowercase", checked)
                                    }
                                />
                            </div>
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="password_require_digit">Require Digit</Label>
                                    <p className="text-xs text-slate-500">At least one number</p>
                                </div>
                                <Switch
                                    id="password_require_digit"
                                    checked={config.password_require_digit}
                                    onCheckedChange={(checked) =>
                                        updateConfig("password_require_digit", checked)
                                    }
                                />
                            </div>
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="password_require_special">Require Special Character</Label>
                                    <p className="text-xs text-slate-500">At least one special character</p>
                                </div>
                                <Switch
                                    id="password_require_special"
                                    checked={config.password_require_special}
                                    onCheckedChange={(checked) =>
                                        updateConfig("password_require_special", checked)
                                    }
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Login Security */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Login Security</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_login_attempts">Max Login Attempts</Label>
                                <Input
                                    id="max_login_attempts"
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={config.max_login_attempts}
                                    onChange={(e) =>
                                        updateConfig("max_login_attempts", parseInt(e.target.value) || 5)
                                    }
                                />
                                <p className="text-xs text-slate-500">Before account lockout</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="lockout_duration_minutes">Lockout Duration (minutes)</Label>
                                <Input
                                    id="lockout_duration_minutes"
                                    type="number"
                                    min={1}
                                    max={1440}
                                    value={config.lockout_duration_minutes}
                                    onChange={(e) =>
                                        updateConfig("lockout_duration_minutes", parseInt(e.target.value) || 30)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-1440 minutes</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="session_timeout_minutes">Session Timeout (minutes)</Label>
                                <Input
                                    id="session_timeout_minutes"
                                    type="number"
                                    min={5}
                                    max={1440}
                                    value={config.session_timeout_minutes}
                                    onChange={(e) =>
                                        updateConfig("session_timeout_minutes", parseInt(e.target.value) || 60)
                                    }
                                />
                                <p className="text-xs text-slate-500">5-1440 minutes</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="require_email_verification">Email Verification</Label>
                                    <p className="text-xs text-slate-500">Require email verification for new users</p>
                                </div>
                                <Switch
                                    id="require_email_verification"
                                    checked={config.require_email_verification}
                                    onCheckedChange={(checked) =>
                                        updateConfig("require_email_verification", checked)
                                    }
                                />
                            </div>
                            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                <div>
                                    <Label htmlFor="allow_social_login">Social Login</Label>
                                    <p className="text-xs text-slate-500">Allow Google and other social logins</p>
                                </div>
                                <Switch
                                    id="allow_social_login"
                                    checked={config.allow_social_login}
                                    onCheckedChange={(checked) =>
                                        updateConfig("allow_social_login", checked)
                                    }
                                />
                            </div>
                            <div className="flex items-center justify-between p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                                <div>
                                    <Label htmlFor="admin_require_2fa">Admin 2FA Required</Label>
                                    <p className="text-xs text-amber-600 dark:text-amber-400">
                                        Require 2FA for all admin users
                                    </p>
                                </div>
                                <Switch
                                    id="admin_require_2fa"
                                    checked={config.admin_require_2fa}
                                    onCheckedChange={(checked) =>
                                        updateConfig("admin_require_2fa", checked)
                                    }
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
