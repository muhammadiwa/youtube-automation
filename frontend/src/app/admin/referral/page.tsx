"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Users,
    Gift,
    DollarSign,
    Save,
    RefreshCcw,
    AlertCircle,
    CheckCircle,
    Settings,
    Trophy,
    Percent,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type {
    ReferralProgramConfig,
    ReferralProgramConfigUpdate,
    PromotionAnalyticsResponse
} from "@/types/admin"
import { useToast } from "@/components/ui/toast"

function StatsCard({
    title,
    value,
    icon: Icon,
    gradient,
    delay = 0,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    gradient: string
    delay?: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay }}
        >
            <Card className="relative overflow-hidden border border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-all duration-300 group bg-white dark:bg-slate-900">
                <div className={cn("absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity bg-gradient-to-br", gradient)} />
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                            <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
                        </div>
                        <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm",
                            gradient
                        )}>
                            <Icon className="h-5 w-5 text-white" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}


export default function AdminReferralProgramPage() {
    const { addToast } = useToast()
    const [config, setConfig] = useState<ReferralProgramConfig | null>(null)
    const [analytics, setAnalytics] = useState<PromotionAnalyticsResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [hasChanges, setHasChanges] = useState(false)
    const [formData, setFormData] = useState<ReferralProgramConfigUpdate>({})

    const fetchData = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const [configRes, analyticsRes] = await Promise.all([
                adminApi.getReferralConfig(),
                adminApi.getPromotionAnalytics(),
            ])
            setConfig(configRes.config)
            setAnalytics(analyticsRes)
            setFormData({
                is_enabled: configRes.config.is_enabled,
                rewards: configRes.config.rewards,
                max_referrals_per_user: configRes.config.max_referrals_per_user,
                referral_code_prefix: configRes.config.referral_code_prefix,
                minimum_subscription_days: configRes.config.minimum_subscription_days,
                eligible_plans: configRes.config.eligible_plans,
            })
        } catch (err) {
            console.error("Failed to fetch referral config:", err)
            setError("Failed to load referral program configuration.")
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const handleSave = async () => {
        setIsSaving(true)
        try {
            const res = await adminApi.updateReferralConfig(formData)
            setConfig(res.config)
            setHasChanges(false)
            addToast({
                type: "success",
                title: "Settings saved",
                description: "Referral program configuration updated successfully.",
            })
        } catch (err) {
            console.error("Failed to save config:", err)
            addToast({
                type: "error",
                title: "Error",
                description: "Failed to save referral program configuration.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    const updateFormData = (updates: Partial<ReferralProgramConfigUpdate>) => {
        setFormData(prev => ({ ...prev, ...updates }))
        setHasChanges(true)
    }

    const updateRewards = (field: string, value: string | number) => {
        setFormData(prev => ({
            ...prev,
            rewards: {
                ...prev.rewards,
                [field]: value,
            },
        }))
        setHasChanges(true)
    }

    const topReferrers = analytics?.top_referrers || []
    const referralStats = analytics?.referral_analytics

    return (
        <AdminLayout breadcrumbs={[
            { label: "Configuration" },
            { label: "Referral Program" }
        ]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Referral Program
                        </h1>
                        <p className="text-muted-foreground">
                            Configure referral rewards and view top referrers
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={fetchData} disabled={isLoading}>
                            <RefreshCcw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
                            Refresh
                        </Button>
                        <Button onClick={handleSave} disabled={!hasChanges || isSaving}>
                            <Save className="h-4 w-4 mr-2" />
                            {isSaving ? "Saving..." : "Save Changes"}
                        </Button>
                    </div>
                </motion.div>

                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-12">
                        <div className="relative">
                            <div className="h-12 w-12 rounded-full border-4 border-violet-500/20 border-t-violet-500 animate-spin" />
                            <Users className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-5 w-5 text-violet-500" />
                        </div>
                        <p className="mt-4 text-muted-foreground">Loading referral program...</p>
                    </div>
                ) : error ? (
                    <Card className="border-red-200 dark:border-red-800">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
                            <p className="text-red-500 mb-4">{error}</p>
                            <Button variant="outline" onClick={fetchData}>Try Again</Button>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        {/* Stats Cards */}
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <StatsCard
                                title="Total Referrals"
                                value={referralStats?.total_referrals || 0}
                                icon={Users}
                                gradient="from-violet-500 to-violet-600"
                                delay={0}
                            />
                            <StatsCard
                                title="Successful"
                                value={referralStats?.successful_referrals || 0}
                                icon={CheckCircle}
                                gradient="from-emerald-500 to-emerald-600"
                                delay={0.05}
                            />
                            <StatsCard
                                title="Conversion Rate"
                                value={`${((referralStats?.conversion_rate || 0) * 100).toFixed(1)}%`}
                                icon={Percent}
                                gradient="from-blue-500 to-blue-600"
                                delay={0.1}
                            />
                            <StatsCard
                                title="Rewards Given"
                                value={`$${(referralStats?.total_rewards_given || 0).toFixed(2)}`}
                                icon={Gift}
                                gradient="from-amber-500 to-amber-600"
                                delay={0.15}
                            />
                        </div>

                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Configuration Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                            >
                                <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                    <CardHeader>
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Settings className="h-5 w-5" />
                                            Program Settings
                                        </CardTitle>
                                        <CardDescription>
                                            Configure referral program behavior
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <Label>Enable Referral Program</Label>
                                                <p className="text-sm text-muted-foreground">Allow users to refer others</p>
                                            </div>
                                            <Switch
                                                checked={formData.is_enabled}
                                                onCheckedChange={(checked) => updateFormData({ is_enabled: checked })}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Referral Code Prefix</Label>
                                            <Input
                                                value={formData.referral_code_prefix || ""}
                                                onChange={(e) => updateFormData({ referral_code_prefix: e.target.value })}
                                                placeholder="REF"
                                                maxLength={10}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Max Referrals Per User</Label>
                                            <Input
                                                type="number"
                                                value={formData.max_referrals_per_user || 0}
                                                onChange={(e) => updateFormData({ max_referrals_per_user: parseInt(e.target.value) || 0 })}
                                                min={0}
                                            />
                                            <p className="text-xs text-muted-foreground">0 for unlimited</p>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Minimum Subscription Days</Label>
                                            <Input
                                                type="number"
                                                value={formData.minimum_subscription_days || 0}
                                                onChange={(e) => updateFormData({ minimum_subscription_days: parseInt(e.target.value) || 0 })}
                                                min={0}
                                            />
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* Rewards Configuration */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.25 }}
                            >
                                <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                    <CardHeader>
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Gift className="h-5 w-5" />
                                            Reward Settings
                                        </CardTitle>
                                        <CardDescription>Configure rewards for referrers and referees</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                                            <h4 className="font-medium flex items-center gap-2">
                                                <DollarSign className="h-4 w-4 text-emerald-500" />
                                                Referrer Reward
                                            </h4>
                                            <div className="grid gap-4 sm:grid-cols-2">
                                                <div className="space-y-2">
                                                    <Label>Reward Type</Label>
                                                    <Select
                                                        value={formData.rewards?.referrer_reward_type || "credit"}
                                                        onValueChange={(value) => updateRewards("referrer_reward_type", value)}
                                                    >
                                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="credit">Account Credit</SelectItem>
                                                            <SelectItem value="discount">Discount %</SelectItem>
                                                            <SelectItem value="free_days">Free Days</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="space-y-2">
                                                    <Label>Reward Value</Label>
                                                    <Input
                                                        type="number"
                                                        value={formData.rewards?.referrer_reward_value || 0}
                                                        onChange={(e) => updateRewards("referrer_reward_value", parseFloat(e.target.value) || 0)}
                                                        min={0}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                        <div className="space-y-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                                            <h4 className="font-medium flex items-center gap-2">
                                                <Users className="h-4 w-4 text-blue-500" />
                                                Referee Reward
                                            </h4>
                                            <div className="grid gap-4 sm:grid-cols-2">
                                                <div className="space-y-2">
                                                    <Label>Reward Type</Label>
                                                    <Select
                                                        value={formData.rewards?.referee_reward_type || "extended_trial"}
                                                        onValueChange={(value) => updateRewards("referee_reward_type", value)}
                                                    >
                                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="credit">Account Credit</SelectItem>
                                                            <SelectItem value="discount">Discount %</SelectItem>
                                                            <SelectItem value="free_days">Free Days</SelectItem>
                                                            <SelectItem value="extended_trial">Extended Trial</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="space-y-2">
                                                    <Label>Reward Value</Label>
                                                    <Input
                                                        type="number"
                                                        value={formData.rewards?.referee_reward_value || 0}
                                                        onChange={(e) => updateRewards("referee_reward_value", parseFloat(e.target.value) || 0)}
                                                        min={0}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Top Referrers Table */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Trophy className="h-5 w-5" />
                                        Top Referrers
                                    </CardTitle>
                                    <CardDescription>Users with the most successful referrals</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {topReferrers.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-12 text-center">
                                            <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                                                <Users className="h-6 w-6 text-muted-foreground" />
                                            </div>
                                            <p className="text-muted-foreground">No referrers yet</p>
                                        </div>
                                    ) : (
                                        <div className="rounded-lg border overflow-hidden">
                                            <Table>
                                                <TableHeader>
                                                    <TableRow className="bg-slate-50 dark:bg-slate-800/50">
                                                        <TableHead className="w-[50px]">#</TableHead>
                                                        <TableHead>User</TableHead>
                                                        <TableHead className="text-center">Referrals</TableHead>
                                                        <TableHead className="text-center">Successful</TableHead>
                                                        <TableHead className="text-right">Rewards Earned</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                    {topReferrers.map((referrer, index) => (
                                                        <TableRow key={referrer.user_id}>
                                                            <TableCell>
                                                                {index < 3 ? (
                                                                    <Badge className={cn(
                                                                        "w-6 h-6 rounded-full flex items-center justify-center p-0",
                                                                        index === 0 && "bg-amber-500",
                                                                        index === 1 && "bg-slate-400",
                                                                        index === 2 && "bg-amber-700"
                                                                    )}>
                                                                        {index + 1}
                                                                    </Badge>
                                                                ) : (
                                                                    <span className="text-muted-foreground">{index + 1}</span>
                                                                )}
                                                            </TableCell>
                                                            <TableCell>
                                                                <div>
                                                                    <p className="font-medium">{referrer.user_name || "Unknown"}</p>
                                                                    <p className="text-sm text-muted-foreground">{referrer.user_email}</p>
                                                                </div>
                                                            </TableCell>
                                                            <TableCell className="text-center">
                                                                <Badge variant="secondary">{referrer.referral_count}</Badge>
                                                            </TableCell>
                                                            <TableCell className="text-center">
                                                                <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                                                                    {referrer.successful_referrals}
                                                                </Badge>
                                                            </TableCell>
                                                            <TableCell className="text-right font-medium">
                                                                ${referrer.total_rewards_earned.toFixed(2)}
                                                            </TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    </>
                )}
            </div>
        </AdminLayout>
    )
}
