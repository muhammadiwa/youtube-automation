"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
    Flag,
    Edit2,
    X,
    Save,
    Loader2,
    CheckCircle,
    XCircle,
    Users,
    Percent,
    CreditCard,
    Search,
} from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/components/ui/toast"
import { configApi, type FeatureFlag } from "@/lib/api/admin"

// Available plans for targeting
const AVAILABLE_PLANS = [
    { id: "free", name: "Free" },
    { id: "starter", name: "Starter" },
    { id: "professional", name: "Professional" },
    { id: "enterprise", name: "Enterprise" },
]

const defaultFlags: FeatureFlag[] = [
    {
        flag_name: "ai_title_generation",
        description: "AI-powered title generation for videos",
        is_enabled: true,
        enabled_for_plans: ["professional", "enterprise"],
        enabled_for_users: [],
        rollout_percentage: 100,
    },
    {
        flag_name: "competitor_analysis",
        description: "Competitor channel analysis feature",
        is_enabled: false,
        enabled_for_plans: ["enterprise"],
        enabled_for_users: [],
        rollout_percentage: 0,
    },
]

export default function FeatureFlagsPage() {
    const [flags, setFlags] = useState<FeatureFlag[]>(defaultFlags)
    const [isLoading, setIsLoading] = useState(true)
    const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null)
    const [isSaving, setIsSaving] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const { addToast } = useToast()

    const fetchFlags = useCallback(async () => {
        try {
            const data = await configApi.getFeatureFlags()
            setFlags(data.flags)
        } catch (error) {
            console.error("Failed to fetch feature flags:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchFlags()
    }, [fetchFlags])

    const handleSaveFlag = async () => {
        if (!editingFlag) return
        setIsSaving(true)
        try {
            await configApi.updateFeatureFlag(editingFlag.flag_name, editingFlag)
            setFlags((prev) =>
                prev.map((f) =>
                    f.flag_name === editingFlag.flag_name ? editingFlag : f
                )
            )
            setEditingFlag(null)
            addToast({
                type: "success",
                title: "Feature flag updated",
                description: `${editingFlag.flag_name} has been updated successfully.`,
            })
        } catch (error) {
            console.error("Failed to update feature flag:", error)
            addToast({
                type: "error",
                title: "Failed to update",
                description: "An error occurred while updating the feature flag.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    const handleQuickToggle = async (flag: FeatureFlag) => {
        const updatedFlag = { ...flag, is_enabled: !flag.is_enabled }
        try {
            await configApi.updateFeatureFlag(flag.flag_name, { is_enabled: updatedFlag.is_enabled })
            setFlags((prev) =>
                prev.map((f) =>
                    f.flag_name === flag.flag_name ? updatedFlag : f
                )
            )
            addToast({
                type: "success",
                title: updatedFlag.is_enabled ? "Feature enabled" : "Feature disabled",
                description: `${flag.flag_name} has been ${updatedFlag.is_enabled ? "enabled" : "disabled"}.`,
            })
        } catch (error) {
            console.error("Failed to toggle feature flag:", error)
            addToast({
                type: "error",
                title: "Failed to update",
                description: "An error occurred while toggling the feature flag.",
            })
        }
    }

    const updateEditingFlag = <K extends keyof FeatureFlag>(
        key: K,
        value: FeatureFlag[K]
    ) => {
        if (!editingFlag) return
        setEditingFlag((prev) => (prev ? { ...prev, [key]: value } : null))
    }

    const togglePlanForFlag = (planId: string) => {
        if (!editingFlag) return
        const currentPlans = editingFlag.enabled_for_plans
        const newPlans = currentPlans.includes(planId)
            ? currentPlans.filter((p) => p !== planId)
            : [...currentPlans, planId]
        updateEditingFlag("enabled_for_plans", newPlans)
    }

    const filteredFlags = flags.filter(
        (flag) =>
            flag.flag_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            flag.description.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const getRolloutBadgeColor = (percentage: number) => {
        if (percentage === 0) return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
        if (percentage < 50) return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
        if (percentage < 100) return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
        return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
    }

    return (
        <ConfigFormWrapper
            title="Feature Flags"
            description="Manage feature flags to control feature rollout and access."
            icon={<Flag className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={async () => { }}
            onReset={() => { }}
            isDirty={false}
            isLoading={isLoading}
        >
            <div className="space-y-4">
                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        placeholder="Search feature flags..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Flag List */}
                <div className="space-y-3">
                    {filteredFlags.map((flag) => (
                        <motion.div
                            key={flag.flag_name}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card className={!flag.is_enabled ? "opacity-70" : ""}>
                                <CardHeader className="pb-2">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <Switch
                                                checked={flag.is_enabled}
                                                onCheckedChange={() => handleQuickToggle(flag)}
                                            />
                                            <div>
                                                <CardTitle className="text-base font-mono">
                                                    {flag.flag_name}
                                                </CardTitle>
                                                <p className="text-sm text-slate-500 mt-0.5">
                                                    {flag.description}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {flag.is_enabled ? (
                                                <Badge variant="outline" className="text-green-600 border-green-200">
                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                    Enabled
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="text-slate-500">
                                                    <XCircle className="h-3 w-3 mr-1" />
                                                    Disabled
                                                </Badge>
                                            )}
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setEditingFlag(flag)}
                                            >
                                                <Edit2 className="h-4 w-4 mr-1" />
                                                Configure
                                            </Button>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex flex-wrap items-center gap-4 text-sm">
                                        {/* Rollout Percentage */}
                                        <div className="flex items-center gap-2">
                                            <Percent className="h-4 w-4 text-slate-400" />
                                            <Badge className={getRolloutBadgeColor(flag.rollout_percentage)}>
                                                {flag.rollout_percentage}% rollout
                                            </Badge>
                                        </div>

                                        {/* Plan Targeting */}
                                        {flag.enabled_for_plans.length > 0 && (
                                            <div className="flex items-center gap-2">
                                                <CreditCard className="h-4 w-4 text-slate-400" />
                                                <div className="flex flex-wrap gap-1">
                                                    {flag.enabled_for_plans.map((plan) => (
                                                        <Badge key={plan} variant="secondary" className="text-xs">
                                                            {plan}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Beta Users */}
                                        {flag.enabled_for_users.length > 0 && (
                                            <div className="flex items-center gap-2">
                                                <Users className="h-4 w-4 text-slate-400" />
                                                <span className="text-slate-600 dark:text-slate-400">
                                                    {flag.enabled_for_users.length} beta user(s)
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}

                    {filteredFlags.length === 0 && (
                        <div className="text-center py-8 text-slate-500">
                            No feature flags found matching your search.
                        </div>
                    )}
                </div>
            </div>


            {/* Edit Flag Dialog */}
            <AnimatePresence>
                {editingFlag && (
                    <Dialog open={!!editingFlag} onOpenChange={() => setEditingFlag(null)}>
                        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
                            <DialogHeader>
                                <DialogTitle className="font-mono">{editingFlag.flag_name}</DialogTitle>
                                <DialogDescription>
                                    Configure feature flag settings, rollout percentage, and plan targeting.
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-6 py-4">
                                {/* Global Enable/Disable */}
                                <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                    <div>
                                        <Label className="text-base">Global Status</Label>
                                        <p className="text-sm text-slate-500">
                                            Enable or disable this feature globally
                                        </p>
                                    </div>
                                    <Switch
                                        checked={editingFlag.is_enabled}
                                        onCheckedChange={(checked) =>
                                            updateEditingFlag("is_enabled", checked)
                                        }
                                    />
                                </div>

                                {/* Description */}
                                <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                        value={editingFlag.description}
                                        onChange={(e) =>
                                            updateEditingFlag("description", e.target.value)
                                        }
                                        placeholder="Describe what this feature does..."
                                        rows={2}
                                    />
                                </div>

                                <Separator />

                                {/* Rollout Percentage */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <Label className="text-base flex items-center gap-2">
                                                <Percent className="h-4 w-4" />
                                                Rollout Percentage
                                            </Label>
                                            <p className="text-sm text-slate-500">
                                                Gradually roll out to a percentage of users
                                            </p>
                                        </div>
                                        <Badge className={getRolloutBadgeColor(editingFlag.rollout_percentage)}>
                                            {editingFlag.rollout_percentage}%
                                        </Badge>
                                    </div>
                                    <Slider
                                        value={[editingFlag.rollout_percentage]}
                                        onValueChange={(value) =>
                                            updateEditingFlag("rollout_percentage", value[0])
                                        }
                                        max={100}
                                        step={5}
                                        className="w-full"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>0%</span>
                                        <span>25%</span>
                                        <span>50%</span>
                                        <span>75%</span>
                                        <span>100%</span>
                                    </div>
                                </div>

                                <Separator />

                                {/* Plan Targeting */}
                                <div className="space-y-4">
                                    <div>
                                        <Label className="text-base flex items-center gap-2">
                                            <CreditCard className="h-4 w-4" />
                                            Plan Targeting
                                        </Label>
                                        <p className="text-sm text-slate-500">
                                            Select which plans have access to this feature
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        {AVAILABLE_PLANS.map((plan) => (
                                            <div
                                                key={plan.id}
                                                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${editingFlag.enabled_for_plans.includes(plan.id)
                                                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                                        : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                                                    }`}
                                                onClick={() => togglePlanForFlag(plan.id)}
                                            >
                                                <Checkbox
                                                    checked={editingFlag.enabled_for_plans.includes(plan.id)}
                                                    onCheckedChange={() => togglePlanForFlag(plan.id)}
                                                />
                                                <span className="font-medium">{plan.name}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <Separator />

                                {/* Beta Users */}
                                <div className="space-y-4">
                                    <div>
                                        <Label className="text-base flex items-center gap-2">
                                            <Users className="h-4 w-4" />
                                            Beta Users
                                        </Label>
                                        <p className="text-sm text-slate-500">
                                            Add specific user IDs for beta testing (comma-separated)
                                        </p>
                                    </div>
                                    <Textarea
                                        value={editingFlag.enabled_for_users.join(", ")}
                                        onChange={(e) => {
                                            const users = e.target.value
                                                .split(",")
                                                .map((u) => u.trim())
                                                .filter((u) => u.length > 0)
                                            updateEditingFlag("enabled_for_users", users)
                                        }}
                                        placeholder="user-id-1, user-id-2, user-id-3"
                                        rows={2}
                                    />
                                    {editingFlag.enabled_for_users.length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                            {editingFlag.enabled_for_users.map((userId) => (
                                                <Badge key={userId} variant="secondary" className="text-xs">
                                                    {userId}
                                                </Badge>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-4 border-t">
                                <Button
                                    variant="outline"
                                    onClick={() => setEditingFlag(null)}
                                    disabled={isSaving}
                                >
                                    <X className="h-4 w-4 mr-2" />
                                    Cancel
                                </Button>
                                <Button onClick={handleSaveFlag} disabled={isSaving}>
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
