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
    Sparkles,
    Edit2,
    X,
    Save,
    Loader2,
    Plus,
    Trash2,
    Star,
    Check,
    Zap,
    Crown,
    Building2,
    Rocket,
    Gift,
    Shield,
    Gem,
    Award,
    type LucideIcon,
} from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useToast } from "@/components/ui/toast"
import { configApi, type PlanConfig, type PlanConfigCreate } from "@/lib/api/admin"

// Available features that can be assigned to plans
const AVAILABLE_FEATURES = [
    { slug: "basic_upload", name: "Basic Upload", description: "Upload videos to YouTube" },
    { slug: "basic_analytics", name: "Basic Analytics", description: "View basic video analytics" },
    { slug: "scheduled_publishing", name: "Scheduled Publishing", description: "Schedule video uploads" },
    { slug: "ai_titles", name: "AI Titles", description: "AI-generated video titles" },
    { slug: "ai_thumbnails", name: "AI Thumbnails", description: "AI-generated thumbnails" },
    { slug: "ai_descriptions", name: "AI Descriptions", description: "AI-generated descriptions" },
    { slug: "ai_tags", name: "AI Tags", description: "AI-generated tags" },
    { slug: "bulk_upload", name: "Bulk Upload", description: "Upload multiple videos at once" },
    { slug: "live_streaming", name: "Live Streaming", description: "Stream live to YouTube" },
    { slug: "simulcast", name: "Simulcast", description: "Stream to multiple platforms" },
    { slug: "chat_moderation", name: "Chat Moderation", description: "Moderate live chat" },
    { slug: "competitor_analysis", name: "Competitor Analysis", description: "Analyze competitor channels" },
    { slug: "api_access", name: "API Access", description: "Access to REST API" },
    { slug: "webhooks", name: "Webhooks", description: "Webhook notifications" },
    { slug: "priority_support", name: "Priority Support", description: "Priority customer support" },
    { slug: "custom_branding", name: "Custom Branding", description: "Custom branding options" },
    { slug: "sla_guarantee", name: "SLA Guarantee", description: "Service level agreement" },
    { slug: "advanced_analytics", name: "Advanced Analytics", description: "Detailed analytics dashboard" },
    { slug: "team_collaboration", name: "Team Collaboration", description: "Multi-user team features" },
]

// Available icons for plans
const AVAILABLE_ICONS: { name: string; icon: LucideIcon }[] = [
    { name: "Sparkles", icon: Sparkles },
    { name: "Zap", icon: Zap },
    { name: "Crown", icon: Crown },
    { name: "Building2", icon: Building2 },
    { name: "Rocket", icon: Rocket },
    { name: "Gift", icon: Gift },
    { name: "Shield", icon: Shield },
    { name: "Gem", icon: Gem },
    { name: "Award", icon: Award },
    { name: "Star", icon: Star },
]

// Available colors for plans (Tailwind color names)
const AVAILABLE_COLORS = [
    { name: "slate", label: "Slate", bg: "bg-slate-500", text: "text-slate-500" },
    { name: "blue", label: "Blue", bg: "bg-blue-500", text: "text-blue-500" },
    { name: "violet", label: "Violet", bg: "bg-violet-500", text: "text-violet-500" },
    { name: "amber", label: "Amber", bg: "bg-amber-500", text: "text-amber-500" },
    { name: "emerald", label: "Emerald", bg: "bg-emerald-500", text: "text-emerald-500" },
    { name: "rose", label: "Rose", bg: "bg-rose-500", text: "text-rose-500" },
    { name: "cyan", label: "Cyan", bg: "bg-cyan-500", text: "text-cyan-500" },
    { name: "orange", label: "Orange", bg: "bg-orange-500", text: "text-orange-500" },
]

// Helper to get icon component by name
const getIconByName = (name: string): LucideIcon => {
    const found = AVAILABLE_ICONS.find((i) => i.name === name)
    return found?.icon || Sparkles
}

// Helper to get color classes by name
const getColorClasses = (name: string) => {
    const found = AVAILABLE_COLORS.find((c) => c.name === name)
    return found || AVAILABLE_COLORS[0]
}

const emptyPlan: PlanConfigCreate = {
    name: "",
    description: "",
    price_monthly: 0,
    price_yearly: 0,
    currency: "USD",
    max_accounts: 1,
    max_videos_per_month: 5,
    max_streams_per_month: 0,
    max_storage_gb: 1,
    max_bandwidth_gb: 5,
    ai_generations_per_month: 0,
    api_calls_per_month: 1000,
    encoding_minutes_per_month: 60,
    concurrent_streams: 1,
    features: [],
    display_features: [],
    icon: "Sparkles",
    color: "slate",
    is_active: true,
    is_popular: false,
    sort_order: 0,
}

// Helper function to format limit value
const formatLimitValue = (value: number): string => {
    return value === -1 ? "Unlimited" : value.toString()
}

// Generate display_features based on features and quotas
const generateDisplayFeatures = (plan: {
    features: string[]
    max_accounts: number
    max_videos_per_month: number
    max_streams_per_month: number
    max_storage_gb: number
    max_bandwidth_gb: number
    ai_generations_per_month: number
    api_calls_per_month: number
    encoding_minutes_per_month: number
    concurrent_streams: number
}): Array<{ name: string; included: boolean }> => {
    const displayFeatures: Array<{ name: string; included: boolean }> = []

    // Add quota-based features first
    displayFeatures.push({
        name: `${formatLimitValue(plan.max_accounts)} YouTube Account${plan.max_accounts !== 1 ? "s" : ""}`,
        included: true,
    })
    displayFeatures.push({
        name: `${formatLimitValue(plan.max_videos_per_month)} Videos/month`,
        included: plan.max_videos_per_month !== 0,
    })
    displayFeatures.push({
        name: `${formatLimitValue(plan.max_storage_gb)} GB Storage`,
        included: plan.max_storage_gb !== 0,
    })

    // Add AI features
    const hasAiFeatures = plan.features.some((f) =>
        ["ai_titles", "ai_thumbnails", "ai_descriptions", "ai_tags"].includes(f)
    )
    displayFeatures.push({
        name: hasAiFeatures
            ? `AI Features (${formatLimitValue(plan.ai_generations_per_month)}/month)`
            : "AI Features",
        included: hasAiFeatures && plan.ai_generations_per_month !== 0,
    })

    // Add streaming features
    const hasStreaming = plan.features.includes("live_streaming") || plan.features.includes("simulcast")
    displayFeatures.push({
        name: hasStreaming
            ? `Live Streaming (${formatLimitValue(plan.max_streams_per_month)}/month)`
            : "Live Streaming",
        included: hasStreaming && plan.max_streams_per_month !== 0,
    })

    // Add analytics
    const hasAdvancedAnalytics = plan.features.includes("advanced_analytics")
    displayFeatures.push({
        name: hasAdvancedAnalytics ? "Advanced Analytics" : "Basic Analytics",
        included: plan.features.includes("basic_analytics") || hasAdvancedAnalytics,
    })

    // Add API access
    displayFeatures.push({
        name: plan.features.includes("api_access")
            ? `API Access (${formatLimitValue(plan.api_calls_per_month)} calls/month)`
            : "API Access",
        included: plan.features.includes("api_access"),
    })

    // Add priority support
    displayFeatures.push({
        name: "Priority Support",
        included: plan.features.includes("priority_support"),
    })

    return displayFeatures
}

export default function PlansConfigPage() {
    const [plans, setPlans] = useState<PlanConfig[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [editingPlan, setEditingPlan] = useState<PlanConfig | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [newPlan, setNewPlan] = useState<PlanConfigCreate>(emptyPlan)
    const [isSaving, setIsSaving] = useState(false)
    const [deletingPlan, setDeletingPlan] = useState<PlanConfig | null>(null)
    const { addToast } = useToast()

    const fetchPlans = useCallback(async () => {
        try {
            const data = await configApi.getPlanConfigs()
            setPlans(data.plans)
        } catch (error) {
            console.error("Failed to fetch plans:", error)
            addToast({
                type: "error",
                title: "Failed to load plans",
                description: "Could not fetch plan configurations.",
            })
        } finally {
            setIsLoading(false)
        }
    }, [addToast])

    useEffect(() => {
        fetchPlans()
    }, [fetchPlans])

    const handleSavePlan = async () => {
        if (!editingPlan) return
        setIsSaving(true)
        try {
            // Auto-generate display_features based on features and quotas
            const display_features = generateDisplayFeatures({
                features: editingPlan.features,
                max_accounts: editingPlan.max_accounts,
                max_videos_per_month: editingPlan.max_videos_per_month,
                max_streams_per_month: editingPlan.max_streams_per_month,
                max_storage_gb: editingPlan.max_storage_gb,
                max_bandwidth_gb: editingPlan.max_bandwidth_gb,
                ai_generations_per_month: editingPlan.ai_generations_per_month,
                api_calls_per_month: editingPlan.api_calls_per_month,
                encoding_minutes_per_month: editingPlan.encoding_minutes_per_month,
                concurrent_streams: editingPlan.concurrent_streams,
            })

            const { id, slug, ...updateData } = { ...editingPlan, display_features }
            await configApi.updatePlanConfig(slug, updateData)

            const updatedPlan = { ...editingPlan, display_features }
            setPlans((prev) =>
                prev.map((p) => (p.slug === editingPlan.slug ? updatedPlan : p))
            )
            setEditingPlan(null)
            addToast({
                type: "success",
                title: "Plan updated",
                description: `${editingPlan.name} plan has been updated successfully.`,
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

    const handleCreatePlan = async () => {
        if (!newPlan.name) {
            addToast({
                type: "error",
                title: "Validation error",
                description: "Plan name is required.",
            })
            return
        }
        setIsSaving(true)
        try {
            // Auto-generate display_features based on features and quotas
            const display_features = generateDisplayFeatures({
                features: newPlan.features || [],
                max_accounts: newPlan.max_accounts || 1,
                max_videos_per_month: newPlan.max_videos_per_month || 5,
                max_streams_per_month: newPlan.max_streams_per_month || 0,
                max_storage_gb: newPlan.max_storage_gb || 1,
                max_bandwidth_gb: newPlan.max_bandwidth_gb || 5,
                ai_generations_per_month: newPlan.ai_generations_per_month || 0,
                api_calls_per_month: newPlan.api_calls_per_month || 1000,
                encoding_minutes_per_month: newPlan.encoding_minutes_per_month || 60,
                concurrent_streams: newPlan.concurrent_streams || 1,
            })

            const planToCreate = { ...newPlan, display_features }
            const created = await configApi.createPlanConfig(planToCreate)
            setPlans((prev) => [...prev, created])
            setIsCreating(false)
            setNewPlan(emptyPlan)
            addToast({
                type: "success",
                title: "Plan created",
                description: `${created.name} plan has been created successfully.`,
            })
        } catch (error: unknown) {
            console.error("Failed to create plan:", error)
            const errorMessage = error && typeof error === 'object' && 'detail' in error
                ? String((error as { detail: string }).detail)
                : "An error occurred while creating the plan."
            addToast({
                type: "error",
                title: "Failed to create",
                description: errorMessage,
            })
        } finally {
            setIsSaving(false)
        }
    }

    const handleDeletePlan = async () => {
        if (!deletingPlan) return
        setIsSaving(true)
        try {
            await configApi.deletePlanConfig(deletingPlan.slug)
            setPlans((prev) => prev.filter((p) => p.slug !== deletingPlan.slug))
            setDeletingPlan(null)
            addToast({
                type: "success",
                title: "Plan deleted",
                description: `${deletingPlan.name} plan has been deleted.`,
            })
        } catch (error) {
            console.error("Failed to delete plan:", error)
            addToast({
                type: "error",
                title: "Failed to delete",
                description: "An error occurred while deleting the plan.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <ConfigFormWrapper
            title="Subscription Plans Configuration"
            description="Configure subscription plans, pricing, limits, and features for each tier."
            icon={<CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            isLoading={isLoading}
            hideDefaultActions
            customActions={
                <Button onClick={() => setIsCreating(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Plan
                </Button>
            }
        >
            <div className="space-y-6">

                {/* Plan Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {plans.map((plan) => (
                        <motion.div
                            key={plan.slug}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className={`relative ${!plan.is_active ? "opacity-60" : ""}`}>
                                {plan.is_popular && (
                                    <div className="absolute -top-2 -right-2">
                                        <Badge className="bg-amber-500 text-white">
                                            <Star className="h-3 w-3 mr-1" />
                                            Popular
                                        </Badge>
                                    </div>
                                )}
                                <CardHeader className="pb-2">
                                    {/* Plan Icon */}
                                    <div className="flex justify-center mb-2">
                                        <div className={`p-3 rounded-full ${getColorClasses(plan.color).bg} bg-opacity-10`}>
                                            {(() => {
                                                const IconComponent = getIconByName(plan.icon)
                                                return <IconComponent className={`h-6 w-6 ${getColorClasses(plan.color).text}`} />
                                            })()}
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="text-lg">{plan.name}</CardTitle>
                                            <p className="text-xs text-slate-500">{plan.slug}</p>
                                        </div>
                                        <div className="flex items-center gap-1">
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
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => setDeletingPlan(plan)}
                                                className="text-red-500 hover:text-red-600"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-2xl font-bold">
                                            ${plan.price_monthly.toFixed(2)}
                                        </span>
                                        <span className="text-slate-500">/month</span>
                                    </div>
                                    <p className="text-sm text-slate-500">
                                        ${plan.price_yearly.toFixed(2)}/year
                                    </p>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center gap-2">
                                            <Users className="h-4 w-4 text-slate-400" />
                                            <span>{formatLimitValue(plan.max_accounts)} accounts</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Video className="h-4 w-4 text-slate-400" />
                                            <span>{formatLimitValue(plan.max_videos_per_month)} videos/month</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Radio className="h-4 w-4 text-slate-400" />
                                            <span>{formatLimitValue(plan.max_streams_per_month)} streams/month</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <HardDrive className="h-4 w-4 text-slate-400" />
                                            <span>{formatLimitValue(plan.max_storage_gb)} GB storage</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Sparkles className="h-4 w-4 text-slate-400" />
                                            <span>{formatLimitValue(plan.ai_generations_per_month)} AI/month</span>
                                        </div>
                                    </div>
                                    <Separator />
                                    <div className="flex flex-wrap gap-1">
                                        {plan.features.slice(0, 4).map((feature) => (
                                            <Badge key={feature} variant="outline" className="text-xs">
                                                {feature}
                                            </Badge>
                                        ))}
                                        {plan.features.length > 4 && (
                                            <Badge variant="outline" className="text-xs">
                                                +{plan.features.length - 4} more
                                            </Badge>
                                        )}
                                    </div>
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
                                <DialogTitle>Edit {editingPlan.name} Plan</DialogTitle>
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
                                                value={editingPlan.name}
                                                onChange={(e) =>
                                                    setEditingPlan({ ...editingPlan, name: e.target.value })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Slug (readonly)</Label>
                                            <Input value={editingPlan.slug} disabled />
                                        </div>
                                        <div className="col-span-2 space-y-2">
                                            <Label>Description</Label>
                                            <Textarea
                                                value={editingPlan.description || ""}
                                                onChange={(e) =>
                                                    setEditingPlan({ ...editingPlan, description: e.target.value })
                                                }
                                                rows={2}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Status</Label>
                                            <div className="flex items-center gap-2 h-10">
                                                <Switch
                                                    checked={editingPlan.is_active}
                                                    onCheckedChange={(checked) =>
                                                        setEditingPlan({ ...editingPlan, is_active: checked })
                                                    }
                                                />
                                                <span className="text-sm">
                                                    {editingPlan.is_active ? "Active" : "Inactive"}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Popular Badge</Label>
                                            <div className="flex items-center gap-2 h-10">
                                                <Switch
                                                    checked={editingPlan.is_popular}
                                                    onCheckedChange={(checked) =>
                                                        setEditingPlan({ ...editingPlan, is_popular: checked })
                                                    }
                                                />
                                                <span className="text-sm">
                                                    {editingPlan.is_popular ? "Show badge" : "Hidden"}
                                                </span>
                                            </div>
                                        </div>
                                        {/* Icon Selection */}
                                        <div className="space-y-2">
                                            <Label>Icon</Label>
                                            <div className="flex flex-wrap gap-2">
                                                {AVAILABLE_ICONS.map((iconOption) => {
                                                    const IconComp = iconOption.icon
                                                    return (
                                                        <button
                                                            key={iconOption.name}
                                                            type="button"
                                                            onClick={() => setEditingPlan({ ...editingPlan, icon: iconOption.name })}
                                                            className={`p-2 rounded-md border-2 transition-colors ${editingPlan.icon === iconOption.name
                                                                ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                                                : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                                                                }`}
                                                        >
                                                            <IconComp className="h-5 w-5" />
                                                        </button>
                                                    )
                                                })}
                                            </div>
                                        </div>
                                        {/* Color Selection */}
                                        <div className="space-y-2">
                                            <Label>Color</Label>
                                            <div className="flex flex-wrap gap-2">
                                                {AVAILABLE_COLORS.map((colorOption) => (
                                                    <button
                                                        key={colorOption.name}
                                                        type="button"
                                                        onClick={() => setEditingPlan({ ...editingPlan, color: colorOption.name })}
                                                        className={`w-8 h-8 rounded-full ${colorOption.bg} transition-all ${editingPlan.color === colorOption.name
                                                            ? "ring-2 ring-offset-2 ring-blue-500"
                                                            : "hover:scale-110"
                                                            }`}
                                                        title={colorOption.label}
                                                    />
                                                ))}
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
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="space-y-2">
                                            <Label>Monthly Price ($)</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                step={0.01}
                                                value={editingPlan.price_monthly}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        price_monthly: parseFloat(e.target.value) || 0,
                                                    })
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
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        price_yearly: parseFloat(e.target.value) || 0,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Sort Order</Label>
                                            <Input
                                                type="number"
                                                min={0}
                                                value={editingPlan.sort_order}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        sort_order: parseInt(e.target.value) || 0,
                                                    })
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Limits */}
                                <div>
                                    <h4 className="font-medium mb-3">Resource Limits (-1 = unlimited)</h4>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="space-y-2">
                                            <Label>Max Accounts</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.max_accounts}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        max_accounts: parseInt(e.target.value) || 1,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Videos/Month</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.max_videos_per_month}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        max_videos_per_month: parseInt(e.target.value) || 1,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Streams/Month</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.max_streams_per_month}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        max_streams_per_month: parseInt(e.target.value) || 0,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Storage (GB)</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.max_storage_gb}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        max_storage_gb: parseInt(e.target.value) || 1,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Bandwidth (GB)</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.max_bandwidth_gb}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        max_bandwidth_gb: parseInt(e.target.value) || 1,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>AI Generations/Month</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.ai_generations_per_month}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        ai_generations_per_month: parseInt(e.target.value) || 0,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>API Calls/Month</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.api_calls_per_month}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        api_calls_per_month: parseInt(e.target.value) || 1000,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Encoding Min/Month</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.encoding_minutes_per_month}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        encoding_minutes_per_month: parseInt(e.target.value) || 60,
                                                    })
                                                }
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Concurrent Streams</Label>
                                            <Input
                                                type="number"
                                                min={-1}
                                                value={editingPlan.concurrent_streams}
                                                onChange={(e) =>
                                                    setEditingPlan({
                                                        ...editingPlan,
                                                        concurrent_streams: parseInt(e.target.value) || 1,
                                                    })
                                                }
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Features */}
                                <div>
                                    <h4 className="font-medium mb-3 flex items-center gap-2">
                                        <Check className="h-4 w-4" />
                                        Plan Features
                                    </h4>
                                    <div className="grid grid-cols-2 gap-3 max-h-[200px] overflow-y-auto p-2 border rounded-md">
                                        {AVAILABLE_FEATURES.map((feature) => (
                                            <div key={feature.slug} className="flex items-start gap-2">
                                                <Checkbox
                                                    id={`edit-${feature.slug}`}
                                                    checked={editingPlan.features.includes(feature.slug)}
                                                    onCheckedChange={(checked) => {
                                                        if (checked) {
                                                            setEditingPlan({
                                                                ...editingPlan,
                                                                features: [...editingPlan.features, feature.slug],
                                                            })
                                                        } else {
                                                            setEditingPlan({
                                                                ...editingPlan,
                                                                features: editingPlan.features.filter((f) => f !== feature.slug),
                                                            })
                                                        }
                                                    }}
                                                />
                                                <label
                                                    htmlFor={`edit-${feature.slug}`}
                                                    className="text-sm cursor-pointer leading-tight"
                                                >
                                                    <span className="font-medium">{feature.name}</span>
                                                    <p className="text-xs text-slate-500">{feature.description}</p>
                                                </label>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-xs text-slate-500 mt-2">
                                        {editingPlan.features.length} features selected
                                    </p>
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

            {/* Create Plan Dialog */}
            <Dialog open={isCreating} onOpenChange={setIsCreating}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Create New Plan</DialogTitle>
                        <DialogDescription>
                            Add a new subscription plan with pricing and limits.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-6 py-4">
                        {/* Basic Info */}
                        <div>
                            <h4 className="font-medium mb-3 flex items-center gap-2">
                                <CreditCard className="h-4 w-4" />
                                Basic Information
                            </h4>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="space-y-2">
                                    <Label>Plan Name *</Label>
                                    <Input
                                        value={newPlan.name}
                                        onChange={(e) =>
                                            setNewPlan({ ...newPlan, name: e.target.value })
                                        }
                                        placeholder="e.g., Starter Plan"
                                    />
                                    <p className="text-xs text-slate-500">
                                        Slug will be auto-generated: {newPlan.name ? newPlan.name.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "") : "..."}
                                    </p>
                                </div>
                                <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                        value={newPlan.description || ""}
                                        onChange={(e) =>
                                            setNewPlan({ ...newPlan, description: e.target.value })
                                        }
                                        rows={2}
                                        placeholder="Brief description of the plan"
                                    />
                                </div>
                                {/* Icon Selection */}
                                <div className="space-y-2">
                                    <Label>Icon</Label>
                                    <div className="flex flex-wrap gap-2">
                                        {AVAILABLE_ICONS.map((iconOption) => {
                                            const IconComp = iconOption.icon
                                            return (
                                                <button
                                                    key={iconOption.name}
                                                    type="button"
                                                    onClick={() => setNewPlan({ ...newPlan, icon: iconOption.name })}
                                                    className={`p-2 rounded-md border-2 transition-colors ${newPlan.icon === iconOption.name
                                                            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                                            : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                                                        }`}
                                                >
                                                    <IconComp className="h-5 w-5" />
                                                </button>
                                            )
                                        })}
                                    </div>
                                </div>
                                {/* Color Selection */}
                                <div className="space-y-2">
                                    <Label>Color</Label>
                                    <div className="flex flex-wrap gap-2">
                                        {AVAILABLE_COLORS.map((colorOption) => (
                                            <button
                                                key={colorOption.name}
                                                type="button"
                                                onClick={() => setNewPlan({ ...newPlan, color: colorOption.name })}
                                                className={`w-8 h-8 rounded-full ${colorOption.bg} transition-all ${newPlan.color === colorOption.name
                                                        ? "ring-2 ring-offset-2 ring-blue-500"
                                                        : "hover:scale-110"
                                                    }`}
                                                title={colorOption.label}
                                            />
                                        ))}
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
                            <div className="grid grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <Label>Monthly Price ($)</Label>
                                    <Input
                                        type="number"
                                        min={0}
                                        step={0.01}
                                        value={newPlan.price_monthly}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                price_monthly: parseFloat(e.target.value) || 0,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Yearly Price ($)</Label>
                                    <Input
                                        type="number"
                                        min={0}
                                        step={0.01}
                                        value={newPlan.price_yearly}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                price_yearly: parseFloat(e.target.value) || 0,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Sort Order</Label>
                                    <Input
                                        type="number"
                                        min={0}
                                        value={newPlan.sort_order}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                sort_order: parseInt(e.target.value) || 0,
                                            })
                                        }
                                    />
                                </div>
                            </div>
                        </div>

                        <Separator />

                        {/* Limits */}
                        <div>
                            <h4 className="font-medium mb-3">Resource Limits (-1 = unlimited)</h4>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <Label>Max Accounts</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.max_accounts}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                max_accounts: parseInt(e.target.value) || 1,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Videos/Month</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.max_videos_per_month}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                max_videos_per_month: parseInt(e.target.value) || 5,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Streams/Month</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.max_streams_per_month}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                max_streams_per_month: parseInt(e.target.value) || 0,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Storage (GB)</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.max_storage_gb}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                max_storage_gb: parseInt(e.target.value) || 1,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Bandwidth (GB)</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.max_bandwidth_gb}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                max_bandwidth_gb: parseInt(e.target.value) || 5,
                                            })
                                        }
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>AI Generations/Month</Label>
                                    <Input
                                        type="number"
                                        min={-1}
                                        value={newPlan.ai_generations_per_month}
                                        onChange={(e) =>
                                            setNewPlan({
                                                ...newPlan,
                                                ai_generations_per_month: parseInt(e.target.value) || 0,
                                            })
                                        }
                                    />
                                </div>
                            </div>
                        </div>

                        <Separator />

                        {/* Features */}
                        <div>
                            <h4 className="font-medium mb-3 flex items-center gap-2">
                                <Check className="h-4 w-4" />
                                Plan Features
                            </h4>
                            <div className="grid grid-cols-2 gap-3 max-h-[200px] overflow-y-auto p-2 border rounded-md">
                                {AVAILABLE_FEATURES.map((feature) => (
                                    <div key={feature.slug} className="flex items-start gap-2">
                                        <Checkbox
                                            id={`create-${feature.slug}`}
                                            checked={newPlan.features?.includes(feature.slug) || false}
                                            onCheckedChange={(checked) => {
                                                const currentFeatures = newPlan.features || []
                                                if (checked) {
                                                    setNewPlan({
                                                        ...newPlan,
                                                        features: [...currentFeatures, feature.slug],
                                                    })
                                                } else {
                                                    setNewPlan({
                                                        ...newPlan,
                                                        features: currentFeatures.filter((f) => f !== feature.slug),
                                                    })
                                                }
                                            }}
                                        />
                                        <label
                                            htmlFor={`create-${feature.slug}`}
                                            className="text-sm cursor-pointer leading-tight"
                                        >
                                            <span className="font-medium">{feature.name}</span>
                                            <p className="text-xs text-slate-500">{feature.description}</p>
                                        </label>
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-slate-500 mt-2">
                                {newPlan.features?.length || 0} features selected
                            </p>
                        </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-4 border-t">
                        <Button
                            variant="outline"
                            onClick={() => {
                                setIsCreating(false)
                                setNewPlan(emptyPlan)
                            }}
                            disabled={isSaving}
                        >
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                        </Button>
                        <Button onClick={handleCreatePlan} disabled={isSaving}>
                            {isSaving ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Plus className="h-4 w-4 mr-2" />
                                    Create Plan
                                </>
                            )}
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!deletingPlan} onOpenChange={() => setDeletingPlan(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Plan</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete the &quot;{deletingPlan?.name}&quot; plan?
                            This action cannot be undone. Users subscribed to this plan may be affected.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isSaving}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDeletePlan}
                            disabled={isSaving}
                            className="bg-red-600 hover:bg-red-700"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Deleting...
                                </>
                            ) : (
                                "Delete"
                            )}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </ConfigFormWrapper>
    )
}
