"use client"

import { useState } from "react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
    ArrowUpCircle,
    ArrowDownCircle,
    Clock,
    Calendar,
    CreditCard,
    User,
    CheckCircle2,
    XCircle,
    AlertCircle,
    PauseCircle,
    Loader2,
} from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { AdminSubscription } from "@/types/admin"
import { useToast } from "@/components/ui/toast"


interface SubscriptionDetailModalProps {
    subscription: AdminSubscription | null
    isOpen: boolean
    onClose: () => void
    onUpdated: () => void
}

const statusConfig: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
    active: {
        color: "text-emerald-600 dark:text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        icon: <CheckCircle2 className="h-4 w-4" />,
        label: "Active",
    },
    canceled: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        icon: <XCircle className="h-4 w-4" />,
        label: "Canceled",
    },
    past_due: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        icon: <AlertCircle className="h-4 w-4" />,
        label: "Past Due",
    },
    trialing: {
        color: "text-blue-600 dark:text-blue-400",
        bg: "bg-blue-500/10 border-blue-500/20",
        icon: <Clock className="h-4 w-4" />,
        label: "Trial",
    },
    paused: {
        color: "text-slate-600 dark:text-slate-400",
        bg: "bg-slate-500/10 border-slate-500/20",
        icon: <PauseCircle className="h-4 w-4" />,
        label: "Paused",
    },
}

const planHierarchy = ["free", "starter", "professional", "enterprise"]

export function SubscriptionDetailModal({
    subscription,
    isOpen,
    onClose,
    onUpdated,
}: SubscriptionDetailModalProps) {
    const { addToast } = useToast()
    const [activeTab, setActiveTab] = useState("details")
    const [isLoading, setIsLoading] = useState(false)

    // Upgrade/Downgrade state
    const [selectedPlan, setSelectedPlan] = useState("")
    const [planChangeReason, setPlanChangeReason] = useState("")

    // Extend state
    const [extendDays, setExtendDays] = useState("")
    const [extendReason, setExtendReason] = useState("")

    if (!subscription) return null

    const statusCfg = statusConfig[subscription.status] || statusConfig.active
    const currentPlanIndex = planHierarchy.indexOf(subscription.plan_tier.toLowerCase())

    const handleUpgrade = async () => {
        if (!selectedPlan || !subscription) return
        setIsLoading(true)
        try {
            await adminApi.upgradeSubscription(subscription.id, {
                new_plan: selectedPlan,
                reason: planChangeReason || undefined,
            })
            addToast({
                type: "success",
                title: "Subscription upgraded",
                description: `Successfully upgraded to ${selectedPlan} plan`,
            })
            onUpdated()
            setSelectedPlan("")
            setPlanChangeReason("")
            setActiveTab("details")
        } catch (err) {
            console.error("Failed to upgrade subscription:", err)
            addToast({
                type: "error",
                title: "Upgrade failed",
                description: "Failed to upgrade subscription. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleDowngrade = async () => {
        if (!selectedPlan || !subscription) return
        setIsLoading(true)
        try {
            await adminApi.downgradeSubscription(subscription.id, {
                new_plan: selectedPlan,
                reason: planChangeReason || undefined,
            })
            addToast({
                type: "success",
                title: "Subscription downgraded",
                description: `Successfully downgraded to ${selectedPlan} plan`,
            })
            onUpdated()
            setSelectedPlan("")
            setPlanChangeReason("")
            setActiveTab("details")
        } catch (err) {
            console.error("Failed to downgrade subscription:", err)
            addToast({
                type: "error",
                title: "Downgrade failed",
                description: "Failed to downgrade subscription. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleExtend = async () => {
        if (!extendDays || !subscription) return
        const days = parseInt(extendDays)
        if (isNaN(days) || days < 1 || days > 365) {
            addToast({
                type: "error",
                title: "Invalid days",
                description: "Please enter a valid number of days (1-365)",
            })
            return
        }
        setIsLoading(true)
        try {
            await adminApi.extendSubscription(subscription.id, {
                days,
                reason: extendReason || undefined,
            })
            addToast({
                type: "success",
                title: "Subscription extended",
                description: `Successfully extended by ${days} days`,
            })
            onUpdated()
            setExtendDays("")
            setExtendReason("")
            setActiveTab("details")
        } catch (err) {
            console.error("Failed to extend subscription:", err)
            addToast({
                type: "error",
                title: "Extension failed",
                description: "Failed to extend subscription. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const getUpgradePlans = () => {
        return planHierarchy.slice(currentPlanIndex + 1)
    }

    const getDowngradePlans = () => {
        return planHierarchy.slice(0, currentPlanIndex)
    }


    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
                            {(subscription.user_name || subscription.user_email || "U").charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <span>{subscription.user_name || "Unknown User"}</span>
                            <p className="text-sm font-normal text-muted-foreground">{subscription.user_email}</p>
                        </div>
                    </DialogTitle>
                    <DialogDescription>
                        Manage subscription details, upgrade/downgrade plans, or extend the subscription period.
                    </DialogDescription>
                </DialogHeader>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="details">Details</TabsTrigger>
                        <TabsTrigger value="upgrade">Upgrade</TabsTrigger>
                        <TabsTrigger value="downgrade">Downgrade</TabsTrigger>
                        <TabsTrigger value="extend">Extend</TabsTrigger>
                    </TabsList>

                    {/* Details Tab */}
                    <TabsContent value="details" className="space-y-4 mt-4">
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base flex items-center gap-2">
                                    <CreditCard className="h-4 w-4" />
                                    Subscription Info
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="grid gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Plan</Label>
                                        <p className="font-semibold capitalize">{subscription.plan_tier}</p>
                                    </div>
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Status</Label>
                                        <Badge
                                            variant="outline"
                                            className={cn(
                                                "gap-1.5 font-medium mt-1",
                                                statusCfg.bg,
                                                statusCfg.color
                                            )}
                                        >
                                            {statusCfg.icon}
                                            {statusCfg.label}
                                        </Badge>
                                    </div>
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Billing Cycle</Label>
                                        <p className="font-semibold capitalize">{subscription.billing_cycle}</p>
                                    </div>
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Cancel at Period End</Label>
                                        <p className="font-semibold">{subscription.cancel_at_period_end ? "Yes" : "No"}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base flex items-center gap-2">
                                    <Calendar className="h-4 w-4" />
                                    Billing Period
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="grid gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Period Start</Label>
                                        <p className="font-semibold">{format(new Date(subscription.current_period_start), "PPP")}</p>
                                    </div>
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Period End</Label>
                                        <p className="font-semibold">{format(new Date(subscription.current_period_end), "PPP")}</p>
                                    </div>
                                    <div>
                                        <Label className="text-muted-foreground text-xs">Created</Label>
                                        <p className="font-semibold">{format(new Date(subscription.created_at), "PPP")}</p>
                                    </div>
                                    {subscription.canceled_at && (
                                        <div>
                                            <Label className="text-muted-foreground text-xs">Canceled At</Label>
                                            <p className="font-semibold text-red-600">{format(new Date(subscription.canceled_at), "PPP")}</p>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>


                    {/* Upgrade Tab */}
                    <TabsContent value="upgrade" className="space-y-4 mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <ArrowUpCircle className="h-4 w-4 text-emerald-500" />
                                    Upgrade Subscription
                                </CardTitle>
                                <CardDescription>
                                    Upgrade to a higher plan. Prorated billing will be applied.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Current Plan</Label>
                                    <p className="text-lg font-semibold capitalize">{subscription.plan_tier}</p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="upgrade-plan">New Plan</Label>
                                    <Select value={selectedPlan} onValueChange={setSelectedPlan}>
                                        <SelectTrigger id="upgrade-plan">
                                            <SelectValue placeholder="Select a plan to upgrade to" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {getUpgradePlans().map((plan) => (
                                                <SelectItem key={plan} value={plan} className="capitalize">
                                                    {plan}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    {getUpgradePlans().length === 0 && (
                                        <p className="text-sm text-muted-foreground">Already on the highest plan</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="upgrade-reason">Reason (optional)</Label>
                                    <Textarea
                                        id="upgrade-reason"
                                        placeholder="Enter reason for upgrade..."
                                        value={planChangeReason}
                                        onChange={(e) => setPlanChangeReason(e.target.value)}
                                        rows={3}
                                    />
                                </div>

                                <Button
                                    onClick={handleUpgrade}
                                    disabled={!selectedPlan || isLoading || getUpgradePlans().length === 0}
                                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Upgrading...
                                        </>
                                    ) : (
                                        <>
                                            <ArrowUpCircle className="h-4 w-4 mr-2" />
                                            Upgrade to {selectedPlan || "..."}
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Downgrade Tab */}
                    <TabsContent value="downgrade" className="space-y-4 mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <ArrowDownCircle className="h-4 w-4 text-amber-500" />
                                    Downgrade Subscription
                                </CardTitle>
                                <CardDescription>
                                    Downgrade to a lower plan. Prorated credit will be applied.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Current Plan</Label>
                                    <p className="text-lg font-semibold capitalize">{subscription.plan_tier}</p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="downgrade-plan">New Plan</Label>
                                    <Select value={selectedPlan} onValueChange={setSelectedPlan}>
                                        <SelectTrigger id="downgrade-plan">
                                            <SelectValue placeholder="Select a plan to downgrade to" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {getDowngradePlans().map((plan) => (
                                                <SelectItem key={plan} value={plan} className="capitalize">
                                                    {plan}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    {getDowngradePlans().length === 0 && (
                                        <p className="text-sm text-muted-foreground">Already on the lowest plan</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="downgrade-reason">Reason (optional)</Label>
                                    <Textarea
                                        id="downgrade-reason"
                                        placeholder="Enter reason for downgrade..."
                                        value={planChangeReason}
                                        onChange={(e) => setPlanChangeReason(e.target.value)}
                                        rows={3}
                                    />
                                </div>

                                <Button
                                    onClick={handleDowngrade}
                                    disabled={!selectedPlan || isLoading || getDowngradePlans().length === 0}
                                    variant="outline"
                                    className="w-full border-amber-500 text-amber-600 hover:bg-amber-50"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Downgrading...
                                        </>
                                    ) : (
                                        <>
                                            <ArrowDownCircle className="h-4 w-4 mr-2" />
                                            Downgrade to {selectedPlan || "..."}
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </TabsContent>


                    {/* Extend Tab */}
                    <TabsContent value="extend" className="space-y-4 mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <Clock className="h-4 w-4 text-blue-500" />
                                    Extend Subscription
                                </CardTitle>
                                <CardDescription>
                                    Add days to the current subscription period without additional charge.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Current Period End</Label>
                                    <p className="text-lg font-semibold">{format(new Date(subscription.current_period_end), "PPP")}</p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="extend-days">Days to Add</Label>
                                    <Input
                                        id="extend-days"
                                        type="number"
                                        min="1"
                                        max="365"
                                        placeholder="Enter number of days (1-365)"
                                        value={extendDays}
                                        onChange={(e) => setExtendDays(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="extend-reason">Reason (optional)</Label>
                                    <Textarea
                                        id="extend-reason"
                                        placeholder="Enter reason for extension..."
                                        value={extendReason}
                                        onChange={(e) => setExtendReason(e.target.value)}
                                        rows={3}
                                    />
                                </div>

                                {extendDays && parseInt(extendDays) > 0 && (
                                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                        <p className="text-sm text-blue-700 dark:text-blue-300">
                                            New period end date will be:{" "}
                                            <span className="font-semibold">
                                                {format(
                                                    new Date(new Date(subscription.current_period_end).getTime() + parseInt(extendDays) * 24 * 60 * 60 * 1000),
                                                    "PPP"
                                                )}
                                            </span>
                                        </p>
                                    </div>
                                )}

                                <Button
                                    onClick={handleExtend}
                                    disabled={!extendDays || isLoading}
                                    className="w-full bg-blue-600 hover:bg-blue-700"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Extending...
                                        </>
                                    ) : (
                                        <>
                                            <Clock className="h-4 w-4 mr-2" />
                                            Extend by {extendDays || "..."} days
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    )
}
