"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Zap,
    Save,
    RefreshCcw,
    FileText,
    MessageSquare,
    Image,
    Sparkles,
    Tag,
    Settings,
    AlertCircle,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

// Types
interface AIPlanLimits {
    plan_id: string
    plan_name: string
    max_title_generations: number
    max_description_generations: number
    max_thumbnail_generations: number
    max_chatbot_messages: number
    max_total_tokens: number
}

interface AILimitsConfig {
    limits_by_plan: AIPlanLimits[]
    global_daily_limit: number
    throttle_at_percentage: number
}

// Feature icons
const featureIcons: Record<string, React.ReactNode> = {
    titles: <FileText className="h-4 w-4" />,
    descriptions: <MessageSquare className="h-4 w-4" />,
    thumbnails: <Image className="h-4 w-4" />,
    chatbot: <Sparkles className="h-4 w-4" />,
    tokens: <Tag className="h-4 w-4" />,
}

export default function AILimitsConfigPage() {
    const [config, setConfig] = useState<AILimitsConfig | null>(null)
    const [originalConfig, setOriginalConfig] = useState<AILimitsConfig | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const { toast } = useToast()

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch("/api/admin/ai/limits", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })
            if (!response.ok) throw new Error("Failed to fetch AI limits")
            const data = await response.json()
            setConfig(data)
            setOriginalConfig(data)
        } catch (err) {
            console.error("Failed to fetch AI limits:", err)
            setError("Failed to load AI limits configuration")
            // Set mock data for development
            const mockConfig: AILimitsConfig = {
                limits_by_plan: [
                    { plan_id: "free", plan_name: "Free", max_title_generations: 10, max_description_generations: 10, max_thumbnail_generations: 5, max_chatbot_messages: 50, max_total_tokens: 10000 },
                    { plan_id: "starter", plan_name: "Starter", max_title_generations: 100, max_description_generations: 100, max_thumbnail_generations: 50, max_chatbot_messages: 500, max_total_tokens: 100000 },
                    { plan_id: "professional", plan_name: "Professional", max_title_generations: 500, max_description_generations: 500, max_thumbnail_generations: 200, max_chatbot_messages: 2000, max_total_tokens: 500000 },
                    { plan_id: "enterprise", plan_name: "Enterprise", max_title_generations: 2000, max_description_generations: 2000, max_thumbnail_generations: 1000, max_chatbot_messages: 10000, max_total_tokens: 2000000 },
                ],
                global_daily_limit: 10000,
                throttle_at_percentage: 90,
            }
            setConfig(mockConfig)
            setOriginalConfig(mockConfig)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        if (!config) return
        setIsSaving(true)
        try {
            const token = localStorage.getItem("access_token")

            // Save global limits
            await fetch("/api/admin/ai/limits/global", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    global_daily_limit: config.global_daily_limit,
                    throttle_at_percentage: config.throttle_at_percentage,
                }),
            })

            // Save each plan's limits
            for (const plan of config.limits_by_plan) {
                await fetch("/api/admin/ai/limits", {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        plan_id: plan.plan_id,
                        max_title_generations: plan.max_title_generations,
                        max_description_generations: plan.max_description_generations,
                        max_thumbnail_generations: plan.max_thumbnail_generations,
                        max_chatbot_messages: plan.max_chatbot_messages,
                        max_total_tokens: plan.max_total_tokens,
                    }),
                })
            }

            setOriginalConfig(config)
            toast({
                title: "Settings saved",
                description: "AI limits configuration has been updated.",
            })
        } catch (err) {
            console.error("Failed to save AI limits:", err)
            toast({
                title: "Error",
                description: "Failed to save AI limits configuration.",
                variant: "destructive",
            })
        } finally {
            setIsSaving(false)
        }
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updatePlanLimit = (planId: string, field: keyof AIPlanLimits, value: number) => {
        if (!config) return
        setConfig({
            ...config,
            limits_by_plan: config.limits_by_plan.map(plan =>
                plan.plan_id === planId ? { ...plan, [field]: value } : plan
            ),
        })
    }

    const updateGlobalConfig = (field: "global_daily_limit" | "throttle_at_percentage", value: number) => {
        if (!config) return
        setConfig({ ...config, [field]: value })
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(0)}K`
        return num.toString()
    }

    return (
        <AdminLayout breadcrumbs={[
            { label: "AI Service", href: "/admin/ai" },
            { label: "Limits Configuration" }
        ]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
                                className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/25"
                            >
                                <Zap className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                                    AI Limits Configuration
                                </h1>
                                <p className="text-muted-foreground">
                                    Configure AI generation limits per subscription plan
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <Button variant="outline" onClick={handleReset} disabled={!isDirty || isLoading}>
                            <RefreshCcw className="h-4 w-4 mr-2" />
                            Reset
                        </Button>
                        <Button onClick={handleSave} disabled={!isDirty || isSaving}>
                            <Save className="h-4 w-4 mr-2" />
                            {isSaving ? "Saving..." : "Save Changes"}
                        </Button>
                    </div>
                </motion.div>

                {isLoading ? (
                    <LoadingSkeleton />
                ) : config ? (
                    <>
                        {/* Global Settings */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Settings className="h-5 w-5 text-slate-500" />
                                        <CardTitle>Global Settings</CardTitle>
                                    </div>
                                    <CardDescription>Platform-wide AI limits and throttling</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid gap-6 sm:grid-cols-2">
                                        <div className="space-y-2">
                                            <Label htmlFor="global_daily_limit">Global Daily API Limit</Label>
                                            <Input
                                                id="global_daily_limit"
                                                type="number"
                                                min={0}
                                                value={config.global_daily_limit}
                                                onChange={(e) => updateGlobalConfig("global_daily_limit", parseInt(e.target.value) || 0)}
                                            />
                                            <p className="text-xs text-muted-foreground">
                                                Maximum API calls per day across all users
                                            </p>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="throttle_at_percentage">Throttle at Budget %</Label>
                                            <Input
                                                id="throttle_at_percentage"
                                                type="number"
                                                min={0}
                                                max={100}
                                                value={config.throttle_at_percentage}
                                                onChange={(e) => updateGlobalConfig("throttle_at_percentage", parseInt(e.target.value) || 0)}
                                            />
                                            <p className="text-xs text-muted-foreground">
                                                Start throttling when budget usage reaches this percentage
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Plan Limits */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Zap className="h-5 w-5 text-blue-500" />
                                        <CardTitle>Limits per Plan</CardTitle>
                                    </div>
                                    <CardDescription>Configure AI generation limits for each subscription tier</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-8">
                                        {config.limits_by_plan.map((plan, index) => (
                                            <div key={plan.plan_id}>
                                                {index > 0 && <Separator className="mb-8" />}
                                                <div className="space-y-4">
                                                    <h3 className="text-lg font-semibold flex items-center gap-2">
                                                        <span className={cn(
                                                            "h-3 w-3 rounded-full",
                                                            plan.plan_id === "free" && "bg-slate-400",
                                                            plan.plan_id === "starter" && "bg-blue-500",
                                                            plan.plan_id === "professional" && "bg-purple-500",
                                                            plan.plan_id === "enterprise" && "bg-amber-500",
                                                        )} />
                                                        {plan.plan_name}
                                                    </h3>
                                                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                                                        <div className="space-y-2">
                                                            <Label className="flex items-center gap-2">
                                                                {featureIcons.titles}
                                                                Title Generations
                                                            </Label>
                                                            <Input
                                                                type="number"
                                                                min={0}
                                                                value={plan.max_title_generations}
                                                                onChange={(e) => updatePlanLimit(plan.plan_id, "max_title_generations", parseInt(e.target.value) || 0)}
                                                            />
                                                            <p className="text-xs text-muted-foreground">per month</p>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label className="flex items-center gap-2">
                                                                {featureIcons.descriptions}
                                                                Description Generations
                                                            </Label>
                                                            <Input
                                                                type="number"
                                                                min={0}
                                                                value={plan.max_description_generations}
                                                                onChange={(e) => updatePlanLimit(plan.plan_id, "max_description_generations", parseInt(e.target.value) || 0)}
                                                            />
                                                            <p className="text-xs text-muted-foreground">per month</p>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label className="flex items-center gap-2">
                                                                {featureIcons.thumbnails}
                                                                Thumbnail Generations
                                                            </Label>
                                                            <Input
                                                                type="number"
                                                                min={0}
                                                                value={plan.max_thumbnail_generations}
                                                                onChange={(e) => updatePlanLimit(plan.plan_id, "max_thumbnail_generations", parseInt(e.target.value) || 0)}
                                                            />
                                                            <p className="text-xs text-muted-foreground">per month</p>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label className="flex items-center gap-2">
                                                                {featureIcons.chatbot}
                                                                Chatbot Messages
                                                            </Label>
                                                            <Input
                                                                type="number"
                                                                min={0}
                                                                value={plan.max_chatbot_messages}
                                                                onChange={(e) => updatePlanLimit(plan.plan_id, "max_chatbot_messages", parseInt(e.target.value) || 0)}
                                                            />
                                                            <p className="text-xs text-muted-foreground">per month</p>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label className="flex items-center gap-2">
                                                                {featureIcons.tokens}
                                                                Total Tokens
                                                            </Label>
                                                            <Input
                                                                type="number"
                                                                min={0}
                                                                value={plan.max_total_tokens}
                                                                onChange={(e) => updatePlanLimit(plan.plan_id, "max_total_tokens", parseInt(e.target.value) || 0)}
                                                            />
                                                            <p className="text-xs text-muted-foreground">{formatNumber(plan.max_total_tokens)} per month</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Info Box */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-blue-900 dark:text-blue-100">About AI Limits</p>
                                        <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                            These limits control how many AI generations each user can perform per month based on their subscription plan.
                                            When a user reaches their limit, they will need to upgrade their plan or wait for the next billing cycle.
                                            Token limits provide an additional safeguard against excessive API usage.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </>
                ) : null}
            </div>
        </AdminLayout>
    )
}

// Loading Skeleton
function LoadingSkeleton() {
    return (
        <div className="space-y-6">
            <Card>
                <CardContent className="p-6">
                    <Skeleton className="h-6 w-48 mb-4" />
                    <div className="grid gap-4 sm:grid-cols-2">
                        <Skeleton className="h-20" />
                        <Skeleton className="h-20" />
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="p-6">
                    <Skeleton className="h-6 w-48 mb-4" />
                    <div className="space-y-8">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="space-y-4">
                                <Skeleton className="h-6 w-32" />
                                <div className="grid gap-4 sm:grid-cols-5">
                                    {[1, 2, 3, 4, 5].map((j) => (
                                        <Skeleton key={j} className="h-20" />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
