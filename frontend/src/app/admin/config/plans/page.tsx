"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
    CreditCard,
    DollarSign,
    Users,
    Video,
    Radio,
    HardDrive,
    Wifi,
    Sparkles,
    BarChart3,
    Code,
    Headphones,
    Edit2,
    X,
    Save,
    Loader2,
    CheckCircle2,
} from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/components/ui/toast"
import { configApi, type PlanConfig } from "@/lib/api/admin"

const defaultPlans: PlanConfig[] = [
    {
        plan_id: "free",
        plan_name: "Free",
        price_monthly: 0,
        price_yearly: 0,
        max_youtube_accounts: 1,
        max_videos_per_month: 5,
        max_streams_per_month: 5,
        max_storage_gb: 1,
        max_bandwidth_gb: 10,
        max_ai_generations_per_month: 10,
        max_concurrent_streams: 1,
        max_simulcast_platforms: 1,
        enable_analytics: false,
        enable_competitor_analysis: false,
        enable_ai_features: false,
        enable_api_access: false,
        api_rate_limit_per_minute: 30,
        support_level: "community",
        is_active: true,
    },
]

export default function PlansConfigPage() {
    const [plans, setPlans] = useState<PlanConfig[]>(defaultPlans)
    const [isLoading, setIsLoading] = useState(true)
    const [editingPlan, setEditingPlan] = useState<PlanConfig | null>(null)
    const [isSaving, setIsSaving] = useState(false)
    const { addToast } = useToast()

    const fetchPlans = useCallback(async () => {
        try {
            const data = await configApi.getPlanConfigs()
            setPlans(data.plans)
        } catch (error) {
            console.error("Failed to fetch plans:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchPlans()
    }, [fetchPlans])

    const handleSavePlan = async () => {
        if (!editingPlan) return
        setIsSaving(true)
        try {
            await configApi.updatePlanConfig(editingPlan.plan_id, editingPlan)
            setPlans((prev) =>
                prev.map((p) => (p.plan_id === editingPlan.plan_id ? editingPlan : p))
            )
            setEditingPlan(null)
            addToast({
                type: "success",
                title: "Plan updated",
                description: `${editingPlan.plan_name} plan has been updated successfully.`,
            })
        } catch (error) {
            console.error("Failed to update plan:", error)
            addToast({
                type: "error",
                title: "Failed to update",
                description: "An error occurred while updating the plan.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    const updateEditingPlan = <K extends keyof PlanConfig>(
        key: K,
        value: PlanConfig[K]
    ) => {
        if (!editingPlan) return
        setEditingPlan((prev) => (prev ? { ...prev, [key]: value } : null))
    }

    const getSupportLevelBadge = (level: string) => {
        const colors: Record<string, string> = {
            community: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
            email: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
            priority: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
            dedicated: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
        }
        return colors[level] || colors.community
    }

    return (
        <ConfigFormWrapper
            title="Subscription Plans Configuration"
            description="Configure subscription plans, pricing, limits, and features for each tier."
            icon={<CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={async () => { }}
            onReset={() => { }}
            isDirty={false}
            isLoading={isLoading}
        >
            <div className="space-y-6">
                {/* Plan Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {plans.map((plan) => (
                        <motion.div
                            key={plan.plan_id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className={`relative ${!plan.is_active ? "opacity-60" : ""}`}>
                                <CardHeader className="pb-2">
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-lg">{plan.plan_name}</CardTitle>
                                        <div className="flex items-center gap-2">
                                            {!plan.is_active && (
                                                <Badge variant="secondary">Inactive</Badge>
                                            )}
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => setEditingPlan(plan)}
                                            >
                                                <Edit2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-2xl font-bold">
                                            ${plan.price_monthly}
                                        </span>
                                        <span className="text-slate-500">/month</span>
                                    </div>
                                    <p className="text-sm text-slate-500">
                                        ${plan.price_yearly}/year
                                    </p>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center gap-2">
                                            <Users className="h-4 w-4 text-slate-400" />
                                            <span>{plan.max_youtube_accounts} YouTube accounts</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Video className="h-4 w-4 text-slate-400" />
                                            <span>{plan.max_videos_per_month} videos/month</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Radio className="h-4 w-4 text-slate-400" />
                                            <span>{plan.max_streams_per_month} streams/month</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <HardDrive className="h-4 w-4 text-slate-400" />
                                            <span>{plan.max_storage_gb} GB storage</span>
                                        </div>
                                    </div>
                                    <Separator />
                                    <div className="flex flex-wrap gap-1">
                                        {plan.enable_analytics && (
                                            <Badge variant="outline" className="text-xs">
                                                <BarChart3 className="h-3 w-3 mr-1" />
                                                Analytics
                                            </Badge>
                                        )}
                                        {plan.enable_ai_features && (
                                            <Badge variant="outline" className="text-xs">
                                                <Sparkles className="h-3 w-3 mr-1" />
                                                AI
                                            </Badge>
                                        )}
                                        {plan.enable_api_access && (
                                            <Badge variant="outline" className="text-xs">
                                                <Code className="h-3 w-3 mr-1" />
                                                API
                                            </Badge>
                                        )}
                                    </div>
                                    <Badge className={getSupportLevelBadge(plan.support_level)}>
                                        <Headphones className="h-3 w-3 mr-1" />
                                        {plan.support_level} support
                                    </Badge>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Edit Plan Dialog */}
            <AnimatePresence>
                {editingPlan && (
                    <Dialog open={!!editingPlan} onOpenChange={() => setEditingPlan(null)}>
                        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                            <DialogHeader>
                                <DialogTitle>Edit {editingPlan.plan_name} Plan</DialogTitle>
                                <DialogDescription>
                                    Configure pricing, limits, and features for this plan.
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-6 py-4">
                                {/* Basic Info */}
                                <div>
                                    <h4 className="font-medium mb-3 flex items-center gap-2">
                                        <CreditCard className="h-4 w-4" />
                                        Basic Information
                                    </h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Plan Name</Label>
                                            <Input
                                                value={editingPlan.plan_name}
                                                onChange={(e) =>
                                                    updateEditingPlan("plan_name", e.target.value)
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Status</Label>
                                            <div className="flex items-center gap-2 h-10">
                                                <Switch
                                                    checked={editingPlan.is_active}
                                                    onCheckedChange={(checked) =>
                                                        updateEditingPlan("is_active", checked)
                                                    }
                                                />
                                                <span className="text-sm">
                                                    {editingPlan.is_active ? "Active" : "Inactive"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Pricing */}
                                <div>
                                    <h4 className="font-medium mb-3 flex items-center gap-2">
                                        <DollarSign className="h-4 w-4" />
                                        Pricing
                                    </h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Monthly Price ($)</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                step={0.01}
                                                value={editingPlan.price_monthly}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "price_monthly",
                                                        parseFloat(e.target.value) || 0
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Yearly Price ($)</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                step={0.01}
                                                value={editingPlan.price_yearly}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "price_yearly",
                                                        parseFloat(e.target.value) || 0
                                                    )
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Limits */}
                                <div>
                                    <h4 className="font-medium mb-3">Resource Limits</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>Max YouTube Accounts</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_youtube_accounts}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_youtube_accounts",
                                                        parseInt(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Max Videos/Month</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_videos_per_month}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_videos_per_month",
                                                        parseInt(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Max Streams/Month</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_streams_per_month}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_streams_per_month",
                                                        parseInt(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Max Concurrent Streams</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_concurrent_streams}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_concurrent_streams",
                                                        parseInt(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Storage (GB)</Label>
                                            <Input
                                                type="number"
                                                min={0.1}
                                                step={0.1}
                                                value={editingPlan.max_storage_gb}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_storage_gb",
                                                        parseFloat(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Bandwidth (GB)</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_bandwidth_gb}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_bandwidth_gb",
                                                        parseFloat(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>AI Generations/Month</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                value={editingPlan.max_ai_generations_per_month}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_ai_generations_per_month",
                                                        parseInt(e.target.value) || 0
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Simulcast Platforms</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.max_simulcast_platforms}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "max_simulcast_platforms",
                                                        parseInt(e.target.value) || 1
                                                    )
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Features */}
                                <div>
                                    <h4 className="font-medium mb-3">Features</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                            <div>
                                                <Label>Analytics</Label>
                                                <p className="text-xs text-slate-500">
                                                    Advanced analytics features
                                                </p>
                                            </div>
                                            <Switch
                                                checked={editingPlan.enable_analytics}
                                                onCheckedChange={(checked) =>
                                                    updateEditingPlan("enable_analytics", checked)
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                            <div>
                                                <Label>Competitor Analysis</Label>
                                                <p className="text-xs text-slate-500">
                                                    Competitor tracking
                                                </p>
                                            </div>
                                            <Switch
                                                checked={editingPlan.enable_competitor_analysis}
                                                onCheckedChange={(checked) =>
                                                    updateEditingPlan("enable_competitor_analysis", checked)
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                            <div>
                                                <Label>AI Features</Label>
                                                <p className="text-xs text-slate-500">
                                                    AI-powered tools
                                                </p>
                                            </div>
                                            <Switch
                                                checked={editingPlan.enable_ai_features}
                                                onCheckedChange={(checked) =>
                                                    updateEditingPlan("enable_ai_features", checked)
                                                }
                                            />
                                        </div>
                                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                            <div>
                                                <Label>API Access</Label>
                                                <p className="text-xs text-slate-500">
                                                    REST API access
                                                </p>
                                            </div>
                                            <Switch
                                                checked={editingPlan.enable_api_access}
                                                onCheckedChange={(checked) =>
                                                    updateEditingPlan("enable_api_access", checked)
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* API & Support */}
                                <div>
                                    <h4 className="font-medium mb-3">API & Support</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>API Rate Limit (req/min)</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={editingPlan.api_rate_limit_per_minute}
                                                onChange={(e) =>
                                                    updateEditingPlan(
                                                        "api_rate_limit_per_minute",
                                                        parseInt(e.target.value) || 60
                                                    )
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Support Level</Label>
                                            <Select
                                                value={editingPlan.support_level}
                                                onValueChange={(value) =>
                                                    updateEditingPlan("support_level", value)
                                                }
                                            >
                                                <SelectTrigger>
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="community">Community</SelectItem>
                                                    <SelectItem value="email">Email</SelectItem>
                                                    <SelectItem value="priority">Priority</SelectItem>
                                                    <SelectItem value="dedicated">Dedicated</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-4 border-t">
                                <Button
                                    variant="outline"
                                    onClick={() => setEditingPlan(null)}
                                    disabled={isSaving}
                                >
                                    <X className="h-4 w-4 mr-2" />
                                    Cancel
                                </Button>
                                <Button onClick={handleSavePlan} disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="h-4 w-4 mr-2" />
                                            Save Changes
                                        </>
                                    )}
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                )}
            </AnimatePresence>
        </ConfigFormWrapper>
    )
}
